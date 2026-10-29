// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'compras',
  label: 'Compras',
  icon: 'receipt'
};
export const rows = [
  ['OC-0231', 'Distribuidora El Constructor', 'Hoy, 8:30 a. m.', '₡540 000', 'En tránsito'],
  ['OC-0230', 'Materiales del Norte', 'Ayer, 2:15 p. m.', '₡318 750', 'Recibida'],
  ['OC-0229', 'Pinturas del Valle', '22 oct, 11:00 a. m.', '₡96 000', 'Pendiente'],
];
export const config = {
  title: 'Compras',
  desc: 'Órdenes de compra y recepción de mercadería.',
  action: 'Nueva orden',
  columns: ['N.º orden', 'Proveedor', 'Fecha', 'Total', 'Estado']
};
