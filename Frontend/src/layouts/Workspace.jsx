import React from 'react';
import Brand from '../components/Brand.jsx';
import Icon from '../components/Icon.jsx';
import Dashboard from '../modules/inicio/Dashboard.jsx';
import InventarioPage from '../modules/inventario/InventarioPage.jsx';
import ProveedoresPage from '../modules/proveedores/ProveedoresPage.jsx';
import ComprasPage from '../modules/compras/ComprasPage.jsx';
import Sales from '../modules/ventas/Sales.jsx';
import Users from '../modules/usuarios/Users.jsx';
import Sentiments from '../modules/sentimientos/Sentiments.jsx';
import PowerBIReport from '../modules/reportes/PowerBIReport.jsx';

const sections = [
  { id: 'inicio', label: 'Panel principal', icon: 'chart' },
  { id: 'inventario', label: 'Inventario', icon: 'box' },
  { id: 'proveedores', label: 'Proveedores', icon: 'layers' },
  { id: 'compras', label: 'Compras', icon: 'receipt' },
  { id: 'ventas', label: 'Ventas locales', icon: 'cart' },
  { id: 'usuarios', label: 'Usuarios', icon: 'user' },
  { id: 'sentimientos', label: 'Comentarios', icon: 'info' },
  { id: 'reportes', label: 'Estadísticas y reportes', icon: 'chart' },
];

const pageComponents = {
  inventario: InventarioPage,
  proveedores: ProveedoresPage,
  compras: ComprasPage,
  ventas: Sales,
  usuarios: Users,
  sentimientos: Sentiments,
};

export default function Workspace({ data, mutate, page, user, token, feedback, onNavigate, onLogout, onStore }) {
  const active = sections.find(section => section.id === page);
  if (!active) {
    return <main className="container">
      <h1>Sección administrativa no encontrada</h1>
      <button type="button" onClick={() => onNavigate('inicio')}>Volver al panel</button>
    </main>;
  }
  const CurrentPage = pageComponents[page];
  return <div className="workspace workspace--erp">
    <aside className="sidebar sidebar--erp">
      <div className="sidebar-brand"><Brand onClick={() => onNavigate('inicio')} /></div>
      <div className="nav-caption">ESPACIO DE TRABAJO</div>
      <nav aria-label="Administración">
        {sections.map(section => <button key={section.id} title={section.label} aria-label={section.label} aria-current={page === section.id ? 'page' : undefined} className={`nav-item ${page === section.id ? 'active' : ''}`} onClick={() => onNavigate(section.id)}>
          <Icon name={section.icon} size={19} /><span>{section.label}</span>
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="user-card" aria-label={`Sesión iniciada por ${[user.nombre, user.apellido].filter(Boolean).join(' ') || user.correo || 'usuario'}`}>
          <span className="avatar">{[user.nombre, user.apellido].filter(Boolean).map(part => part[0]).join('').slice(0, 2).toUpperCase() || 'U'}</span>
          <span className="user-card__identity"><strong>{[user.nombre, user.apellido].filter(Boolean).join(' ') || user.correo || 'Usuario'}</strong><small>Sesión activa</small></span>
          <i className="user-card__status" aria-hidden="true" />
        </div>
      </div>
    </aside>
    <main className="work-main">
      <header className="work-topbar"><div className="breadcrumbs"><span>FerreLSA</span><span className="breadcrumb-divider">/</span><strong>{active.label}</strong></div><div className="topbar-right"><button type="button" className="workspace-link workspace-link--store" onClick={onStore}><Icon name="cart" size={17} /><span>Ver tienda</span></button><button type="button" className="workspace-link workspace-link--logout" onClick={onLogout}><Icon name="logout" size={17} /><span>Salir</span></button></div></header>
      <div className="work-content">
        {feedback && <p role="status">{feedback}</p>}
        {!feedback && (page === 'inicio' ? <Dashboard data={data} navigate={onNavigate} /> : page === 'reportes'
          ? <PowerBIReport token={token} />
          : <CurrentPage key={page} data={data} mutate={mutate} currentUser={user} />)}
      </div>
    </main>
  </div>;
}
