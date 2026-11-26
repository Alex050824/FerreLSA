from decimal import Decimal
import re
import unicodedata

from django import forms
from django.db import transaction

from .db import insert, one, query, update
from .http import ApiError, ImageURL, JsonBoolean, RecordId, body, clean, endpoint, no_content, record_id, response, text


def decimal_field(scale, *, required=True, minimum=0):
    return forms.DecimalField(max_digits=12, decimal_places=scale, min_value=minimum, required=required)


ACTIVE = {"activo": JsonBoolean(required=False)}
CATEGORY = {"nombre": text(100), "descripcion": text(255, required=False), **ACTIVE}
SUPPLIER = {
    "nombre": text(160), "identificacion": text(30, required=False), "telefono": text(30, required=False),
    "correo": forms.EmailField(max_length=180, required=False, empty_value=None),
    "direccion": text(500, required=False), "contacto": text(120, required=False), **ACTIVE,
}
PRODUCT = {
    "nombre": text(180), "codigo": text(60), "categoria_id": RecordId(),
    "proveedor_id": RecordId(required=False), "descripcion": text(10000, required=False),
    "unidad_medida": text(30), "precio_compra": decimal_field(2), "precio_venta": decimal_field(2),
    "stock_minimo": decimal_field(3), "imagen_url": ImageURL(max_length=500, required=False, empty_value=None),
    **ACTIVE,
}
PRODUCT_DEFAULTS = {"unidad_medida": "unidad", "precio_compra": "0", "precio_venta": "0", "stock_minimo": "0"}
PUBLIC_PRODUCT = "id, categoria_id, codigo, nombre, descripcion, unidad_medida, precio_venta, existencia, imagen_url"
CATALOGS = {"categorias": CATEGORY, "proveedores": SUPPLIER, "productos": PRODUCT}


def category_prefix(name):
    normalized = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    normalized = re.sub(r"[^a-z0-9 ]", " ", normalized)
    words = [word for word in normalized.split() if word not in {"y", "de", "del", "la", "el", "los", "las"}]
    label = " ".join(words)
    known = {
        "construccion": "CTN", "adhesivos selladores": "ADS", "ferreteria general": "FEG",
        "muebles organizacion": "MYO", "herramientas": "HER", "pinturas": "PIN",
        "plomeria": "PLO", "electricidad": "ELE", "jardineria": "JAR", "seguridad": "SEG",
        "limpieza": "LIM", "automotriz": "AUT", "banos": "BAN", "cocinas": "COC",
        "pisos": "PIS", "lamparas": "LAM", "exteriores": "EXT",
    }
    if label in known:
        return known[label]
    if not words:
        return "GEN"
    if len(words) == 1:
        return words[0][:3].upper()
    return (words[0][:2] + words[-1][0]).upper()


def generate_product_code(category_id):
    category = one("SELECT id, nombre FROM categorias WHERE id = %s FOR UPDATE", (category_id,))
    prefix = category_prefix(category["nombre"])
    codes = query("SELECT codigo FROM productos WHERE codigo LIKE %s", (f"{prefix}-%",))
    sequences = []
    for row in codes:
        match = re.fullmatch(rf"{re.escape(prefix)}-(\d+)", str(row["codigo"]))
        if match:
            sequences.append(int(match.group(1)))
    next_sequence = max(sequences, default=0) + 1
    candidate = f"{prefix}-{next_sequence:03d}"
    while query("SELECT id FROM productos WHERE codigo = %s LIMIT 1", (candidate,)):
        next_sequence += 1
        candidate = f"{prefix}-{next_sequence:03d}"
    return candidate


@endpoint("GET", "POST", access="ADMIN")
@transaction.atomic
def catalog(request, resource):
    if resource not in CATALOGS:
        raise ApiError(404, "Catálogo desconocido.")
    if request.method == "GET":
        return response(query(f"SELECT * FROM {resource} ORDER BY id"))
    submitted = body(request)
    defaults = PRODUCT_DEFAULTS if resource == "productos" else {}
    if resource == "productos":
        category_id = record_id(submitted.get("categoria_id"))
        submitted["codigo"] = generate_product_code(category_id)
    data = clean({**defaults, **submitted}, CATALOGS[resource])
    pk = insert(resource, data)
    return response(one(f"SELECT * FROM {resource} WHERE id = %s", (pk,)), 201)


@endpoint("GET", "PATCH", "DELETE", access="ADMIN")
@transaction.atomic
def catalog_detail(request, resource, pk):
    if resource not in CATALOGS:
        raise ApiError(404, "Catálogo desconocido.")
    pk = record_id(pk)
    sql = f"SELECT * FROM {resource} WHERE id = %s"
    row = one(sql + (" FOR UPDATE" if request.method != "GET" else ""), (pk,))
    if request.method == "GET":
        return response(row)
    if request.method == "DELETE":
        update(resource, pk, {"activo": False})
        return no_content()
    submitted = body(request)
    if resource == "productos":
        if submitted.get("codigo") and submitted["codigo"] != row["codigo"]:
            raise ApiError(422, "El cÃ³digo de producto no se puede editar manualmente.")
        submitted.pop("codigo", None)
        if "categoria_id" in submitted and str(submitted["categoria_id"]) != str(row["categoria_id"]):
            submitted["codigo"] = generate_product_code(record_id(submitted["categoria_id"]))
    update(resource, pk, clean(submitted, CATALOGS[resource], partial=True))
    return response(one(sql, (pk,)))


@endpoint("GET")
def categories(request):
    return response(query("SELECT id, nombre, descripcion FROM categorias WHERE activo = 1 ORDER BY nombre"))


@endpoint("GET")
def products(request):
    category = request.GET.get("categoria_id")
    sql = f"SELECT {PUBLIC_PRODUCT} FROM productos WHERE activo = 1"
    if category is not None:
        return response(query(sql + " AND categoria_id = %s ORDER BY nombre", (record_id(category),)))
    return response(query(sql + " ORDER BY nombre"))


@endpoint("GET")
def product_detail(request, pk):
    return response(one(f"SELECT {PUBLIC_PRODUCT} FROM productos WHERE id = %s AND activo = 1", (record_id(pk),)))


@endpoint("GET", "POST")
def product_comments(request, pk):
    product_id = record_id(pk)
    if request.method == "POST":
        from .sentiments import analyze_comment
        from .users import authenticate

        user = authenticate(request)
        if user["rol"] != "CLIENTE":
            raise ApiError(403, "Solo los clientes pueden publicar comentarios.")
        data = clean(body(request), {"comentario": text(1000)})
        one("SELECT id FROM productos WHERE id = %s AND activo = 1", (product_id,))
        sentiment = analyze_comment(data["comentario"])
        comment_id = insert("comentarios_productos", {
            "producto_id": product_id, "usuario_id": user["id"],
            "comentario": data["comentario"], "sentimiento": sentiment,
        })
        return response(one(
            "SELECT c.id, c.producto_id, c.comentario, c.fecha, u.nombre, u.apellido "
            "FROM comentarios_productos c JOIN usuarios u ON u.id = c.usuario_id WHERE c.id = %s",
            (comment_id,),
        ), 201)
    one("SELECT id FROM productos WHERE id = %s AND activo = 1", (product_id,))
    sql = (
        "SELECT c.id, c.producto_id, c.comentario, c.fecha, u.nombre, u.apellido "
        "FROM comentarios_productos c JOIN usuarios u ON u.id = c.usuario_id "
    )
    return response(query(sql + "WHERE c.producto_id = %s ORDER BY c.fecha DESC, c.id DESC", (product_id,)))


def lock_products(ids):
    return {pk: one("SELECT * FROM productos WHERE id = %s FOR UPDATE", (pk,)) for pk in sorted(set(ids))}


def require_active(products):
    if any(not row["activo"] for row in products.values()):
        raise ApiError(409, "Hay productos inactivos.")


def move_stock(product, *, user_id, kind, quantity, reason):
    before = product["existencia"]
    if kind == "AJUSTE":
        after = quantity
    elif kind == "ENTRADA":
        after = before + quantity
    else:
        after = before - quantity
    if after < 0:
        raise ApiError(409, "Existencias insuficientes.")
    if after >= Decimal("1000000000"):
        raise ApiError(422, "Existencia fuera del rango permitido.")
    if after == before:
        raise ApiError(409, "El movimiento no cambia la existencia.")
    update("productos", product["id"], {"existencia": after})
    pk = insert("movimientos_inventario", {
        "producto_id": product["id"], "usuario_id": user_id, "tipo": kind, "cantidad": abs(after - before),
        "existencia_anterior": before, "existencia_nueva": after, "motivo": reason,
    })
    product["existencia"] = after
    return pk


@endpoint("GET", "POST", access="ADMIN")
def movements(request):
    if request.method == "GET":
        product = request.GET.get("producto_id")
        sql = "SELECT * FROM movimientos_inventario"
        if product is not None:
            return response(query(sql + " WHERE producto_id = %s ORDER BY id DESC", (record_id(product),)))
        return response(query(sql + " ORDER BY id DESC"))
    data = clean(body(request), {
        "producto_id": RecordId(), "tipo": forms.ChoiceField(choices=[(k, k) for k in ("ENTRADA", "SALIDA", "AJUSTE")]),
        "cantidad": decimal_field(3), "motivo": text(255),
    })
    with transaction.atomic():
        product = lock_products([data["producto_id"]])[data["producto_id"]]
        pk = move_stock(
            product, user_id=request.api_user["id"], kind=data["tipo"], quantity=data["cantidad"], reason=data["motivo"],
        )
    return response(one("SELECT * FROM movimientos_inventario WHERE id = %s", (pk,)), 201)
