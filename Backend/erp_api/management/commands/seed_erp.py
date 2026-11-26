from decimal import Decimal
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from ...db import insert, query
from ...http import ApiError
from ...inventory import generate_product_code, lock_products, move_stock
from ...order_values import money, totals
from ...sales import create_sale
from ...users import get_user


# Descripciones basadas en el nombre y la presentación registrados. Evitamos
# atribuir marcas, compatibilidades o características que no constan en la ficha.
PRODUCT_DESCRIPTIONS = {
    "Martillo": "Herramienta manual para golpear y realizar tareas de montaje o reparación en el hogar y el taller.",
    "Taladro": "Herramienta para realizar perforaciones en trabajos de montaje y reparación. Consultá las brocas y superficies compatibles antes de usarlo.",
    "Silicón transparente": "Sellador transparente en cartucho de 280 ml, útil para sellar juntas y uniones en proyectos de reparación y bricolaje.",
    "Cargador de batería 12 V": "Cargador para baterías de 12 V. Antes de conectarlo, verificá la compatibilidad con la batería y seguí las indicaciones del fabricante.",
    "Ducha teléfono cromada": "Ducha de mano tipo teléfono con acabado cromado, para dirigir el agua durante el baño. Verificá la compatibilidad de la conexión antes de instalarla.",
    "Llave para fregadero": "Grifo para fregadero de cocina, para controlar el paso de agua. Verificá las medidas y conexiones de tu instalación antes de comprar.",
    "Cemento de uso general": "Cemento de uso general para preparar mezclas en trabajos de construcción y reparación. Se presenta en saco de 50 kg.",
    "Interruptor sencillo": "Interruptor sencillo para controlar el encendido y apagado de un circuito de iluminación. Su instalación debe adecuarse a la instalación eléctrica existente.",
    "Manguera para jardín": "Manguera de 15 metros para el riego de plantas y otras tareas con agua en el jardín. Se vende en rollo.",
    "Candado laminado 40 mm": "Candado laminado de 40 mm para asegurar portones, casilleros u otros elementos con un cierre compatible.",
    "Martillo de uña 16 oz": "Martillo de uña de 16 oz para clavar y extraer clavos en trabajos de carpintería, montaje y reparación.",
    "Tijera de podar": "Tijera manual para podar plantas y recortar ramas en tareas de mantenimiento del jardín.",
    "Bombillo LED 9 W": "Bombillo de tecnología LED y potencia de 9 W para iluminación. Verificá que la base sea compatible con tu lámpara antes de comprar.",
    "Hidrolavadora compacta": "Hidrolavadora compacta para tareas de limpieza con agua a presión. Consultá las indicaciones del fabricante para cada superficie.",
    "Estante metálico 4 niveles": "Estante metálico de cuatro niveles para organizar herramientas, suministros u otros artículos en espacios de trabajo o almacenamiento.",
    "Pintura blanca mate": "Pintura blanca con acabado mate, en presentación de galón, para proyectos de pintura y renovación de superficies.",
    "Adhesivo para cerámica": "Adhesivo para la colocación de piezas cerámicas, en saco de 20 kg. Revisá las indicaciones del fabricante antes de preparar y aplicar la mezcla.",
    "Tubo PVC 1/2 pulgada": "Tubo de PVC de media pulgada para instalaciones de plomería. Verificá las medidas y conexiones requeridas para tu proyecto.",
    "Lentes de protección": "Lentes de protección para cubrir los ojos durante trabajos de bricolaje y otras tareas que puedan generar partículas. Elegí el equipo adecuado para cada riesgo.",
}


CATEGORIES = [
    ("Adhesivos y selladores", "Adhesivos, siliconas y selladores."),
    ("Automotriz", "Accesorios y mantenimiento automotriz."),
    ("Baños", "Grifería, accesorios y artículos para baño."),
    ("Cocinas", "Accesorios y equipamiento para cocina."),
    ("Construcción", "Materiales y suministros para construcción."),
    ("Electricidad", "Materiales y accesorios eléctricos."),
    ("Exteriores", "Mobiliario y productos para exteriores."),
    ("Ferretería general", "Artículos de uso general para el hogar y taller."),
    ("Herramientas", "Herramientas manuales y eléctricas."),
    ("Jardinería", "Herramientas y suministros de jardinería."),
    ("Lámparas", "Lámparas y soluciones de iluminación."),
    ("Limpieza", "Productos y accesorios de limpieza."),
    ("Muebles y organización", "Muebles, estantería y organización."),
    ("Pinturas", "Pinturas, brochas y accesorios."),
    ("Pisos", "Pisos, revestimientos y accesorios."),
    ("Plomería", "Tubería, conexiones y accesorios de plomería."),
    ("Seguridad", "Equipo y accesorios de seguridad."),
]

SUPPLIERS = [
    {"nombre": "Suministros Ferreteros CR", "contacto": "Ventas", "telefono": "2222-1000", "correo": "ventas@suministros-demo.cr"},
    {"nombre": "Distribuidora Valle Central", "contacto": "Servicio al cliente", "telefono": "2222-2000", "correo": "pedidos@vallecentral-demo.cr"},
]

PRODUCTS = [
    ("Adhesivos y selladores", "Silicón transparente", "Cartucho 280 ml", "3200.00", "4900.00", "5.000"),
    ("Automotriz", "Cargador de batería 12 V", "unidad", "14500.00", "21900.00", "2.000"),
    ("Baños", "Ducha teléfono cromada", "unidad", "8500.00", "12900.00", "3.000"),
    ("Cocinas", "Llave para fregadero", "unidad", "12500.00", "18900.00", "2.000"),
    ("Construcción", "Cemento de uso general", "saco 50 kg", "5200.00", "6500.00", "10.000"),
    ("Electricidad", "Interruptor sencillo", "unidad", "750.00", "1250.00", "10.000"),
    ("Exteriores", "Manguera para jardín", "rollo 15 m", "7800.00", "11900.00", "3.000"),
    ("Ferretería general", "Candado laminado 40 mm", "unidad", "2800.00", "4500.00", "5.000"),
    ("Herramientas", "Martillo de uña 16 oz", "unidad", "4200.00", "6900.00", "4.000"),
    ("Jardinería", "Tijera de podar", "unidad", "3900.00", "6200.00", "3.000"),
    ("Lámparas", "Bombillo LED 9 W", "unidad", "650.00", "1100.00", "10.000"),
    ("Limpieza", "Hidrolavadora compacta", "unidad", "46000.00", "64900.00", "1.000"),
    ("Muebles y organización", "Estante metálico 4 niveles", "unidad", "24000.00", "34900.00", "2.000"),
    ("Pinturas", "Pintura blanca mate", "galón", "9800.00", "14500.00", "3.000"),
    ("Pisos", "Adhesivo para cerámica", "saco 20 kg", "4300.00", "6200.00", "5.000"),
    ("Plomería", "Tubo PVC 1/2 pulgada", "unidad", "950.00", "1500.00", "10.000"),
    ("Seguridad", "Lentes de protección", "unidad", "1200.00", "2100.00", "5.000"),
]


class Command(BaseCommand):
    help = "Agrega datos iniciales idempotentes al ERP en una base de desarrollo o demostración."

    def add_arguments(self, parser):
        parser.add_argument("--base", required=True, help="Nombre exacto de la base MySQL configurada.")

    def handle(self, *args, **options):
        database = query("SELECT DATABASE() AS nombre")[0]["nombre"]
        if not database or database != options["base"]:
            raise CommandError("El nombre indicado con --base no coincide con la base configurada.")

        admins = query("SELECT id FROM usuarios WHERE rol = 'ADMIN' AND activo = 1 ORDER BY id LIMIT 1")
        if not admins:
            raise CommandError("Creá primero un usuario ADMIN activo y volvé a ejecutar la semilla.")
        admin = get_user(admins[0]["id"])
        try:
            with transaction.atomic():
                categories = self.seed_categories()
                suppliers = self.seed_suppliers()
                products = self.seed_products(categories, suppliers, admin["id"])
                self.seed_purchase(products["Construcción"], suppliers["Suministros Ferreteros CR"], admin["id"])
                self.seed_sale(products["Herramientas"], admin)
        except ApiError as error:
            raise CommandError(str(error)) from None

        self.stdout.write(self.style.SUCCESS(
            "Semillas ERP listas: categorías, proveedores, productos, existencias, movimientos, compra y venta. "
            "No se agregaron comentarios ni fotos de productos."
        ))

    @staticmethod
    def seed_categories():
        result = {}
        for name, description in CATEGORIES:
            rows = query("SELECT id FROM categorias WHERE nombre = %s LIMIT 1", (name,))
            result[name] = rows[0]["id"] if rows else insert(
                "categorias", {"nombre": name, "descripcion": description, "activo": 1}
            )
        return result

    @staticmethod
    def seed_suppliers():
        result = {}
        for supplier in SUPPLIERS:
            rows = query("SELECT id FROM proveedores WHERE nombre = %s LIMIT 1", (supplier["nombre"],))
            result[supplier["nombre"]] = rows[0]["id"] if rows else insert(
                "proveedores", {**supplier, "activo": 1}
            )
        return result

    @staticmethod
    def seed_products(categories, suppliers, admin_id):
        result = {}
        supplier_ids = list(suppliers.values())
        for index, (category, name, unit, cost, price, minimum) in enumerate(PRODUCTS):
            category_id = categories[category]
            rows = query(
                "SELECT id, existencia FROM productos WHERE categoria_id = %s AND nombre = %s LIMIT 1",
                (category_id, name),
            )
            if rows:
                product_id = rows[0]["id"]
            else:
                product_id = insert("productos", {
                    "categoria_id": category_id,
                    "proveedor_id": supplier_ids[index % len(supplier_ids)],
                    "codigo": generate_product_code(category_id),
                    "nombre": name,
                    "descripcion": PRODUCT_DESCRIPTIONS[name],
                    "unidad_medida": unit,
                    "precio_compra": Decimal(cost),
                    "precio_venta": Decimal(price),
                    "existencia": Decimal("0"),
                    "stock_minimo": Decimal(minimum),
                    "imagen_url": None,
                    "activo": 1,
                })
            result[category] = product_id
            marker = "Semilla inicial FerreLSA"
            existing_move = query(
                "SELECT id FROM movimientos_inventario WHERE producto_id = %s AND motivo = %s LIMIT 1",
                (product_id, marker),
            )
            if not existing_move:
                product = lock_products([product_id])[product_id]
                move_stock(product, user_id=admin_id, kind="ENTRADA", quantity=Decimal("20"), reason=marker)
        return result

    @staticmethod
    def seed_purchase(product_id, supplier_id, admin_id):
        number = "SEED-OC-001"
        if query("SELECT id FROM ordenes_compra WHERE numero = %s LIMIT 1", (number,)):
            return
        quantity = Decimal("5.000")
        cost = Decimal("5200.00")
        row = {"total_linea": money(quantity * cost)}
        order_totals = totals([row])
        order_id = insert("ordenes_compra", {
            "numero": number,
            "proveedor_id": supplier_id,
            "fecha": timezone.localdate(),
            "observaciones": "Orden de ejemplo creada por la semilla inicial.",
            **order_totals,
            "usuario_id": admin_id,
            "estado": "PENDIENTE",
        })
        insert("detalles_orden_compra", {
            "orden_compra_id": order_id,
            "producto_id": product_id,
            "cantidad": quantity,
            "costo_unitario": cost,
            "total_linea": row["total_linea"],
        })

    @staticmethod
    def seed_sale(product_id, admin):
        number = "SEED-VTA-001"
        if query("SELECT id FROM ventas WHERE numero = %s LIMIT 1", (number,)):
            return
        create_sale({
            "numero": number,
            "canal": "LOCAL",
            "metodo_pago": "EFECTIVO",
            "tipo_comprobante": "TIQUETE",
            "modalidad_entrega": "RETIRO_TIENDA",
            "direccion_entrega": "",
            "observaciones": "Venta de ejemplo creada por la semilla inicial.",
        }, [{"producto_id": product_id, "cantidad": Decimal("1.000")}], admin)
