from unittest import TestCase
from unittest.mock import patch

from . import busqueda_semantica as buscador


class BusquedaTest(TestCase):
    def test_texto_plural_varios_nombres_y_atributos_no_registrados(self):
        filas = [
            ("A1", "Llave inglesa", "Mango corto", 11, 3),
            ("B2", "Alicate universal", "Acabado pulido", 30, 9),
            ("A2", "Llave fija", "De 12 mm", 10, 7),
        ]

        def codigos(pregunta):
            return [fila[0] for fila, _ in buscador.buscar_productos(pregunta, productos=filas)]

        self.assertCountEqual(codigos("¿Qué precio tienen las llaves y los alicates?"), ["A1", "A2", "B2"])
        self.assertEqual(codigos("¿Tienen llaves inglesas?"), ["A1"])
        self.assertEqual(codigos("¿Me podés decir cuánto cuesta la llave de mango corto?"), ["A1"])
        self.assertEqual(codigos("¿Tienen una llave inalámbrica?"), [])
        self.assertEqual(codigos("¿Tienen llaves inalámbricas para apretar tuercas?"), [])
        self.assertEqual(codigos("Alicates de 450 mm"), [])
        self.assertEqual(codigos("¿Cuánto cuesta una enciclopedia?"), [])

    def test_lectura_de_fila_actual_en_catalogo_de_500(self):
        productos = [(str(i), f"Referencia {i}", "", i, 1) for i in range(500)]
        nueva = ("490", "Referencia 490", "", 1234, 0)
        productos[490] = nueva
        respuesta = buscador.buscar_productos("Referencia 490", productos=productos)
        self.assertEqual([fila for fila, _ in respuesta], [nueva])

    @patch.object(buscador, "convertir_a_vectores")
    def test_reutiliza_textos_iguales_y_elimina_bajas_del_indice(self, codificar):
        import torch

        codificar.side_effect = lambda lote: torch.ones(len(lote), 4)
        indice = buscador.IndiceCatalogo()
        matriz = indice.actualizar(("Nombre inicial", "Otra ficha"))
        self.assertIs(matriz, indice.actualizar(("Nombre inicial", "Otra ficha")))
        indice.actualizar(("Otra ficha", "Nombre cambiado", "Otra ficha"))
        self.assertEqual(codificar.call_count, 2)

        self.assertEqual(codificar.call_args_list[0].args[0], ["passage: Nombre inicial", "passage: Otra ficha"])
        self.assertEqual(codificar.call_args_list[1].args[0], ["passage: Nombre cambiado"])
        self.assertEqual(set(indice.vectores), {"Otra ficha", "Nombre cambiado"})
        indice.actualizar(("Otra ficha",))
        self.assertEqual(codificar.call_count, 2)

    def test_reconoce_tareas_sin_nombres_de_catalogo(self):
        for consulta in ("busco algo que haga agujeros", "se me rompio una bisagra",
                         "hay que emparejar una superficie", "quisiera preparar una mezcla"):
            with self.subTest(consulta=consulta):
                self.assertTrue(buscador._es_tarea(consulta))

    @patch.object(buscador, "_candidatos_semanticos", return_value=[0, 1])
    def test_homonimos_con_distinta_descripcion_se_evalúan_por_separado(self, candidatos):
        filas = [("A", "Broca", "Para madera", 100, 2), ("B", "Broca", "Para vidrio", 200, 4)]
        with patch.object(buscador, "_evaluar_uso") as evaluar:
            evaluar.side_effect = lambda _, opciones: (opciones.index("Broca — Para madera"), 1)
            respuesta = buscador.buscar_productos("Necesito hacer un agujero en una tabla", productos=filas)
        self.assertEqual([fila[0] for fila, _ in respuesta], ["A"])
        candidatos.assert_called_once()
