// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'administracion',
  label: 'Administración',
  icon: 'settings'
};
export const rows = [
  ['USR-001', 'Administrador del sistema', 'admin@ferrelsa.cr', 'Administrador', 'Activo'],
  ['USR-002', 'Andrea Vargas', 'andrea@ferrelsa.cr', 'Ventas', 'Activo'],
  ['USR-003', 'Luis Morales', 'luis@ferrelsa.cr', 'Inventario', 'Activo'],
];
export const config = {
  title: 'Administración',
  desc: 'Usuarios y accesos del sistema.',
  action: 'Invitar usuario',
  columns: ['Código', 'Usuario', 'Correo', 'Rol', 'Estado']
};
