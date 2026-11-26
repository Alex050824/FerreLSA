from datetime import date, timedelta

from django.utils import timezone

from .db import query
from .http import endpoint, response


def month_start(months_back=0):
    today = timezone.localdate()
    index = today.year * 12 + today.month - 1 - months_back
    return date(index // 12, index % 12 + 1, 1)


@endpoint("GET", access="ADMIN")
def summary(request):
    today = timezone.localdate()
    start = today.replace(day=1)
    chart_start = month_start(5)

    financial_rows = query(
        "SELECT YEAR(fecha) AS anio, MONTH(fecha) AS mes, "
        "SUM(ingreso) AS ingresos, SUM(salida) AS salidas FROM ("
        "SELECT fecha, total AS ingreso, 0 AS salida FROM ventas "
        "WHERE estado = 'PAGADA' AND fecha >= %s "
        "UNION ALL "
        "SELECT fecha, 0 AS ingreso, total AS salida FROM ordenes_compra "
        "WHERE estado = 'RECIBIDA' AND fecha >= %s"
        ") AS movimientos_financieros GROUP BY YEAR(fecha), MONTH(fecha) ORDER BY anio, mes",
        (chart_start, chart_start),
    )
    monthly = {
        (int(row["anio"]), int(row["mes"])): {
            "ingresos": row["ingresos"] or 0,
            "salidas": row["salidas"] or 0,
        }
        for row in financial_rows
    }
    months = []
    for offset in reversed(range(6)):
        first = month_start(offset)
        values = monthly.get((first.year, first.month), {"ingresos": 0, "salidas": 0})
        months.append({"periodo": first.isoformat()[:7], **values})

    sales = query(
        "SELECT COALESCE(SUM(total), 0) AS total FROM ventas "
        "WHERE estado = 'PAGADA' AND fecha >= %s AND fecha < %s",
        (start, month_start(-1)),
    )[0]["total"]
    purchases = query(
        "SELECT COALESCE(SUM(total), 0) AS total FROM ordenes_compra "
        "WHERE estado = 'RECIBIDA' AND fecha >= %s AND fecha < %s",
        (start, month_start(-1)),
    )[0]["total"]
    product_stats = query(
        "SELECT "
        "COALESCE(SUM(CASE WHEN activo = 1 AND existencia > 0 THEN 1 ELSE 0 END), 0) AS disponibles, "
        "COALESCE(SUM(CASE WHEN activo = 1 AND existencia <= 0 THEN 1 ELSE 0 END), 0) AS agotados, "
        "COALESCE(SUM(CASE WHEN activo = 1 AND existencia > 0 AND existencia <= stock_minimo THEN 1 ELSE 0 END), 0) AS stock_bajo, "
        "COALESCE(SUM(CASE WHEN activo = 1 THEN existencia * precio_compra ELSE 0 END), 0) AS valor_inventario "
        "FROM productos"
    )[0]
    stats = query(
        "SELECT "
        "(SELECT COUNT(*) FROM ordenes_compra WHERE estado = 'PENDIENTE') AS compras_pendientes, "
        "(SELECT COUNT(*) FROM ventas WHERE canal = 'EN_LINEA' AND estado = 'PENDIENTE') AS pedidos_web_pendientes, "
        "(SELECT COUNT(*) FROM usuarios WHERE rol = 'CLIENTE' AND activo = 1) AS clientes_activos, "
        "(SELECT COALESCE(SUM(cantidad), 0) FROM movimientos_inventario "
        " WHERE tipo = 'SALIDA' AND fecha >= %s) AS unidades_salida_30d",
        (today - timedelta(days=30),),
    )[0]
    alerts = query(
        "SELECT p.id, p.nombre, p.existencia, p.stock_minimo, p.unidad_medida, c.nombre AS categoria "
        "FROM productos p LEFT JOIN categorias c ON c.id = p.categoria_id "
        "WHERE p.activo = 1 AND p.existencia <= p.stock_minimo "
        "ORDER BY (p.existencia <= 0) DESC, p.existencia ASC, p.stock_minimo DESC, p.nombre LIMIT 8"
    )
    recent_sales = query(
        "SELECT id, numero, canal, estado, fecha, total FROM ventas ORDER BY fecha DESC, id DESC LIMIT 6"
    )
    pending_purchases = query(
        "SELECT o.id, o.numero, o.fecha, o.total, p.nombre AS proveedor "
        "FROM ordenes_compra o LEFT JOIN proveedores p ON p.id = o.proveedor_id "
        "WHERE o.estado = 'PENDIENTE' ORDER BY o.fecha ASC, o.id ASC LIMIT 6"
    )
    recent_movements = query(
        "SELECT m.id, m.tipo, m.cantidad, m.existencia_anterior, m.existencia_nueva, m.fecha, m.motivo, "
        "p.nombre AS producto, p.unidad_medida FROM movimientos_inventario m "
        "JOIN productos p ON p.id = m.producto_id ORDER BY m.fecha DESC, m.id DESC LIMIT 8"
    )

    month_sales = sales or 0
    month_purchases = purchases or 0
    return response({
        "periodo": start.isoformat()[:7],
        "metricas": {
            "ventas_cobradas": month_sales,
            "compras_recibidas": month_purchases,
            "diferencia_ventas_compras": month_sales - month_purchases,
            "valor_inventario": product_stats["valor_inventario"],
            "productos_disponibles": product_stats["disponibles"],
            "productos_agotados": product_stats["agotados"],
            "productos_stock_bajo": product_stats["stock_bajo"],
            "compras_pendientes": stats["compras_pendientes"],
            "pedidos_web_pendientes": stats["pedidos_web_pendientes"],
            "clientes_activos": stats["clientes_activos"],
            "unidades_salida_30d": stats["unidades_salida_30d"],
        },
        "meses": months,
        "alertas_inventario": alerts,
        "ventas_recientes": recent_sales,
        "compras_pendientes_recientes": pending_purchases,
        "movimientos_recientes": recent_movements,
    })
