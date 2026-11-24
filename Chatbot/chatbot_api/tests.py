from decimal import Decimal
from unittest.mock import patch

from django.test import Client, SimpleTestCase

from . import views


URL = "/api/chatbot/preguntar/"


def fila(codigo="A", nombre="Artículo de prueba", precio="5500.00", existencia="8.000", unidad="unidad"):
    # Datos en memoria. Estas pruebas nunca crean tablas ni productos en MySQL.
    return (codigo, nombre, "Ficha técnica", Decimal(precio), Decimal(existencia), unidad)


class ChatbotHTTPTests(SimpleTestCase):
    def preguntar(self, pregunta):
        return self.client.post(URL, {"pregunta": pregunta}, content_type="application/json")

    def test_validacion_y_metodo(self):
        self.assertEqual(self.client.get(URL).status_code, 405)
        for cuerpo in ("[", "[]", "null"):
            with self.subTest(cuerpo=cuerpo):
                self.assertEqual(self.client.post(URL, cuerpo, content_type="application/json").status_code, 400)
        for pregunta in (None, 24, "", "   ", "x" * 301):
            with self.subTest(pregunta=pregunta):
                self.assertEqual(self.preguntar(pregunta).status_code, 400)

    @patch.object(views, "obtener_productos", return_value=())
    def test_csrf_y_catalogo_vacio(self, leer):
        cliente = Client(enforce_csrf_checks=True)
        cuerpo = {"pregunta": "¿Qué productos tienen disponibles?"}
        self.assertEqual(cliente.post(URL, cuerpo, content_type="application/json").status_code, 403)
        cliente.get("/api/chatbot/csrf/")
        token = cliente.cookies["csrftoken"].value
        respuesta = cliente.post(URL, cuerpo, content_type="application/json", HTTP_X_CSRFTOKEN=token)
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["productos"], [])
        self.assertIn("no hay", respuesta.json()["respuesta"])
        leer.assert_called_once()

    @patch("chatbot_api.modelo_qwen.generar_explicacion", return_value="Te comparto la ficha.")
    @patch("chatbot_api.busqueda_semantica.buscar_productos")
    @patch.object(views, "obtener_productos")
    def test_datos_actuales_y_exactos_en_dos_peticiones(self, leer, buscar, generar):
        leer.side_effect = [(fila(),), (fila(precio="5450.75", existencia="1.500", unidad="metro"),)]
        buscar.side_effect = lambda _, productos: [(productos[0], 1)]
        primera = self.preguntar("¿Cuánto cuesta el artículo?").json()
        segunda = self.preguntar("¿Cuánto cuesta el artículo?").json()
        self.assertIn("₡5.500 · 8 unidades", primera["respuesta"])
        self.assertNotIn("₡55.000", primera["respuesta"])
        self.assertNotIn("8.000", primera["respuesta"])
        self.assertIn("₡5.450,75 · Existencia (metro): 1,5", segunda["respuesta"])
        ficha = segunda["productos"][0]
        self.assertEqual(Decimal(ficha["precio_venta"]), Decimal("5450.75"))
        self.assertEqual(Decimal(ficha["existencia"]), Decimal("1.5"))
        self.assertEqual(ficha["moneda"], "CRC")
        self.assertEqual(leer.call_count, 2)
        self.assertEqual(generar.call_count, 2)
        self.assertEqual(set(segunda["tiempos_ms"]), {"catalogo", "busqueda", "generacion", "total"})

    @patch("chatbot_api.modelo_qwen.generar_explicacion", return_value="Podés consultar estas fichas.")
    @patch.object(views, "obtener_productos")
    def test_listado_acotado_y_solo_con_existencias(self, leer, generar):
        filas = [fila(str(i)) for i in range(500)]
        leer.return_value = [fila("AGOTADO", existencia="0"), *filas]
        datos = self.preguntar("¿Qué productos tienen disponibles?").json()
        self.assertEqual([f["codigo"] for f in datos["productos"]], [f[0] for f in filas[:views.LIMITE_LISTADO]])
        self.assertIn(f"de {len(filas)} productos", datos["respuesta"])
        self.assertLessEqual(len(generar.call_args.args[1]), 3)
        self.assertFalse(generar.call_args.kwargs["incluir_descripcion"])

    @patch("chatbot_api.modelo_qwen.generar_explicacion")
    @patch("chatbot_api.busqueda_semantica.buscar_productos", return_value=[])
    @patch.object(views, "obtener_productos", return_value=(fila(),))
    def test_sin_evidencia_no_publica_productos(self, leer, buscar, generar):
        datos = self.preguntar("¿Qué productos tienen para astronomía?").json()
        self.assertFalse(datos["productos"])
        self.assertNotIn("₡", datos["respuesta"])
        buscar.assert_called_once()
        generar.assert_not_called()

    def test_producto_agotado_sin_redondear_precio(self):
        texto = views._linea_producto(fila(precio="0.50", existencia="0"))
        self.assertIn("₡0,50", texto)
        self.assertIn("Agotado", texto)
