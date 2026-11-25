
import os

import cloudinary
import cloudinary.uploader
from cloudinary.exceptions import Error as CloudinaryError

from .http import ApiError, endpoint, response


@endpoint("POST", access="ADMIN")
def subir_imagen(request):
    imagen = request.FILES.get("imagen")

    if not imagen:
        raise ApiError(400, "Seleccioná una imagen.")

    if imagen.size > 5 * 1024 * 1024:
        raise ApiError(422, "La imagen no puede superar los 5 MB.")

    if imagen.content_type not in (
        "image/jpeg",
        "image/png",
        "image/webp",
    ):
        raise ApiError(422, "Solo se permiten imágenes JPG, PNG o WebP.")

    cloud_name = os.getenv("CLOUDINARY_CLOUD_NAME")
    api_key = os.getenv("CLOUDINARY_API_KEY")
    api_secret = os.getenv("CLOUDINARY_API_SECRET")

    if not all((cloud_name, api_key, api_secret)):
        raise ApiError(503, "Cloudinary no está configurado.")

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=api_key,
        api_secret=api_secret,
        secure=True,
    )

    try:
        resultado = cloudinary.uploader.upload(
            imagen,
            folder="FerreLSA",
            resource_type="image",
            unique_filename=True,
            overwrite=False,
        )
    except CloudinaryError:
        raise ApiError(
            502,
            "No se pudo subir la imagen a Cloudinary.",
        ) from None

    url = resultado.get("secure_url")

    if not url or len(url) > 500:
        raise ApiError(502, "Cloudinary no devolvió una URL válida.")

    return response({"imagen_url": url})
