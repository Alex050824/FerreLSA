from django import forms
from django.db import transaction

from .db import insert, one, query, update
from .http import ApiError, RecordId, body, clean, endpoint, record_id, response, text
from .inventory import decimal_field, lock_products, move_stock, require_active
from .order_values import ITEM, NUMBER, money, parse_items, totals

HEADER = {
    "numero": NUMBER, "proveedor_id": RecordId(), "fecha": forms.DateField(input_formats=["%Y-%m-%d"]),
    "observaciones": text(10000, required=False),
}
ITEM_FIELDS = {**ITEM, "costo_unitario": decimal_field(2)}


def lines(pk):
    return query("SELECT * FROM detalles_orden_compra WHERE orden_compra_id = %s ORDER BY id", (pk,))


def details(pk):
    order = one("SELECT * FROM ordenes_compra WHERE id = %s", (pk,))
    return {**order, "detalles": lines(pk)}


@endpoint("GET", "POST", access="ADMIN")
def purchases(request):
    if request.method == "GET":
        return response(query("SELECT * FROM ordenes_compra ORDER BY id DESC"))
    data = body(request)
    rows = parse_items(data, ITEM_FIELDS)
    header = clean(data, HEADER)
    for row in rows:
        row["total_linea"] = money(row["cantidad"] * row["costo_unitario"])
    with transaction.atomic():
        one("SELECT id FROM proveedores WHERE id = %s AND activo = 1 FOR SHARE", (header["proveedor_id"],))
        require_active(lock_products(row["producto_id"] for row in rows))
        pk = insert("ordenes_compra", {**header, **totals(rows), "usuario_id": request.api_user["id"]})
        for row in rows:
            insert("detalles_orden_compra", {**row, "orden_compra_id": pk})
    return response(details(pk), 201)


@endpoint("GET", access="ADMIN")
def purchase_detail(request, pk):
    return response(details(record_id(pk)))


@endpoint("POST", access="ADMIN")
def transition(request, pk, status):
    pk = record_id(pk)
    with transaction.atomic():
        order = one("SELECT * FROM ordenes_compra WHERE id = %s FOR UPDATE", (pk,))
        if order["estado"] != status:
            if order["estado"] != "PENDIENTE":
                raise ApiError(409, "La orden ya fue cerrada.")
            if status == "RECIBIDA":
                rows = lines(pk)
                products = lock_products(row["producto_id"] for row in rows)
                for row in rows:
                    move_stock(
                        products[row["producto_id"]], user_id=request.api_user["id"], kind="ENTRADA",
                        quantity=row["cantidad"], reason=f"Recepción {order['numero']}",
                    )
            update("ordenes_compra", pk, {"estado": status})
    return response(details(pk))
