
from django.db import connection


def obtener_productos():
    with connection.cursor() as cursor:
        cursor.execute("""
            SELECT codigo, nombre, descripcion, precio_venta, existencia
            FROM productos
            WHERE activo = 1
            ORDER BY nombre
        """)

        productos = cursor.fetchall()

    return productos
