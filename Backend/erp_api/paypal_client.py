
import os
import re
from decimal import Decimal, ROUND_HALF_UP

import requests


PAYPAL_URL = "https://api-m.sandbox.paypal.com"


def obtener_token_paypal():
    client_id = os.getenv("PAYPAL_CLIENT_ID")
    client_secret = os.getenv("PAYPAL_CLIENT_SECRET")

    if not client_id or not client_secret:
        raise RuntimeError("Faltan las credenciales de PayPal.")

    respuesta = requests.post(
        f"{PAYPAL_URL}/v1/oauth2/token",
        auth=(client_id, client_secret),
        data={"grant_type": "client_credentials"},
        timeout=20,
    )

    respuesta.raise_for_status()
    return respuesta.json()["access_token"]


def solicitar_paypal(ruta, datos, identificador):
    respuesta = requests.post(
        f"{PAYPAL_URL}{ruta}",
        headers={
            "Authorization": f"Bearer {obtener_token_paypal()}",
            "Content-Type": "application/json",
            "PayPal-Request-Id": identificador,
        },
        json=datos,
        timeout=30,
    )

    respuesta.raise_for_status()
    return respuesta.json()


def crear_orden_paypal(venta_id, total_usd):
    monto = Decimal(str(total_usd))

    if not monto.is_finite() or monto <= 0:
        raise ValueError("El monto debe ser positivo.")

    monto = monto.quantize(
        Decimal("0.01"),
        rounding=ROUND_HALF_UP,
    )

    datos = {
        "intent": "CAPTURE",
        "purchase_units": [{
            "reference_id": str(venta_id),
            "amount": {
                "currency_code": "USD",
                "value": format(monto, ".2f"),
            },
        }],
    }

    return solicitar_paypal(
        "/v2/checkout/orders",
        datos,
        f"ferrelsa-crear-{venta_id}",
    )


def capturar_orden_paypal(venta_id, orden_id):
    if not re.fullmatch(r"[A-Z0-9]{1,36}", orden_id):
        raise ValueError("Identificador de orden inválido.")

    return solicitar_paypal(
        f"/v2/checkout/orders/{orden_id}/capture",
        {},
        f"ferrelsa-capturar-{venta_id}",
    )
