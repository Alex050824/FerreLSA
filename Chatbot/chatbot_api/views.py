import json
import logging
import re
import unicodedata
from time import perf_counter

from django.db import DatabaseError, connection
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_GET, require_POST


logger = logging.getLogger(__name__)
LIMITE_LISTADO = 6


def obtener_productos():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT codigo, nombre, descripcion, precio_venta, existencia, unidad_medida
            FROM productos
            WHERE activo = 1
            ORDER BY nombre, codigo
        """)
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


def _palabras(pregunta):
    texto = unicodedata.normalize("NFKD", pregunta.casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return set(re.findall(r"\w+", texto))


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


def consultar_catalogo(pregunta):
    inicio = perf_counter()
    catalogo = obtener_productos()
    leido = perf_counter()
    palabras = _palabras(pregunta)
    listado = _es_listado(palabras)
    if listado:
        disponibles = [fila for fila in catalogo if fila[4] is not None and fila[4] > 0]
        seleccion = disponibles[:LIMITE_LISTADO]
    elif catalogo:
        from .busqueda_semantica import buscar_productos

        seleccion = [fila for fila, _ in buscar_productos(pregunta, productos=catalogo)]
    else:
        seleccion = []
    buscado = perf_counter()

    if seleccion:
        from .modelo_qwen import generar_explicacion

        consulta_comercial = bool(palabras & {
            "cuesta", "cuestan", "precio", "precios", "vale", "valen", "stock",
            "existencia", "existencias", "disponible", "disponibles", "quedan",
        })
        pide_detalles = bool(palabras & {
            "caracteristicas", "descripcion", "especificaciones", "sirve", "uso", "para",
        })
        incluir_descripcion = not listado and (pide_detalles or not consulta_comercial)
        explicacion = generar_explicacion(pregunta, seleccion[:3], incluir_descripcion=incluir_descripcion)
    generado = perf_counter()

    if seleccion:
        lineas = [explicacion, *(_linea_producto(fila) for fila in seleccion)]
        if listado and len(disponibles) > len(seleccion):
            lineas.append(f"Te muestro {len(seleccion)} de {len(disponibles)} productos disponibles. "
                          "Podés pedirme un artículo por nombre o por uso.")
        respuesta = "\n".join(lineas)
    elif listado:
        respuesta = "En este momento no hay productos con existencias disponibles en el catálogo."
    else:
        respuesta = ("No encontré una coincidencia clara en el catálogo de FerreLSA. "
                     "¿Me indicás el nombre del artículo o para qué lo necesitás?")

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
    try:
        resultado = consultar_catalogo(pregunta.strip())
    except DatabaseError:
        logger.exception("No se pudo consultar el catálogo del chatbot")
        return JsonResponse({"error": "No pude consultar el inventario en este momento."}, status=503)
    except (OSError, RuntimeError):
        logger.exception("Fallo de inferencia del chatbot")
        return JsonResponse({"error": "El asistente no está disponible en este momento."}, status=503)
    return JsonResponse(resultado)


@require_GET
@ensure_csrf_cookie
def iniciar_csrf(request):
    return JsonResponse({"mensaje": "CSRF listo"})
