# Ajuste de RoBERTuito para FerreLSA

`entrenar_ferrelsa.py` parte del modelo original de sentimientos en español y
ajusta su cabeza de clasificación con 221 frases sintéticas sobre productos,
utilidad y precio. El encoder de RoBERTuito permanece congelado. Los ejemplos
están en el propio script, con clases positivas, negativas y neutrales; no se
utilizan las clasificaciones automáticas de `comentarios.csv` como etiquetas.

El conjunto es pequeño y sintético. Es un ajuste inicial, no una garantía de
precisión general. Para medir y mejorar la calidad hacen falta comentarios
reales etiquetados y revisados por personas, y un conjunto de prueba independiente
que no participe en el entrenamiento.

Con el entorno de este proyecto y el modelo original ya en caché, reproducí el
ajuste desde `sistema_sentimientos` con:

```powershell
.\.venv\Scripts\python.exe entrenar_ferrelsa.py
```

Una nueva ejecución guarda su resultado en `modelo_ferrelsa_v2/` y no modifica
los pesos originales en `.modelos/` ni el modelo activo `modelo_ferrelsa/`.
También se conserva el primer candidato en `modelo_ferrelsa_v1/`. El ajuste
puede tardar varios minutos en CPU y requiere espacio para otra copia del
modelo. Evaluá el resultado con casos independientes antes de aplicarlo.

Al iniciar FerreLSA mediante `npm run dev`, su servicio de análisis usa la
carpeta `modelo_ferrelsa/` de este proyecto por defecto. Para probar otro modelo,
definí la ruta absoluta en el entorno **antes** de iniciar el comando:

```powershell
$env:SENTIMIENTOS_MODELO = 'C:\Users\Dell\Desktop\sistema_sentimientos\modelo_ferrelsa'
```

El servicio carga el modelo una sola vez al arrancar. Hay que reiniciarlo para
aplicar cambios. Si la ruta configurada no es válida, el servicio informa el
error; no la sustituye silenciosamente por otro modelo. Para volver al modelo
original al arrancar FerreLSA, establecé la variable en `original` y reiniciá:

```powershell
$env:SENTIMIENTOS_MODELO = 'original'
```

Si se arranca `servicio_api.py` directamente, sin `npm run dev`, se usa el
modelo original salvo que `SENTIMIENTOS_MODELO` indique una ruta local.

El servicio también aplica `reglas_precios.py` a frases o cláusulas completas
que expresan claramente una valoración del precio, con negación incluida. Una
crítica explícita de precio prevalece incluso en un comentario mixto, por la
preferencia indicada para FerreLSA. No se deduce si un importe numérico es alto.
Las preguntas, expresiones de duda y cláusulas de precio contradictorias se
dejan al modelo. En los demás casos decide el modelo. La respuesta JSON identifica el origen como
`regla_precio` o `modelo`; `puntuaciones` contiene siempre las estimaciones del
modelo, incluso cuando la regla cambia el sentimiento final.

Las clasificaciones almacenadas previamente en MySQL no cambian por reiniciar
el servicio: solo se aplica el modelo a comentarios analizados posteriormente.
