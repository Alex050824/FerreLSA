import json
import logging
import re
from time import perf_counter
from urllib.parse import quote, unquote

from django.conf import settings
from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST

from .conversacion import campos_solicitados, es_orientacion_general, es_seguimiento, interpretar_social, normalizar, pedir_orientacion

logger = logging.getLogger(__name__)
LIMITE_LISTADO = 6
_DURACION_CONTEXTO = 15 * 60
_RUTA_CHAT = "/api/chatbot/"


def obtener_productos(codigo=None):
    with connection.cursor() as cursor:
        consulta = """
            SELECT codigo, nombre, descripcion, precio_venta, existencia, unidad_medida
            FROM productos
            WHERE activo = 1
        """
        if codigo is None:
            cursor.execute(consulta + " ORDER BY nombre, codigo")
        else:
            cursor.execute(consulta + " AND codigo = %s", [codigo])
        return cursor.fetchall()


# Solo una petición genérica abre el listado. Un material, tarea o nombre
# adicional ("productos para carpintería") debe pasar por el buscador.
_VOCABULARIO_LISTADO = set("""
    a al actualmente algun algunos articulos catalogo cual cuales
    cuentan de del disponible disponibles el en ensena ensename
    esta estan existencia existencias ferrelsa hay hola inventario la las lista
    listado lo los me mercaderia mostrar mostrame muestrame muestre ofrecen
    ahora para por favor podria podrias producto productos que quiero quisiera saber
    se son stock su sus tenes tienen tienda todo todos tu un una ver venden venta y
""".split())


def _es_listado(palabras):
    return palabras <= _VOCABULARIO_LISTADO and bool(palabras & {
        "productos", "articulos", "catalogo", "inventario", "stock", "existencias",
        "venden", "disponible", "disponibles", "ofrecen", "mercaderia",
    })


def _numero_local(valor, agrupar=False):
    entero, _, fraccion = format(valor, "f").partition(".")
    fraccion = fraccion.rstrip("0")
    if agrupar:
        entero = f"{int(entero):,}".replace(",", ".")
        if fraccion:
            fraccion = fraccion.ljust(2, "0")
    return entero + ("," + fraccion if fraccion else "")


def _ficha(fila):
    codigo, nombre, descripcion, precio, existencia, unidad = fila
    return {
        "codigo": codigo, "nombre": nombre, "descripcion": descripcion,
        "precio_venta": format(precio, "f") if precio is not None else None,
        "moneda": "CRC",
        "existencia": _numero_local(existencia).replace(",", ".") if existencia is not None else None,
        "unidad_medida": unidad,
    }


def _linea_producto(fila):
    _, nombre, _, precio, existencia, unidad = fila
    importe = "Precio sin registrar" if precio is None else "₡" + _numero_local(precio, True)
    if existencia is None:
        stock = "Existencia sin registrar"
    elif existencia <= 0:
        stock = "Agotado"
    else:
        cantidad = _numero_local(existencia)
        if (unidad or "").casefold() == "unidad":
            stock = f"{cantidad} {'unidad' if existencia == 1 else 'unidades'}"
        elif unidad:
            stock = f"Existencia ({unidad}): {cantidad}"
        else:
            stock = f"Existencia: {cantidad}"
    return f"{nombre} — {importe} · {stock}."


def _respuesta_breve(mensaje):
    return {
        "respuesta": mensaje,
        "productos": [],
        "tiempos_ms": {"catalogo": 0, "busqueda": 0, "generacion": 0, "total": 0},
    }


def consultar_catalogo(pregunta):
    resultado, _ = _conversar(pregunta)
    return resultado


def _conversar(pregunta, anterior=None):
    pregunta, mensaje, despedida = interpretar_social(pregunta)
    if mensaje:
        return _respuesta_breve(mensaje), None if despedida else anterior
    texto = normalizar(pregunta)
    orientacion = pedir_orientacion(texto)
    if orientacion:
        return _respuesta_breve(orientacion), None
    palabras = set(texto.split())
    seguimiento = es_seguimiento(texto)
    if seguimiento and anterior is None and not _es_listado(palabras):
        return _respuesta_breve("¿De cuál producto querés saber? Decime el nombre o el código."), None
    if seguimiento and anterior and re.fullmatch(r"(?:(?:me|nos) )?(?:sirve|funciona) para [a-z0-9 ]{1,120}", texto.removeprefix("y ").removeprefix("entonces ")):
        filas = obtener_productos(anterior)
        if not filas:
            return _respuesta_breve("Ya no encuentro ese producto en el catálogo activo. ¿Qué otro artículo querés consultar?"), None
        fila = filas[0]
        descripcion = (fila[2] or "").strip()
        respuesta = f"No puedo confirmar esa compatibilidad de {fila[1]} con la información disponible."
        if descripcion:
            respuesta += f" La ficha indica: {descripcion}"
        respuesta += " Consultá la ficha técnica o las indicaciones del fabricante antes de usarlo."
        resultado = _respuesta_breve(respuesta)
        resultado["productos"] = [_ficha(fila)]
        return resultado, anterior
    if not seguimiento and es_orientacion_general(pregunta):
        from .orientacion import orientar

        respuesta = orientar(pregunta)
        if not respuesta:
            respuesta = "Para orientarte mejor, contame qué trabajo querés hacer y en qué superficie o material vas a trabajar."
        return _respuesta_breve(respuesta), anterior
    resultado = _consultar_productos(pregunta, palabras, anterior if seguimiento else None)
    fichas = resultado["productos"]
    codigo = str(fichas[0]["codigo"]) if len(fichas) == 1 else None
    return resultado, codigo


def _consultar_productos(pregunta, palabras, codigo):
    inicio = perf_counter()
    catalogo = obtener_productos(codigo)
    leido = perf_counter()
    listado = codigo is None and _es_listado(palabras)
    if codigo is not None:
        seleccion = [fila for fila in catalogo if str(fila[0]) == codigo]
    elif listado:
        disponibles = [fila for fila in catalogo if fila[4] is not None and fila[4] > 0]
        seleccion = disponibles[:LIMITE_LISTADO]
    elif catalogo:
        from .busqueda_semantica import buscar_productos

        seleccion = [fila for fila, _ in buscar_productos(pregunta, productos=catalogo)]
    else:
        seleccion = []
    buscado = perf_counter()


    if seleccion:
        from .busqueda_semantica import coincidencias_nombre

        campos = campos_solicitados(normalizar(pregunta))
        pide_precio = "precio" in campos
        pide_cantidad = "cantidad" in campos
        pide_disponibilidad = "disponibilidad" in campos
        pide_detalles = "descripcion" in campos
        ficha_completa = "completa" in campos
        # «Duchas» o «¿y duchas?» consulta otro artículo, no una tarea.
        # En nombres como «llave para fregadero», «para» forma parte del nombre.
        es_uso = "recomendacion" in campos and not coincidencias_nombre(pregunta, seleccion)
        if not (pide_precio or pide_cantidad or pide_disponibilidad or pide_detalles or ficha_completa or es_uso):
            pide_disponibilidad = True

        lineas = []

        if listado:
            lineas = [f"• {fila[1]}" for fila in seleccion]

            if len(disponibles) > len(seleccion):
                lineas.append(
                    f"Te muestro {len(seleccion)} de "
                    f"{len(disponibles)} productos disponibles."
                )

        else:
            consulta_comercial = (
                pide_precio or pide_cantidad or pide_disponibilidad
            )

            if pide_detalles or ficha_completa or es_uso:
                from .modelo_qwen import generar_explicacion

                explicacion = generar_explicacion(
                    pregunta,
                    seleccion[:3],
                    incluir_descripcion=True
                )

                lineas.append(explicacion)

            for fila in seleccion:
                nombre = fila[1]

                if ficha_completa:
                    lineas.append(_linea_producto(fila))
                    continue

                if not consulta_comercial:
                    continue

                # Reutilizar los formatos existentes de MySQL.
                datos = _linea_producto(fila).partition(" — ")[2]
                precio, _, existencia = datos.partition(" · ")
                existencia = existencia.removesuffix(".")

                if pide_precio and pide_cantidad:
                    lineas.append(
                        f"{nombre} cuesta {precio}. {existencia}."
                    )

                elif pide_precio:
                    lineas.append(f"{nombre} cuesta {precio}.")
                    if pide_disponibilidad:
                        if fila[4] is None:
                            lineas.append(f"No tengo la disponibilidad registrada de {nombre}.")
                        elif fila[4] > 0:
                            lineas.append(f"Sí, tenemos {nombre} disponible.")
                        else:
                            lineas.append(f"Por ahora {nombre} está agotado.")

                elif pide_cantidad:
                    lineas.append(f"{nombre}: {existencia}.")

                elif pide_disponibilidad:
                    if fila[4] is None:
                        lineas.append(
                            f"No tengo la disponibilidad registrada de {nombre}."
                        )
                    elif fila[4] > 0:
                        lineas.append(f"Sí, tenemos {nombre} disponible.")
                    else:
                        lineas.append(f"Por ahora {nombre} está agotado.")

        respuesta = "\n".join(lineas)

    elif codigo is not None:
        respuesta = (
            "Ya no encuentro ese producto en el catálogo activo. "
            "¿Qué otro artículo querés consultar?"
        )

    elif listado:
        respuesta = (
            "En este momento no hay productos con existencias "
            "disponibles en el catálogo."
        )

    else:
        respuesta = (
            "No encontré una coincidencia clara en el catálogo. "
            "Puedo ayudarte con productos, precios y existencias. "
            "¿Qué artículo buscás o para qué lo necesitás?"
        )

    generado = perf_counter()


    fichas = [_ficha(fila) for fila in seleccion]
    return {
        "respuesta": respuesta,
        "productos": fichas,
        "tiempos_ms": {
            "catalogo": round((leido - inicio) * 1000, 1),
            "busqueda": round((buscado - leido) * 1000, 1),
            "generacion": round((generado - buscado) * 1000, 1),
            "total": round((perf_counter() - inicio) * 1000, 1),
        },
    }


@require_POST
def preguntar_chatbot(request):
    try:
        datos = json.loads(request.body)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"error": "El formato JSON no es válido."}, status=400)
    if not isinstance(datos, dict):
        return JsonResponse({"error": "Se esperaba un objeto JSON."}, status=400)
    pregunta = datos.get("pregunta")
    if not isinstance(pregunta, str) or not pregunta.strip():
        return JsonResponse({"error": "Debe escribir una pregunta."}, status=400)
    if len(pregunta) > 300:
        return JsonResponse({"error": "La pregunta es demasiado larga."}, status=400)
    cookie = "ferrelsa_chat"
    if "conversacion" in datos:
        conversacion = datos["conversacion"]
        if not isinstance(conversacion, str) or not re.fullmatch(r"[0-9a-f]{32}", conversacion):
            return JsonResponse({"error": "El identificador de conversación no es válido."}, status=400)
        cookie += "_" + conversacion
    valor = request.get_signed_cookie(cookie, default=None, max_age=_DURACION_CONTEXTO)
    anterior = unquote(valor) if valor is not None else None
    try:
        resultado, codigo = _conversar(pregunta.strip(), anterior)
    except DatabaseError:
        logger.exception("No se pudo consultar el catálogo del chatbot")
        return JsonResponse({"error": "No pude consultar el inventario en este momento."}, status=503)
    except (OSError, RuntimeError):
        logger.exception("Fallo de inferencia del chatbot")
        return JsonResponse({"error": "El asistente no está disponible en este momento."}, status=503)
    respuesta = JsonResponse(resultado)
    if codigo is not None and codigo != anterior:
        respuesta.set_signed_cookie(cookie, quote(codigo, safe=""), max_age=_DURACION_CONTEXTO,
                                    path=_RUTA_CHAT, httponly=True, samesite="Lax",
                                    secure=request.is_secure() or settings.SESSION_COOKIE_SECURE)
    elif codigo is None and cookie in request.COOKIES:
        respuesta.delete_cookie(cookie, path=_RUTA_CHAT, samesite="Lax")
    return respuesta


@require_GET
@ensure_csrf_cookie
def iniciar_csrf(request):
    return JsonResponse({"mensaje": "CSRF listo"})
