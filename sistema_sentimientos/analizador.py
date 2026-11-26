"""Inferencia de sentimiento con RoBERTuito, entrenado para español.

El modelo se carga una sola vez al arrancar y se ejecuta localmente. La
primera ejecución descarga el tokenizador y los pesos desde Hugging Face.
"""

import os
import threading
from pathlib import Path

MODELO = "pysentimiento/robertuito-sentiment-analysis"
MAX_TOKENS = 128
ETIQUETAS = {"POS": "Positivo", "NEG": "Negativo", "NEU": "Neutral"}
# Umbrales orientativos, no calibrados ni validados para esta actividad.
UMBRAL_PUNTUACION = 0.55
UMBRAL_MARGEN = 0.20

_cerrojo = threading.Lock()
_tokenizador = None
_modelo = None
_torch = None


def inicializar_modelo():
    """Carga una vez los pesos y comprueba las etiquetas esperadas.

    Lanza RuntimeError si falta una dependencia o no se puede cargar el
    modelo; nunca sustituye la IA por reglas sin avisar.
    """
    global _tokenizador, _modelo, _torch
    with _cerrojo:
        if _modelo is not None:
            return
        try:
            # Hugging Face lee esta variable durante su importación. La caché
            # queda junto al proyecto salvo que el usuario configure otra.
            os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parent / ".modelos"))
            import torch
            from transformers import AutoModelForSequenceClassification, AutoTokenizer
        except (ImportError, OSError) as error:
            raise RuntimeError(
                "No se pudieron cargar las librerías de IA. Instala las "
                "dependencias con: python -m pip install -r requirements.txt"
            ) from error

        modelo_configurado = os.environ.get("SENTIMIENTOS_MODELO", "").strip()
        origen = str(Path(modelo_configurado).expanduser().resolve()) if modelo_configurado else MODELO
        try:
            # Reutilizar la caché primero evita esperas de red en cada inicio.
            # Si falta algún archivo, el segundo intento permite descargarlo.
            try:
                tokenizador = AutoTokenizer.from_pretrained(origen, local_files_only=True)
                modelo = AutoModelForSequenceClassification.from_pretrained(
                    origen, use_safetensors=True, local_files_only=True
                )
            except (OSError, ValueError):
                if modelo_configurado:
                    raise
                tokenizador = AutoTokenizer.from_pretrained(MODELO)
                modelo = AutoModelForSequenceClassification.from_pretrained(
                    MODELO, use_safetensors=True
                )
            etiquetas = set(modelo.config.id2label.values())
            if etiquetas != set(ETIQUETAS):
                raise ValueError(f"Etiquetas inesperadas: {etiquetas}")
            modelo.eval()
        except Exception as error:
            if modelo_configurado:
                raise RuntimeError(
                    f"No se pudo cargar el modelo local configurado en SENTIMIENTOS_MODELO: {origen}. "
                    f"Comprueba su ruta y sus archivos. Detalle: {error}"
                ) from error
            raise RuntimeError(
                "No se pudo cargar RoBERTuito. La primera vez se necesita "
                "conexión a Internet para descargar el modelo; revisa la "
                f"conexión y vuelve a intentarlo. Detalle: {error}"
            ) from error

        _torch, _tokenizador, _modelo = torch, tokenizador, modelo


def clasificar(texto):
    """Devuelve (etiqueta, puntuaciones por clase) para el comentario.

    El modelo admite 128 tokens; el contenido posterior se descarta.
    Las puntuaciones son estimaciones del modelo, no garantías de acierto.
    """
    if not isinstance(texto, str) or not texto.strip():
        raise ValueError("El comentario no puede estar vacío.")
    with _cerrojo:
        if _modelo is None:
            raise RuntimeError("Primero debes inicializar el modelo de IA.")
        entradas = _tokenizador(
            texto, return_tensors="pt", truncation=True, max_length=MAX_TOKENS
        )
        with _torch.inference_mode():
            probabilidades = _torch.softmax(_modelo(**entradas).logits, dim=-1)[0]
        puntuaciones = {
            ETIQUETAS[_modelo.config.id2label[indice]]: float(valor)
            for indice, valor in enumerate(probabilidades.tolist())
        }
        resultado = max(puntuaciones, key=puntuaciones.get)
        return resultado, puntuaciones


def alerta_ambiguedad(puntuaciones):
    """Advierte cuando el modelo no muestra una preferencia clara.

    La regla compara sus puntuaciones; no detecta por sí sola todos los
    mensajes ambiguos. El modelo puede dar una puntuación alta y equivocarse.
    Los umbrales son heurísticos, no probabilidades calibradas de acierto.
    """
    ordenadas = sorted(puntuaciones.values(), reverse=True)
    if len(ordenadas) < 2:
        raise ValueError("Se necesitan al menos dos puntuaciones para comparar.")
    if (ordenadas[0] < UMBRAL_PUNTUACION or
            ordenadas[0] - ordenadas[1] < UMBRAL_MARGEN):
        return ("El modelo no distingue claramente entre las opciones. "
                "Se recomienda revisar este comentario manualmente.")
    return None
