import React, { useState } from 'react';
import Brand from '../components/Brand.jsx';
import Icon from '../components/Icon.jsx';
import Dashboard from '../modules/inicio/Dashboard.jsx';
import InventarioPage from '../modules/inventario/InventarioPage.jsx';
import ProveedoresPage from '../modules/proveedores/ProveedoresPage.jsx';
import ComprasPage from '../modules/compras/ComprasPage.jsx';
import Sales from '../modules/ventas/Sales.jsx';
import Users from '../modules/usuarios/Users.jsx';
import Sentiments from '../modules/sentimientos/Sentiments.jsx';

const sections = [
  { id: 'inicio', label: 'Panel principal', icon: 'chart' },
  { id: 'inventario', label: 'Inventario', icon: 'box' },
  { id: 'proveedores', label: 'Proveedores', icon: 'layers' },
  { id: 'compras', label: 'Compras', icon: 'receipt' },
  { id: 'ventas', label: 'Ventas locales', icon: 'cart' },
  { id: 'usuarios', label: 'Usuarios', icon: 'user' },
  { id: 'sentimientos', label: 'Comentarios', icon: 'info' },
];

const pageComponents = {
  inventario: InventarioPage,
  proveedores: ProveedoresPage,
  compras: ComprasPage,
  ventas: Sales,
  usuarios: Users,
  sentimientos: Sentiments,
};

export default function Workspace({ data, setData, onLogout, onStore }) {
  const [page, setPage] = useState('inicio');
  const active = sections.find(section => section.id === page);
  const CurrentPage = pageComponents[page];
  const lowStock = data.productos.filter(p => p.activo && Number(p.existencia) <= Number(p.stock_minimo)).length;
  return <div className="workspace">
    <aside className="sidebar">
      <Brand onClick={() => setPage('inicio')} />
      <div className="nav-caption">ESPACIO DE TRABAJO</div>
      <nav aria-label="Administración">
        {sections.map(section => <button key={section.id} title={section.label} aria-label={section.label} aria-current={page === section.id ? 'page' : undefined} className={`nav-item ${page === section.id ? 'active' : ''}`} onClick={() => setPage(section.id)}>
          <Icon name={section.icon} size={19} /><span>{section.label}</span>
          {section.id === 'inventario' && lowStock > 0 && <i className="nav-badge">{lowStock}</i>}
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <button className="nav-item" onClick={onStore}><Icon name="cart" size={19} /><span>Ir a la tienda</span></button>
        <div className="user-card"><span className="avatar">D</span><span><strong>Vista de demostración</strong><small>Datos temporales</small></span><button aria-label="Volver al inicio" title="Volver al inicio" onClick={onLogout}><Icon name="logout" size={17} /></button></div>
      </div>
    </aside>
    <main className="work-main">
      <header className="work-topbar"><div className="breadcrumbs">FerreLSA <span>/</span> {active.label}</div><div className="topbar-right"><button className="workspace-link" onClick={onStore}>Ver tienda</button><button className="workspace-link" onClick={onLogout}>Salir</button></div></header>
      <div className="work-content">
        <div className="demo-banner" role="status">Modo demostración: los cambios se mantienen solo mientras esta página esté abierta.</div>
        {page === 'inicio' ? <Dashboard data={data} navigate={setPage} /> : <CurrentPage key={page} data={data} setData={setData} />}
      </div>
    </main>
  </div>;
}
