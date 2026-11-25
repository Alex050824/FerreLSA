from math import sqrt
from unittest import TestCase
from unittest.mock import patch

import torch

from . import busqueda_semantica as buscador


# Filas con la misma estructura que devuelve obtener_productos().
SOPORTE = ("S", "Mordaza para soldar tuberías", "Solo inmoviliza las piezas durante la unión.", 9500, 3, "unidad")
CORTE = ("C", "Cabezal modular", "Secciona conductos de cobre a la medida.", 6700, 10, "unidad")
LIMPIEZA = ("L", "Cabezal modular", "Elimina rebabas del extremo de conductos de cobre.", 6100, 6, "unidad")
MARTILLO = ("M", "Martillo de bola", "Conforma láminas metálicas mediante impactos.", 7000, 4, "unidad")
UNION = ("U", "Aplicador térmico TX", "Une conductos de cobre por capilaridad con aporte de estaño.", 31250, 2, "unidad")
DECAPANTE = ("D", "Preparado AB", "Gel que elimina recubrimientos de muebles conservando la superficie original.", 4500, 7, "litro")
BARNIZ = ("B", "Preparado AF", "Forma una capa protectora sobre muebles de madera.", 3900, 12, "litro")


def catalogo(cantidad, fichas):
    familias = ("Escuadra", "Arandela", "Abrazadera", "Bisagra", "Tornillo")
    relleno = [
        (f"R{i}", f"{familias[i % len(familias)]} ref. {i}", "Acabado galvanizado.", 1200 + i, 4, "unidad")
        for i in range(cantidad - len(fichas))
    ]
    return [*relleno, *fichas]


class IdoneidadCatalogoTests(TestCase):
    def setUp(self):
        # Solo se sustituyen las salidas de los modelos. El índice, la fusión de
        # candidatos, la construcción de fichas y la selección de filas son reales.
        self.enterContext(patch.object(buscador, "_indice", buscador.IndiceCatalogo()))
        self.enterContext(patch.object(buscador, "_vector_consulta", return_value=torch.tensor([1., 0.])))
        self.codificar = self.enterContext(patch.object(buscador, "convertir_a_vectores", side_effect=self.vectores))
        self.evaluar = self.enterContext(patch.object(buscador, "_evaluar_uso"))

    @staticmethod
    def vectores(pasajes):
        # Las fichas difíciles se sitúan cerca entre sí, incluso cuando solo
        # describen una tarea adyacente. La posición en MySQL no les da prioridad.
        proximidad = {
            texto: 0.99 - i * 0.01
            for i, fila in enumerate((SOPORTE, CORTE, LIMPIEZA, MARTILLO, UNION, BARNIZ, DECAPANTE))
            for texto in fila[1:3]
        }
        valores = [proximidad.get(p.removeprefix("passage: "), 0.1) for p in pasajes]
        return torch.tensor([[v, sqrt(1 - v * v)] for v in valores])

    def aprobar_solo(self, fila):
        ficha_completa = f"{fila[1]} — {fila[2]}"

        def dictamen(pregunta, opciones):
            if ficha_completa in opciones:
                return opciones.index(ficha_completa), 1.0
            return None

        self.evaluar.side_effect = dictamen

    def test_alta_dinamica_entre_consultas_de_100_y_500_productos(self):
        pregunta = "Busco algo para soldar tuberías"
        self.aprobar_solo(UNION)
        for cantidad in (100, 500):
            with self.subTest(cantidad=cantidad):
                filas = catalogo(cantidad, [SOPORTE, CORTE, LIMPIEZA, MARTILLO])
                with patch("chatbot_api.views.obtener_productos", side_effect=[filas, [*filas, UNION], filas]) as leer:
                    self.assertEqual(buscador.buscar_productos(pregunta), [])
                    self.assertEqual([f for f, _ in buscador.buscar_productos(pregunta)], [UNION])
                    nuevos = self.codificar.call_args.args[0]
                    self.assertEqual(set(nuevos), {"passage: " + t for t in UNION[1:3]})
                    self.assertEqual(buscador.buscar_productos(pregunta), [])
                    self.assertEqual(leer.call_count, 3)

                opciones = self.evaluar.call_args_list[-2].args[1]
                self.assertLessEqual(len(opciones), 8)
                for ficha in (SOPORTE, CORTE, LIMPIEZA, UNION):
                    self.assertIn(f"{ficha[1]} — {ficha[2]}", opciones)

    def test_necesidad_ambigua_entre_productos_similares(self):
        self.evaluar.return_value = None
        for cantidad in (100, 500):
            with self.subTest(cantidad=cantidad):
                filas = catalogo(cantidad, [CORTE, LIMPIEZA, UNION])
                resultado = buscador.buscar_productos("Necesito trabajar con estos conductos", productos=filas)
                self.assertEqual(resultado, [])
                self.assertLessEqual(len(self.evaluar.call_args.args[1]), 8)
                self.assertIn(f"{CORTE[1]} — {CORTE[2]}", self.evaluar.call_args.args[1])
                self.assertIn(f"{LIMPIEZA[1]} — {LIMPIEZA[2]}", self.evaluar.call_args.args[1])

    def test_parafrasis_sin_terminos_en_comun_en_otro_rubro(self):
        pregunta = "¿Cómo puedo quitar el barniz sin desgastar la madera?"
        self.assertFalse(buscador._terminos(pregunta) & buscador._terminos(" ".join(DECAPANTE[1:3])))
        self.aprobar_solo(DECAPANTE)
        for cantidad in (100, 500):
            with self.subTest(cantidad=cantidad):
                filas = catalogo(cantidad, [DECAPANTE, BARNIZ])
                resultado = buscador.buscar_productos(pregunta, productos=filas)
                self.assertEqual([f for f, _ in resultado], [DECAPANTE])
