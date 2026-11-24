from types import SimpleNamespace
from unittest import TestCase
from unittest.mock import Mock, patch

import torch

from . import modelo_qwen as qwen


class TokenizadorDePrueba:
    """Un token representa una oración para probar ambos caminos sin cargar pesos."""

    eos_token_id = 0

    def __init__(self, borrador):
        self.frases = ["", borrador]
        self.mensajes = None

    def apply_chat_template(self, mensajes, **kwargs):
        self.mensajes = mensajes
        return {"input_ids": torch.tensor([[42]])}

    def __call__(self, frases, **kwargs):
        self.frases.extend(frases)
        return {"input_ids": [[self.frases.index(f)] for f in frases]}

    def decode(self, ids, **kwargs):
        return "".join(self.frases[i] for i in ids)


class RedaccionQwenTests(TestCase):
    fila = ("cod-reservado", "Taladro", "Taladro de 650W.", "87654.32", "904")

    def redactar(self, borrador, filas=None, incluir_descripcion=True):
        tokenizador = TokenizadorDePrueba(borrador)
        logits = torch.zeros(1, 1, 256)
        logits[0, 0, 1] = 10
        modelo = Mock(return_value=SimpleNamespace(logits=logits, cache=Mock()))
        modelo.return_value.cache.get_seq_length.return_value = 2
        with patch.object(qwen, "_cargar_qwen", return_value=(tokenizador, modelo)):
            resultado = qwen.generar_explicacion("¿Qué características tiene?", filas or [self.fila],
                                                incluir_descripcion=incluir_descripcion)
        return resultado, tokenizador, modelo.return_value.cache

    def test_acepta_redaccion_abierta_y_solamente_transmite_fuentes_necesarias(self):
        texto, tokenizador, cache = self.redactar("Sobre tu consulta, la ficha de [N1] indica [D1a].")
        self.assertEqual(texto, "Sobre tu consulta, la ficha de Taladro indica «Taladro de 650W».")
        cache.crop.assert_not_called()
        for dato in ("cod-reservado", "87654.32", "904"):
            self.assertNotIn(dato, str(tokenizador.mensajes))

    def test_respaldo_ante_valores_o_caracteristicas_inventadas(self):
        for borrador in ("[N1] cuesta ₡55.000.", "Hay ocho mil unidades de [N1].",
                         "[N1] es inalámbrico.", "En el catálogo figura [N2]."):
            with self.subTest(borrador=borrador):
                texto, _, cache = self.redactar(borrador)
                cache.crop.assert_called_once_with(-1)
                self.assertIn("«Taladro de 650W»", texto)
                self.assertNotIn(borrador, texto)

    def test_valida_que_la_cita_corresponda_al_producto(self):
        fila2 = ("otra", "Sierra", "Sierra con mango de madera.", "500", "0")
        texto, _, cache = self.redactar("La ficha de [N1] indica [D2a].", [self.fila, fila2])
        cache.crop.assert_called_once_with(-1)
        self.assertIn("Taladro de 650W", texto)
        self.assertNotIn("Sierra", texto)

    def test_excluye_importes_de_descripciones_y_distingue_descripcion_ausente(self):
        fila = ("a", "Martillo", "Precio: ₡50. Agotado.", "60", "2")
        texto, tokenizador, _ = self.redactar("Aquí figura [N1].", [fila])
        self.assertIn("detalle técnico verificable", texto)
        self.assertNotIn("₡50", str(tokenizador.mensajes))
        self.assertNotIn("Agotado", str(tokenizador.mensajes))
        texto, tokenizador, _ = self.redactar("Aquí figura [N1].", incluir_descripcion=False)
        self.assertNotIn("detalle técnico", texto)
        self.assertNotIn("650W", str(tokenizador.mensajes))
