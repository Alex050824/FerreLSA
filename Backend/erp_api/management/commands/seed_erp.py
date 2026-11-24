from decimal import Decimal
from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from ...db import insert, query
from ...http import ApiError, clean
from ...inventory import lock_products, move_stock
from ...users import PROFILE, save_user


class Command(BaseCommand):
    help = "Crea cuentas y catálogo de demostración en una base de pruebas."

    def add_arguments(self, parser):
        parser.add_argument("--base", required=True, help="Nombre exacto de la base MySQL configurada.")

    def handle(self, *args, **options):
        database = query("SELECT DATABASE() AS nombre")[0]["nombre"]
        if not database or database != options["base"]:
            raise CommandError("El nombre indicado con --base no coincide con la base configurada.")
        if query("SELECT id FROM usuarios WHERE correo IN (%s, %s)", ("admin.demo@example.com", "cliente.demo@example.com")):
            raise CommandError("Los usuarios de demostración ya existen.")
        password = getpass("Contraseña temporal para ambas cuentas: ")
        try:
            with transaction.atomic():
                admin = self.account("Admin Demo", "admin.demo@example.com", password, "ADMIN")
                self.account("Cliente Demo", "cliente.demo@example.com", password, "CLIENTE")
                categories = query("SELECT id FROM categorias WHERE nombre = %s", ("Herramientas",))
                category = categories[0]["id"] if categories else insert("categorias", {"nombre": "Herramientas"})
                supplier = insert("proveedores", {"nombre": "Proveedor Demo"})
                product = insert("productos", {
                    "categoria_id": category, "proveedor_id": supplier, "codigo": "DEMO-01", "nombre": "Martillo Demo",
                    "precio_compra": Decimal("2000"), "precio_venta": Decimal("3500"),
                })
                move_stock(
                    lock_products([product])[product], user_id=admin["id"], kind="ENTRADA",
                    quantity=Decimal("20"), reason="Seed ERP",
                )
        except ApiError as error:
            raise CommandError(str(error)) from None
        self.stdout.write(self.style.SUCCESS("Datos de prueba creados para admin.demo@example.com y cliente.demo@example.com."))

    @staticmethod
    def account(name, email, password, role):
        data = clean({"nombre": name, "correo": email, "password": password}, PROFILE)
        return save_user({**data, "rol": role})
