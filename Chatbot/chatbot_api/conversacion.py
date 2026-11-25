"""Expresiones sociales, preguntas de seguimiento y aclaraciones del chat."""

import re
import unicodedata

from .busqueda_semantica import _es_tarea


_SOCIAL = re.compile(
    r"^[\s¿¡]*(?:"
    r"(?P<despedida>adi[oó]s|cha[ou]|hasta (?:luego|pronto|ma[ñn]ana)|nos vemos|"
    r"eso (?:es|ser[ií]a) todo|que (?:teng[aá]s?|pas[eé]s?) (?:un )?(?:buen d[ií]a|buena tarde|buena noche))|"
    r"(?P<gracias>(?:(?:ok(?:ay)?|listo|perfecto)[,\s]+)?(?:much(?:as|[ií]simas) )?gracias"
    r"(?: por (?:la |tu |su )?(?:ayuda|informaci[oó]n|atenci[oó]n))?)|"
    r"(?P<saludo>hola+|buen(?:os d[ií]as| d[ií]a)|buenas(?: (?:tardes|noches))?|"
    r"saludos|pura vida|qu[eé] tal|c[oó]mo (?:est[aá]s|vas))"
    r")\b(?:[ ,]+(?:FerreLSA|asistente|chatbot|bot|mae)\b)?", re.IGNORECASE,
)
_PODER = r"(?:pod[eé]s|puedes?|podr[ií]as?)"
_AYUDA = re.compile(
    rf"(?:ayuda|(?:necesito|quiero|quisiera) (?:tu |su )?ayuda|"
    rf"(?:(?:en|con) qu[eé] |c[oó]mo )?(?:me {_PODER} ayudar|{_PODER} ayudarme)|"
    rf"qu[eé] {_PODER} hacer(?: por m[ií])?|qu[eé] (?:te |le )?puedo preguntar)"
    r"(?:[, ]+por favor)?", re.IGNORECASE,
)
_RESPUESTAS = {
    "saludo": "¡Hola! ¿Qué producto buscás o qué trabajo necesitás hacer?",
    "gracias": "¡Con gusto!",
    "despedida": "¡Hasta luego! Gracias por visitar FerreLSA.",
    "ayuda": ("Podés preguntarme por productos, características, precios y existencias, "
              "o contarme qué trabajo necesitás hacer."),
}


def normalizar(pregunta):
    texto = unicodedata.normalize("NFKD", pregunta.casefold())
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.findall(r"\w+", texto))


_COMPLETA = (r"ficha (?:tecnica )?completa|(?:toda (?:la |su )?informacion|informacion completa)|"
             r"todos (?:los |sus )?(?:datos|detalles)|(?:datos|detalles) completos")
_TECNICOS = r"caracteristicas?|descripciones|descripcion|especificaciones?|especificacion|atributos?|detalles?|ficha tecnica"
_PETICION = (r"(?:(?:por favor |me )?(?:mostrame|muestrame|muestra|dame|deme|decime|dime|indica(?:me)?|"
             r"quiero (?:ver|saber)|quisiera (?:ver|saber)) )?")

# Solo una pregunta sin nombre ni atributos nuevos puede heredar el producto anterior.
_SEGUIMIENTO = re.compile(
    _PETICION + r"(?:"
    rf"(?:la |su )?(?:{_COMPLETA})|cuanto (?:cuestan?|valen?|salen?)|"
    r"(?:cual es |que )?(?:el |su )?(?:precio|costo)(?: tiene)?|"
    r"(?:cuant[oa]s?(?: unidades| stock| existencias?)?|(?:que |la )?cantidad)"
    r"(?: (?:hay|quedan?|tienen|les quedan))?(?: disponibles)?|"
    r"(?:lo |la )?tienen(?: disponible| en (?:existencia|stock))?|(?:hay|tienen) (?:existencias?|stock)|"
    r"(?:esta|sigue) (?:disponible|en stock)|(?:su )?disponibilidad|para que sirve|"
    rf"(?:(?:cuales son|cual es|que) )?(?:(?:sus|su|la|las|los) )?(?:{_TECNICOS})(?: tiene)?"
    r")(?: (?:ese|esa|este|esta)(?: (?:producto|articulo|herramienta))?)?(?: por favor)?"
)
_INCOMPLETA = re.compile(
    r"(?:(?:necesito|busco|quiero|quisiera|ocupo|ando buscando|estoy buscando)"
    r"(?: (?:algo|un|una|un producto|una herramienta|un articulo|informacion))?(?: (?:para|sobre))?|"
    r"(?:cuanto|cuantos|y|para|me interesa|me podes ayudar con|tengo una (?:pregunta|consulta)))?"
)
_FUERA_DE_ALCANCE = re.compile(
    r"(?:y )?(?:(?:(?:cual es |cuales son |que )?(?:el |los |su |sus )?"
    r"(?:horarios?|direccion|ubicacion|telefono|formas de pago|metodos de pago)"
    r"(?: de (?:atencion|la tienda|la ferreteria|ferrelsa)| (?:tienen|manejan))?$)|"
    r"a que hora (?:abren|cierran)|donde (?:estan|queda la (?:tienda|ferreteria))|"
    r"(?:(?:quiero|quisiera|puedo|necesito) )?(?:hacer|realizar|cancelar|rastrear|seguir) (?:un|mi|el) pedido|"
    r"(?:cual es el estado de|donde esta) mi pedido|"
    r"(?:hacen|ofrecen|tienen|realizan) (?:envios?|entregas?)|cuanto (?:cuesta|tarda) el envio|"
    r"precio del envio|envios? a domicilio|"
    r"(?:que|como esta el) clima|que tiempo (?:hara|hace)|pronostico del tiempo|"
    r"(?:contame|cuentame) un chiste)\b"
)


def es_seguimiento(texto):
    texto = texto.removeprefix("y ").removeprefix("entonces ")
    return all(_SEGUIMIENTO.fullmatch(parte) for parte in texto.split(" y "))


def campos_solicitados(texto):
    """Reconoce lo pedido en la pregunta normalizada, incluidos varios campos juntos."""
    campos = set()
    for parte in texto.split(" y "):
        if re.search(rf"\b(?:{_COMPLETA})\b", parte):
            campos.add("completa")
        elif re.search(rf"\b(?:{_TECNICOS}|para que sirve)\b", parte):
            campos.add("descripcion")
        if re.search(r"\b(?:precios?|costos?|cuestan?|valen?|cuanto salen?)\b", parte):
            campos.add("precio")
        if re.search(r"\b(?:cantidades|cantidad|cuant[oa]s|cuant[oa] (?:stock|existencia|hay|queda))\b", parte):
            campos.add("cantidad")
        elif re.search(r"\b(?:disponibles?|disponibilidad|stock|existencias?|agotad[oa]s?)\b", parte):
            campos.add("disponibilidad")
    if not campos and _es_tarea(texto):
        campos.add("recomendacion")
    if not campos and re.search(r"\b(?:tienen|hay|venden|quedan|cuentan con)\b", texto):
        if not re.search(r"\b(?:productos|articulos|catalogo|inventario|mercaderia)\b", texto):
            campos.add("disponibilidad")
    return campos


def consulta_de_busqueda(pregunta):
    """Quita un encabezado de ficha o atributo y conserva literalmente el artículo solicitado."""
    for enlace in re.finditer(r"\b(?:del?|sobre|tienen?|hay|quedan?)\s+", pregunta, re.IGNORECASE):
        prefijo = normalizar(pregunta[:enlace.start()])
        if es_seguimiento(prefijo):
            articulo = pregunta[enlace.end():].strip(" ¿?¡!.,;")
            if articulo:
                return articulo
    return pregunta


def pedir_orientacion(texto):
    if _INCOMPLETA.fullmatch(texto) or texto.endswith((" para", " sobre")):
        return "¿Qué producto buscás o qué trabajo querés hacer?"
    if _FUERA_DE_ALCANCE.match(texto):
        return "Desde este chat puedo ayudarte con productos, precios, existencias y características. ¿Qué necesitás?"
    return None


def interpretar_social(pregunta):
    """Devuelve la consulta pendiente, una respuesta social y si hubo despedida."""
    resto = pregunta.strip()
    intenciones = set()
    while coincidencia := _SOCIAL.match(resto):
        intenciones.add(coincidencia.lastgroup)
        resto = resto[coincidencia.end():].lstrip(" \t\r\n,;:.!?…")
        if resto[:2].casefold() == "y " and _SOCIAL.match(resto[2:]):
            resto = resto[2:]

    if _AYUDA.fullmatch(resto.strip(" ¿?¡!.,;…")):
        return "", _RESPUESTAS["ayuda"], False
    if resto or not intenciones:
        return resto, None, False
    if "despedida" in intenciones:
        return "", _RESPUESTAS["despedida"], True
    intencion = "gracias" if "gracias" in intenciones else "saludo"
    return "", _RESPUESTAS[intencion], False
