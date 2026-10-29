import React, { useState } from 'react';
import Brand from '../components/Brand.jsx';
import Icon from '../components/Icon.jsx';
import Dashboard from '../pages/Dashboard.jsx';
import ModulePage from '../pages/ModulePage.jsx';
import { modules } from '../modules/index.js';
export default function Workspace({
  onLogout
}) {
  const [page, setPage] = useState('inicio');
  const [notice, setNotice] = useState('');
  const active = modules.find(m => m.id === page);
  function action(label) {
    setNotice(`${label}: esta acción estará disponible cuando se conecte el backend.`);
    window.setTimeout(() => setNotice(''), 3500);
  }
  return <div className="workspace">
    <aside className="sidebar">
      <Brand onClick={() => setPage('inicio')} />
      <div className="nav-caption">ESPACIO DE TRABAJO</div>
      <nav>
        {modules.map(m => <button key={m.id} className={`nav-item ${page === m.id ? 'active' : ''}`} onClick={() => setPage(m.id)}>
          <Icon name={m.icon} size={19} />
          <span>
            {m.label}
          </span>
          {m.id === 'inventario' && <i className="nav-badge">2</i>}
        </button>)}
      </nav>
      <div className="sidebar-bottom">
        <div className="user-card">
          <span className="avatar">SA</span>
          <span>
            <strong>Shirley Araya</strong>
            <small>Administradora</small>
          </span>
          <button aria-label="Cerrar sesión" title="Cerrar sesión" onClick={onLogout}>
            <Icon name="logout" size={17} />
          </button>
        </div>
      </div>
    </aside>
    <main className="work-main">
      <header className="work-topbar">
        <div className="breadcrumbs">FerreLSA <span>/</span> {active.label}
        </div>
        <div className="topbar-right">
          <button className="notification-button" aria-label="Notificaciones">
            <Icon name="bell" size={19} />
            <i />
          </button>
          <span className="top-avatar">SA</span>
        </div>
      </header>
      <div className="work-content">
        {page === 'inicio' ? <Dashboard navigate={setPage} /> : <ModulePage page={page} onAction={action} />}
      </div>
    </main>
    {notice && <div className="toast">
      <Icon name="info" size={18} />
      {notice}
    </div>}
  </div>;
}
