// Información de ejemplo y configuración visual del módulo.
export const navigation = {
  id: 'inventario',
  label: 'Inventario',
  icon: 'box'
};
export const rows = [
  ['INV-001', 'Cemento gris 50 kg', 'Construcción', '24 sacos', 'Disponible'],
  ['INV-002', 'Tubo PVC 1/2 pulg.', 'Plomería', '8 unidades', 'Stock bajo'],
  ['INV-003', 'Cable THHN #12', 'Electricidad', '120 m', 'Disponible'],
  ['INV-004', 'Pintura blanca 1 galón', 'Pinturas', '0 unidades', 'Agotado'],
];
export const config = {
  title: 'Inventario',
  desc: 'Control de existencias y disponibilidad de productos.',
  action: 'Agregar producto',
  columns: ['Código', 'Producto', 'Categoría', 'Existencia', 'Estado']
};
