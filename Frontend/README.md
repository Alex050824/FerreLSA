# FerreLSA — frontend

Aplicación React y Vite para administrar FerreLSA y consultar su catálogo en línea.

## Ejecutar

Iniciá Django desde la raíz con `python Chatbot/manage.py runserver`. En otra terminal, desde `Frontend/`:

```powershell
npm.cmd ci
npm.cmd run dev
```

Abrí la dirección que indique Vite. En desarrollo, Vite envía las solicitudes
de `/api` a Django en `127.0.0.1:8000`.

El catálogo consulta los productos y categorías activos de MySQL. Iniciá
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
