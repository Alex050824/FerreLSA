# Integración local con FerreLSA

Instala las dependencias según `LEEME.txt` y ejecuta desde esta carpeta:

```powershell
.\.venv\Scripts\python.exe servicio_api.py
```

El servicio escucha solo en `127.0.0.1:8001`. Para cambiar el puerto, configura
la variable de entorno `SENTIMIENTOS_PUERTO` y usa el mismo puerto en FerreLSA.
En Windows el puerto se reserva de forma exclusiva: si ya hay otro proceso
escuchando, el servicio informa el error en vez de compartir el puerto.
El modelo se carga una vez al iniciar; mientras carga, la API responde 503. Si
falla la carga, consulta la terminal, corrige la causa y reinicia el servicio.
La primera descarga del modelo requiere conexión a internet.

`POST /analizar` recibe JSON, por ejemplo `{"texto":"Excelente producto"}`.
Devuelve `sentimiento` (`POSITIVO`, `NEGATIVO` o `NEUTRAL`), `puntuaciones`
por categoría y una `alerta` opcional. `GET /salud` indica si el modelo está
listo. La API no escribe CSV ni accede a la base de datos: FerreLSA persiste el
comentario y el resultado. No expongas esta API sin autenticación a la red o a
internet.
