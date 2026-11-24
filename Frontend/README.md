# FerreLSA — frontend

Aplicación React y Vite para el panel administrativo y la tienda de FerreLSA. Las vistas usan datos de demostración compartidos, basados en el esquema SQL del proyecto. Los cambios existen solo en memoria: se pierden al recargar o cerrar la página y no se sincronizan entre navegadores.

## Ejecutar

Desde la carpeta `Frontend` en PowerShell:

```powershell
npm.cmd install
npm.cmd run dev
```

Abrí la dirección que indica Vite. Para comprobar la compilación: `npm.cmd run build`.

Desde el acceso se puede entrar al panel o a la tienda de demostración. No es una autenticación ni un control de permisos. No ingresés datos reales en las vistas de prueba.

## Alcance actual

- Administración: productos e inventario, proveedores, órdenes de compra, ventas locales, usuarios y sentimientos de comentarios.
- Tienda: catálogo, detalle de productos, comentarios, carrito, checkout, historial y ventana visual de chat.
- Los productos, usuarios, compras, ventas, comentarios y movimientos de ejemplo viven en `src/data/demoData.js` y en el estado de React. Las operaciones de las vistas modifican únicamente ese estado.
- Las imágenes suministradas en la demostración tampoco se envían a un servidor. El almacenamiento de imágenes debe acordarse con el backend.
- El pago de PayPal, el chatbot y el análisis de sentimientos no se ejecutan: requieren servicios reales. Los comentarios nuevos reciben una clasificación provisional.

## Integración futura

`src/modules/acceso/auth.js` conserva un punto de integración opcional para el inicio de sesión mediante `VITE_LOGIN_ENDPOINT`; su contrato `{ username, password }` es provisional. El backend deberá definir el contrato de autenticación, el manejo del JWT o sesión y la autorización por roles. Las rutas de demostración no deben considerarse protegidas.

Para conectar los módulos, reemplazá el estado de demostración por servicios que consuman los endpoints acordados. Coordiná los nombres de campos, respuestas de errores, paginación, carga de imágenes, cálculo de impuestos, validación de existencias y transiciones de estado. La validación y los cálculos definitivos deben ejecutarse también en el servidor. Las variables `VITE_*` son públicas y no deben contener secretos.

## Organización del código

```text
src/
├── App.jsx                   # Selección de vista y estado compartido de demostración
├── components/               # Marca, iconos y controles compartidos de administración
├── data/                     # Datos iniciales de demostración
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

Las vistas administrativas reciben los datos y la función de actualización desde `App.jsx` a través de `Workspace.jsx`. Para integrar un módulo, incorporá sus servicios de API en su carpeta y sustituí gradualmente el acceso al estado de demostración, respetando el contrato que acuerden con el backend.
