from decimal import Decimal
from unittest.mock import patch

from django.test import Client, SimpleTestCase

from . import views
from .tests import URL


CINTA = ("C1", "Cinta métrica", "Longitud de 3 metros.", Decimal("3200.00"), Decimal("7"), "unidad")
NIVEL = ("N2", "Nivel magnético", "Base de aluminio.", Decimal("8400.00"), Decimal("2"), "unidad")


class ConversacionHTTPTests(SimpleTestCase):
    def setUp(self):
        super().setUp()
        self.leer = self.enterContext(patch.object(views, "obtener_productos", return_value=(CINTA, NIVEL)))
        self.buscar = self.enterContext(patch("chatbot_api.busqueda_semantica.buscar_productos"))
        self.buscar.side_effect = lambda pregunta, productos: [
            (fila, 1) for fila in productos if fila[1].casefold() in pregunta.casefold()
        ]
        self.redactar = self.enterContext(patch("chatbot_api.modelo_qwen.generar_explicacion"))
        self.redactar.side_effect = lambda _, filas, incluir_descripcion: (
            " ".join(fila[2] for fila in filas) if incluir_descripcion else "Estos son los datos del catálogo."
        )

    def preguntar(self, pregunta, cliente=None, conversacion=None):
        cuerpo = {"pregunta": pregunta}
        if conversacion is not None:
            cuerpo["conversacion"] = conversacion
        respuesta = (cliente or self.client).post(URL, cuerpo, content_type="application/json")
        self.assertEqual(respuesta.status_code, 200)
        datos = respuesta.json()
        self.assertTrue(datos["respuesta"].strip())
        return datos

    def unica_ficha(self, datos, codigo):
        self.assertEqual([fila["codigo"] for fila in datos["productos"]], [codigo])
        return datos["productos"][0]

    def test_saludo_agradecimiento_ayuda_y_despedida(self):
        textos = []
        for pregunta in ("¡Hola, buenos días!", "Muchas gracias", "¿En qué me podés ayudar?", "Hasta luego"):
            with self.subTest(pregunta=pregunta):
                datos = self.preguntar(pregunta)
                self.assertEqual(datos["productos"], [])
                textos.append(datos["respuesta"])
        self.assertEqual(len(set(textos)), 4)
        self.leer.assert_not_called()
        self.buscar.assert_not_called()
        self.redactar.assert_not_called()

    def test_el_saludo_con_consulta_conserva_el_producto(self):
        datos = self.preguntar("Hola, ¿cuánto cuesta la cinta métrica?")
        self.assertEqual(Decimal(self.unica_ficha(datos, "C1")["precio_venta"]), Decimal("3200.00"))

    def test_seguimientos_reflejan_el_precio_existencia_descripcion_y_baja_actuales(self):
        self.unica_ficha(self.preguntar("¿Tienen cinta métrica?"), "C1")
        actual = ("C1", "Cinta métrica", "Longitud de 5 metros.", Decimal("3195.25"), Decimal("3"), "unidad")
        self.leer.return_value = (NIVEL, actual)
        precio = self.unica_ficha(self.preguntar("¿Cuánto cuesta?"), "C1")
        self.assertEqual(Decimal(precio["precio_venta"]), actual[3])

        self.leer.return_value = (NIVEL, (*actual[:4], Decimal("0"), actual[5]))
        existencias = self.unica_ficha(self.preguntar("¿Cuántas unidades quedan?"), "C1")
        self.assertEqual(Decimal(existencias["existencia"]), 0)
        detalles = self.preguntar("¿Qué características tiene?")
        self.assertEqual(self.unica_ficha(detalles, "C1")["descripcion"], actual[2])
        self.assertIn(actual[2].rstrip("."), detalles["respuesta"])

        self.leer.return_value = (NIVEL,)
        baja = self.preguntar("¿Cuánto cuesta?")
        self.assertEqual(baja["productos"], [])
        self.assertNotIn("₡", baja["respuesta"])

    def test_dos_sesiones_mantienen_referencias_distintas(self):
        otra = Client()
        self.unica_ficha(self.preguntar("¿Tienen cinta métrica?"), "C1")
        self.unica_ficha(self.preguntar("¿Tienen nivel magnético?", otra), "N2")
        self.unica_ficha(self.preguntar("¿Cuánto cuesta?"), "C1")
        self.unica_ficha(self.preguntar("¿Cuánto cuesta?", otra), "N2")

    def test_dos_conversaciones_del_mismo_cliente_mantienen_referencias_distintas(self):
        cinta = "1" * 32
        nivel = "2" * 32
        self.unica_ficha(self.preguntar("¿Tienen cinta métrica?", conversacion=cinta), "C1")
        self.unica_ficha(self.preguntar("¿Tienen nivel magnético?", conversacion=nivel), "N2")
        self.unica_ficha(self.preguntar("¿Cuánto cuesta?", conversacion=cinta), "C1")
        self.unica_ficha(self.preguntar("¿Cuánto cuesta?", conversacion=nivel), "N2")

    def test_ignora_una_cookie_de_contexto_manipulada(self):
        self.unica_ficha(self.preguntar("¿Tienen cinta métrica?"), "C1")
        self.client.cookies["ferrelsa_chat"] = self.client.cookies["ferrelsa_chat"].value + "x"
        datos = self.preguntar("¿Cuánto cuesta?")
        self.assertEqual(datos["productos"], [])
        self.assertNotIn("₡", datos["respuesta"])

    def test_varias_referencias_requieren_aclaracion_y_se_puede_precisar_el_nombre(self):
        datos = self.preguntar("¿Tienen cinta métrica y nivel magnético?")
        self.assertCountEqual([f["codigo"] for f in datos["productos"]], ["C1", "N2"])
        aclaracion = self.preguntar("¿Cuánto cuesta?")
        self.assertEqual(aclaracion["productos"], [])
        self.assertNotIn("₡", aclaracion["respuesta"])
        self.assertRegex(aclaracion["respuesta"].casefold(), r"cuál|cual|artículo|producto|nombre|código|referencia|especific")
        self.unica_ficha(self.preguntar("El nivel magnético"), "N2")

    def test_precio_sin_antecedente_solicita_identificar_el_producto(self):
        datos = self.preguntar("¿Cuánto cuesta?")
        self.assertEqual(datos["productos"], [])
        self.assertNotIn("₡", datos["respuesta"])
        self.assertRegex(datos["respuesta"].casefold(), r"cuál|cual|artículo|producto|nombre|código|referencia|especific")
        self.buscar.assert_not_called()

    def test_horario_y_pedido_quedan_fuera_de_la_consulta_de_productos(self):
        for pregunta in ("¿Cuál es el horario de atención?", "Quiero hacer un pedido"):
            with self.subTest(pregunta=pregunta):
                datos = self.preguntar(pregunta)
                self.assertEqual(datos["productos"], [])
                self.assertNotIn("₡", datos["respuesta"])
        self.buscar.assert_not_called()
        self.redactar.assert_not_called()

    def test_agradecer_conserva_la_referencia_y_despedirse_la_borra(self):
        self.unica_ficha(self.preguntar("¿Tienen cinta métrica?"), "C1")
        self.preguntar("Muchas gracias")
        precio = self.unica_ficha(self.preguntar("Hola, ¿cuánto cuesta?"), "C1")
        self.assertEqual(Decimal(precio["precio_venta"]), CINTA[3])
        self.preguntar("Hasta luego")
        datos = self.preguntar("¿Cuánto cuesta?")
        self.assertEqual(datos["productos"], [])
        self.assertNotIn("₡", datos["respuesta"])

    def test_un_producto_nuevo_reemplaza_el_anterior_y_una_busqueda_fallida_lo_descarta(self):
        self.unica_ficha(self.preguntar("¿Tienen cinta métrica?"), "C1")
        self.unica_ficha(self.preguntar("¿Tienen nivel magnético?"), "N2")
        self.unica_ficha(self.preguntar("¿Cuánto cuesta?"), "N2")
        sin_coincidencia = self.preguntar("¿Tienen una llave dinamométrica?")
        self.assertEqual(sin_coincidencia["productos"], [])
        seguimiento = self.preguntar("¿Cuánto cuesta?")
        self.assertEqual(seguimiento["productos"], [])
        self.assertNotIn("₡", seguimiento["respuesta"])

    def test_una_tarea_incompleta_pide_aclarar(self):
        datos = self.preguntar("Necesito algo para…")
        self.assertEqual(datos["productos"], [])
        self.assertNotIn("₡", datos["respuesta"])
        self.assertRegex(datos["respuesta"].casefold(), r"qué|cuál|tarea|trabajo|detalle|producto")
        self.buscar.assert_not_called()
        self.redactar.assert_not_called()

    def test_clima_y_envios_se_distinguen_de_una_consulta_de_inventario(self):
        for pregunta in ("¿Qué tiempo hará mañana?", "¿Cuánto cuesta el envío a domicilio?"):
            with self.subTest(pregunta=pregunta):
                datos = self.preguntar(pregunta)
                self.assertEqual(datos["productos"], [])
                self.assertNotIn("₡", datos["respuesta"])
        self.buscar.assert_not_called()
        self.redactar.assert_not_called()
