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
    busco buscaba buscando cantidad cantidades caracteristica caracteristicas codigo como
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
        posiciones = {texto: i for i, texto in enumerate(pasajes)}
        nuevos = [texto for texto in posiciones if texto not in self.vectores]
        vectores = self.vectores.copy()
        if nuevos:
            lote = convertir_a_vectores(["passage: " + texto for texto in nuevos])
            vectores.update(zip(nuevos, lote))
        matriz = torch.stack([vectores[texto] for texto in pasajes]) if pasajes else None
        # Cada texto vigente apunta a una fila de la nueva matriz y comparte su memoria.
        vistas = {texto: matriz[i] for texto, i in posiciones.items()}
        self.pasajes, self.vectores, self.matriz = pasajes, vistas, matriz
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
            elif pedidos & en_nombre and pedidos <= en_ficha:
                calidad = 1 + len(pedidos & en_nombre) / len(pedidos)
            else:
                continue
            seleccion[i] = max(calidad, seleccion.get(i, 0))
    return sorted(seleccion.items(), key=lambda par: -par[1])


def coincidencias_nombre(consulta, productos):
    """Identifica nombres explícitos, sin confundir «para» del nombre con una tarea."""
    # Una acción después de «para» sigue siendo una pregunta de uso y debe
    # contrastarse con la ficha, incluso si aparece también en el nombre.
    if re.search(r"\bpara\s+(?:(?:poder|mejor)\s+)?[a-z]+(?:ar|er|ir)\b", _normalizar(consulta)):
        return []
    pedidos = _terminos(consulta)
    return [(indice, valor) for indice, valor in _coincidencias_directas(consulta, productos)
            if valor >= 2 and pedidos and (
                pedidos <= _terminos(productos[indice][1]) or pedidos == _terminos(productos[indice][0])
            )]


def _es_tarea(consulta):
    return bool(re.search(
        r"(?:\bpara\b|^(?!comprar\b|encontrar\b|conseguir\b)\w{2,}(?:ar|er|ir)\b|"
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
    nombres = coincidencias_nombre(consulta, productos)
    if nombres:
        return [(productos[i], valor) for i, valor in nombres[:limite]]
    if not _es_tarea(consulta):
        directas = _coincidencias_directas(consulta, productos)
        return [(productos[i], valor) for i, valor in directas[:limite]]

    # Si la pregunta identifica un artículo, valida el uso de ese artículo.
    # Conserva la consulta entera para que Qwen compruebe todas las restricciones.
    introduccion, separador, _ = consulta.partition(" para ")
    if separador:
        articulo = re.sub(
            r"\b(?:sirv\w*|servir\w*|funcion[aá]\w*|recom\w*|suger\w*|sugier\w*|"
            r"adecuad[oa]s?|apropiad[oa]s?)\b", " ", introduccion,
        ).strip()
        terminos = _terminos(articulo)
        if terminos and not _es_tarea(articulo):
            directas = _coincidencias_directas(articulo, productos)
            if directas:
                return _buscar_por_uso(pregunta, productos, limite, [i for i, _ in directas])
            elif any(terminos & _terminos(fila[1]) for fila in productos):
                return []  # El artículo existe, pero los detalles pedidos no coinciden.
    return _buscar_por_uso(pregunta, productos, limite)


def _candidatos_semanticos(pregunta, productos, permitidos=None):
    # Nombre y descripción se evalúan por separado: la longitud de una ficha
    # técnica no debe diluir la identidad del producto en el vector.
    campos = tuple((str(fila[1]), str(fila[2] or fila[1])) for fila in productos)
    pasajes = tuple(texto for par in campos for texto in par)
    with _turno_e5:
        matriz = _indice.actualizar(pasajes)
        vector = _vector_consulta(pregunta)
        cosenos = (matriz @ vector).reshape(-1, 2).max(dim=1).values.tolist()
    considerados = range(len(productos)) if permitidos is None else permitidos
    por_coseno = sorted(considerados, key=cosenos.__getitem__, reverse=True)

    # Fusión por posición: la semejanza E5 y la coincidencia léxica tienen
    # escalas distintas. Solo las coincidencias reales votan en la segunda lista.
    pedidos = _terminos(pregunta)
    coincidencias = [
        pedidos & (_terminos(nombre) | _terminos(descripcion)) for nombre, descripcion in campos
    ]
    frecuencia = Counter(p for conjunto in coincidencias for p in conjunto)
    puntaje_textual = [sum(1 / frecuencia[p] for p in conjunto) for conjunto in coincidencias]
    por_texto = sorted(
        (i for i in considerados if coincidencias[i]),
        key=puntaje_textual.__getitem__, reverse=True,
    )
    fusion = {i: 1 / lugar for lugar, i in enumerate(por_coseno, 1)}
    for lugar, i in enumerate(por_texto, 1):
        fusion[i] += 1 / lugar
    # Las presentaciones idénticas comparten un puesto entre los ocho finalistas.
    indices = {}
    for i in sorted(fusion, key=fusion.__getitem__, reverse=True):
        indices.setdefault(campos[i], i)
        if len(indices) == 8:
            break
    return list(indices.values())


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
    indices = []
    for etiqueta in etiquetas:
        token, = tokenizador.encode(etiqueta, add_special_tokens=False)
        indices.append(token)
    return logits[:, indices].float().tolist()


@lru_cache(maxsize=128)
def _evaluar_uso(pregunta, fichas):
    from .modelo_qwen import usar_qwen

    cantidad = len(fichas)
    letras = "ABCDEFGH"[:cantidad]
    ordenes = [list(range(cantidad))]
    if cantidad > 1:
        ordenes.append(ordenes[0][::-1])
    sistema = ("Elige la ficha que describe cómo realizar la tarea del cliente. "
               "Si falta la tarea concreta o ninguna ficha la resuelve directamente, "
               "elige X. Responde solo con la letra.")
    conversaciones = []
    for orden in ordenes:
        opciones = [f"{letra}. {fichas[i][:260]}" for letra, i in zip(letras, orden)]
        contenido = "\n".join([pregunta, *opciones, "X. Ninguna de las anteriores"])
        conversaciones.append([{"role": "system", "content": sistema},
                                {"role": "user", "content": contenido}])
    with usar_qwen() as (tokenizador, modelo):
        votos = _logits_etiquetas(tokenizador, modelo, conversaciones, letras + "X")
        diferencias = [[] for _ in fichas]
        for orden, puntajes in zip(ordenes, votos):
            for i, valor in zip(orden, puntajes):
                diferencias[i].append(valor - puntajes[-1])
        # Un rechazo unánime evita otra inferencia. En los demás casos el voto
        # colectivo solo ordena las comprobaciones: no descarta a los siguientes.
        if all(max(margenes) <= 0 for margenes in diferencias):
            return None
        orden = sorted(range(cantidad), key=lambda i: sum(diferencias[i]), reverse=True)
        # Solo se retira la introducción genérica de la consulta, nunca un
        # artículo, un material ni una restricción del cliente.
        tarea = re.sub(r"^(?:(?:necesito|quiero|quisiera|busco)\s+)?(?:algo\s+para\s+)?",
                       "", pregunta.strip("¿?¡!. "), flags=re.IGNORECASE)
        while orden:
            lote = orden[:4]
            # Una ficha larga se lee entera y sola, sin rellenar las demás
            # entradas del lote hasta su longitud ni perder restricciones.
            for pos, i in enumerate(lote):
                if len(fichas[i]) > 1600:
                    lote = lote[:max(1, pos)]
                    break
            orden = orden[len(lote):]
            conversaciones = []
            posiciones = []
            for i in lote:
                nombre, _, descripcion = fichas[i].partition(" — ")
                # Una circunstancia temporal puede mencionar una tarea que hace
                # otro artículo. La función ha de sostenerse sin esa circunstancia
                # y también con las restricciones de la ficha completa.
                principal = re.split(r"\s+(?:mientras\b|durante\b|(?:antes|después) de\b|"
                                     r"al\s+\w+(?:ar|er|ir)\b)", descripcion, maxsplit=1,
                                     flags=re.IGNORECASE)[0]
                inicio_ficha = len(conversaciones)
                for texto in dict.fromkeys((descripcion, principal)):
                    fuente = f"{nombre}. {texto}" if texto else nombre
                    if texto != descripcion:
                        fuente = texto
                    conversaciones.append([
                        {"role": "system", "content": "Answer Yes or No."},
                        {"role": "user", "content": f"Catalog: {fuente}\nIs its primary function to {tarea}?"},
                    ])
                posiciones.append((inicio_ficha, len(conversaciones)))
            votos = _logits_etiquetas(tokenizador, modelo, conversaciones, ("Yes", "No"))
            for i, (desde, hasta) in zip(lote, posiciones):
                margen = min(si - no for si, no in votos[desde:hasta])
                if margen > 0:
                    return i, margen
    return None


def _buscar_por_uso(pregunta, productos, limite, permitidos=None):
    candidatos = _candidatos_semanticos(pregunta, productos, permitidos)
    fichas = sorted({(productos[i][1], productos[i][2] or "") for i in candidatos})
    opciones = tuple(f"{nombre} — {descripcion}" if descripcion else nombre
                     for nombre, descripcion in fichas)
    resultado = _evaluar_uso(pregunta.strip().rstrip(".!"), opciones)
    if resultado is None:
        return []
    i, evidencia = resultado
    considerados = productos if permitidos is None else (productos[j] for j in permitidos)
    return [(fila, evidencia) for fila in considerados
            if (fila[1], fila[2] or "") == fichas[i]][:limite]
