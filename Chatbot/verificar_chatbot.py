"""Ejecutar con el Python del proyecto: python verificar_chatbot.py.

Prueba el endpoint con CSRF y modelos reales. Solo lee el catálogo configurado
en Django. Muestra los textos completos para revisar también las recomendaciones.
"""

import os
import re
import sys
from decimal import Decimal
from time import perf_counter

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

import django

django.setup()

from django.db import connection
from django.test import Client, override_settings
from chatbot_api.views import LIMITE_LISTADO


# Las etiquetas solo se usan para evaluar. Si el artículo no está en MySQL,
# se espera abstención. Una recomendación abierta requiere revisar su explicación.
CASOS = [
    ("¿Cuánto cuesta el martillo de acero?", ("martillo de acero",)),
    ("¿Tienen taladros disponibles?", ("taladro",)),
    ("¿Venden cemento?", ("cemento",)),
    ("Necesito algo para perforar paredes.", ("taladro",)),
    ("Necesito clavar un clavo.", ("martillo",)),
    ("Quiero cambiar el color de una habitación.", ("pintura",)),
    ("¿Qué características tiene el taladro eléctrico?", ("taladro eléctrico",)),
    ("¿Qué productos tienen disponibles?", "listado"),
    ("¿Cuánto cuesta un producto que no está registrado?", ()),
    ("¿Qué me recomiendas para realizar trabajos de carpintería?", None),
    ("¿Cuánto cuestan el martillo y el taladro?", ("martillo", "taladro")),
    ("¿Venden telescopios astronómicos?", ("telescopio",)),
    ("Necesito imprimir un documento.", ("impresora",)),
    ("Quiero hornear un pastel.", ("horno",)),
    ("Busco algo que haga agujeros en una pared.", ("taladro",)),
    ("Quiero pintar el dormitorio.", ("pintura",)),
]


def verificar(criterio, datos, catalogo):
    productos = datos["productos"]
    codigos = {p["codigo"] for p in productos}
    lineas = datos["respuesta"].splitlines()
    for ficha in productos:
        nombre, descripcion, precio, cantidad, unidad = catalogo[ficha["codigo"]]
        assert (ficha["nombre"], ficha["descripcion"], ficha["unidad_medida"]) == (nombre, descripcion, unidad)
        for campo, valor in (("precio_venta", precio), ("existencia", cantidad)):
            assert (None if ficha[campo] is None else Decimal(ficha[campo])) == valor
        assert ficha["moneda"] == "CRC" and nombre in datos["respuesta"]
        encabezado = f"{nombre} — "
        importe = "Precio sin registrar"
        if precio is not None:
            entero, _, decimales = f"{precio:,f}".partition(".")
            decimales = decimales.rstrip("0")
            importe = "₡" + entero.replace(",", ".") + ("," + decimales.ljust(2, "0") if decimales else "")
        if cantidad is None:
            stock = "Existencia sin registrar"
        elif cantidad <= 0:
            stock = "Agotado"
        else:
            numero = format(cantidad.normalize(), "f").replace(".", ",")
            if (unidad or "").casefold() == "unidad":
                stock = numero + (" unidad" if cantidad == 1 else " unidades")
            else:
                stock = f"Existencia ({unidad}): {numero}" if unidad else f"Existencia: {numero}"
        assert f"{encabezado}{importe} · {stock}." in lineas, f"Ficha visible incorrecta para {nombre}"
    importes = re.findall(r"₡([\d.]+(?:,\d+)?)", datos["respuesta"])
    importes = [Decimal(importe.replace(".", "").replace(",", ".")) for importe in importes]
    precios = [catalogo[c][2] for c in codigos if catalogo[c][2] is not None]
    assert sorted(importes) == sorted(precios), "Importe inesperado en el chat"

    if criterio == "listado":
        disponibles = {c for c, fila in catalogo.items() if fila[3] is not None and fila[3] > 0}
        assert codigos <= disponibles and len(codigos) == min(LIMITE_LISTADO, len(disponibles))
    elif criterio is not None:
        grupos = [{c for c, fila in catalogo.items() if palabra in fila[0].casefold()} for palabra in criterio]
        assert codigos <= set().union(*grupos), "Artículo fuera de los esperados"
        assert all(not grupo or grupo & codigos for grupo in grupos), "Faltó un producto esperado"


def main():
    # Consulta independiente de la implementación que se está evaluando.
    with connection.cursor() as cursor:
        cursor.execute("""SELECT codigo, nombre, descripcion, precio_venta, existencia, unidad_medida
                          FROM productos WHERE activo = 1""")
        catalogo = {codigo: fila for codigo, *fila in cursor.fetchall()}
    print(f"Productos activos en MySQL: {len(catalogo)}", flush=True)
    fallos = 0
    with override_settings(ALLOWED_HOSTS=["testserver"]):
        cliente = Client(enforce_csrf_checks=True)
        cliente.get("/api/chatbot/csrf/")
        token = cliente.cookies["csrftoken"].value
        for pregunta, criterio in CASOS:
            inicio = perf_counter()
            respuesta = cliente.post("/api/chatbot/preguntar/", {"pregunta": pregunta},
                                     content_type="application/json", HTTP_X_CSRFTOKEN=token)
            duracion = perf_counter() - inicio
            try:
                assert respuesta.status_code == 200, f"HTTP {respuesta.status_code}"
                datos = respuesta.json()
                print(f"\n{pregunta}\n{datos['respuesta']}\n{datos['tiempos_ms']} · HTTP {duracion:.3f} s",
                      flush=True)
                verificar(criterio, datos, catalogo)
            except (AssertionError, KeyError) as error:
                fallos += 1
                print(f"FALLÓ: {pregunta} — {error}", flush=True)
    print(f"\n{len(CASOS)} consultas, {fallos} fallos. Revisá el texto del caso abierto de carpintería.")
    return bool(fallos)


if __name__ == "__main__":
    sys.exit(main())
