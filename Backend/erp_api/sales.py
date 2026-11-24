from django.db import transaction

from .db import insert, one, query, update
from .http import ApiError, RecordId, body, clean, endpoint, record_id, response, text
from .inventory import lock_products, move_stock, require_active
from .order_values import ITEM, NUMBER, choices, money, parse_items, totals

HEADER = {
    "numero": NUMBER, "canal": choices("LOCAL", "EN_LINEA"), "metodo_pago": choices("EFECTIVO", "TARJETA", "PAYPAL"),
    "usuario_id": RecordId(required=False), "tipo_comprobante": choices("TIQUETE", "FACTURA"),
    "modalidad_entrega": choices("RETIRO_TIENDA", "ENVIO_DOMICILIO"),
    "direccion_entrega": text(500, required=False), "observaciones": text(10000, required=False),
}


def lines(pk):
    return query("SELECT * FROM detalles_venta WHERE venta_id = %s ORDER BY id", (pk,))


def visible_sales(user):
    return ("", ()) if user["rol"] == "ADMIN" else ("usuario_id = %s", (user["id"],))


def find_sale(pk, user):
    owner, params = visible_sales(user)
    condition = " AND " + owner if owner else ""
    return one("SELECT * FROM ventas WHERE id = %s" + condition, (pk, *params))


@transaction.atomic
def create_sale(data, rows, user):
    online = data["canal"] == "EN_LINEA"
    customer = data.pop("usuario_id", None)
    if online != (data["metodo_pago"] == "PAYPAL"):
        raise ApiError(422, "Método de pago incompatible con el canal.")
    if not online and user["rol"] != "ADMIN":
        raise ApiError(403, "La venta local requiere un administrador.")
    if online and customer is not None:
        raise ApiError(422, "La cuenta de la venta en línea se toma del token.")
    if data["modalidad_entrega"] == "ENVIO_DOMICILIO" and not data.get("direccion_entrega"):
        raise ApiError(422, "Indicá la dirección de entrega.")
    if customer is not None:
        one("SELECT id FROM usuarios WHERE id = %s AND activo = 1 AND rol = 'CLIENTE' FOR SHARE", (customer,))
    products = lock_products(row["producto_id"] for row in rows)
    require_active(products)
    for row in rows:
        price = products[row["producto_id"]]["precio_venta"]
        row.update(precio_unitario=price, total_linea=money(row["cantidad"] * price))
    pk = insert("ventas", {
        **data, **totals(rows), "usuario_id": user["id"] if online else customer,
        "atendido_por_id": None if online else user["id"], "estado": "PENDIENTE" if online else "PAGADA",
        "numero_comprobante": None if online else f"C-{data['numero']}",
    })
    for row in rows:
        insert("detalles_venta", {**row, "venta_id": pk})
        move_stock(
            products[row["producto_id"]], user_id=user["id"], kind="SALIDA",
            quantity=row["cantidad"], reason=f"Venta API #{pk}",
        )
    return pk


@transaction.atomic
def reverse_sale(pk, user_id, *, credit):
    sale = one("SELECT * FROM ventas WHERE id = %s FOR UPDATE", (pk,))
    expected_channel = "LOCAL" if credit else "EN_LINEA"
    if sale["canal"] != expected_channel:
        raise ApiError(409, "El canal de la venta no admite esta operación.")
    if sale["estado"] == "ANULADA" and bool(sale["numero_comprobante"]) == credit:
        return sale
    if sale["estado"] != ("PAGADA" if credit else "PENDIENTE") or bool(sale["numero_comprobante"]) != credit:
        raise ApiError(409, "El estado de la venta no admite esta operación.")
    rows = lines(pk)
    reserved = query(
        "SELECT producto_id, cantidad FROM movimientos_inventario WHERE motivo = %s AND tipo = 'SALIDA'",
        (f"Venta API #{pk}",),
    )
    by_product = {row["producto_id"]: row["cantidad"] for row in reserved}
    if not rows or len(reserved) != len(rows) or any(by_product.get(row["producto_id"]) != row["cantidad"] for row in rows):
        raise ApiError(409, "No se encontraron los movimientos de salida de esta venta.")
    products = lock_products(row["producto_id"] for row in rows)
    for row in rows:
        move_stock(
            products[row["producto_id"]], user_id=user_id, kind="ENTRADA",
            quantity=row["cantidad"], reason=f"Anulación {sale['numero']}",
        )
    update("ventas", pk, {"estado": "ANULADA"})
    return sale


def credit_note(sale):
    return {"tipo": "NOTA_CREDITO", "numero": f"NC-{sale['numero_comprobante']}", "total": sale["total"]}


@endpoint("GET", "POST", access="USER")
def sales(request):
    user = request.api_user
    if request.method == "GET":
        where, params = visible_sales(user)
        clause = " WHERE " + where if where else ""
        return response(query("SELECT * FROM ventas" + clause + " ORDER BY id DESC", params))
    data = body(request)
    rows = parse_items(data, ITEM)
    values = clean({"tipo_comprobante": "TIQUETE", "modalidad_entrega": "RETIRO_TIENDA", **data}, HEADER)
    pk = create_sale(values, rows, user)
    return response({**find_sale(pk, user), "detalles": lines(pk)}, 201)


@endpoint("GET", access="USER")
def sale_detail(request, pk):
    pk = record_id(pk)
    return response({**find_sale(pk, request.api_user), "detalles": lines(pk)})


@endpoint("GET", access="USER")
def receipt(request, pk):
    pk = record_id(pk)
    sale = find_sale(pk, request.api_user)
    if not sale["numero_comprobante"]:
        raise ApiError(404, "La venta todavía no tiene comprobante.")
    note = credit_note(sale) if sale["canal"] == "LOCAL" and sale["estado"] == "ANULADA" else None
    return response({**sale, "detalles": lines(pk), "nota_credito": note})


@endpoint("POST", access="ADMIN")
def refund(request, pk):
    return response(credit_note(reverse_sale(record_id(pk), request.api_user["id"], credit=True)))
