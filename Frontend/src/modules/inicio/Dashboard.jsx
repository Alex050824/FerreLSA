import React from 'react';
import Icon from '../../components/Icon.jsx';

const money = value => new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC' }).format(Number(value) || 0);

export default function Dashboard({ data, navigate }) {
  const alerts = data.productos.filter(p => p.activo && Number(p.existencia) <= Number(p.stock_minimo));
  const currentMonth = new Date().toISOString().slice(0, 7);
  const monthly = data.ventas.filter(v => String(v.fecha || '').startsWith(currentMonth) && v.estado !== 'ANULADA').reduce((sum, v) => sum + Number(v.total || 0), 0);
  const cards = [
    { label: 'Ventas del mes', value: money(monthly), icon: 'chart', tone: 'orange' },
    { label: 'Productos disponibles', value: data.productos.filter(p => p.activo && Number(p.existencia) > 0).length, icon: 'box', tone: 'blue' },
    { label: 'Compras pendientes', value: data.compras.filter(c => c.estado === 'PENDIENTE').length, icon: 'receipt', tone: 'violet' },
    { label: 'Clientes registrados', value: data.usuarios.filter(u => u.rol === 'CLIENTE').length, icon: 'user', tone: 'green' },
  ];
  return <>
    <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line" /> RESUMEN DEL NEGOCIO</div><h1>Bienvenido<span className="orange-dot">.</span></h1></div></div>
    <div className="stat-grid">{cards.map(c => <article className="stat-card" key={c.label}><span className={`stat-icon ${c.tone}`}><Icon name={c.icon} size={20} /></span><span className="stat-label">{c.label}</span><strong>{c.value}</strong></article>)}</div>
    <div className="dashboard-grid">
      <section className="surface inventory-alerts"><div className="surface-heading"><div><h2>Alertas de inventario</h2><p>Existencia igual o inferior al mínimo</p></div></div><div className="inventory-alerts__list">{alerts.length ? alerts.map(p => <div className="inventory-alert" key={p.id}><div className="inventory-alert__details"><strong>{p.nombre}</strong><span>Existencia: {p.existencia} {p.unidad_medida}</span></div><span className="status status--stock-bajo">{Number(p.existencia) === 0 ? 'Agotado' : 'Stock bajo'}</span></div>) : <p className="inventory-alerts__empty">No hay productos con alertas.</p>}</div><div className="inventory-alerts__actions"><button className="text-button" onClick={() => navigate('inventario')}>Ver inventario <Icon name="arrow" size={16} /></button><button className="text-button" onClick={() => navigate('compras')}>Ver compras <Icon name="arrow" size={16} /></button></div></section>
      <section className="surface inventory-alerts"><div className="surface-heading"><div><h2>Ventas recientes</h2><p>Últimas ventas registradas</p></div></div>{data.ventas.length ? <div className="inventory-alerts__list">{[...data.ventas].reverse().slice(0, 4).map(v => <div className="inventory-alert" key={v.id}><div className="inventory-alert__details"><strong>{v.numero}</strong><span>{v.canal === 'EN_LINEA' ? 'En línea' : 'Local'} · {v.estado}</span></div><strong>{money(v.total)}</strong></div>)}</div> : <p className="inventory-alerts__empty">Todavía no hay ventas registradas.</p>}<div className="inventory-alerts__actions"><button className="text-button" onClick={() => navigate('ventas')}>Ver ventas <Icon name="arrow" size={16} /></button></div></section>
    </div>
  </>;
}
