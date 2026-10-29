import * as ventas from './ventas/index.js';
import * as inventario from './inventario/index.js';
import * as compras from './compras/index.js';
import * as facturacion from './facturacion/index.js';
import * as clientes from './clientes/index.js';
import * as proveedores from './proveedores/index.js';
import * as administracion from './administracion/index.js';
const sections = [ventas, inventario, compras, facturacion, clientes, proveedores, administracion];
export const modules = [{
  id: 'inicio',
  label: 'Panel principal',
  icon: 'chart'
}, ...sections.map(section => section.navigation)];
export const rows = Object.fromEntries(sections.map(section => [section.navigation.id, section.rows]));
export const config = Object.fromEntries(sections.map(section => [section.navigation.id, section.config]));
