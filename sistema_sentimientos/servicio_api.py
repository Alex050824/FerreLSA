"""API local para integrar el analizador con otras aplicaciones.

No escribe comentarios: la aplicación cliente es responsable de persistirlos.
"""
import json
import logging
import os
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlsplit

from analizador import alerta_ambiguedad, clasificar, inicializar_modelo
from reglas_precios import sentimiento_precio

HOST = "127.0.0.1"
MAX_CUERPO = 8192
MAX_TEXTO = 1000
ETIQUETAS = {"Positivo": "POSITIVO", "Negativo": "NEGATIVO", "Neutral": "NEUTRAL"}
estado = "cargando"


class ServidorExclusivo(ThreadingHTTPServer):
    # En Windows SO_REUSEADDR permite que otro proceso escuche en el mismo
    # puerto y reciba solicitudes de forma impredecible. Usar exclusividad.
    allow_reuse_address = os.name != "nt"

    def server_bind(self):
        if os.name == "nt":
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def cargar_modelo():
    global estado
    try:
        inicializar_modelo()
        estado = "listo"
        logging.info("Modelo listo para analizar comentarios.")
    except Exception:
        estado = "error"
        logging.exception("No se pudo inicializar el modelo; revisa las dependencias y la caché.")


class Servidor(BaseHTTPRequestHandler):
    server_version = "SentimientosAPI"
    sys_version = ""

    def setup(self):
        super().setup()
        self.connection.settimeout(10)

    def log_message(self, formato, *args):
        # No registrar el cuerpo ni los comentarios.
        logging.info("%s - %s", self.address_string(), formato % args)

    def responder(self, codigo, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(cuerpo)

    def do_GET(self):
        if urlsplit(self.path).path != "/salud":
            self.responder(404, {"error": "Ruta no encontrada."})
            return
        self.responder(200 if estado == "listo" else 503, {"estado": estado})

    def do_POST(self):
        if urlsplit(self.path).path != "/analizar":
            self.responder(404, {"error": "Ruta no encontrada."})
            return
        if self.headers.get_content_type() != "application/json":
            self.responder(400, {"error": "Se requiere JSON."})
            return
        try:
            longitud = int(self.headers.get("Content-Length", ""))
        except ValueError:
            self.responder(400, {"error": "Longitud de solicitud inválida."})
            return
        if longitud <= 0 or longitud > MAX_CUERPO:
            self.responder(400, {"error": "La solicitud está vacía o es demasiado grande."})
            return
        try:
            datos = json.loads(self.rfile.read(longitud).decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError, TimeoutError):
            self.responder(400, {"error": "JSON inválido."})
            return
        texto = datos.get("texto") if isinstance(datos, dict) else None
        if not isinstance(texto, str) or not texto.strip() or len(texto) > MAX_TEXTO:
            self.responder(400, {"error": "El texto debe contener entre 1 y 1000 caracteres."})
            return
        if estado != "listo":
            self.responder(503, {"error": "El modelo de sentimientos no está disponible."})
            return
        try:
            sentimiento, puntuaciones = clasificar(texto)
            regla = sentimiento_precio(texto)
            resultado = regla or sentimiento
            self.responder(200, {
                "sentimiento": ETIQUETAS[resultado],
                "puntuaciones": {ETIQUETAS[k]: v for k, v in puntuaciones.items()},
                "alerta": alerta_ambiguedad(puntuaciones),
                "origen": "regla_precio" if regla else "modelo",
            })
        except Exception:
            logging.exception("Error al analizar un comentario.")
            self.responder(503, {"error": "No se pudo analizar el comentario."})


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        puerto = int(os.environ.get("SENTIMIENTOS_PUERTO", "8001"))
        if not 1 <= puerto <= 65535:
            raise ValueError
    except ValueError:
        raise SystemExit("SENTIMIENTOS_PUERTO debe ser un puerto entre 1 y 65535.")
    try:
        servidor = ServidorExclusivo((HOST, puerto), Servidor)
    except OSError as error:
        raise SystemExit(
            f"No se pudo iniciar el analizador en {HOST}:{puerto}. "
            f"Comprueba si el puerto ya está ocupado o si tienes permisos. Detalle: {error}"
        ) from error
    threading.Thread(target=cargar_modelo, daemon=True).start()
    logging.info("API disponible en http://%s:%s; cargando el modelo.", HOST, puerto)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()


if __name__ == "__main__":
    main()
