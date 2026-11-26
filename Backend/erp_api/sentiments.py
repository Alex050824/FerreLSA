"""Cliente del servicio de análisis de comentarios."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings

from .http import ApiError


def analyze_comment(comment):
    try:
        request = Request(
            settings.SENTIMIENTOS_URL.rstrip("/") + "/analizar",
            data=json.dumps({"texto": comment}, ensure_ascii=False).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(request, timeout=120) as result:
            payload = json.loads(result.read(65536).decode("utf-8"))
        sentiment = payload.get("sentimiento") if isinstance(payload, dict) else None
        if not isinstance(sentiment, str) or sentiment not in {"POSITIVO", "NEGATIVO", "NEUTRAL"}:
            raise ValueError("Respuesta de sentimiento inválida")
        return sentiment
    except (HTTPError, URLError, TimeoutError, OSError, ValueError, UnicodeError):
        raise ApiError(503, "No se pudo analizar el comentario. Intentá nuevamente más tarde.") from None
