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
Con MySQL iniciado, levantá ambos servidores desde la raíz con un solo comando:

```powershell
npm.cmd run dev
```

Presioná Ctrl+C para detenerlos. Abrí la dirección que indique Vite. En desarrollo, Vite envía las solicitudes
de `/api` a Django en `127.0.0.1:8000`.

Si Django está en otra dirección, definí `VITE_API_PROXY_TARGET` en un archivo
`Frontend/.env.local`, por ejemplo `VITE_API_PROXY_TARGET=http://127.0.0.1:8001`,
y reiniciá Vite. En producción, el servidor que entrega el frontend debe
redirigir las solicitudes `/api` al mismo backend de Django, incluido el chatbot.

La página principal muestra el catálogo público con productos y categorías activos de MySQL. Iniciá
sesión con una cuenta ADMIN para administrar inventario, proveedores,
compras, ventas y usuarios, y consultar comentarios. Las cuentas CLIENTE
pueden consultar su historial de pedidos. El carrito se mantiene en memoria.
El pago en línea y la publicación de comentarios siguen pendientes.

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
