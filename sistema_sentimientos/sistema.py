"""Demostración educativa de análisis de sentimiento con un modelo en español."""
import csv
import hashlib
import html
import hmac
import json
import os
import re
import secrets
import socket
import tempfile
import threading
import traceback
from collections import Counter
from datetime import datetime
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http.cookies import SimpleCookie, CookieError
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from analizador import inicializar_modelo, clasificar, alerta_ambiguedad
from grafico import grafico_resultados

PUERTO = 8000
ARCHIVO = Path(__file__).resolve().with_name("comentarios.csv")
ARCHIVO_ENLACE = Path(__file__).resolve().with_name(".clave_panel")
CERROJO = threading.Lock()
CAMPOS = ["fecha", "comentario", "clasificacion", "pistas"]
MARCA_DIRECTA = "RoBERTuito (texto original): "
CATEGORIAS = ("Positivo", "Negativo", "Neutral")
CATEGORIAS_SENTIMIENTO = ("Positivo", "Negativo", "Neutral")
ENLACE_ADMIN = secrets.token_urlsafe(16)
SESION_ADMIN = secrets.token_urlsafe(32)


def cargar_enlace_privado(ruta=ARCHIVO_ENLACE):
    """Recupera el token persistente o lo crea sin reemplazar uno existente.

    La creación usa un archivo temporal y un enlace duro para publicar el
    contenido completo de forma atómica sin sobrescribir otro token.
    """
    ruta = Path(ruta)
    temporal = None
    try:
        if not ruta.exists():
            with tempfile.NamedTemporaryFile(mode="w", encoding="ascii", newline="",
                                             dir=ruta.parent, delete=False) as archivo:
                temporal = Path(archivo.name)
                archivo.write(secrets.token_urlsafe(16))
            try:
                os.link(temporal, ruta)
            except FileExistsError:
                # Otra instancia creó el token; siempre se respeta el existente.
                pass
        token = ruta.read_text(encoding="ascii").strip()
    except (OSError, UnicodeError) as error:
        raise RuntimeError(
            f"No se pudo leer o crear el archivo del enlace privado: {ruta}. "
            "Revisa los permisos de la carpeta."
        ) from error
    finally:
        if temporal is not None:
            try:
                temporal.unlink(missing_ok=True)
            except OSError:
                pass
    if not re.fullmatch(r"[A-Za-z0-9_-]{22,128}", token):
        raise RuntimeError(
            f"El archivo del enlace privado es inválido: {ruta}. "
            "No se cambió su contenido; revisa el archivo."
        )
    return token


def guardar(comentario, clasificacion, pistas):
    with CERROJO:
        nuevo = not ARCHIVO.exists() or ARCHIVO.stat().st_size == 0
        with ARCHIVO.open("a", encoding="utf-8-sig", newline="") as archivo:
            escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
            if nuevo:
                escritor.writeheader()
            escritor.writerow(dict(fecha=datetime.now().strftime("%Y-%m-%d %H:%M:%S"), comentario=comentario, clasificacion=clasificacion, pistas=pistas))


def leer():
    with CERROJO:
        if not ARCHIVO.exists():
            return []
        with ARCHIVO.open(encoding="utf-8-sig", newline="") as archivo:
            return list(csv.DictReader(archivo))


def huella_registro(registro):
    datos = json.dumps([registro.get(campo, "") for campo in CAMPOS], ensure_ascii=False)
    return hashlib.sha256(datos.encode("utf-8")).hexdigest()


def actualizar_registro(indice, huella, comentario, clasificacion, pistas):
    """Actualiza un registro si no cambió desde que se mostró en el panel."""
    with CERROJO:
        with ARCHIVO.open(encoding="utf-8-sig", newline="") as archivo:
            registros = list(csv.DictReader(archivo))
        if (indice < 0 or indice >= len(registros)
                or registros[indice].get("comentario", "") != comentario
                or not hmac.compare_digest(huella_registro(registros[indice]), huella)):
            return False
        registros[indice]["clasificacion"] = clasificacion
        registros[indice]["pistas"] = pistas
        temporal = None
        try:
            with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8-sig", newline="",
                                             dir=ARCHIVO.parent, delete=False) as archivo:
                temporal = Path(archivo.name)
                escritor = csv.DictWriter(archivo, fieldnames=CAMPOS)
                escritor.writeheader()
                escritor.writerows(registros)
            os.replace(temporal, ARCHIVO)
        finally:
            if temporal and temporal.exists():
                temporal.unlink()
        return True


def escapar(valor):
    return html.escape(str(valor), quote=True)


def mostrar_detalles(pistas):
    """Muestra las puntuaciones y la alerta derivada del modelo."""
    partes = pistas.split(" · ")
    puntuaciones = [parte for parte in partes if parte.startswith(
        ("Positivo: ", "Negativo: ", "Neutral: "))]
    if not puntuaciones:
        return ""
    alerta = next((parte for parte in partes if parte.startswith("Alerta: ")), "")
    aviso = f"<p class='pequeno'>{escapar(alerta)}</p>" if alerta else ""
    return (aviso + "<details class='pequeno'><summary>Ver puntuaciones de RoBERTuito</summary>"
            f"<p>{escapar(' · '.join(puntuaciones))}</p></details>")


ESTILO = """<style>
*{box-sizing:border-box}body{font-family:system-ui,sans-serif;background:#f4f6fb;color:#17223b;margin:0;padding:24px}
main{max-width:760px;margin:auto;background:white;padding:28px;border-radius:16px;box-shadow:0 4px 20px #17223b12}
h1{font-size:1.7rem}p{line-height:1.55}textarea{width:100%;font:inherit;padding:12px;border:1px solid #aab5c8;border-radius:8px;resize:vertical}
button,.boton{display:inline-block;background:#2058bc;color:white;border:0;border-radius:8px;padding:12px 18px;font:inherit;text-decoration:none;cursor:pointer}
a{color:#2058bc} .aviso{background:#edf3ff;padding:12px;border-radius:8px}.fila{border-top:1px solid #e0e5ed;padding:12px 0;overflow-wrap:anywhere}
.etiqueta{font-weight:bold;color:#244b87}.pequeno{font-size:.9rem;color:#526078}.resumen{display:flex;gap:8px;flex-wrap:wrap}.resumen span{background:#edf3ff;padding:8px 12px;border-radius:8px}
</style>"""


def pagina(titulo, contenido):
    return ("<!doctype html><html lang='es'><head><meta charset='utf-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{escapar(titulo)}</title>{ESTILO}</head><body><main>{contenido}</main></body></html>")


class Servidor(BaseHTTPRequestHandler):
    def log_request(self, code="-", size="-"):
        # No registrar rutas: el enlace privado contiene un token de acceso.
        self.log_message('"%s" %s %s', self.command, str(code), str(size))

    def enviar(self, contenido, estado=200, cabeceras=()):
        datos = contenido.encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(datos)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        for nombre, valor in cabeceras:
            self.send_header(nombre, valor)
        self.end_headers()
        self.wfile.write(datos)

    def autorizado(self):
        try:
            cookies = SimpleCookie()
            cookies.load(self.headers.get("Cookie", ""))
            sesion = cookies.get("sesion_admin")
            return bool(sesion and hmac.compare_digest(sesion.value.encode("utf-8"), SESION_ADMIN.encode("utf-8")))
        except (CookieError, ValueError):
            return False

    def pedir_acceso(self):
        self.enviar(pagina("Acceso restringido", "<h1>Acceso restringido</h1><p>Abre el enlace privado del panel que aparece en la terminal de la computadora.</p>"), 403)

    def redirigir(self, ruta, cabeceras=()):
        self.send_response(303)
        self.send_header("Location", ruta)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Referrer-Policy", "no-referrer")
        for nombre, valor in cabeceras:
            self.send_header(nombre, valor)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self):
        ruta = urlsplit(self.path).path
        if ruta.startswith("/panel/"):
            token = ruta[len("/panel/"):]
            if hmac.compare_digest(token.encode("utf-8"), ENLACE_ADMIN.encode("utf-8")):
                self.redirigir("/resultados", (("Set-Cookie", f"sesion_admin={SESION_ADMIN}; HttpOnly; SameSite=Lax; Path=/"),))
            else:
                self.enviar(pagina("No encontrado", "<h1>Página no encontrada</h1>"), 404)
        elif ruta == "/":
            self.enviar(pagina("Comparte tu opinión", """
                <h1>¿Qué opinas?</h1>
                <p>Escribe tu opinión sobre el producto o servicio elegido por el grupo.</p>
                <p class='aviso'>El responsable de la actividad podrá leer tu comentario. No incluyas nombres ni información personal.</p>
                <form method='post' action='/enviar'><label for='comentario'><strong>Tu comentario</strong></label>
                <p><textarea id='comentario' name='comentario' rows='5' maxlength='1000' required placeholder='Por ejemplo: La atención fue excelente'></textarea></p>
                <button type='submit'>Enviar comentario</button></form>
            """))
        elif ruta == "/resultados":
            if not self.autorizado():
                self.pedir_acceso()
                return
            registros = leer()
            analizados = [(i, r) for i, r in enumerate(registros) if r.get("pistas", "").startswith(MARCA_DIRECTA)]
            pendientes = [(i, r) for i, r in enumerate(registros) if not r.get("pistas", "").startswith(MARCA_DIRECTA)]
            conteo = Counter(r["clasificacion"] for _, r in analizados)
            total = len(analizados)
            cifras = "".join(
                f"<span>{escapar(k)}: <strong>{conteo[k]}</strong> "
                f"({conteo[k] / total * 100:.1f}%)</span>" if total else
                f"<span>{escapar(k)}: <strong>0</strong> (0.0%)</span>"
                for k in CATEGORIAS
            )
            filas = "".join(
                f"<div class='fila'><p>{escapar(r.get('comentario', ''))}</p>"
                f"<div class='etiqueta'>Resultado final: {escapar(r.get('clasificacion', ''))}</div>"
                f"{mostrar_detalles(r.get('pistas', ''))}<div class='pequeno'>{escapar(r.get('fecha', ''))}</div>"
                + f"<form method='post' action='/reanalizar'><input type='hidden' name='indice' value='{indice}'><input type='hidden' name='huella' value='{huella_registro(r)}'><button type='submit'>Analizar de nuevo</button></form></div>"
                for indice, r in reversed(analizados)
            )
            filas_pendientes = "".join(
                f"<div class='fila'><p>{escapar(r.get('comentario', ''))}</p>"
                f"<div class='pequeno'>{escapar(r.get('fecha', ''))}</div>"
                f"<form method='post' action='/reanalizar'><input type='hidden' name='indice' value='{indice}'><input type='hidden' name='huella' value='{huella_registro(r)}'><button type='submit'>Analizar con RoBERTuito</button></form></div>"
                for indice, r in reversed(pendientes)
            )
            contenido = (f"<h1>Resultados de la clase</h1><p>Comentarios analizados con RoBERTuito: <strong>{total}</strong></p>"
                         f"<div class='resumen'>{cifras}</div>{grafico_resultados(conteo, total)}"
                         "<p class='pequeno'>Los resultados muestran la clasificación directa de RoBERTuito. Las estimaciones pueden equivocarse.</p>"
                         "<p class='pequeno'>Al analizar un comentario de nuevo, se actualiza su clasificación sin duplicarlo en el gráfico.</p>"
                         f"{filas or '<p>Todavía no hay comentarios analizados con RoBERTuito.</p>'}"
                         + (f"<section><h2>Pendientes de análisis con RoBERTuito ({len(pendientes)})</h2>"
                            "<p class='pequeno'>Estos registros anteriores no se incluyen en las estadísticas hasta que se vuelvan a analizar.</p>"
                            f"{filas_pendientes}</section>" if pendientes else "")
                         +
                         "<p><a href='/'>Volver al formulario</a> · <a href='/resultados'>Actualizar resultados</a></p>"
                         "<form method='post' action='/salir'><button type='submit'>Cerrar sesión</button></form>")
            self.enviar(pagina("Resultados", contenido))
        else:
            self.enviar(pagina("No encontrado", "<h1>Página no encontrada</h1><a href='/'>Inicio</a>"), 404)

    def do_POST(self):
        global SESION_ADMIN
        ruta = urlsplit(self.path).path
        if ruta not in ("/enviar", "/reanalizar", "/salir"):
            self.enviar(pagina("No encontrado", "<h1>Página no encontrada</h1>"), 404)
            return
        if ruta in ("/reanalizar", "/salir") and not self.autorizado():
            self.pedir_acceso()
            return
        if ruta == "/salir":
            SESION_ADMIN = secrets.token_urlsafe(32)
            self.redirigir("/resultados", (("Set-Cookie", "sesion_admin=; HttpOnly; SameSite=Lax; Path=/; Max-Age=0"),))
            return
        try:
            longitud = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            longitud = 0
        if longitud <= 0 or longitud > 12000:
            self.enviar(pagina("Error", "<p>El comentario está vacío o es demasiado largo.</p><a href='/'>Volver</a>"), 400)
            return
        datos = parse_qs(self.rfile.read(longitud).decode("utf-8", errors="replace"))
        if ruta == "/reanalizar":
            try:
                indice = int(datos.get("indice", [""])[0])
                huella = datos.get("huella", [""])[0]
                if len(huella) != 64 or any(c not in "0123456789abcdef" for c in huella):
                    raise ValueError("Huella inválida")
            except ValueError:
                self.enviar(pagina("Error", "<p>No se pudo identificar el comentario. Actualiza el panel e inténtalo de nuevo.</p>"), 400)
                return
            registros = leer()
            if (indice < 0 or indice >= len(registros)
                    or not hmac.compare_digest(huella_registro(registros[indice]), huella)):
                self.enviar(pagina("Resultado actualizado", "<p>El comentario cambió. Actualiza el panel e inténtalo de nuevo.</p><a href='/resultados'>Volver</a>"), 409)
                return
            comentario = registros[indice].get("comentario", "")
        else:
            comentario = datos.get("comentario", [""])[0].strip()
        if not comentario or len(comentario) > 1000:
            self.enviar(pagina("Error", "<p>Escribe un comentario de hasta 1000 caracteres.</p><a href='/'>Volver</a>"), 400)
            return
        try:
            sugerido, puntuaciones = clasificar(comentario)
            alerta = alerta_ambiguedad(puntuaciones)
            resultado = sugerido
            detalle = (MARCA_DIRECTA + f"Modelo de texto: {sugerido} · "
                       + " · ".join(f"{k}: {puntuaciones[k] * 100:.1f}%" for k in CATEGORIAS_SENTIMIENTO)
                       + (" · Alerta: " + alerta if alerta else ""))
            if ruta == "/reanalizar":
                if not actualizar_registro(indice, huella, comentario, resultado, detalle):
                    self.enviar(pagina("Resultado actualizado", "<p>El comentario cambió. Actualiza el panel e inténtalo de nuevo.</p><a href='/resultados'>Volver</a>"), 409)
                    return
            else:
                guardar(comentario, resultado, detalle)
        except Exception:
            traceback.print_exc()
            self.enviar(pagina("Error de análisis", "<h1>No se pudo analizar el comentario</h1><p>El comentario no se guardó. Inténtalo de nuevo o revisa los mensajes de la terminal.</p><a href='/'>Volver</a>"), 503)
            return
        if ruta == "/reanalizar":
            self.redirigir("/resultados")
        else:
            self.enviar(pagina("Comentario recibido", "<h1>¡Gracias por participar!</h1><p>Tu comentario se ha recibido.</p><p><a href='/'>Enviar otro comentario</a></p>"))


def direccion_local():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as conexion:
            conexion.connect(("192.0.2.1", 80))
            return conexion.getsockname()[0]
    except OSError:
        return "TU_DIRECCION_IP"


if __name__ == "__main__":
    try:
        ENLACE_ADMIN = cargar_enlace_privado()
    except RuntimeError as error:
        print(f"No se pudo preparar el enlace privado: {error}", flush=True)
        raise SystemExit(1) from error
    print("Cargando RoBERTuito. La primera vez puede tardar mientras se descarga...", flush=True)
    try:
        inicializar_modelo()
    except Exception as error:
        print(f"No se pudo cargar el modelo: {error}", flush=True)
        print("Revisa la instalación y la conexión a Internet según LEEME.txt.", flush=True)
        raise SystemExit(1) from error
    servidor = ThreadingHTTPServer(("0.0.0.0", PUERTO), Servidor)
    print("Sistema listo. Deja esta ventana abierta durante la actividad.", flush=True)
    print(f"En esta computadora: http://localhost:{PUERTO}", flush=True)
    direccion = direccion_local()
    print(f"Comparte con la clase: http://{direccion}:{PUERTO}", flush=True)
    print(f"Panel privado para ti (no lo compartas): http://{direccion}:{PUERTO}/panel/{ENLACE_ADMIN}", flush=True)
    print(f"Panel privado en esta computadora: http://localhost:{PUERTO}/panel/{ENLACE_ADMIN}", flush=True)
    print(f"Los comentarios se guardan en: {ARCHIVO}", flush=True)
    print("Para detenerlo, presiona Ctrl+C.", flush=True)
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nSistema detenido.")
    finally:
        servidor.server_close()
