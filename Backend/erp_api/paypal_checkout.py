
import os
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

import requests
from django.db import transaction

from .db import insert, one, query, update
from .http import ApiError, endpoint, record_id, response
from .paypal_client import (
    PAYPAL_URL,
    obtener_token_paypal,
    crear_orden_paypal,
    capturar_orden_paypal,
)
from .sales import reverse_sale


def obtener_tipo_cambio():
    try:
        tasa = Decimal(os.getenv("PAYPAL_CRC_POR_USD", ""))
    except InvalidOperation:
        raise ApiError(503, "Configurá el tipo de cambio de PayPal.")

    if not tasa.is_finite() or tasa <= 0:
        raise ApiError(503, "El tipo de cambio es inválido.")

    return tasa


@endpoint("POST", access="USER")
def crear_orden_venta(request, pk):
    venta_id = record_id(pk)

    with transaction.atomic():
        venta = one(
            """
            SELECT id, usuario_id, canal, metodo_pago,
                   estado, total
            FROM ventas
            WHERE id = %s AND usuario_id = %s
            FOR UPDATE
            """,
            (venta_id, request.api_user["id"]),
        )

        if (
            venta["canal"] != "EN_LINEA"
            or venta["metodo_pago"] != "PAYPAL"
            or venta["estado"] != "PENDIENTE"
        ):
            raise ApiError(
                409, "La venta no está pendiente de pago con PayPal."
            )

        pagos = query(
            "SELECT * FROM pagos_paypal WHERE venta_id = %s",
            (venta_id,),
        )

        if pagos:
            pago = pagos[0]

            if pago["estado"] != "CREADO" or not pago["paypal_orden_id"]:
                raise ApiError(
                    409, "El pago existente requiere revisión."
                )

            return response({
                "orden_id": pago["paypal_orden_id"],
                "total_crc": str(pago["total_crc"]),
                "total_usd": str(pago["total_usd"]),
                "tipo_cambio": str(pago["tipo_cambio_crc_usd"]),
            })

        tasa = obtener_tipo_cambio()
        total_crc = venta["total"]
        total_usd = (total_crc / tasa).quantize(
            Decimal("0.01"),
            rounding=ROUND_HALF_UP,
        )

        if total_usd <= 0:
            raise ApiError(422, "El importe es demasiado pequeño.")

        pago_id = insert("pagos_paypal", {
            "venta_id": venta_id,
            "total_crc": total_crc,
            "tipo_cambio_crc_usd": tasa,
            "total_usd": total_usd,
            "estado": "INICIADO",
        })

        try:
            orden = crear_orden_paypal(venta_id, total_usd)
        except requests.RequestException:
            raise ApiError(
                502, "No fue posible crear la orden en PayPal."
            ) from None

        if orden.get("status") != "CREATED" or not orden.get("id"):
            raise ApiError(
                502, "PayPal no confirmó la creación de la orden."
            )

        update("pagos_paypal", pago_id, {
            "paypal_orden_id": orden["id"],
            "estado": "CREADO",
        })

    return response({
        "orden_id": orden["id"],
        "total_crc": str(total_crc),
        "total_usd": str(total_usd),
        "tipo_cambio": str(tasa),
    }, 201)
    
    
def consultar_orden_paypal(orden_id):
    respuesta = requests.get(
        f"{PAYPAL_URL}/v2/checkout/orders/{orden_id}",
        headers={
            "Authorization": f"Bearer {obtener_token_paypal()}"
        },
        timeout=20,
    )
    respuesta.raise_for_status()
    return respuesta.json()


def verificar_captura(orden, venta_id, pago):
    if (
        orden.get("id") != pago["paypal_orden_id"]
        or orden.get("status") != "COMPLETED"
    ):
        return None

    unidades = orden.get("purchase_units") or []

    if len(unidades) != 1:
        return None

    unidad = unidades[0]

    if str(unidad.get("reference_id")) != str(venta_id):
        return None

    capturas = (
        unidad.get("payments") or {}
    ).get("captures") or []

    if len(capturas) != 1:
        return None

    captura = capturas[0]
    importe_orden = unidad.get("amount") or {}
    importe_captura = captura.get("amount") or {}

    try:
        total_esperado = Decimal(str(pago["total_usd"]))
        total_orden = Decimal(str(importe_orden["value"]))
        total_capturado = Decimal(str(importe_captura["value"]))
    except (KeyError, ValueError, TypeError, InvalidOperation):
        return None

    if (
        captura.get("status") != "COMPLETED"
        or captura.get("final_capture") is not True
        or importe_orden.get("currency_code") != "USD"
        or importe_captura.get("currency_code") != "USD"
        or total_orden != total_esperado
        or total_capturado != total_esperado
        or not captura.get("id")
    ):
        return None

    return captura["id"]


@endpoint("POST", access="USER")
def capturar_pago_venta(request, pk):
    venta_id = record_id(pk)
    usuario_id = request.api_user["id"]
    bloqueo = f"ferrelsa-paypal-captura:{venta_id}"

    resultado = query(
        "SELECT GET_LOCK(%s, 5) AS adquirido",
        (bloqueo,),
    )

    if resultado[0]["adquirido"] != 1:
        raise ApiError(409, "Hay un pago en proceso.")

    try:
        with transaction.atomic():
            venta = one(
                """
                SELECT *
                FROM ventas
                WHERE id = %s AND usuario_id = %s
                FOR UPDATE
                """,
                (venta_id, usuario_id),
            )

            pago = one(
                """
                SELECT *
                FROM pagos_paypal
                WHERE venta_id = %s
                FOR UPDATE
                """,
                (venta_id,),
            )

            if (
                venta["estado"] == "PAGADA"
                and pago["estado"] == "CAPTURADO"
                and venta["referencia_pago"] == pago["paypal_captura_id"]
            ):
                return response({
                    "estado": "PAGADA",
                    "captura_id": pago["paypal_captura_id"],
                })

            if (
                venta["estado"] != "PENDIENTE"
                or venta["metodo_pago"] != "PAYPAL"
                or venta["canal"] != "EN_LINEA"
                or pago["estado"] != "CREADO"
                or not pago["paypal_orden_id"]
                or venta["total"] != pago["total_crc"]
            ):
                raise ApiError(409, "La venta no admite este pago.")

            orden_id = pago["paypal_orden_id"]

        try:
            orden = consultar_orden_paypal(orden_id)

            if orden.get("status") == "APPROVED":
                try:
                    capturar_orden_paypal(venta_id, orden_id)
                except requests.RequestException:
                    # Consultamos PayPal antes de asumir
                    # que el cobro falló.
                    pass

                orden = consultar_orden_paypal(orden_id)

        except requests.RequestException:
            raise ApiError(
                502,
                "No fue posible verificar el pago. Intentá consultar nuevamente.",
            ) from None

        captura_id = verificar_captura(
            orden, venta_id, pago
        )

        if not captura_id:
            raise ApiError(
                409,
                "PayPal todavía no confirma el cobro.",
            )

        with transaction.atomic():
            venta = one(
                """
                SELECT *
                FROM ventas
                WHERE id = %s AND usuario_id = %s
                FOR UPDATE
                """,
                (venta_id, usuario_id),
            )

            pago_actual = one(
                """
                SELECT *
                FROM pagos_paypal
                WHERE venta_id = %s
                FOR UPDATE
                """,
                (venta_id,),
            )

            if (
                venta["estado"] != "PENDIENTE"
                or pago_actual["estado"] != "CREADO"
                or pago_actual["paypal_orden_id"] != orden_id
                or pago_actual["total_usd"] != pago["total_usd"]
            ):
                raise ApiError(
                    409,
                    "La venta cambió de estado. Revisá el pago.",
                )

            update("pagos_paypal", pago_actual["id"], {
                "paypal_captura_id": captura_id,
                "estado": "CAPTURADO",
            })

            update("ventas", venta_id, {
                "estado": "PAGADA",
                "referencia_pago": captura_id,
                "numero_comprobante": f"C-{venta['numero']}",
            })

        return response({
            "estado": "PAGADA",
            "captura_id": captura_id,
        })

    finally:
        query(
            "SELECT RELEASE_LOCK(%s)",
            (bloqueo,),
        )

@endpoint("POST", access="USER")
def cancelar_orden_venta(request, pk):
    venta_id = record_id(pk)
    usuario_id = request.api_user["id"]

    # Utilizamos el mismo bloqueo que la captura.
    bloqueo = f"ferrelsa-paypal-captura:{venta_id}"

    resultado = query(
        "SELECT GET_LOCK(%s, 5) AS adquirido",
        (bloqueo,),
    )

    if not resultado or resultado[0]["adquirido"] != 1:
        raise ApiError(409, "Hay un pago en proceso.")

    try:
        venta = one(
            """
            SELECT *
            FROM ventas
            WHERE id = %s AND usuario_id = %s
            """,
            (venta_id, usuario_id),
        )

        if venta["estado"] == "ANULADA":
            return response({"estado": "ANULADA"})

        if (
            venta["estado"] != "PENDIENTE"
            or venta["canal"] != "EN_LINEA"
            or venta["metodo_pago"] != "PAYPAL"
        ):
            raise ApiError(
                409, "La venta no puede cancelarse."
            )

        pagos = query(
            "SELECT * FROM pagos_paypal WHERE venta_id = %s",
            (venta_id,),
        )

        pago = pagos[0] if pagos else None

        if pago:
            if pago["estado"] not in ("INICIADO", "CREADO"):
                raise ApiError(
                    409, "El pago requiere revisión."
                )

            if pago["estado"] == "CREADO" and not pago["paypal_orden_id"]:
                raise ApiError(
                    409, "La orden requiere revisión."
                )

            if pago["paypal_orden_id"]:
                try:
                    orden = consultar_orden_paypal(
                        pago["paypal_orden_id"]
                    )
                except requests.RequestException:
                    raise ApiError(
                        502,
                        "No se pudo verificar PayPal. "
                        "No se canceló la venta.",
                    ) from None

                estados_permitidos = {
                    "CREATED",
                    "SAVED",
                    "APPROVED",
                    "PAYER_ACTION_REQUIRED",
                    "VOIDED",
                }

                if orden.get("status") not in estados_permitidos:
                    raise ApiError(
                        409,
                        "Revisá el estado del pago en PayPal."
                    )

                unidades = orden.get("purchase_units") or []

                if any(
                    (unidad.get("payments") or {}).get("captures")
                    or (unidad.get("payments") or {}).get("authorizations")
                    for unidad in unidades
                ):
                    raise ApiError(
                        409,
                        "PayPal registra una operación de pago."
                    )

        # Se devuelve el inventario y se actualiza
        # el pago en una misma transacción de MySQL.
        with transaction.atomic():
            reverse_sale(venta_id, usuario_id, credit=False)

            if pago:
                update("pagos_paypal", pago["id"], {
                    "estado": "CANCELADO",
                })

        return response({
            "estado": "ANULADA",
            "mensaje": "Pedido cancelado e inventario recuperado.",
        })

    finally:
        query(
            "SELECT RELEASE_LOCK(%s)",
            (bloqueo,),
        )

