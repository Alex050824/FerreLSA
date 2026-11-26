"""Detección orientativa de temas mencionados en comentarios en español.

Una coincidencia indica que el tema aparece en el texto, no si la opinión
del comentario es favorable o desfavorable para ese tema.
"""

import re
import unicodedata


TEMAS = ("Entregas", "Precios", "Atención al cliente", "Calidad", "Otros")


def _normalizar(texto):
    return "".join(
        caracter
        for caracter in unicodedata.normalize("NFD", texto.casefold())
        if unicodedata.category(caracter) != "Mn"
    )


_PATRONES = (
    (
        "Entregas",
        re.compile(
            r"\b(?:entreg\w*|envi(?:o|os|ar|aron|ado|ada|ados|adas|an|e|amos)|"
            r"lleg(?:o|an|aron|ada|adas|ar|ue|uen)|repart\w*|despach\w*|"
            r"paqueteria|mensajeria|paquete(?:s)?)\b"
        ),
    ),
    (
        "Precios",
        re.compile(
            r"\b(?:precio(?:s)?|car(?:o|a|os|as|isimo|isima|isimos|isimas)|"
            r"barat(?:o|a|os|as|isimo|isima|isimos|isimas)|cost(?:o|os|ar|aba|aron|oso|osa|osos|osas)|"
            r"tarifa(?:s)?|cobr\w*|pag(?:o|ue|ar|amos|aron|ado|ada|an)|"
            r"factur\w*|descuento(?:s)?|oferta(?:s)?|gratis|gratuit(?:o|a|os|as))\b"
        ),
    ),
    (
        "Atención al cliente",
        re.compile(
            r"\b(?:atencion|atend\w*|atien\w*|servicio(?:s)?|"
            r"cliente(?:s)?|personal|vendedor(?:a|es|as)?|"
            r"emplead(?:o|a|os|as)|soporte|contact\w*|"
            r"esper(?:a|as|ar|e|amos|aron|ado|ando))\b"
        ),
    ),
    (
        "Calidad",
        re.compile(
            r"\b(?:calidad|defect\w*|fall(?:a|as|o|an|aron)|averi\w*|"
            r"rot(?:o|a|os|as)|danad(?:o|a|os|as)|romp(?:e|io|ieron|er|ia)|"
            r"funcion\w*|descompuest(?:o|a|os|as)|durabilidad|resistencia|"
            r"bateria(?:s)?|camara(?:s)?|material(?:es)?|"
            r"(?:mal|buen|perfecto|pesimo)\s+estado)\b"
            r"|\b(?:producto|articulo|aparato|equipo)\b[^.!?;,]{0,30}"
            r"\b(?:buen(?:o|a|os|as)?|mal(?:o|a|os|as)?|excelente|"
            r"defectuos(?:o|a|os|as)|durader(?:o|a|os|as)|"
            r"resistente|fragil)\b"
            r"|\b(?:buen|mal|excelente)\s+(?:producto|articulo|aparato|equipo)\b"
        ),
    ),
)


def detectar_temas(texto):
    """Devuelve los temas presentes en orden estable; «Otros» si no hay coincidencias."""
    if not isinstance(texto, str):
        raise TypeError("El comentario debe ser texto.")
    normalizado = _normalizar(texto)
    encontrados = tuple(nombre for nombre, patron in _PATRONES if patron.search(normalizado))
    return encontrados or ("Otros",)
