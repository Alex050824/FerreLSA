import React from 'react';
import Icon from '../components/Icon.jsx';
import DataTable from '../components/DataTable.jsx';
import { config, rows } from '../modules/index.js';
export default function Dashboard({
  navigate
}) {
  const currentDate = new Intl.DateTimeFormat('es-CR', {
    weekday: 'long',
    day: 'numeric',
    month: 'long'
  }).format(new Date());
  const dateLabel = currentDate.charAt(0).toLocaleUpperCase('es-CR') + currentDate.slice(1);
  const inventoryAlerts = rows.inventario.filter(
    product => product[4] === 'Stock bajo' || product[4] === 'Agotado'
  );
  const cards = [{
    label: 'Ventas del mes',
    value: '₡8 420 500',
    delta: '+12,8%',
    icon: 'chart',
    tone: 'orange'
  }, {
    label: 'Productos activos',
    value: '1 284',
    delta: 'En catálogo',
    icon: 'box',
    tone: 'blue'
  }, {
    label: 'Órdenes pendientes',
    value: '8',
    delta: 'Requieren atención',
    icon: 'receipt',
    tone: 'violet'
  }, {
    label: 'Clientes registrados',
    value: '342',
    delta: '+18 este mes',
    icon: 'user',
    tone: 'green'
  }];
  return <>
    <div className="page-heading">
      <div>
        <div className="eyebrow">
          <span className="eyebrow__line" /> RESUMEN DEL NEGOCIO</div>
        <h1>Bienvenido<span className="orange-dot">.</span>
        </h1>
        <p>Este es el resumen de actividad de FerreLSA.</p>
      </div>
      <span className="date-chip">{dateLabel}</span>
    </div>
    <div className="stat-grid">
      {cards.map(c => <article className="stat-card" key={c.label}>
        <span className={`stat-icon ${c.tone}`}>
          <Icon name={c.icon} size={20} />
        </span>
        <span className="stat-label">
          {c.label}
        </span>
        <strong>
          {c.value}
        </strong>
        <small>
          {c.delta}
        </small>
      </article>)}
    </div>
    <div className="dashboard-grid">
      <section className="surface chart-panel">
        <div className="surface-heading">
          <div>
            <h2>Actividad de ventas</h2>
            <p>Resumen semanal ilustrativo</p>
          </div>
          <span className="period-select">Esta semana⌄</span>
        </div>
        <div className="chart-area">
          <div className="chart-y">
            <span>₡1,2 M</span>
            <span>₡900 mil</span>
            <span>₡600 mil</span>
            <span>₡300 mil</span>
            <span>₡0</span>
          </div>
          <div className="chart-content">
            <div className="chart-gridlines">
              <i />
              <i />
              <i />
              <i />
              <i />
            </div>
            <div className="bars">
              {[['Lun', 55], ['Mar', 76], ['Mié', 62], ['Jue', 88], ['Vie', 70], ['Sáb', 96], ['Dom', 42]].map(([d, h]) => <div className="bar-col" key={d}>
                <span className="bar" style={{
                  height: `${h}%`
                }} />
                <small>
                  {d}
                </small>
              </div>)}
            </div>
          </div>
        </div>
      </section>
      <section className="surface inventory-alerts">
        <div className="surface-heading">
          <div>
            <h2>Alertas de inventario</h2>
            <p>Productos que necesitan atención</p>
          </div>
        </div>
        <div className="inventory-alerts__list">
          {inventoryAlerts.length ? inventoryAlerts.map(([code, product, , stock, status]) => (
            <div className="inventory-alert" key={code}>
              <div className="inventory-alert__details">
                <strong>{product}</strong>
                <span>Existencia: {stock}</span>
              </div>
              <span className={`status ${status === 'Agotado' ? 'status--agotado' : 'status--stock-bajo'}`}>
                {status}
              </span>
            </div>
          )) : <p className="inventory-alerts__empty">No hay productos con alertas.</p>}
        </div>
        <div className="inventory-alerts__actions">
          <button className="text-button" onClick={() => navigate('inventario')}>
            Ver inventario <Icon name="arrow" size={16} />
          </button>
          <button className="text-button" onClick={() => navigate('compras')}>
            Ver compras <Icon name="arrow" size={16} />
          </button>
        </div>
      </section>
    </div>
    <section className="surface recent-panel">
      <div className="surface-heading">
        <div>
          <h2>Movimientos recientes</h2>
          <p>Últimas operaciones registradas en el sistema</p>
        </div>
        <button className="text-button" onClick={() => navigate('ventas')}>Ver todas <Icon name="arrow" size={16} />
        </button>
      </div>
      <DataTable columns={config.ventas.columns} data={rows.ventas.slice(0, 3)} />
    </section>
  </>;
}
