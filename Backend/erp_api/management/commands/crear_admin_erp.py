from getpass import getpass

from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError

from ...http import ApiError, clean
from ...users import PROFILE, save_user


class Command(BaseCommand):
    help = "Crea un administrador en la tabla usuarios de FerreLSA."

    def add_arguments(self, parser):
        parser.add_argument("correo")
        parser.add_argument("nombre")

    def handle(self, *args, **options):
        password = getpass("Contraseña: ")
        if password != getpass("Repetí la contraseña: "):
            raise CommandError("Las contraseñas no coinciden.")
        try:
            data = clean({"correo": options["correo"], "nombre": options["nombre"], "password": password}, PROFILE)
            save_user({**data, "rol": "ADMIN"})
        except ApiError as error:
            raise CommandError(str(error)) from None
        except IntegrityError as error:
            if error.args[0] == 1062:
                raise CommandError("El correo ya existe.") from None
            raise
        self.stdout.write(self.style.SUCCESS("Administrador creado."))
