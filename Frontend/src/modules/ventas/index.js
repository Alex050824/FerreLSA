// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'ventas',
  label: 'Ventas',
  icon: 'cart'
};
export const rows = [
  ['V-1048', 'María Fernanda Rojas', 'Hoy, 10:42 a. m.', '₡184 500', 'Completada'],
  ['V-1047', 'Construcciones Vega', 'Hoy, 9:18 a. m.', '₡926 000', 'Pendiente'],
  ['V-1046', 'Carlos Jiménez', 'Ayer, 3:35 p. m.', '₡76 250', 'Completada'],
  ['V-1045', 'Obras del Valle S. A.', 'Ayer, 11:06 a. m.', '₡1 245 900', 'Completada'],
];
export const config = {
  title: 'Ventas',
  desc: 'Consulta y seguimiento de las ventas del negocio.',
  action: 'Nueva venta',
  columns: ['N.º venta', 'Cliente', 'Fecha', 'Total', 'Estado']
};
