"""Señales textuales orientativas que justifican una revisión humana.

Son reglas sencillas, no identifican la intención ni determinan sentimiento.
"""

import re
import unicodedata


def _normalizar(texto):
    return "".join(
        caracter for caracter in unicodedata.normalize("NFD", texto.casefold())
        if unicodedata.category(caracter) != "Mn"
    )


_ELOGIO = re.compile(
    r"\b(?:excelente|excelentes|genial|buen(?:o|a|os|as|isimo|isima)?|"
    r"encant(?:a|an|o|ado|ada)|maravillos(?:o|a)|perfect(?:o|a)|"
    r"increible|fantastic(?:o|a)|recomend(?:able|ado|ada)|"
    r"me gust(?:a|an|o)|(?:muy\s+)?bien|vale la pena)\b"
)
_NEGATIVO = re.compile(
    r"\b(?:mal(?:o|a|os|as|isimo|isima)?|pesim(?:o|a)|horrible|"
    r"terrible|lent(?:o|a|os|as)|rot(?:o|a|os|as)|defectuos(?:o|a)|"
    r"fall(?:a|an|o|as)|problema(?:s)?|decepcion\w*|"
    r"retras\w*|tard\w*|demor\w*|car(?:o|a|os|as|isimo|isima)|"
    r"romp\w*|no funciona|no sirve|"
    r"deja mucho que desear)\b"
)
_POCA_DURACION = re.compile(
    r"\b(?:bateria|carga|autonomia|duracion|dura\w*)\b.{0,40}"
    r"\b(?:muy\s+)?poc(?:o|a|os|as)\b"
    r"|\b(?:muy\s+)?poc(?:o|a|os|as)\b.{0,40}"
    r"\b(?:bateria|carga|autonomia|duracion|dura\w*)\b"
)
_BATERIA_DESCARGA = re.compile(
    r"\b(?:bateria|carga)\b[^.!?;,]{0,35}\b(?:descarg\w*|agot\w*)\b"
    r"[^.!?;,]{0,20}\b(?:rapid(?:o|a)|pronto|enseguida)\b"
)
_TRAMO_ESPERA = r"(?:(?!\b(?:pero|aunque|sino|sin embargo|no obstante)\b)[^.!?;,\n]){0,45}"
_EVENTO_ESPERA = r"\b(?:espera(?:s)?|espere|esperamos|esperaron|esperar|esperado|esperando)\b"
_BREVE = r"\b(?:cort(?:o|a|os|as)|breve(?:s)?|poc(?:o|a|os|as)|minim(?:o|a|os|as))\b"
_LARGA = (r"\b(?:larg(?:o|a|os|as)|much(?:o|a|os|as)|demasiad(?:o|a|os|as)|"
          r"prolongad(?:o|a|os|as)|etern(?:o|a|os|as)|"
          r"(?:[2-9]|[1-9]\d+|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|diez)\s+"
          r"(?:horas?|dias?|semanas?|meses?))\b")
_ESPERA_BREVE = re.compile(rf"(?:{_EVENTO_ESPERA}{_TRAMO_ESPERA}{_BREVE}|{_BREVE}\s+(?:fue\s+)?(?:la\s+)?(?:tiempo\s+de\s+)?esperas?\b)")
_ESPERA_LARGA = re.compile(rf"(?:{_EVENTO_ESPERA}{_TRAMO_ESPERA}{_LARGA}|{_LARGA}\s+(?:fue\s+)?(?:la\s+)?(?:de\s+)?esperas?\b)")
_MARCADOR_IRONIA = re.compile(r"(?:#(?:sarcasmo|ironia)\b|(?<!\w)/s\b)")
_ENTREGA_RECORD = re.compile(
    r"\b(?:llego|llegaron|entrega|envio|recibi|recibimos|recibido)\b"
    r"[^.!?;]{0,50}\b(?:en\s+)?tiempo\s+record\b"
)
_ENTREGA_RAPIDA = re.compile(
    r"\b(?:entrega|envio|reparto|pedido|producto|paquete|llego|llegaron|"
    r"llegada|entregaron|recibi|recibimos|recibido)\b[^.!?;]{0,40}"
    r"\b(?:rapid(?:o|a|os|as|isimo|isima)|veloz|puntual|pronto)\b"
    r"|\b(?:rapid(?:o|a|os|as|isimo|isima)|veloz|puntual)\b"
    r"[^.!?;]{0,25}\b(?:entrega|envio|reparto)\b"
)
_QUEJA_DESPECTIVA = re.compile(
    r"^\s*(?:(?:unos?|unas?|los|las)\s+)?(?:ladron(?:es|a|as)?|estafador(?:es|a|as)?)\s*[!?.]*\s*$"
    r"|\b(?:son|es|sois|eres|parecen|parece|ustedes|empresa|tienda|vendedores)\b"
    r"[^.!?;]{0,40}\b(?:ladron(?:es|a|as)?|estafador(?:es|a|as)?)\b"
    r"|\b(?:me|nos)\s+(?:estafaron|estafo|robaron|estafa|robo)\b"
)
_TERCEROS = re.compile(r"\b(?:segun|mi amigo dice|mi amiga dice|la competencia|otra empresa|otro negocio|la policia|una noticia)\b")
_SENTIDO_FIGURADO = re.compile(r"\b(?:ladron(?:es|a|as)?|roba\w*)\s+de\s+(?:corazones?|besos|miradas)\b")


def quitar_emojis(texto):
    """Retira pictogramas y modificadores del texto enviado a los modelos.

    El comentario original se conserva sin cambios para mostrarlo y guardarlo.
    """
    texto = re.sub(r"[0-9#*]\ufe0f?\u20e3", "", texto)
    return "".join(c for c in texto if unicodedata.category(c) not in {"So", "Sk"}
                   and c not in "\ufe0e\ufe0f\u200d\u20e3")


def _negado(texto, inicio):
    """Busca una negación cercana, limitada por signos de puntuación.

    Es una aproximación, no resuelve todas las construcciones del español.
    """
    anterior = re.split(r"[.!?,;:\n]", texto[:inicio])[-1]
    anterior = re.split(r"\b(?:pero|aunque|sino|sin embargo|no obstante)\b", anterior)[-1]
    palabras = re.findall(r"\b\w+\b", anterior)[-4:]
    for indice, palabra in enumerate(palabras):
        if palabra in {"no", "nunca", "jamas", "sin", "tampoco", "nada"}:
            # «No solo es bueno» afirma el elogio, no lo niega.
            if palabra == "no" and indice + 1 < len(palabras) and palabras[indice + 1] in {"solo", "solamente"}:
                continue
            return True
    return False


def _coincidencia_negada(texto, hallazgo):
    dentro = hallazgo.group()
    negacion_interna = re.search(r"\b(?:no(?!\s+(?:solo|solamente)\b)|nunca|jamas|sin|tampoco|nada)\b", dentro)
    return bool(_negado(texto, hallazgo.start()) or _negado(texto, hallazgo.end()) or negacion_interna)


def _senales_palabras(texto):
    positivos = negativos = False
    for hallazgo in _ELOGIO.finditer(texto):
        if _negado(texto, hallazgo.start()):
            negativos = True
        else:
            positivos = True
    for patron in (_NEGATIVO, _POCA_DURACION, _BATERIA_DESCARGA, _ESPERA_LARGA):
        for hallazgo in patron.finditer(texto):
            # «No funciona» y «no sirve» son quejas completas, no palabras
            # negativas que deban invertirse otra vez.
            if patron in (_BATERIA_DESCARGA, _ESPERA_LARGA) and _coincidencia_negada(texto, hallazgo):
                continue
            if not hallazgo.group().startswith(("no funciona", "no sirve")) and _negado(texto, hallazgo.start()):
                positivos = True
            else:
                negativos = True
    for patron in (_ENTREGA_RECORD, _ENTREGA_RAPIDA, _ESPERA_BREVE):
        for hallazgo in patron.finditer(texto):
            if not _coincidencia_negada(texto, hallazgo):
                positivos = True
    if not _SENTIDO_FIGURADO.search(texto):
        for hallazgo in _QUEJA_DESPECTIVA.finditer(texto):
            if not _coincidencia_negada(texto, hallazgo):
                negativos = True
    return positivos, negativos


def alertas_texto(texto):
    """Devuelve avisos orientativos, sin afirmar sarcasmo ni cambiar sentimiento."""
    if not isinstance(texto, str):
        raise TypeError("El comentario debe ser texto.")
    normalizado = _normalizar(texto)
    alertas = []
    positivo, negativo = _senales_palabras(normalizado)
    espera_larga = any(not _coincidencia_negada(normalizado, m) for m in _ESPERA_LARGA.finditer(normalizado))
    if _MARCADOR_IRONIA.search(normalizado):
        alertas.append("Contiene un marcador de posible sarcasmo o ironía; revisar el contexto")
    if _TERCEROS.search(normalizado):
        alertas.append("El texto puede referirse a otra persona o entidad; revisar el contexto")
    if _SENTIDO_FIGURADO.search(normalizado):
        alertas.append("El texto puede usar una expresión figurada; revisar el contexto")
    if any(_coincidencia_negada(normalizado, hallazgo)
           for patron in (_ENTREGA_RECORD, _ENTREGA_RAPIDA, _QUEJA_DESPECTIVA, _ESPERA_BREVE, _ESPERA_LARGA)
           for hallazgo in patron.finditer(normalizado)):
        alertas.append("Una negación cambia el sentido de la frase; revisar el contexto")
    if positivo and (negativo or espera_larga):
        alertas.append("Combina un elogio con una posible queja; revisar el contexto")
    return alertas
