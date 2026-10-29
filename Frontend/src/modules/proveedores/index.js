// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'proveedores',
  label: 'Proveedores',
  icon: 'building'
};
export const rows = [
  ['PRO-0038', 'Distribuidora El Constructor', 'ventas@constructor.cr', '2222-1100', 'Activo'],
  ['PRO-0037', 'Materiales del Norte', 'pedidos@matnorte.cr', '2233-4500', 'Activo'],
  ['PRO-0036', 'Pinturas del Valle', 'info@pinturasvalle.cr', '2444-2000', 'Activo'],
];
export const config = {
  title: 'Proveedores',
  desc: 'Directorio de proveedores y contactos comerciales.',
  action: 'Nuevo proveedor',
  columns: ['Código', 'Proveedor', 'Correo', 'Teléfono', 'Estado']
};
