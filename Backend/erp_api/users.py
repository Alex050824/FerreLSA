from datetime import timedelta
from hashlib import scrypt
from hmac import compare_digest
import re

import jwt
from django import forms
from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.sessions.backends.db import SessionStore
from django.db import connection, transaction
from django.utils import timezone

from .db import insert, one, query, update
from .http import ApiError, JsonBoolean, body, clean, endpoint, no_content, record_id, response, text

FIELDS = "id, rol, nombre, apellido, identificacion, telefono, correo, provincia, canton, distrito, direccion_exacta, activo"
ROLES = [(role, role) for role in ("ADMIN", "CLIENTE")]
PROFILE = {
    "nombre": text(255),
    "correo": forms.EmailField(max_length=255),
    "apellido": text(255, required=False),
    "identificacion": text(30, required=False),
    "telefono": text(30, required=False),
    "provincia": text(80, required=False),
    "canton": text(80, required=False),
    "distrito": text(80, required=False),
    "direccion_exacta": text(500, required=False),
    "password": forms.CharField(min_length=8, max_length=128, strip=False),
}
ADMIN_FIELDS = {
    **PROFILE, "rol": forms.ChoiceField(choices=ROLES, required=False), "activo": JsonBoolean(required=False),
}


def signing_key():
    if len(settings.ERP_JWT_SECRET) < 32:
        raise ApiError(503, "Configurá ERP_JWT_SECRET con al menos 32 caracteres.")
    return settings.ERP_JWT_SECRET


def authenticate(request):
    parts = request.headers.get("Authorization", "").split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise ApiError(401, "Se requiere el token de acceso.")
    key = signing_key()
    try:
        claims = jwt.decode(
            parts[1], key, algorithms=["HS256"], issuer="ferrelsa-api", audience="ferrelsa",
            options={"require": ["sub", "exp", "iat", "sid"]},
        )
        user_id = record_id(claims["sub"])
    except (jwt.InvalidTokenError, ApiError):
        raise ApiError(401, "El token no es válido o venció.") from None
    session_key = claims["sid"]
    if not isinstance(session_key, str) or not re.fullmatch(r"[a-z0-9]{32}", session_key):
        raise ApiError(401, "La sesión no es válida.")
    session = SessionStore(session_key=session_key)
    if session.get("erp_user_id") != user_id:
        raise ApiError(401, "La sesión venció o se cerró.")
    request.erp_session = session
    users = query(f"SELECT {FIELDS} FROM usuarios WHERE id = %s AND activo = 1", (user_id,))
    if not users:
        raise ApiError(401, "La cuenta no está disponible.")
    return users[0]


def get_user(user_id):
    return one(f"SELECT {FIELDS} FROM usuarios WHERE id = %s", (user_id,))


def password_matches(password, encoded):
    legacy = re.fullmatch(r"scrypt\$([a-f0-9]{32})\$([a-f0-9]{128})", encoded or "")
    if legacy:
        salt, digest = legacy.groups()
        actual = scrypt(password.encode(), salt=salt.encode(), n=16384, r=8, p=1, dklen=64)
        return compare_digest(actual.hex(), digest)
    if not encoded or not check_password(password, encoded):
        if not encoded:
            make_password(password)
        return False
    return True


def save_user(values, user_id=None):
    data = dict(values)
    if "correo" in data:
        data["correo"] = data["correo"].lower()
    if "password" in data:
        data["contrasena_hash"] = make_password(data.pop("password"))
    if user_id is None:
        user_id = insert("usuarios", data)
    else:
        update("usuarios", user_id, data)
    return get_user(user_id)


@endpoint("POST")
def register(request):
    return response(save_user({**clean(body(request), PROFILE), "rol": "CLIENTE"}), 201)


@endpoint("POST")
def login(request):
    data = clean(body(request), {
        "username": forms.EmailField(max_length=255),
        "password": forms.CharField(max_length=128, strip=False),
    })
    key = signing_key()
    users = query("SELECT id, activo, rol, contrasena_hash FROM usuarios WHERE correo = %s", (data["username"].lower(),))
    user = users[0] if users else None
    if not password_matches(data["password"], user["contrasena_hash"] if user else None) or not user["activo"]:
        raise ApiError(401, "Correo o contraseña incorrectos.")
    now = timezone.now()
    session = SessionStore()
    session["erp_user_id"] = user["id"]
    session.set_expiry(3600)
    session.create()
    token = jwt.encode({
        "sub": str(user["id"]), "rol": user["rol"], "iat": now, "exp": now + timedelta(hours=1),
        "iss": "ferrelsa-api", "aud": "ferrelsa", "sid": session.session_key,
    }, key, algorithm="HS256")
    return response({"token": token, "usuario": get_user(user["id"])})

@endpoint("POST", access="USER")
def logout(request):
    request.erp_session.delete()
    return no_content()


@endpoint("GET", "PATCH", access="USER")
def profile(request):
    if request.method == "GET":
        return response(request.api_user)
    return response(save_user(clean(body(request), PROFILE, partial=True), request.api_user["id"]))


@endpoint("GET", "POST", access="ADMIN")
def users(request):
    if request.method == "POST":
        data = clean(body(request), ADMIN_FIELDS)
        if not data.get("rol"):
            data["rol"] = "CLIENTE"
        return response(save_user(data), 201)
    role = request.GET.get("rol")
    if role is not None:
        if role not in ("ADMIN", "CLIENTE"):
            raise ApiError(422, "Rol inválido.")
        return response(query(f"SELECT {FIELDS} FROM usuarios WHERE rol = %s ORDER BY id", (role,)))
    return response(query(f"SELECT {FIELDS} FROM usuarios ORDER BY id"))


@transaction.atomic
def delete_inactive_user(user_id):
    user = one("SELECT activo FROM usuarios WHERE id = %s FOR UPDATE", (user_id,))
    if user["activo"]:
        raise ApiError(409, "Desactivá la cuenta antes de eliminarla definitivamente.")
    history = query(
        "SELECT (EXISTS(SELECT 1 FROM comentarios_productos WHERE usuario_id = %s)"
        " OR EXISTS(SELECT 1 FROM movimientos_inventario WHERE usuario_id = %s)"
        " OR EXISTS(SELECT 1 FROM ordenes_compra WHERE usuario_id = %s)"
        " OR EXISTS(SELECT 1 FROM ventas WHERE usuario_id = %s OR atendido_por_id = %s)) AS vinculado",
        (user_id,) * 5,
    )
    if history[0]["vinculado"]:
        raise ApiError(409, "La cuenta tiene historial asociado y debe conservarse inactiva.")
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM usuarios WHERE id = %s", (user_id,))


@endpoint("GET", "PATCH", "DELETE", access="ADMIN")
def user_detail(request, pk):
    user_id = record_id(pk)
    if request.method == "DELETE" and request.GET.get("permanente") == "1":
        if user_id == request.api_user["id"]:
            raise ApiError(409, "No podés eliminar tu propia cuenta.")
        delete_inactive_user(user_id)
        return no_content()
    user = get_user(user_id)
    if request.method == "GET":
        return response(user)
    data = {"activo": False} if request.method == "DELETE" else clean(body(request), ADMIN_FIELDS, partial=True)
    if "rol" in data and not data["rol"]:
        raise ApiError(422, "Rol inválido.")
    if user_id == request.api_user["id"] and (data.get("activo") is False or data.get("rol") == "CLIENTE"):
        raise ApiError(409, "Usá otra cuenta administrativa para cambiar tu acceso.")
    saved = save_user(data, user_id)
    return no_content() if request.method == "DELETE" else response(saved)
