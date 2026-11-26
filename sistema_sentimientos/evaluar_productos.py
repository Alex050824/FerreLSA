"""Evaluación fija de ejemplos de producto contra el servicio HTTP local.

Es un conjunto pequeño de ejemplos redactados, no una medición representativa
de la calidad con comentarios reales. No debe incluirse en el entrenamiento.
"""
import argparse
from collections import Counter
import json
from pathlib import Path
from urllib.request import Request, urlopen


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:8001/analizar")
    parser.add_argument("--modelo", help="Ruta a un modelo local para evaluarlo sin cambiar el servicio")
    parser.add_argument("--datos", default=str(Path(__file__).with_name("evaluacion_productos.json")),
                        help="Conjunto JSON de frases y etiquetas esperadas")
    parser.add_argument("--reglas-precio", action="store_true", help="Aplicar reglas de precio sobre el modelo local")
    args = parser.parse_args()
    samples = json.loads(Path(args.datos).read_text(encoding="utf-8"))
    if args.modelo:
        import torch
        from transformers import AutoModelForSequenceClassification, AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(args.modelo, local_files_only=True)
        model = AutoModelForSequenceClassification.from_pretrained(args.modelo, local_files_only=True)
        model.eval()
        entries = tokenizer([s["texto"] for s in samples], padding=True, truncation=True,
                            max_length=128, return_tensors="pt")
        with torch.inference_mode():
            labels = model(**entries).logits.argmax(dim=-1).tolist()
        mapping = {"POS": "POSITIVO", "NEG": "NEGATIVO", "NEU": "NEUTRAL"}
        results = [mapping[model.config.id2label[label]] for label in labels]
        if args.reglas_precio:
            from reglas_precios import sentimiento_precio
            results = [((sentimiento_precio(sample["texto"]) or "").upper() or result)
                       for sample, result in zip(samples, results)]
    else:
        if args.reglas_precio:
            parser.error("--reglas-precio requiere --modelo")
        results = []
        for sample in samples:
            request = Request(args.url, data=json.dumps({"texto": sample["texto"]}, ensure_ascii=False).encode("utf-8"),
                              headers={"Content-Type": "application/json"})
            with urlopen(request, timeout=120) as response:
                results.append(json.load(response)["sentimiento"])
    totals, hits = Counter(), Counter()
    errors = []
    for sample, actual in zip(samples, results):
        expected = sample["esperado"]
        totals[expected] += 1
        hits[expected] += actual == expected
        if actual != expected:
            errors.append({"texto": sample["texto"], "esperado": expected, "obtenido": actual})
    print(json.dumps({"aciertos": sum(hits.values()), "total": len(samples),
                      "por_clase": {label: {"aciertos": hits[label], "total": totals[label]}
                                    for label in sorted(totals)},
                      "errores": errors}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
