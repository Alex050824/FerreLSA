import React from 'react';
import Icon from '../../components/Icon.jsx';

const money = value => new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC' }).format(Number(value) || 0);
const count = value => new Intl.NumberFormat('es-CR').format(Number(value) || 0);
const date = value => value ? new Intl.DateTimeFormat('es-CR', { dateStyle: 'medium' }).format(new Date(`${String(value).slice(0, 10)}T12:00:00`)) : '—';
const statusLabel = value => { const text = String(value || '').replaceAll('_', ' ').toLocaleLowerCase('es-CR'); return text ? text[0].toLocaleUpperCase('es-CR') + text.slice(1) : ''; };

function CashflowChart({ months }) {
  const max = Math.max(1, ...months.flatMap(month => [Number(month.ingresos) || 0, Number(month.salidas) || 0]));
  const monthName = value => new Intl.DateTimeFormat('es-CR', { month: 'short' }).format(new Date(`${value}-01T12:00:00`)).replace('.', '');
  return <section className="surface dashboard-panel dashboard-cashflow">
    <div className="surface-heading"><div><h2>Ventas y compras recibidas</h2><p>Comparación mensual de los últimos seis meses</p></div>
      <div className="dashboard-legend"><span><i className="dashboard-legend__sales" />Ventas cobradas</span><span><i className="dashboard-legend__purchases" />Compras recibidas</span></div>
    </div>
    {months.length ? <div className="cashflow-chart" role="img" aria-label="Gráfico comparativo mensual de ventas cobradas y compras recibidas">
      {months.map(month => {
        const sales = Number(month.ingresos) || 0;
        const purchases = Number(month.salidas) || 0;
        return <div className="cashflow-month" key={month.periodo}>
          <div className="cashflow-bars">
            <span className="cashflow-bar cashflow-bar--sales" style={{ height: `${Math.max(sales ? 5 : 0, sales / max * 100)}%` }} title={`Ventas ${money(sales)}`} />
            <span className="cashflow-bar cashflow-bar--purchases" style={{ height: `${Math.max(purchases ? 5 : 0, purchases / max * 100)}%` }} title={`Compras ${money(purchases)}`} />
          </div>
          <span className="cashflow-month__label">{monthName(month.periodo)}</span>
        </div>;
      })}
    </div> : <p className="dashboard-empty">Todavía no hay movimientos financieros para graficar.</p>}
    <p className="dashboard-footnote">La diferencia entre ventas y compras no descuenta salarios, alquiler ni otros gastos operativos.</p>
  </section>;
}

export default function Dashboard({ data, navigate }) {
  const summary = data.dashboard || {};
  const metrics = summary.metricas || {};
  const alerts = summary.alertas_inventario || [];
  const recentSales = summary.ventas_recientes || [];
  const pendingPurchases = summary.compras_pendientes_recientes || [];
  const recentMovements = summary.movimientos_recientes || [];
  const months = summary.meses || [];
  const cards = [
    { label: 'Ventas cobradas · este mes', value: money(metrics.ventas_cobradas), icon: 'chart', tone: 'orange' },
    { label: 'Compras recibidas · este mes', value: money(metrics.compras_recibidas), icon: 'receipt', tone: 'violet' },
    { label: 'Diferencia ventas − compras', value: money(metrics.diferencia_ventas_compras), icon: 'layers', tone: Number(metrics.diferencia_ventas_compras) >= 0 ? 'green' : 'red' },
    { label: 'Valor del inventario · al costo', value: money(metrics.valor_inventario), icon: 'box', tone: 'blue' },
    { label: 'Pedidos web pendientes', value: count(metrics.pedidos_web_pendientes), icon: 'cart', tone: 'orange' },
    { label: 'Órdenes de compra pendientes', value: count(metrics.compras_pendientes), icon: 'receipt', tone: 'violet' },
    { label: 'Productos disponibles', value: count(metrics.productos_disponibles), icon: 'box', tone: 'green' },
    { label: 'Unidades con salida · últimos 30 días', value: count(metrics.unidades_salida_30d), icon: 'arrow', tone: 'blue' },
  ];

  return <div className="dashboard-view">
    <div className="page-heading dashboard-heading"><div><div className="eyebrow"><span className="eyebrow__line" /> RESUMEN DEL NEGOCIO</div><h1>Panel principal<span className="orange-dot">.</span></h1><p>Ventas, compras, flujo de inventario y alertas para la operación diaria.</p></div></div>
    <div className="stat-grid dashboard-metrics">{cards.map(card => <article className="stat-card" key={card.label}>
      <span className={`stat-icon ${card.tone}`}><Icon name={card.icon} size={20} /></span><span className="stat-label">{card.label}</span><strong>{card.value}</strong>
    </article>)}</div>

    <div className="dashboard-grid dashboard-activity dashboard-activity--expanded">
      <CashflowChart months={months} />

      <section className="surface inventory-alerts dashboard-panel">
        <div className="surface-heading"><div><h2>Salud del inventario</h2><p>{count(metrics.productos_agotados)} agotados · {count(metrics.productos_stock_bajo)} con stock bajo</p></div></div>
        <div className="inventory-alerts__list">{alerts.length ? alerts.map(product => <div className="inventory-alert" key={product.id}>
          <div className="inventory-alert__details"><strong>{product.nombre}</strong><span>{product.categoria || 'Sin categoría'} · {count(product.existencia)} {product.unidad_medida}</span></div>
          <span className={`status ${Number(product.existencia) <= 0 ? 'status--stock-bajo' : ''}`}>{Number(product.existencia) <= 0 ? 'Agotado' : `Mín. ${count(product.stock_minimo)}`}</span>
        </div>) : <p className="inventory-alerts__empty">No hay alertas de existencias.</p>}</div>
        <div className="inventory-alerts__actions"><button className="text-button" onClick={() => navigate('inventario')}>Revisar inventario <Icon name="arrow" size={16} /></button><button className="text-button" onClick={() => navigate('compras')}>Crear compra <Icon name="arrow" size={16} /></button></div>
      </section>

      <section className="surface inventory-alerts dashboard-panel">
        <div className="surface-heading"><div><h2>Movimientos de inventario</h2><p>Entradas, salidas y ajustes recientes</p></div></div>
        <div className="inventory-alerts__list">{recentMovements.length ? recentMovements.map(move => <div className="inventory-alert dashboard-ledger-row" key={move.id}>
          <span className={`dashboard-movement-mark dashboard-movement-mark--${String(move.tipo).toLowerCase()}`}>{move.tipo === 'ENTRADA' ? '+' : move.tipo === 'SALIDA' ? '−' : '±'}</span>
          <div className="inventory-alert__details"><strong>{move.producto}</strong><span>{date(move.fecha)} · {statusLabel(move.tipo)}{move.motivo ? ` · ${move.motivo}` : ''}</span></div>
          <strong className="dashboard-movement-quantity">{count(move.cantidad)} {move.unidad_medida}</strong>
        </div>) : <p className="inventory-alerts__empty">Todavía no hay movimientos registrados.</p>}</div>
        <div className="inventory-alerts__actions"><button className="text-button" onClick={() => navigate('inventario')}>Ver inventario <Icon name="arrow" size={16} /></button></div>
      </section>

      <section className="surface inventory-alerts dashboard-panel">
        <div className="surface-heading"><div><h2>Ventas recientes</h2><p>Incluye ventas locales y pedidos en línea</p></div></div>
        <div className="inventory-alerts__list">{recentSales.length ? recentSales.map(sale => <div className="inventory-alert" key={sale.id}>
          <div className="inventory-alert__details"><strong>{sale.numero}</strong><span>{date(sale.fecha)} · {sale.canal === 'EN_LINEA' ? 'En línea' : 'Local'} · {statusLabel(sale.estado)}</span></div>
          <strong>{money(sale.total)}</strong>
        </div>) : <p className="inventory-alerts__empty">Todavía no hay ventas registradas.</p>}</div>
        <div className="inventory-alerts__actions"><button className="text-button" onClick={() => navigate('ventas')}>Ver ventas locales <Icon name="arrow" size={16} /></button></div>
      </section>

      <section className="surface inventory-alerts dashboard-panel">
        <div className="surface-heading"><div><h2>Compras por recibir</h2><p>Órdenes pendientes de recepción</p></div><strong className="dashboard-panel-total">{count(metrics.compras_pendientes)}</strong></div>
        <div className="inventory-alerts__list">{pendingPurchases.length ? pendingPurchases.map(order => <div className="inventory-alert" key={order.id}>
          <div className="inventory-alert__details"><strong>{order.numero} · {order.proveedor || 'Proveedor'}</strong><span>{date(order.fecha)} · Pendiente</span></div>
          <strong>{money(order.total)}</strong>
        </div>) : <p className="inventory-alerts__empty">No hay órdenes pendientes de recepción.</p>}</div>
        <div className="inventory-alerts__actions"><button className="text-button" onClick={() => navigate('compras')}>Gestionar compras <Icon name="arrow" size={16} /></button></div>
      </section>
    </div>
  </div>;
}
