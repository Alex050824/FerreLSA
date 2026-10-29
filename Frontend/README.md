# FerreLSA ERP — Prototipo de frontend

Aplicación React y Vite con una pantalla de acceso y una vista previa de los módulos del ERP. Los registros, indicadores y acciones de la vista previa son ilustrativos; no guardan cambios ni procesan operaciones reales.

## Ejecutar localmente

Desde la carpeta `Frontend`, ejecutar en PowerShell:

```powershell
npm.cmd install
npm.cmd run dev
```

Abrir la dirección local que indique Vite. Para comprobar la compilación de producción, ejecutar `npm.cmd run build`.

## Organización

```text
src/
├── components/       # Componentes reutilizables: marca, tabla e iconos
├── layouts/          # Estructura y navegación de la vista previa
├── modules/          # Configuración y datos de cada módulo
│   ├── ventas/
│   ├── inventario/
│   ├── compras/
│   ├── facturacion/
│   ├── clientes/
│   ├── proveedores/
│   └── administracion/
├── pages/            # Acceso, panel principal y pantalla de módulo compartida
├── services/         # Punto de integración de acceso existente
├── App.jsx           # Selección entre acceso y vista previa
├── main.jsx          # Punto de entrada de React
└── styles.css        # Estilos compartidos
```

Cada carpeta de `modules/` contiene la configuración de navegación, las columnas y los datos de ejemplo de su sección. `modules/index.js` reúne los módulos para la navegación y las pantallas compartidas. Las fotografías de productos son un requisito pendiente: la vista actual no permite cargarlas ni mostrarlas.

## Acceso y alcance

La vista previa se abre desde la pantalla de acceso sin autenticación. El formulario de acceso conserva el servicio existente en `src/services/auth.js`: si se configura `VITE_LOGIN_ENDPOINT`, intenta enviar las credenciales a ese endpoint; sin configurar ese valor, informa que el acceso no está conectado. No hay backend ni base de datos en este proyecto. La respuesta exitosa actualmente muestra un mensaje, pero no navega automáticamente al panel.

Las variables `VITE_*` son públicas en el navegador y no deben contener secretos. La misión y la visión mostradas son textos propuestos para el proyecto académico.
