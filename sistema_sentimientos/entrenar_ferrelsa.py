"""Ajuste supervisado reproducible de la cabeza de RoBERTuito para FerreLSA.

Los ejemplos son sintéticos: sirven para adaptar vocabulario, no sustituyen
una evaluación con comentarios reales etiquetados por personas.
"""
import os
import random
from pathlib import Path

os.environ.setdefault("HF_HOME", str(Path(__file__).resolve().parent / ".modelos"))
os.environ.setdefault("HF_HUB_OFFLINE", "1")

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

BASE = "pysentimiento/robertuito-sentiment-analysis"
DESTINO = Path(__file__).resolve().parent / "modelo_ferrelsa_v2"
SEMILLA = 2026

# Frases redactadas para esta tarea. No usar comentarios.csv: sus etiquetas
# proceden del mismo modelo y no son correcciones humanas verificadas.
EJEMPLOS = {
    "POS": [
        "Muy util", "muy útil", "es util", "bastante útil", "me resultó de mucha utilidad",
        "sirve para lo que necesito", "hace bien su trabajo", "una herramienta práctica", "es muy práctico",
        "funcionó de maravilla", "funciona bien", "el taladro sirve perfectamente", "excelente calidad",
        "buena compra", "me encantó", "lo recomiendo mucho", "buen material", "estoy satisfecho",
        "superó mis expectativas", "buena relación calidad precio", "vale lo que cuesta", "precio justo",
        "a buen precio", "es económico", "me salió barato", "resulta barato", "un producto accesible",
        "no cuesta mucho", "el precio no es alto", "no es costoso", "el costo es razonable",
        "el precio es bajo", "su precio es excelente", "se consigue a un precio cómodo", "ahorré dinero",
        "vale cada colón", "buena calidad y precio", "es resistente", "muy duradero", "muy sencillo de usar",
        "fácil de instalar", "quedó perfecto", "sirve bastante", "le doy buena nota", "llegó en buen estado",
        "me ayudó mucho", "cumple lo prometido", "lo volvería a comprar", "el producto está muy bien",
        "es una buena herramienta", "trabaja correctamente", "no tengo quejas", "precio bastante bajo",
        "no me pareció nada caro", "no está caro", "no es para nada costoso", "el precio no me pareció excesivo",
        "no es de precio alto", "su costo no es elevado", "no me cobró de más", "no resulta nada caro",
        "no cuesta demasiado", "no cobran mucho", "el valor no es exagerado", "el precio no es abusivo",
        "el costo no me parece excesivo", "está a buen precio", "barato y bueno", "es bastante asequible",
        "buena herramienta para el hogar", "se ve de buena calidad", "el material es fuerte", "llegó perfecto",
    ],
    "NEG": [
        "Muy caro", "es demasiado caro", "carísimo", "resulta caro", "demasiado costoso",
        "cuesta demasiado", "el costo es demasiado alto", "un precio exagerado", "precios altos",
        "está muy costoso", "pagué demasiado", "sale carísimo", "el precio es excesivo", "un costo elevado",
        "no vale lo que cuesta", "me parece costoso", "tiene un precio altísimo", "me cobraron mucho",
        "el costo no es razonable", "el precio no es bajo", "no es barato", "es poco económico",
        "nada económico", "el precio es abusivo", "cobra mucho para su calidad", "muy elevado su costo",
        "una compra demasiado cara", "lo venden muy caro", "su valor está por las nubes", "no sirve",
        "no es útil", "no sirve para nada", "no me ayudó", "es inútil", "mala calidad", "funciona mal",
        "no funciona", "se rompió enseguida", "no lo recomiendo", "estoy decepcionado", "no cumple",
        "pésima compra", "muy frágil", "mal material", "se dañó rápido", "el producto falló",
        "no lo volvería a comprar", "muy difícil de usar", "llegó dañado", "nada práctico", "no es bueno",
        "producto defectuoso", "fue una pérdida de dinero", "no cumple mis expectativas", "totalmente inútil",
        "se quebró apenas lo utilicé", "se partió enseguida", "se estropeó al usarlo", "se dañó el primer día",
        "dejó de funcionar después de un uso", "se hizo pedazos en poco tiempo", "la pieza se quebró al instalarla",
        "el mango se rompió rápidamente", "se rajó apenas lo saqué", "lo usé una vez y falló",
        "se rompió antes de terminar el trabajo", "una herramienta que se averió enseguida",
        "duró muy poco y se dañó", "la herramienta vino rota", "después de usarlo ya no sirve",
        "se descompuso de inmediato", "me llegó quebrado", "muy mala durabilidad", "no duró nada",
        "el producto se partió al utilizarlo",
    ],
    "NEU": [
        "El producto es azul", "viene en color negro", "mide diez centímetros", "es de metal",
        "la caja contiene cinco unidades", "lo recibí ayer", "el paquete llegó hoy", "es de madera",
        "es una brocha", "la herramienta es manual", "lo compré el lunes", "tiene dos piezas",
        "el tornillo mide una pulgada", "viene en una bolsa", "es de color gris", "tiene forma rectangular",
        "el paquete pesa un kilo", "lo vi en la tienda", "su código es 123", "tiene un mango de plástico",
        "la pintura es blanca", "hay tres tamaños", "la compré en línea", "tiene una tapa roja",
        "es una llave ajustable", "el modelo es nuevo", "el empaque es de cartón", "contiene cuatro metros",
        "se usa con electricidad", "tiene un cable", "el producto viene en una caja", "la etiqueta dice acero",
        "es de la marca indicada", "el precio aparece en la etiqueta", "el costo es de mil colones",
        "cuesta quinientos colones", "el precio es de dos mil", "precio de venta mil", "el monto es 500",
        "el precio cambió ayer", "compré dos", "lo entregaron esta mañana", "tiene una medida estándar",
        "el material es aluminio", "se vende por unidad", "es para interiores", "su peso es de dos kilos",
        "se instala con tornillos", "la bolsa trae ocho", "el número de serie está en la caja",
        "tiene un botón", "lo recibí en la ferretería", "el precio está indicado en la página",
        "la pieza tiene dos agujeros", "el artículo está en el estante", "compré una pieza", "mide cinco metros",
        "lo envían en una caja", "tiene un tamaño mediano", "viene con una bolsa", "el paquete pesa 500 gramos",
        "es de acero inoxidable", "es un producto para pintar", "la marca está en el empaque", "llegó el martes",
        "la botella contiene un litro", "el equipo tiene una rueda", "el precio figura en la factura",
        "es una herramienta eléctrica", "el modelo tiene dos botones", "la caja tiene una etiqueta", "lo compré hoy",
        "es de uso doméstico",
    ],
}


def representaciones(modelo, tokenizador, textos):
    partes = []
    with torch.no_grad():
        for inicio in range(0, len(textos), 8):
            lote = tokenizador(textos[inicio:inicio + 8], padding=True, truncation=True, max_length=128, return_tensors="pt")
            partes.append(modelo.roberta(**lote).last_hidden_state[:, 0, :].cpu())
    return torch.cat(partes)


def main():
    random.seed(SEMILLA)
    torch.manual_seed(SEMILLA)
    torch.set_num_threads(min(4, os.cpu_count() or 1))
    tokenizer = AutoTokenizer.from_pretrained(BASE, local_files_only=True)
    model = AutoModelForSequenceClassification.from_pretrained(BASE, use_safetensors=True, local_files_only=True)
    model.eval()
    ids = {etiqueta: indice for indice, etiqueta in model.config.id2label.items()}
    ejemplos = [(texto, ids[etiqueta]) for etiqueta, textos in EJEMPLOS.items() for texto in textos]
    random.shuffle(ejemplos)
    textos, etiquetas = zip(*ejemplos)
    print(f"Calculando representaciones de {len(textos)} ejemplos con el modelo original...", flush=True)
    x = representaciones(model, tokenizer, list(textos))
    y = torch.tensor(etiquetas)
    # Se entrena únicamente la cabeza, sobre características congeladas; el
    # punto de partida es la cabeza original, sin alterar el modelo base.
    for parametro in model.roberta.parameters():
        parametro.requires_grad = False
    original = {nombre: valor.detach().clone() for nombre, valor in model.classifier.named_parameters()}
    optimizador = torch.optim.AdamW(model.classifier.parameters(), lr=0.00008, weight_decay=0.01)
    model.classifier.train()
    for epoca in range(18):
        orden = torch.randperm(len(y))
        for indices in orden.split(16):
            # La cabeza RoBERTa espera dimensiones [lote, secuencia, oculto].
            logits = model.classifier(x[indices].unsqueeze(1))
            perdida = torch.nn.functional.cross_entropy(logits, y[indices])
            penalizacion = sum((p - original[n]).pow(2).sum() for n, p in model.classifier.named_parameters())
            perdida = perdida + 0.0001 * penalizacion
            optimizador.zero_grad()
            perdida.backward()
            optimizador.step()
        print(f"Época {epoca + 1}: pérdida {perdida.item():.4f}", flush=True)
    model.eval()
    DESTINO.mkdir(exist_ok=True)
    model.save_pretrained(DESTINO, safe_serialization=True)
    tokenizer.save_pretrained(DESTINO)
    print(f"Modelo candidato guardado en {DESTINO}. Evalúalo independientemente antes de usarlo.", flush=True)


if __name__ == "__main__":
    main()
