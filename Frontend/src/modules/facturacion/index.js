// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'facturacion',
  label: 'Facturación',
  icon: 'receipt'
};
export const rows = [
  ['FAC-2084', 'María Fernanda Rojas', 'Hoy, 10:43 a. m.', '₡184 500', 'Pagada'],
  ['FAC-2083', 'Construcciones Vega', 'Hoy, 9:19 a. m.', '₡926 000', 'Por cobrar'],
  ['FAC-2082', 'Carlos Jiménez', 'Ayer, 3:36 p. m.', '₡76 250', 'Pagada'],
];
export const config = {
  title: 'Facturación',
  desc: 'Facturas emitidas y estado de cobro.',
  action: 'Crear factura',
  columns: ['N.º factura', 'Cliente', 'Fecha', 'Total', 'Estado']
};
