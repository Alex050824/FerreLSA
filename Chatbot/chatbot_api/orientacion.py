"""Orientación general y conservadora para trabajos frecuentes de ferretería.

Las guías no describen productos del catálogo. Una pregunta comercial debe
resolverse con datos de la tienda; una tarea que no entendemos pide aclaración.
"""

import re
import unicodedata


def _normalizar(texto):
    texto = unicodedata.normalize("NFKD", texto.casefold())
    return " ".join(re.findall(r"[a-z0-9]+", "".join(c for c in texto if not unicodedata.combining(c))))


_COMERCIAL = re.compile(
    r"\b(?:precios?|cuestan?|costos?|valen?|cuanto\s+(?:sale|salen)|"
    r"existencias?|stocks?|inventario|disponib\w*|hay\s+en\s+(?:tienda|inventario)|"
    r"venden|tienen|tenes|comprar|venta|horarios?|garantias?|envios?|entregas?|"
    r"direcciones|direccion|ubicacion|telefono|ofertas?|promociones?|pago)\b"
)
_ORIENTACION = re.compile(
    r"\b(?:como|cual(?:es)?|que|necesito|necesitaria|quiero|quisiera|ocupo|"
    r"busco|recomend\w*|suger\w*|elegir|elijo|seleccionar|diferencias?|"
    r"consejos?|ayuda|sirve|se usa|utilizar|usar|preparar|reparar|"
    r"pintar|taladrar|perforar|sellar|podar|instalar|limpiar|colocar)\b"
)


def orientar(pregunta):
    """Da una guía general breve si se reconoce la necesidad; si no, devuelve None.

    No sustituye la búsqueda de productos ni responde por existencia, precios,
    compatibilidad específica o condiciones comerciales de FerreLSA.
    """
    if not isinstance(pregunta, str) or not pregunta.strip():
        return None
    texto = _normalizar(pregunta)
    if _COMERCIAL.search(texto) or not _ORIENTACION.search(texto):
        return None

    # Evitar indicaciones de conexión y reparación en instalaciones peligrosas.
    if re.search(r"\b(?:electricidad|instalacion electrica|cableado|enchufe|tomacorriente|"
                 r"interruptor|corriente|gas|gasoducto)\b", texto):
        return ("Como orientación general, para trabajos en instalaciones eléctricas o de gas "
                "consultá a una persona profesional calificada. ¿Qué trabajo necesitás realizar?")

    if re.search(r"\b(?:brocha|brochas|pincel|pinceles|rodillo|rodillos)\b", texto) and re.search(
            r"\b(?:pintar|pintura|pared|paredes|elegir|elijo|usar|utilizar|cual|cuales|diferencia)\b", texto):
        return ("Como orientación general, elegí la herramienta según la superficie y la pintura: "
                "un rodillo suele facilitar las zonas amplias y una brocha los bordes y detalles. "
                "Revisá las indicaciones de la pintura. ¿Qué tipo de pintura vas a usar y qué tamaño tiene la zona?")

    if re.search(r"\b(?:pintar|pintura|pintado|pintar\w*)\b", texto) and re.search(
            r"\b(?:pared|paredes|muro|muros|superficie|superficies|habitacion|cuarto)\b", texto):
        if re.search(r"\b(?:pintura|pinturas)\b", texto) and re.search(
                r"\b(?:que|cual|cuales|elegir|elijo|tipo|recom\w*)\b", texto):
            pregunta_final = ("¿De qué material es la pared?" if re.search(r"\b(?:interior|exterior|intemperie)\b", texto)
                              else "¿La pared está en interior o a la intemperie?")
            return ("Como orientación general, elegí una pintura indicada para el material de la pared "
                    "y para el uso interior o exterior. Revisá también el acabado y las indicaciones "
                    f"de preparación del fabricante. {pregunta_final}")
        return ("Como orientación general, antes de pintar limpiá la superficie, dejala secar "
                "y retirá la pintura suuelta. Si hay grietas o humedad, atendelas antes de aplicar "
                "la pintura y seguí las indicaciones del fabricante. ¿La pared tiene humedad o pintura suelta?")

    if re.search(r"\b(?:perforar|taladrar|agujero|agujeros|hueco|huecos)\b", texto) and re.search(
            r"\b(?:pared|paredes|muro|muros|superficie|metal|madera|concreto|ceramica)\b", texto):
        return ("Como orientación general, elegí la herramienta y la broca según el material de la superficie. "
                "Antes de perforar, comprobá que no haya cables ni tuberías en la zona. "
                "¿Qué necesitás fijar?")

    if re.search(r"\b(?:fuga|fugas|goteo|gotera|filtracion)\b", texto) and re.search(
            r"\b(?:agua|tubo|tuberia|grifo|llave|fregadero|lavamanos)\b", texto):
        return ("Como orientación general, cerrá el paso de agua y tratá de identificar de dónde proviene "
                "la fuga antes de elegir una reparación. Si no podés localizarla o detenerla, "
                "consultá a una persona de plomería. ¿La fuga está en una unión, un grifo o una tubería?")

    if re.search(r"\b(?:sellar|sellador|silicon|silicona)\b", texto) and re.search(
            r"\b(?:junta|juntas|union|uniones|bano|lavamanos|fregadero|superficie|grieta)\b", texto):
        return ("Como orientación general, elegí un sellador compatible con las superficies y su exposición al agua. "
                "Limpiá la zona y seguí las indicaciones de aplicación y secado del fabricante. "
                "¿Qué materiales querés sellar?")

    if re.search(r"\b(?:pegamento|adhesivo|pegar|unir)\b", texto) and re.search(
            r"\b(?:madera|metal|plastico|ceramica|piezas|materiales|superficies)\b", texto):
        return ("Como orientación general, el adhesivo debe ser compatible con ambos materiales "
                "y con el lugar donde se usará la unión. Revisá la preparación y el tiempo de secado "
                "indicados por el fabricante. ¿La unión estará en interior o exterior y soportará peso?")

    if re.search(r"\b(?:podar|poda|tijera|tijeras)\b", texto) and re.search(
            r"\b(?:planta|plantas|rama|ramas|arbol|arboles|jardin|podar|poda)\b", texto):
        return ("Como orientación general, elegí la herramienta de poda según el tamaño de las ramas "
                "y mantené las hojas limpias. ¿Buscás podar plantas pequeñas o ramas más gruesas?")

    return None


# Solo se conserva un identificador de la pregunta pendiente, nunca el texto
# del cliente. Las claves coinciden con las preguntas que formula orientar().
_PREGUNTAS_PENDIENTES = {
    "¿La pared tiene humedad o pintura suelta?": "pared_humedad",
    "¿La pared está en interior o a la intemperie?": "pintura_ambiente",
    "¿De qué material es la pared?": "pintura_material",
    "¿Qué tipo de pintura vas a usar y qué tamaño tiene la zona?": "brocha",
    "¿Qué necesitás fijar?": "perforacion",
    "¿La fuga está en una unión, un grifo o una tubería?": "fuga",
    "¿Qué materiales querés sellar?": "sellador",
    "¿La unión estará en interior o exterior y soportará peso?": "adhesivo",
    "¿Buscás podar plantas pequeñas o ramas más gruesas?": "poda",
}
TEMAS_SEGUIMIENTO = frozenset(_PREGUNTAS_PENDIENTES.values()) | {
    "pintura_material_interior", "pintura_material_exterior",
}


def tema_pendiente(respuesta):
    """Determina la aclaración pendiente solo a partir de una respuesta propia."""
    return next((tema for pregunta, tema in _PREGUNTAS_PENDIENTES.items()
                 if respuesta.endswith(pregunta)), None)


def responder_seguimiento(pregunta, tema):
    """Devuelve (respuesta, próximo tema) o None si el turno cambia de asunto."""
    if tema not in TEMAS_SEGUIMIENTO or not isinstance(pregunta, str):
        return None
    texto = _normalizar(pregunta)
    if not texto or len(texto) > 120 or _COMERCIAL.search(texto):
        return None
    # Las preguntas y peticiones nuevas se resuelven por el enrutador principal.
    if re.search(r"\b(?:como|cuando|donde|precio|cuesta|quiero|necesito|busco|"
                 r"recom\w*|suger\w*|que producto|cual producto)\b", texto):
        return None

    if tema == "pared_humedad":
        if re.fullmatch(r"(?:(?:si|claro) )?(?:(?:la pared )?(?:tiene|presenta|hay|es|esta) )?(?:mucha |algo de |un poco de )?(?:humedad|humeda|humedo|mojada|mojado)(?: en la pared)?", texto):
            return ("Si la pared tiene humedad, primero identificá y resolvé su origen; dejala secar antes de pintar. "
                    "Si el problema persiste, consultá a una persona especialista.", None)
        if re.fullmatch(r"(?:(?:si|claro) )?(?:(?:la pared )?(?:tiene|hay) )?(?:pintura )?(?:suelta|descascarada|desprendida|descascarandose)", texto):
            return ("Retirá con cuidado la pintura suelta, limpiá la superficie y seguí las indicaciones "
                    "del producto de preparación y de la pintura antes de aplicarlos.", None)
        if re.fullmatch(r"no(?: tiene)?(?: humedad| pintura suelta| ninguna(?: de las dos)?)?", texto):
            return ("Si la pared está seca y sin pintura suelta, limpiá la superficie y seguí las indicaciones "
                    "de preparación de la pintura que vayas a utilizar.", None)

    elif tema == "pintura_ambiente":
        # Si se nombran ambas opciones no asumimos cuál es la correcta.
        interior = bool(re.search(r"\b(?:interior|dentro|adentro)\b", texto))
        exterior = bool(re.search(r"\b(?:exterior|fuera|afuera|intemperie)\b", texto))
        if interior != exterior and not re.search(r"\b(?:no|ni)\b", texto):
            ambiente = "interior" if interior else "exterior"
            return (f"Para una pared de {ambiente}, buscá una pintura indicada para ese uso y compatible "
                    "con el material de la superficie. ¿De qué material es la pared?", f"pintura_material_{ambiente}")

    elif tema.startswith("pintura_material"):
        if re.fullmatch(r"(?:(?:es|de|es de|la pared es de) )?(?:concreto|cemento|madera|metal|ladrillo|yeso|bloque|mamposteria)", texto):
            ambiente = tema.removeprefix("pintura_material_") if tema != "pintura_material" else ""
            uso = f" y para uso {ambiente}" if ambiente else " y para el lugar donde se aplicará"
            return (f"Como orientación general, revisá que la pintura y la preparación indicadas en su etiqueta sean aptas para ese material{uso}.", None)

    elif tema == "brocha":
        if re.search(r"\b(?:acrilica|latex|esmalte|aceite|agua|pequena|pequeno|grande|amplia|amplio|bordes|detalles)\b", texto):
            return ("Revisá en la etiqueta de la pintura qué tipo de brocha o rodillo recomienda el fabricante. "
                    "Para una zona amplia suele ser práctico un rodillo; para bordes y detalles, una brocha.", None)

    elif tema == "perforacion":
        if re.search(r"\b(?:repisa|estante|cuadro|espejo|soporte|mueble|gancho|lampara)\b", texto):
            return ("Para elegir la fijación, tené en cuenta el material de la pared y el peso del objeto. "
                    "Verificá que no haya cables ni tuberías antes de perforar.", None)

    elif tema == "fuga":
        if re.search(r"\b(?:union|grifo|llave|tuberia|tubo|fregadero|lavamanos)\b", texto):
            return ("Con el paso de agua cerrado, revisá de dónde sale el agua y anotá las medidas de la conexión "
                    "antes de elegir un repuesto. Si no podés detener la fuga, consultá a una persona de plomería.", None)

    elif tema == "sellador":
        if re.search(r"\b(?:vidrio|metal|madera|plastico|ceramica|azulejo|porcelana|concreto)\b", texto):
            return ("Verificá en la etiqueta que el sellador sea compatible con los materiales y con su exposición "
                    "al agua; seguí las instrucciones de limpieza, aplicación y secado.", None)

    elif tema == "adhesivo":
        if re.search(r"\b(?:interior|exterior|intemperie|peso|pesado|ligero|liviano)\b", texto):
            return ("Elegí un adhesivo cuya etiqueta indique compatibilidad con ambos materiales y con las "
                    "condiciones de uso y carga de la unión. Seguí las instrucciones del fabricante.", None)

    elif tema == "poda":
        if re.search(r"\b(?:pequena|pequenas|gruesa|gruesas|delgada|delgadas|arbusto|arbol)\b", texto):
            return ("Elegí una herramienta de poda adecuada al grosor de las ramas y al trabajo que vas a hacer. "
                    "Mantené las hojas limpias y seguí las indicaciones de uso de la herramienta.", None)

    return None
