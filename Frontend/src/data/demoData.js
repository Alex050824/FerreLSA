// Datos temporales para probar las pantallas sin servicios externos.
export const initialData = {
  categorias: [
    { id: 1, nombre: 'Construcción', descripcion: 'Materiales de construcción', activo: true },
    { id: 2, nombre: 'Plomería', descripcion: 'Tuberías y accesorios', activo: true },
    { id: 3, nombre: 'Electricidad', descripcion: 'Cables y accesorios', activo: true },
    { id: 4, nombre: 'Pinturas', descripcion: 'Pinturas y selladores', activo: true },
    { id: 5, nombre: 'Herramientas', descripcion: 'Herramientas manuales y eléctricas', activo: true },
    { id: 6, nombre: 'Jardinería', descripcion: 'Herramientas e insumos de jardinería', activo: true },
    { id: 7, nombre: 'Seguridad', descripcion: 'Equipo de protección y seguridad ocupacional', activo: true },
    { id: 8, nombre: 'Adhesivos y selladores', descripcion: 'Pegamentos, siliconas y selladores', activo: true },
    { id: 9, nombre: 'Ferretería general', descripcion: 'Tornillería, fijaciones y accesorios', activo: true },
  ],
  proveedores: [
    { id: 1, nombre: 'Distribuidora El Constructor', identificacion: '3-101-111111', correo: 'ventas@ejemplo.com', telefono: '2222-1100', direccion: 'San José', contacto: 'Ana Rodríguez', activo: true },
    { id: 2, nombre: 'Materiales del Norte', identificacion: '', correo: 'pedidos@ejemplo.com', telefono: '2233-4500', direccion: 'Alajuela', contacto: 'Luis Jiménez', activo: true },
  ],
  productos: [
    { id: 1, categoria_id: 1, proveedor_id: 1, codigo: 'CEM-001', nombre: 'Cemento gris 50 kg', descripcion: 'Saco de cemento para construcción.', unidad_medida: 'saco', precio_compra: 4200, precio_venta: 5200, existencia: 24, stock_minimo: 10, imagen_url: '', activo: true },
    { id: 2, categoria_id: 2, proveedor_id: 2, codigo: 'PVC-001', nombre: 'Tubo PVC ½ pulgada', descripcion: 'Tubo para instalaciones de agua.', unidad_medida: 'unidad', precio_compra: 1200, precio_venta: 1850, existencia: 8, stock_minimo: 10, imagen_url: '', activo: true },
    { id: 3, categoria_id: 3, proveedor_id: 1, codigo: 'ELE-001', nombre: 'Cable THHN #12', descripcion: 'Cable eléctrico para instalaciones.', unidad_medida: 'metro', precio_compra: 500, precio_venta: 750, existencia: 120, stock_minimo: 20, imagen_url: '', activo: true },
    { id: 4, categoria_id: 4, proveedor_id: 2, codigo: 'PIN-001', nombre: 'Pintura blanca 1 galón', descripcion: 'Pintura para interiores.', unidad_medida: 'galón', precio_compra: 8500, precio_venta: 12000, existencia: 0, stock_minimo: 5, imagen_url: '', activo: true },
  ],
  usuarios: [
    { id: 1, rol: 'ADMIN', nombre: 'Administración', apellido: 'FerreLSA', identificacion: '', telefono: '', correo: 'admin@ejemplo.com', provincia: '', canton: '', distrito: '', direccion_exacta: '', activo: true },
    { id: 2, rol: 'CLIENTE', nombre: 'María', apellido: 'Rojas', identificacion: '', telefono: '8888-1200', correo: 'maria@ejemplo.com', provincia: 'San José', canton: '', distrito: '', direccion_exacta: '', activo: true },
  ],
  compras: [], movimientos: [], ventas: [],
  comentarios: [
    { id: 1, producto_id: 1, usuario_id: 2, comentario: 'Buen producto para mis proyectos.', sentimiento: 'POSITIVO', fecha: '2026-01-10T10:30:00' },
  ],
};
