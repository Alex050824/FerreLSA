import json
import re
from functools import wraps

from django import forms
from django.db import IntegrityError, OperationalError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt


class ApiError(Exception):
    def __init__(self, status, message):
        super().__init__(message)
        self.status = status


def response(data, status=200):
    return JsonResponse(data, safe=isinstance(data, dict), status=status)


def endpoint(*methods, access=None):
    def decorate(view):
        @csrf_exempt
        @wraps(view)
        def wrapped(request, *args, **kwargs):
            from .users import authenticate

            try:
                if request.method not in methods:
                    result = response({"error": "Método no permitido."}, 405)
                    result["Allow"] = ", ".join(methods)
                    return result
                if access:
                    request.api_user = authenticate(request)
                    if access == "ADMIN" and request.api_user["rol"] != "ADMIN":
                        raise ApiError(403, "Se requiere acceso de administrador.")
                result = view(request, *args, **kwargs)
            except ApiError as error:
                result = response({"error": str(error)}, error.status)
            except (IntegrityError, OperationalError) as error:
                code = error.args[0]
                if code in (1062, 1205, 1213):
                    result = response({"error": "El registro ya existe o la operación está en conflicto."}, 409)
                elif code in (1451, 1452, 3819):
                    result = response({"error": "Los datos no cumplen las restricciones de MySQL."}, 422)
                else:
                    raise
            result["Cache-Control"] = "no-store"
            return result
        return wrapped
    return decorate


def body(request):
    try:
        data = json.loads(request.body)
    except (ValueError, UnicodeError):
        raise ApiError(400, "JSON inválido.") from None
    if not isinstance(data, dict):
        raise ApiError(422, "Se esperaba un objeto JSON.")
    return data


def clean(data, fields, *, partial=False):
    if not isinstance(data, dict) or data.keys() - fields.keys():
        raise ApiError(422, "Hay campos desconocidos o datos inválidos.")
    result = {}
    for name, field in fields.items():
        if name not in data and (partial or not field.required):
            continue
        value = data.get(name)
        if isinstance(field, forms.CharField) and value is not None and not isinstance(value, str):
            raise ApiError(422, f"{name}: se esperaba texto.")
        try:
            result[name] = field.clean(value)
        except forms.ValidationError as error:
            raise ApiError(422, f"{name}: {error.messages[0]}") from None
    return result


class JsonBoolean(forms.Field):
    def clean(self, value):
        if type(value) is not bool:
            raise forms.ValidationError("Se esperaba true o false.")
        return value


class ImageURL(forms.URLField):
    def clean(self, value):
        if value and not value.lower().startswith(("https://", "http://")):
            raise forms.ValidationError("Usá una URL HTTP o HTTPS.")
        return super().clean(value)


def text(max_length, *, required=True):
    return forms.CharField(max_length=max_length, required=required, empty_value=None)


def record_id(value):
    if not re.fullmatch(r"[1-9][0-9]{0,19}", str(value)) or int(value) > 2**64 - 1:
        raise ApiError(422, "Identificador inválido.")
    return int(value)


class RecordId(forms.Field):
    def clean(self, value):
        if value is None and not self.required:
            return None
        return record_id(value)


def no_content():
    return HttpResponse(status=204)
