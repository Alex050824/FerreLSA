
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from .views import obtener_productos

# 1. Cargar el modelo de la Guía #10
nombre_modelo = "Qwen/Qwen2.5-0.5B-Instruct"

print("Cargando modelo Qwen...")

tokenizador = AutoTokenizer.from_pretrained(nombre_modelo)
modelo = AutoModelForCausalLM.from_pretrained(nombre_modelo)
modelo.eval()


# 2. Recibir una pregunta sobre FerreLSA
def responder_pregunta(pregunta):

    # Obtener los productos desde MySQL
    productos = obtener_productos()

    inventario = ""

    for codigo, nombre, descripcion, precio, existencia in productos:
        precio_formateado = f"{precio:,.0f}".replace(",", ".")
        inventario += f"""
        Código: {codigo}
        Producto: {nombre}
        Descripción: {descripcion}
        Precio: ₡{precio_formateado} colones costarricenses
        Existencia: {existencia} unidades
        """

    # 3. Instrucciones para el chatbot
    instrucciones = """
    Eres el asistente virtual de FerreLSA,
    una ferretería ubicada en Costa Rica.

    Reglas:
    - Responde siempre en español.
    - Utiliza únicamente la información del inventario.
    - Todos los precios están en colones costarricenses (CRC).
    - Cuando menciones un precio, utiliza el símbolo ₡.
    - Nunca utilices pesos ni dólares para indicar precios.
    - No inventes productos, precios ni existencias.
    - Si un producto no aparece en el inventario,
      indica que no está registrado en el catálogo.
    - Si la existencia es cero, indica que está agotado.
    - Responde de manera breve, clara y amable.

    Reglas:
    - Responde siempre en español.
    - Utiliza únicamente la información del inventario.
    - No inventes productos, precios ni existencias.
    - Si un producto no aparece, indica que no está
      registrado en el catálogo.
    - Si la existencia es cero, indica que está agotado.
    - Responde de manera breve y amable.
    """

    mensaje_sistema = instrucciones + "\n\nINVENTARIO:\n" + inventario

    mensajes = [
        {"role": "system", "content": mensaje_sistema},
        {"role": "user", "content": pregunta}
    ]

    # 4. Preparar el texto para el modelo
    texto_prompt = tokenizador.apply_chat_template(
        mensajes,
        tokenize=False,
        add_generation_prompt=True
    )

    entradas = tokenizador(
        texto_prompt,
        return_tensors="pt"
    )

    cantidad_tokens = entradas["input_ids"].shape[1]

    # 5. Generar una respuesta
    with torch.inference_mode():
        salida = modelo.generate(
            **entradas,
            max_new_tokens=150,
            do_sample=False,
            pad_token_id=tokenizador.eos_token_id
        )

    nuevos_tokens = salida[0, cantidad_tokens:]

    respuesta = tokenizador.decode(
        nuevos_tokens,
        skip_special_tokens=True
    )

    return respuesta.strip()
