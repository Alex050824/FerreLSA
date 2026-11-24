from hashlib import sha256
from hmac import compare_digest

from django import forms
from django.conf import settings
from django.db import transaction

from .db import one, query, update
from .http import ApiError, body, clean, endpoint, no_content, record_id
from .inventory import decimal_field
from .sales import reverse_sale


def require_integration(request):
    secret = settings.ERP_PAYPAL_SECRET
    if len(secret) < 32:
        raise ApiError(503, "Integración de pagos sin configurar.")
    supplied = request.headers.get("X-Integration-Key", "")
    if not compare_digest(supplied.encode(), secret.encode()):
        raise ApiError(401, "Credencial de integración inválida.")


@endpoint("POST")
def confirm(request, pk):
    require_integration(request)
    pk = record_id(pk)
    payment = clean(body(request), {
        "referencia_pago": forms.RegexField(r"\A[A-Z0-9-]{1,120}\Z"),
        "importe": decimal_field(2),
        "moneda": forms.RegexField(r"\A[A-Z]{3}\Z"),
    })
    reference = payment["referencia_pago"]
    lock = sha256(f"ferrelsa-paypal:{reference}".encode()).hexdigest()
    result = query("SELECT GET_LOCK(%s, 5) AS acquired", (lock,))
    if result[0]["acquired"] != 1:
        raise ApiError(409, "Operación en curso. Volvé a intentar.")
    try:
        with transaction.atomic():
            sale = one("SELECT * FROM ventas WHERE id = %s FOR UPDATE", (pk,))
            if (sale["metodo_pago"] != "PAYPAL" or sale["total"] != payment["importe"]
                    or payment["moneda"] != settings.ERP_PAYPAL_CURRENCY):
                raise ApiError(422, "El pago no coincide con la venta.")
            if sale["estado"] == "PAGADA" and sale["referencia_pago"] == reference:
                return no_content()
            if sale["estado"] != "PENDIENTE":
                raise ApiError(409, "La venta ya fue procesada.")
            if query("SELECT id FROM ventas WHERE metodo_pago = 'PAYPAL' AND referencia_pago = %s LIMIT 1", (reference,)):
                raise ApiError(409, "La referencia ya pertenece a otra venta.")
            update("ventas", pk, {
                "estado": "PAGADA", "referencia_pago": reference, "numero_comprobante": f"C-{sale['numero']}",
            })
    finally:
        query("SELECT RELEASE_LOCK(%s)", (lock,))
    return no_content()


@endpoint("POST")
def cancel(request, pk):
    require_integration(request)
    reverse_sale(record_id(pk), None, credit=False)
    return no_content()
