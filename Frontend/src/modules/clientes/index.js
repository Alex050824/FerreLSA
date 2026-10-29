// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'clientes',
  label: 'Clientes',
  icon: 'user'
};
export const rows = [
  ['CLI-0142', 'María Fernanda Rojas', 'maria.rojas@email.com', '8888-1200', 'Frecuente'],
  ['CLI-0141', 'Construcciones Vega', 'compras@construevega.cr', '2222-7400', 'Empresa'],
  ['CLI-0140', 'Carlos Jiménez', 'cjimenez@email.com', '8700-6652', 'Regular'],
  ['CLI-0139', 'Obras del Valle S. A.', 'contacto@obrasvalle.cr', '2255-1900', 'Empresa'],
];
export const config = {
  title: 'Clientes',
  desc: 'Directorio de clientes y sus datos de contacto.',
  action: 'Nuevo cliente',
  columns: ['Código', 'Nombre', 'Correo', 'Teléfono', 'Tipo']
};
