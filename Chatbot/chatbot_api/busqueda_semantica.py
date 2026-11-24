"""Recuperación sobre las filas activas de MySQL. Los vectores solo contienen texto."""

from functools import lru_cache
from threading import Lock
from collections import Counter
import re
import unicodedata


NOMBRE_MODELO = "intfloat/multilingual-e5-small"
_turno_e5 = Lock()

# Palabras funcionales y de consulta comercial. El vocabulario de productos se
# obtiene exclusivamente del catálogo, incluidos sus calificativos y medidas.
_OMITIR = frozenset("""
    a al algo algun alguna algunos algunas articulo articulos comprar compra con
    conoce conoces contar cuanto cuanta cuantas cuantos cuesta cuestan cual cuales
    busco buscaba buscando caracteristica caracteristicas codigo como
    consulta costo costos quisiera
    de del disponible disponibles disponibilidad donde el ella en es esa ese esta
    estan este esto existencia existencias favor ficha fichas hay hola informacion la
    las lo los mas me mi muestra muestran muestrame mostrame necesito nos o ofrece
    ofrecen para por precio precios producto productos podria podrias puedes puede
    que queda quedan queres quiero se seria si sobre son stock su sus te tienen
    tenes teneis tiene tienda un una unas uno unos unidad unidades vale valen vende
    venden vendes venta ver viene y saber descripcion detalles especificacion
    especificaciones tecnico tecnicas comparame comparar compara entre diferencia
    podés podes poder pueden decir decirme decime indicame indicar indicarme indica
    mostrar mostrarme mostras mostrame ensenas ensename ayudarme ayudas ayudar gracias
    buenas buenos dias tardes noches porfa porfavor saludo saluda hola favor
""".split())


def _normalizar(texto):
    descompuesto = unicodedata.normalize("NFKD", str(texto).casefold())
    return "".join(caracter for caracter in descompuesto if not unicodedata.combining(caracter))


def _singular(palabra):
    if len(palabra) > 4:
        if palabra.endswith("ces"):
            return palabra[:-3] + "z"
        if palabra.endswith("es"):
            return palabra[:-2]
        if palabra.endswith(("as", "os")):
            return palabra[:-1]
    return palabra.removesuffix("e") if len(palabra) > 3 else palabra


@lru_cache(maxsize=4096)
def _terminos(texto):
    return frozenset(
        _singular(p) for p in re.findall(r"[a-z]+|[0-9]+", _normalizar(texto))
        if p not in _OMITIR
    )


@lru_cache(maxsize=1)
def cargar_modelo_busqueda():
    from transformers import AutoModel, AutoTokenizer

    for solo_local in (True, False):
        try:
            tokenizador = AutoTokenizer.from_pretrained(NOMBRE_MODELO, local_files_only=solo_local)
            modelo = AutoModel.from_pretrained(NOMBRE_MODELO, local_files_only=solo_local)
            return tokenizador, modelo.eval()
        except OSError:
            if not solo_local:
                raise


def convertir_a_vectores(textos):
    import torch
    from torch.nn.functional import normalize

    tokenizador, modelo = cargar_modelo_busqueda()
    vectores = []
    with torch.inference_mode():
        for inicio in range(0, len(textos), 8):
            entradas = tokenizador(
                textos[inicio:inicio + 8], padding=True, truncation=True,
                max_length=512, return_tensors="pt",
            )
            ocultos = modelo(**entradas).last_hidden_state
            mascara = entradas["attention_mask"].unsqueeze(-1)
            promedios = (ocultos * mascara).sum(dim=1) / mascara.sum(dim=1).clamp(min=1)
            vectores.append(normalize(promedios, p=2, dim=1))
    return torch.cat(vectores, dim=0)


class IndiceCatalogo:
    def __init__(self):
        self.pasajes = ()
        self.vectores = {}
        self.matriz = None

    def actualizar(self, pasajes):
        """Reutiliza incluso un pasaje compartido entre varias presentaciones."""
        import torch

        if self.pasajes == pasajes:
            return self.matriz
        unicos = dict.fromkeys(pasajes)
        nuevos = [texto for texto in unicos if texto not in self.vectores]
        vectores = {texto: self.vectores[texto] for texto in unicos if texto in self.vectores}
        if nuevos:
            lote = convertir_a_vectores(["passage: " + texto for texto in nuevos])
            # Copias independientes para poder liberar productos dados de baja.
            vectores.update((texto, vector.clone()) for texto, vector in zip(nuevos, lote))
        matriz = torch.stack([vectores[texto] for texto in pasajes]) if pasajes else None
        self.pasajes, self.vectores, self.matriz = pasajes, vectores, matriz
        return matriz


_indice = IndiceCatalogo()


@lru_cache(maxsize=128)
def _vector_consulta(consulta):
    return convertir_a_vectores(["query: " + consulta])[0]


def _coincidencias_directas(consulta, productos):
    """Una referencia explícita debe acreditar también modelo, color y otros detalles."""
    seleccion = {}
    for fragmento in re.split(r"\s+(?:y|o|versus|vs)\s+|[,;]", consulta):
        pedidos = _terminos(fragmento)
        if not pedidos:
            continue
        for i, (codigo, nombre, descripcion, *_) in enumerate(productos):
            en_nombre = _terminos(nombre)
            en_ficha = en_nombre | _terminos(descripcion or "")
            if _normalizar(codigo) == fragmento.strip() or pedidos == _terminos(str(codigo)):
                calidad = 3
            elif pedidos <= en_nombre:
                calidad = 2 + len(pedidos) / max(1, len(en_nombre))
            elif pedidos <= en_ficha:
                calidad = 1 + len(pedidos & en_nombre) / len(pedidos)
            else:
                continue
            seleccion[i] = max(calidad, seleccion.get(i, 0))
    return sorted(seleccion.items(), key=lambda par: -par[1])


def _es_tarea(consulta):
    if " para " in consulta:
        # Si pidió un artículo específico, "para ..." aporta una restricción.
        # No convertir la ausencia de ese artículo en una oferta de otro.
        introduccion = consulta.split(" para ", 1)[0]
        genericas = {"herramienta", "material", "opcion", "ideal", "mejor", "usar",
                     "utilizar", "sirv", "serviria", "aconsejas", "recomendacion"}
        if any(p not in genericas and not p.startswith(("recom", "suger"))
               for p in _terminos(introduccion)):
            return False
        return True
    return bool(re.search(
        r"(?:^(?!comprar\b|encontrar\b|conseguir\b)\w{2,}(?:ar|er|ir)\b|"
        r"\b(?:recom\w*|suger\w*|consej\w*|como (?:puedo|se|hago)|con que|"
        r"(?:algo|herramienta|material) (?:que|con que)|se me \w+|hay que|"
        r"(?:necesito|quiero|quisiera|puedo|necesitaria|debo|tengo que|me gustaria) "
        r"(?!comprar\b|encontrar\b|saber\b|conocer\b|conseguir\b)\w+(?:ar|er|ir)\b))",
        consulta,
    ))


def buscar_productos(pregunta, limite=3, *, productos=None):
    """Devuelve (fila SQL actual, puntuación de ranking). El listado se trata en la vista."""
    if not pregunta.strip() or limite <= 0:
        return []
    if productos is None:
        from .views import obtener_productos
        productos = obtener_productos()
    if not productos:
        return []
    consulta = _normalizar(pregunta).strip("¿?¡!. ")
    directas = _coincidencias_directas(consulta, productos)
    if directas:
        return [(productos[i], valor) for i, valor in directas[:limite]]
    if not _es_tarea(consulta):
        return []
    return _buscar_por_uso(pregunta, productos, limite)


def _candidatos_semanticos(pregunta, productos):
    # Nombre y descripción se evalúan por separado: la longitud de una ficha
    # técnica no debe diluir la identidad del producto en el vector.
    campos = tuple((str(fila[1]), str(fila[2] or fila[1])) for fila in productos)
    pasajes = tuple(texto for par in campos for texto in par)
    with _turno_e5:
        matriz = _indice.actualizar(pasajes)
        vector = _vector_consulta(pregunta)
        cosenos = (matriz @ vector).reshape(-1, 2).max(dim=1).values.tolist()
    por_coseno = sorted(range(len(productos)), key=cosenos.__getitem__, reverse=True)

    # Fusión por posición: la semejanza E5 y la coincidencia léxica tienen
    # escalas distintas. Solo las coincidencias reales votan en la segunda lista.
    pedidos = _terminos(pregunta)
    coincidencias = [
        pedidos & (_terminos(nombre) | _terminos(descripcion)) for nombre, descripcion in campos
    ]
    frecuencia = {p: sum(p in conjunto for conjunto in coincidencias) for p in pedidos}
    puntaje_textual = [sum(1 / frecuencia[p] for p in conjunto) for conjunto in coincidencias]
    por_texto = sorted(
        (i for i in range(len(productos)) if coincidencias[i]),
        key=puntaje_textual.__getitem__, reverse=True,
    )
    fusion = {i: 1 / lugar for lugar, i in enumerate(por_coseno, 1)}
    for lugar, i in enumerate(por_texto, 1):
        fusion[i] += 1 / lugar
    return sorted(fusion, key=fusion.__getitem__, reverse=True)[:8]


def _foco(pregunta):
    texto = pregunta.strip("¿?¡!. ")
    if " para " in texto.lower():
        return re.split(r"\bpara\s+", texto, maxsplit=1, flags=re.IGNORECASE)[-1]
    return re.sub(
        r"^(?:necesito|quiero|quisiera|me gustaría|tengo que|hay que|debo)\s+",
        "", texto, flags=re.IGNORECASE,
    )


def _logits_etiquetas(tokenizador, modelo, conversaciones, etiquetas):
    """Puntúa opciones en una sola pasada por lote, sin generar respuestas intermedias."""
    import torch

    entradas = [
        tokenizador.apply_chat_template(
            mensajes, tokenize=True, add_generation_prompt=True, return_dict=True,
        )["input_ids"] for mensajes in conversaciones
    ]
    largo = max(map(len, entradas))
    ids = torch.full((len(entradas), largo), tokenizador.pad_token_id, dtype=torch.long)
    mascara = torch.zeros_like(ids)
    for i, entrada in enumerate(entradas):
        ids[i, -len(entrada):] = torch.as_tensor(entrada)
        mascara[i, -len(entrada):] = 1
    posiciones = (mascara.cumsum(dim=1) - 1).clamp(min=0)
    logits = modelo(input_ids=ids, attention_mask=mascara, position_ids=posiciones,
                    use_cache=False, logits_to_keep=1).logits[:, -1]
    indices = [tokenizador.encode(e, add_special_tokens=False)[0] for e in etiquetas]
    return logits[:, indices].float().tolist()


@lru_cache(maxsize=128)
def _evaluar_uso(pregunta, nombres):
    from .modelo_qwen import usar_qwen

    cantidad = len(nombres)
    letras = "ABCDEFGH"[:cantidad]
    ordenes = [list(range(cantidad))]
    if cantidad > 1:
        ordenes.append(ordenes[0][::-1])
    sistema = ("Identifica la herramienta o material apropiado para la tarea. "
               "Si ninguna opción resuelve la tarea, contesta X. Devuelve solo la letra.")
    conversaciones = []
    for orden in ordenes:
        opciones = [f"{letra}. {nombres[i]}" for letra, i in zip(letras, orden)]
        contenido = "\n".join([pregunta, *opciones, "X. Ninguna de las anteriores"])
        conversaciones.append([{"role": "system", "content": sistema},
                                {"role": "user", "content": contenido}])
    with usar_qwen() as (tokenizador, modelo):
        votos = _logits_etiquetas(tokenizador, modelo, conversaciones, letras + "X")
        diferencias = [[] for _ in nombres]
        for orden, puntajes in zip(ordenes, votos):
            for i, valor in zip(orden, puntajes):
                diferencias[i].append(valor - puntajes[-1])
        mejor = max(range(cantidad), key=lambda i: sum(diferencias[i]))
        if max(diferencias[mejor]) <= 0:
            return None

        # La comparación anterior tiene sesgo por letra/posición en Qwen 0.5B.
        # Exigimos además que un segundo juicio, aislado de las otras opciones,
        # elija el mismo producto. La puntuación de "Sí" sola no sirve de umbral.
        sistema = "Evalúa si el producto sirve directamente para la tarea indicada. Responde Sí o No."
        tarea = _foco(pregunta)
        conversaciones = [
            [{"role": "system", "content": sistema},
             {"role": "user", "content": f"Tarea: {tarea}. Producto: {nombre}. "
                                         "¿Es el producto adecuado para esta tarea?"}]
            for nombre in nombres
        ]
        binarios = _logits_etiquetas(tokenizador, modelo, conversaciones, ("Sí", "No"))
    mejor_binario = max(range(cantidad), key=lambda i: binarios[i][0] - binarios[i][1])
    if mejor != mejor_binario or binarios[mejor][0] <= binarios[mejor][1]:
        return None
    return mejor, max(diferencias[mejor])


def _buscar_por_uso(pregunta, productos, limite):
    candidatos = _candidatos_semanticos(pregunta, productos)
    
    # Para un nombre compartido o un código sin significado, la descripción
    # distingue la aplicación concreta. Solo se agrupan fichas de texto idéntico.
    frecuencia = Counter(fila[1] for fila in productos)
    por_ficha = {}
    etiquetas = {}
    for i in candidatos:
        nombre, descripcion = productos[i][1:3]
        ficha = (nombre, descripcion or "")
        por_ficha.setdefault(ficha, []).append(i)
        opaco = not re.search(r"[a-z]{3,}", _normalizar(nombre)) or (
            _terminos(nombre) == _terminos(str(productos[i][0]))
        )
        incluir_ficha = descripcion and (frecuencia[nombre] > 1 or opaco)
        etiquetas[ficha] = f"{nombre} — {descripcion[:220]}" if incluir_ficha else nombre
    fichas = sorted(por_ficha, key=lambda ficha: _normalizar(etiquetas[ficha]))
    opciones = tuple(etiquetas[ficha] for ficha in fichas)
    resultado = _evaluar_uso(pregunta.strip().rstrip(".!"), opciones)
    if resultado is None:
        return []
    i, evidencia = resultado
    if opciones.count(opciones[i]) > 1:
        return []  # Las diferencias quedan fuera del fragmento enviado.
    return [(productos[j], evidencia) for j in por_ficha[fichas[i]][:limite]]
