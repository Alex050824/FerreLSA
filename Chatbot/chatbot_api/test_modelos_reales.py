"""Desde Chatbot, activar FERRELSA_PRUEBA_MODELOS=1 y ejecutar
python -m unittest chatbot_api.test_modelos_reales.
"""

import os
from unittest import TestCase, skipUnless

from .busqueda_semantica import buscar_productos


@skipUnless(os.getenv("FERRELSA_PRUEBA_MODELOS") == "1", "Prueba opcional con E5 y Qwen")
class RecomendacionConModelosRealesTest(TestCase):
    def test_idoneidad_al_incorporar_una_ficha(self):
        inicial = [
            ("M1", "Martillo de acero", "Cabeza plana para clavar puntas.", 3200, 6, "unidad"),
            ("C1", "Cortatubos de cobre", "Su cuchilla corta el tubo a medida.", 7100, 4, "unidad"),
            ("P1", "Manta de soldadura", "Protege la pared del calor al soldar tuberías de cobre.",
             4500, 3, "unidad"),
        ]
        soplete = ("S1", "Soplete de fontanero", "Su llama permite unir tubos de cobre con estaño.",
                   18500, 2, "unidad")
        ampliado = [*inicial, soplete]
        pregunta = "Necesito algo para soldar tuberías de cobre."
        casos = [
            ("sin equipo adecuado", pregunta, inicial, []),
            ("alta del equipo adecuado", pregunta, ampliado, ["S1"]),
            ("sin tarea concreta", "Necesito algo para trabajar con tuberías de cobre.", ampliado, []),
        ]
        for escenario, consulta, filas, esperados in casos:
            with self.subTest(escenario=escenario, consulta=consulta):
                resultado = buscar_productos(consulta, productos=filas)
                self.assertEqual([fila[0] for fila, _ in resultado], esperados)
