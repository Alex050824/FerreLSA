# FerreLSA — frontend

Aplicación React y Vite para administrar FerreLSA y consultar su catálogo en línea.

## Ejecutar

El backend ERP necesita las dependencias de `Backend/requirements-erp.txt`, una base
MySQL con las tablas del ERP y el archivo `.env` de la raíz con `DB_NAME`,
`DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` y `ERP_JWT_SECRET` (de al menos
32 caracteres). También puede usarse `DATABASE_URL` en lugar de las variables
`DB_*`. Aplicá las migraciones de Django para crear las tablas de sesión. El
repositorio no incluye el esquema de las tablas del ERP.
Podés partir de `.env.example`; las variables del sistema tienen prioridad
sobre `.env`, y `Chatbot/.env` se admite como respaldo de instalaciones anteriores.
Si `DATABASE_URL` está definida en cualquiera de esos lugares, prevalece sobre
`DB_NAME` y las demás variables `DB_*`.

Para preparar el entorno la primera vez, desde la raíz del proyecto en Windows:

```powershell
py -m venv Chatbot\.venv
.\Chatbot\.venv\Scripts\python.exe -m pip install -r Backend\requirements-erp.txt
.\Chatbot\.venv\Scripts\python.exe Chatbot\manage.py migrate
npm.cmd --prefix Frontend ci
```

Para usar el chatbot también instalá las dependencias de `Chatbot/requirements.txt`.
Para los comentarios, el proyecto `sistema_sentimientos` debe estar en
`sistema_sentimientos` dentro de la raíz de FerreLSA y tener su
entorno virtual con las dependencias de su `requirements.txt` instaladas. La primera
vez, el modelo puede requerir conexión a Internet para descargar sus archivos.
Para preparar ese entorno desde la raíz de FerreLSA:

```powershell
py -m venv sistema_sentimientos\.venv
sistema_sentimientos\.venv\Scripts\python.exe -m pip install -r sistema_sentimientos\requirements.txt
```

Con MySQL iniciado, levantá los servicios desde la raíz con un solo comando:

```powershell
npm.cmd run dev
```

El comando inicia Django, Vite y el analizador de sentimientos en `127.0.0.1:8001`.
FerreLSA usa por defecto el modelo ajustado guardado en
`sistema_sentimientos/modelo_ferrelsa`. Si esa carpeta no está disponible,
el analizador informa el error; consultá `sistema_sentimientos/AJUSTE_FERRELSA.md`
para reproducir el ajuste. Para volver al modelo original, definí
`$env:SENTIMIENTOS_MODELO = 'original'` antes de iniciar `npm run dev`.
Si el analizador está en otra carpeta, definí `SENTIMIENTOS_DIR` en el entorno
antes de ejecutar el comando. Si el servicio se ejecuta en otra dirección,
configurá `SENTIMIENTOS_URL` en el `.env` de FerreLSA con la dirección base
del servicio, sin `/analizar`. Para usar un servicio iniciado por separado,
definí también `$env:SENTIMIENTOS_LOCAL = '0'` en PowerShell antes de ejecutar
`npm run dev`.
Presioná Ctrl+C para detenerlos. Abrí la dirección que indique Vite. En desarrollo, Vite envía las solicitudes
de `/api` a Django en `127.0.0.1:8000`.

Si Django está en otra dirección, definí `VITE_API_PROXY_TARGET` en un archivo
`Frontend/.env.local`, por ejemplo `VITE_API_PROXY_TARGET=http://127.0.0.1:8001`,
y reiniciá Vite. En producción, el servidor que entrega el frontend debe
redirigir las solicitudes `/api` al mismo backend de Django, incluido el chatbot.

La página principal muestra el catálogo público con productos y categorías activos de MySQL. Iniciá
sesión con una cuenta ADMIN para administrar inventario, proveedores,
compras, ventas y usuarios, y consultar comentarios. Las cuentas CLIENTE
pueden consultar su historial de pedidos y publicar comentarios en los productos.
Cada comentario se clasifica y se guarda junto con su sentimiento en MySQL; si
el analizador no está disponible, se informa el error y no se publica. La
clasificación es una estimación automática y el modelo considera hasta 128 tokens.
El carrito se mantiene en memoria.

## Organización del código

```text
src/
├── App.jsx                   # Rutas, sesión y consultas a la API
├── components/               # Marca, iconos y controles compartidos de administración
├── layouts/                  # Estructura y navegación del panel
├── styles/                   # Estilos base y del panel compartidos
└── modules/
    ├── acceso/               # Inicio de sesión, estilos y servicio de acceso
    ├── inicio/               # Resumen del panel
    ├── inventario/           # Productos, existencias y movimientos
    ├── proveedores/          # Gestión de proveedores
    ├── compras/              # Órdenes de compra
    ├── ventas/               # Ventas locales
    ├── usuarios/             # Perfiles y roles
    ├── sentimientos/         # Consulta de comentarios clasificados
    ├── operaciones/          # Elementos compartidos de ventas, usuarios y sentimientos
    └── tienda/               # Catálogo, detalle, carrito, checkout, historial y chat
        └── components/       # Una vista o componente por parte de la tienda
```

Las vistas administrativas reciben datos de la API a través de `App.jsx` y `Workspace.jsx`.

## Estadísticas y reportes de Power BI

El panel administrativo incluye la sección **Estadísticas y reportes**. Para mostrar un informe:

1. En Power BI Desktop, conectá el informe a la base MySQL de FerreLSA y publicá el informe en Power BI.
2. En Power BI Service, usá **Archivo > Insertar informe > Publicar en la web (público)** y copiá la URL que comienza con https://app.powerbi.com/view?r=.
3. En el archivo .env de la raíz del proyecto, configurá:

   POWER_BI_REPORT_URL=https://app.powerbi.com/view?r=TU_CODIGO_DE_INSERCION

4. Reiniciá npm run dev, iniciá sesión con una cuenta ADMIN y abrí **Estadísticas y reportes**.

La aplicación entrega la URL mediante una API que requiere una sesión ADMIN y solo acepta enlaces HTTPS de inserción de app.powerbi.com. Si la variable está vacía o el enlace no es válido, la sección muestra una indicación. Los filtros, tablas y gráficos se pueden usar dentro del informe embebido.

**Publicar en la web hace público el informe y sus datos para cualquier persona con el enlace, incluso fuera de FerreLSA. Usalo exclusivamente con datos ficticios de prueba.** La restricción ADMIN de FerreLSA protege el acceso a la sección de la aplicación, pero no vuelve privado el enlace público de Power BI. La conexión a MySQL se configura en Power BI; FerreLSA no altera la base de datos. Para datos reales, reemplazá este modo con una modalidad de inserción segura antes de publicarlos.
