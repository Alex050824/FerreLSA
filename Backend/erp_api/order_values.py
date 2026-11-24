from decimal import Decimal, ROUND_HALF_UP

from django import forms
from django.conf import settings

from .http import ApiError, RecordId, clean
from .inventory import decimal_field

NUMBER = forms.RegexField(r"\A[A-Za-z0-9_-]{1,40}\Z")
ITEM = {"producto_id": RecordId(), "cantidad": decimal_field(3, minimum=Decimal("0.001"))}


def choices(*values, required=True):
    return forms.ChoiceField(choices=[(value, value) for value in values], required=required)


def parse_items(data, fields):
    items = data.pop("detalles", None)
    if not isinstance(items, list) or not 1 <= len(items) <= 100:
        raise ApiError(422, "Enviá entre 1 y 100 líneas de detalle.")
    rows = [clean(item, fields) for item in items]
    if len({row["producto_id"] for row in rows}) != len(rows):
        raise ApiError(422, "Cada producto debe aparecer una sola vez.")
    return rows


def money(value):
    rounded = value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    if rounded >= Decimal("10000000000"):
        raise ApiError(422, "El importe excede el rango admitido.")
    return rounded


def totals(rows):
    subtotal = money(sum((row["total_linea"] for row in rows), Decimal("0")))
    tax = money(subtotal * settings.ERP_TAX_RATE)
    return {"subtotal": subtotal, "impuesto": tax, "total": money(subtotal + tax)}
