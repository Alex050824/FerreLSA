# Resultados de evaluación inicial de RoBERTuito para FerreLSA

Se compararon el modelo original y dos ajustes de su cabeza sobre ejemplos
sintéticos redactados para comentarios de productos. Son conjuntos pequeños y
no representan una medición de precisión sobre los clientes de FerreLSA.

| Conjunto | Original | Ajuste 1 | Ajuste 2 | Ajuste 2 y reglas de precio |
| --- | ---: | ---: | ---: | ---: |
| Productos, 45 ejemplos | 35/45 | 42/45 | 43/45 | 44/45 |
| Productos sin las 7 frases que coinciden con entrenamiento | 31/38 | 35/38 | 36/38 | 37/38 |
| Negaciones y calidad, 45 ejemplos sin coincidencias exactas con entrenamiento | 24/45 | 29/45 | 32/45 | 35/45 |
| Contexto de precios, 40 ejemplos | No medido | No medido | 27/40 | 32/40 |

El primer conjunto contiene los dos ejemplos aportados por el usuario y fue
utilizado para detectar errores durante el desarrollo; su resultado no es una
evaluación ciega. La comparación sin solapamiento elimina coincidencias tras
normalizar mayúsculas, espacios y Unicode, pero no elimina paráfrasis similares.
El segundo conjunto se preparó separadamente del entrenamiento y se comprobó
que no había coincidencias exactas. Al comunicar sus resultados, pasa también a
ser información de desarrollo y no debe reutilizarse como prueba final ciega.

En el ajuste 2 se observaron errores de negación de precio, calidad y frases
descriptivas. El entrenamiento con ejemplos redactados permite mejorar algunos
casos, pero no demuestra que el modelo generalice correctamente: hace falta
evaluarlo con una muestra separada de comentarios reales etiquetada por personas.

Las reglas de precio corrigieron cinco casos en el conjunto de contexto frente
al ajuste 2, sin regresiones observadas en ese conjunto. Esta prueba dejó de ser
ciega al comunicar ejemplos al desarrollar las reglas. Persisten errores en
negaciones más complejas y descripciones neutrales. Las reglas son una
corrección complementaria, no un nuevo entrenamiento del modelo.

`evaluar_productos.py` permite volver a ejecutar los desafíos con un modelo
local (`--modelo`) o el servicio (`--url`); el conjunto se elige con `--datos`.
