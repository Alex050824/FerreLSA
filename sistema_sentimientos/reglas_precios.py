"""Corrección conservadora de afirmaciones breves y explícitas sobre precios.

Solo coincide con una oración completa sencilla: los comentarios mixtos,
numéricos o de otro tema quedan a cargo del modelo.
"""
import re
import unicodedata

_SUJETO = r"(?:(?P<sujeto>(?:el|este|su) producto|(?:(?:el|su) )?(?:precio|costo)|(?:los )?precios)\s+)?"
_VERBO = r"(?:(?:es|esta|son|estan|resulta|parece|me parece|tiene un precio|tiene precio|tiene precios|tiene unos precios)\s+)?"
_GRADO = r"(?:(?P<grado>muy|demasiado|bastante|tan|un poco|nada|poco|para nada)\s+)?"
_ADJETIVOS = r"(?P<adjetivo>caro|cara|caros|caras|carisimo|carisima|costoso|costosa|costosos|costosas|barato|barata|baratos|baratas|economico|economica|economicos|economicas|accesible|accesibles|alto|alta|altos|altas|altisimo|altisima|altisimos|altisimas|elevado|elevada|elevados|elevadas|bajo|baja|bajos|bajas)"
_AFIRMACION = re.compile(_SUJETO + r"(?P<negacion>no\s+)?" + _VERBO + _GRADO + _ADJETIVOS)
_COSTOSO = {"caro", "cara", "caros", "caras", "carisimo", "carisima", "costoso", "costosa", "costosos", "costosas", "alto", "alta", "altos", "altas", "altisimo", "altisima", "altisimos", "altisimas", "elevado", "elevada", "elevados", "elevadas"}
_AMBIGUO = {"alto", "alta", "altos", "altas", "altisimo", "altisima", "altisimos", "altisimas", "elevado", "elevada", "elevados", "elevadas", "bajo", "baja", "bajos", "bajas", "accesible", "accesibles"}
_CUESTA = re.compile(r"(?:(?:el|este|su) producto\s+)?(?P<negacion>no\s+)?cuesta\s+(?:demasiado|mucho|un monton)")
_INCERTIDUMBRE = re.compile(
    r"\b(?:quiza|quizas|tal vez|a lo mejor|puede que|podria ser|no se si|"
    r"no estoy segur[oa]|no creo que|no pienso que|no es cierto|no es verdad|"
    r"no lo es|no lo son|no es asi)\b"
)


def _frase_precio(normalizado):
    costo = _CUESTA.fullmatch(normalizado)
    if costo:
        return "Positivo" if costo.group("negacion") else "Negativo"
    coincidencia = _AFIRMACION.fullmatch(normalizado)
    if not coincidencia:
        return None
    sujeto, negacion, grado, adjetivo = (coincidencia.group(k) for k in ("sujeto", "negacion", "grado", "adjetivo"))
    # Alto, bajo y accesible describen muchas cosas además de precios.
    tiene_contexto = bool(sujeto and ("precio" in sujeto or "costo" in sujeto)) or "precio" in normalizado
    if adjetivo in _AMBIGUO and not tiene_contexto:
        return None
    # «No es poco caro» requiere un manejo de doble negación más elaborado.
    if negacion and grado == "poco":
        return None
    negativo = adjetivo in _COSTOSO
    if negacion or grado in {"nada", "para nada", "poco"}:
        negativo = not negativo
    return "Negativo" if negativo else "Positivo"


def sentimiento_precio(texto):
    """Reconoce valoraciones explícitas, sin interpretar importes numéricos."""
    if "?" in texto or "¿" in texto:
        return None
    normalizado = unicodedata.normalize("NFKD", texto.casefold())
    normalizado = "".join(c for c in normalizado if not unicodedata.combining(c))
    normalizado = re.sub(r"\s+", " ", normalizado).strip(" .!¡?¿\t\n\r")
    if _INCERTIDUMBRE.search(normalizado):
        return None
    completo = _frase_precio(normalizado)
    if completo:
        return completo
    # Una crítica explícita del precio prevalece aun si otra cláusula es positiva.
    # Solo se aceptan cláusulas completas; no se busca «caro» dentro de frases.
    clausulas = re.split(r"\s*(?:[,;]|\bpero\b|\baunque\b|\bsin embargo\b)\s*", normalizado)
    resultados = {_frase_precio(parte.strip(" .!¡?¿")) for parte in clausulas}
    if len(clausulas) > 1 and "Negativo" in resultados and "Positivo" not in resultados:
        return "Negativo"
    return None
