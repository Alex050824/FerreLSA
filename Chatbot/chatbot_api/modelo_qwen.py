"""Redacción con Qwen y referencias extractivas a las fichas seleccionadas."""

import json
import logging
import re
from contextlib import contextmanager
from functools import lru_cache
from threading import Lock

NOMBRE_MODELO = "Qwen/Qwen2.5-0.5B-Instruct"
_turno_cpu = Lock()
_log = logging.getLogger(__name__)
_referencia = re.compile(r"\[(?:N\d|D\d[a-b])\]")
_partes = re.compile(r"\[[^\]\s]*(?:\]|$)|[^\W\d_]+|\s+|.", re.UNICODE)
# La redacción libre puede presentar o atribuir datos, pero los hechos concretos
# solo se pueden expresar mediante una referencia a su fuente.
_lenguaje_neutro = frozenset("""
    a al aquí acá abajo acerca además ahora así aparece aparecen artículo artículos
    catálogo cita citada como compartimos comparto con consulta consultar consultá
    consultando continuación corresponde correspondiente datos de del describe
    descripción descriptiva desde detalla detallado detalles dice dicha dicho
    el en encontrarás encontrás encontré es esa ese esta estas este estos
    ficha fichas figura figuran indica indicada indicado información informa
    la las le lo los menciona muestra muestran muestro nombre nuestra nuestro
    para pertenece podés presenta presentamos presento producto productos puedes
    que registrada registrado relación respecto respuesta revisá revisar se según
    señala siguiente siguientes sobre son su sus te tu ver ves y
""".split())
_datos_comerciales = re.compile(
    r"[$€₡]|\b(?:precios?|cuesta[n]?|vale[n]?|costos?|col[oó]n(?:es)?|crc|usd|"
    r"d[oó]lares?|stocks?|existencias?|disponib(?:les?|ilidad)|agotad[oa]s?|"
    r"unidades?|inventario|ofertas?)\b", re.IGNORECASE,
)


@lru_cache(maxsize=1)
def _cargar_qwen():
    import torch
    from transformers import AutoModelForCausalLM, AutoTokenizer

    capacidades = getattr(torch.cpu, "get_capabilities", dict)()
    bf16_nativo = any(capacidades.get(k) for k in ("bf16", "avx512_bf16", "amx_bf16"))
    precision = torch.bfloat16 if bf16_nativo else torch.float32

    # La instalación ya descargada también funciona sin conexión.
    for solo_local in (True, False):
        try:
            tokenizador = AutoTokenizer.from_pretrained(NOMBRE_MODELO, local_files_only=solo_local)
            modelo = AutoModelForCausalLM.from_pretrained(
                NOMBRE_MODELO, local_files_only=solo_local, dtype=precision,
            )
            return tokenizador, modelo.eval()
        except OSError:
            if not solo_local:
                raise


@contextmanager
def usar_qwen():
    """Comparte pesos y turno de CPU entre recuperación y redacción."""
    with _turno_cpu:
        import torch

        with torch.inference_mode():
            yield _cargar_qwen()


def _referencias_de_fichas(productos, incluir_descripcion):
    referencias = {}
    cantidades = []
    for i, fila in enumerate(productos[:3], start=1):
        referencias[f"[N{i}]"] = fila[1]
        fragmentos = []
        if incluir_descripcion:
            for oracion in re.split(r"(?<=[.!?])\s+|[\r\n]+", fila[2] or ""):
                cita = oracion.strip().removesuffix(".")
                if cita and len(cita) <= 300 and not _datos_comerciales.search(cita):
                    fragmentos.append(cita)
                    if len(fragmentos) == 2:
                        break
        for letra, cita in zip("ab", fragmentos):
            referencias[f"[D{i}{letra}]"] = f"«{cita}»"
        cantidades.append(len(fragmentos))
    return referencias, tuple(cantidades)


def _formas_de_redaccion(cantidades):
    """Gramática de atribución: cada cita solo puede seguir al nombre de su ficha."""
    for i, cantidad in enumerate(cantidades, start=1):
        nombre = f"[N{i}]"
        for letra in "ab"[:cantidad]:
            cita = f"[D{i}{letra}]"
            for sujeto in ("La ficha", "La descripción", "La información del catálogo"):
                for verbo in ("indica", "señala", "menciona"):
                    yield f"{sujeto} de {nombre} {verbo} lo siguiente: {cita}."
            for inicio in ("Según la ficha", "Según el catálogo", "En la descripción"):
                yield f"{inicio}, {nombre} se describe así: {cita}."
            yield f"{nombre} figura en el catálogo con esta descripción: {cita}."

    # Ante una consulta técnica, dar una explicación literal cuando exista.
    if any(cantidades):
        return

    if len(cantidades) == 1:
        complementos = ("la ficha de [N1]", "los datos de [N1]", "la información de [N1]")
    else:
        complementos = ("las fichas de estos productos", "los datos de estos artículos",
                        "la información de estos productos")
    for inicio in ("", "Para tu consulta, ", "A continuación, "):
        for verbo in ("te muestro", "te comparto", "podés revisar", "podés consultar"):
            for complemento in complementos:
                frase = inicio + verbo + " " + complemento + "."
                yield frase[0].upper() + frase[1:]


@lru_cache(maxsize=48)
def _gramatica(tokenizador, cantidades):
    # La topología depende de las referencias disponibles, nunca de valores SQL.
    raiz = {}
    formas = list(_formas_de_redaccion(cantidades))
    secuencias = tokenizador(formas, add_special_tokens=False)["input_ids"]
    for ids in secuencias:
        nodo = raiz
        for token in ids:
            nodo = nodo.setdefault(token, {})
    return raiz


def _verificable(texto, referencias, *, completo):
    nombres, citas = [], []
    for parte in _partes.finditer(texto):
        palabra = parte[0]
        parcial = not completo and parte.end() == len(texto)
        if palabra in referencias:
            (nombres if palabra.startswith("[N") else citas).append(palabra)
        elif palabra.startswith("["):
            if not (parcial and any(r.startswith(palabra) for r in referencias)):
                return False
        elif palabra.isalpha():
            palabra = palabra.lower()
            if palabra not in _lenguaje_neutro and not (
                parcial and any(p.startswith(palabra) for p in _lenguaje_neutro)
            ):
                return False
        elif not (palabra.isspace() or palabra in {",", ":", "."}):
            return False
    if len(nombres) > 1 or len(citas) > 1:
        return False
    if citas and (not nombres or citas[0][2] != nombres[0][2]
                  or texto.index(citas[0]) < texto.index(nombres[0])):
        return False
    if not completo:
        return True
    if any(r.startswith("[D") for r in referencias):
        return bool(citas) and texto.endswith((citas[0], citas[0] + "."))
    return bool(nombres) or (
        len(referencias) > 1 and bool(set(texto.lower().rstrip(".").split()) &
                                      {"productos", "artículos", "fichas"})
    )


def _redactar_libre(modelo, tokenizador, paso, entrada, referencias):
    generados = []
    for _ in range(28):
        token = paso.logits[0, -1].argmax().item()
        if token == tokenizador.eos_token_id:
            break
        generados.append(token)
        texto = tokenizador.decode(generados, skip_special_tokens=False).strip()
        if not _verificable(texto, referencias, completo=False):
            return None
        if texto.endswith("."):
            break
        paso = modelo(input_ids=entrada.new_tensor([[token]]), cache=paso.cache,
                      use_cache=True, logits_to_keep=1)
    else:
        return None
    texto = tokenizador.decode(generados, skip_special_tokens=False).strip()
    return texto if _verificable(texto, referencias, completo=True) else None


def _generar_tokens(modelo, entrada, nodo, paso):
    """Respaldo restringido. Los tramos sin bifurcaciones se procesan juntos."""

    generados = []
    pendientes = []
    while nodo:
        opciones = list(nodo)
        if len(opciones) == 1:
            token = opciones[0]
        else:
            if pendientes:
                tramo = entrada.new_tensor([pendientes])
                paso = modelo(input_ids=tramo, cache=paso.cache,
                              use_cache=True, logits_to_keep=1)
                pendientes = []
            token = opciones[paso.logits[0, -1, opciones].argmax().item()]
        generados.append(token)
        pendientes.append(token)
        nodo = nodo[token]
    return generados


def generar_explicacion(pregunta, productos, incluir_descripcion=True):
    """Redacta a partir de hasta tres filas SQL. Django añade precio y existencia."""
    if not productos:
        raise ValueError("La generación de productos requiere al menos una ficha.")

    referencias, cantidades = _referencias_de_fichas(productos, incluir_descripcion)
    mensajes = [
        {"role": "system", "content": (
            "Sos el asistente de FerreLSA. Respondé en una frase en español. "
            "Escribí las marcas entre corchetes en lugar de nombres y datos. "
            "Ejemplo con descripción: La ficha de [N1] indica [D1a]. "
            "Sin descripción, presentá la ficha."
        )},
        {"role": "user", "content": json.dumps(
            {"consulta": pregunta, "fichas": referencias}, ensure_ascii=False,
        )},
    ]
    # Evita dos cargas en la primera visita y la contención entre generaciones CPU.
    with usar_qwen() as (tokenizador, modelo):
        entrada = tokenizador.apply_chat_template(
            mensajes, tokenize=True, add_generation_prompt=True, return_tensors="pt",
            return_dict=True,
        )["input_ids"]
        inicio = modelo(input_ids=entrada, use_cache=True, logits_to_keep=1)
        texto = _redactar_libre(modelo, tokenizador, inicio, entrada, referencias)
        if texto is None:
            # La caché KV se amplía in situ durante el borrador. Conservamos el
            # prompt ya procesado, descartando solo sus tokens de continuación.
            descartados = inicio.cache.get_seq_length() - entrada.shape[1]
            if descartados > 0:
                inicio.cache.crop(-descartados)
            ids = _generar_tokens(modelo, entrada, _gramatica(tokenizador, cantidades), inicio)
            texto = tokenizador.decode(ids, skip_special_tokens=True)
            _log.debug("Qwen usó la redacción restringida")
        else:
            _log.debug("Qwen usó la redacción libre verificada")

    # Una sustitución sola: el contenido de la base nunca se reinterpreta como marca.
    texto = _referencia.sub(lambda match: referencias[match.group()], texto)
    if incluir_descripcion and not any(cantidades):
        texto += " No tengo un detalle técnico verificable que pueda citar en esta consulta."
    return texto


def responder_pregunta(pregunta):
    from .views import consultar_catalogo

    return consultar_catalogo(pregunta)["respuesta"]
