import './sales.css';
import React, { useState } from 'react';
import { Field, Header, money, roundMoney, roundQuantity, nameOf, nextId, label, date } from '../operaciones/OperationsShared.jsx';

const blankSale = () => ({ usuario_id: '', metodo_pago: 'EFECTIVO', tipo_comprobante: 'TIQUETE', numero_comprobante: '', referencia_pago: '', estado: 'PENDIENTE', descuento: '0', impuesto: '0', observaciones: '' });

export default function Sales({ data, setData }) {
  const [form, setForm] = useState(null);
  const [lines, setLines] = useState([]);
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const subtotal = roundMoney(lines.reduce((sum, line) => sum + roundMoney(line.cantidad * line.precio_unitario), 0));
  const discount = Number(form?.descuento || 0);
  const tax = Number(form?.impuesto || 0);
  const total = roundMoney(subtotal - discount + tax);
  const sales = data.ventas.filter(s => s.canal === 'LOCAL' && `${s.numero} ${s.estado} ${nameOf(data.usuarios.find(u => u.id === s.usuario_id))}`.toLowerCase().includes(query.toLowerCase()));
  const currentSale = data.ventas.find(s => s.id === selected);
  const update = (key, value) => setForm(current => ({ ...current, [key]: value }));
  function addLine() {
    const product = data.productos.find(p => String(p.id) === productId);
    const qty = Number(quantity);
    if (!product || !Number.isFinite(qty) || qty <= 0 || Math.abs(Math.round(qty * 1000) - qty * 1000) > 0.000001) return setError('Seleccioná un producto y una cantidad positiva de hasta tres decimales.');
    const existing = lines.find(line => line.producto_id === product.id)?.cantidad || 0;
    if (roundQuantity(qty + existing) > Number(product.existencia)) return setError('La cantidad supera la existencia disponible.');
    setLines(current => existing ? current.map(line => line.producto_id === product.id ? { ...line, cantidad: roundQuantity(line.cantidad + qty) } : line) : [...current, { producto_id: product.id, cantidad: qty, precio_unitario: Number(product.precio_venta), descuento: 0 }]);
    setError(''); setProductId(''); setQuantity('1');
  }
  function save(event) {
    event.preventDefault();
    if (!lines.length) return setError('Agregá al menos un producto.');
    if (!Number.isFinite(discount) || !Number.isFinite(tax) || discount < 0 || tax < 0 || discount > subtotal) return setError('Revisá el descuento y el impuesto. El descuento no puede superar el subtotal.');
    if (form.numero_comprobante.trim() && data.ventas.some(s => s.numero_comprobante === form.numero_comprobante.trim())) return setError('El número de comprobante ya existe.');
    if (lines.some(line => Number(data.productos.find(p => p.id === line.producto_id)?.existencia ?? -1) < line.cantidad)) return setError('Cambió la existencia de un producto. Revisá las cantidades.');
    const id = nextId(data.ventas);
    const timestamp = new Date().toISOString();
    const sale = { ...form, id, numero: `V-${String(id).padStart(4, '0')}`, usuario_id: form.usuario_id ? Number(form.usuario_id) : null, atendido_por_id: null, canal: 'LOCAL', fecha: timestamp, subtotal, descuento: discount, impuesto: tax, costo_envio: 0, total, numero_comprobante: form.numero_comprobante.trim() || null, modalidad_entrega: 'RETIRO_TIENDA', direccion_entrega: '', detalles: lines.map(line => ({ ...line, total_linea: roundMoney(line.cantidad * line.precio_unitario) })) };
    setData(current => {
      let movementId = nextId(current.movimientos);
      const movements = lines.map(line => { const product = current.productos.find(p => p.id === line.producto_id); const before = Number(product.existencia); return { id: movementId++, producto_id: product.id, usuario_id: null, tipo: 'SALIDA', cantidad: line.cantidad, existencia_anterior: before, existencia_nueva: roundQuantity(before - line.cantidad), motivo: `Venta ${sale.numero}`, fecha: timestamp }; });
      return { ...current, ventas: [sale, ...current.ventas], productos: current.productos.map(p => { const line = lines.find(l => l.producto_id === p.id); return line ? { ...p, existencia: roundQuantity(Number(p.existencia) - line.cantidad) } : p; }), movimientos: [...movements, ...current.movimientos] };
    });
    setForm(null); setLines([]); setError(''); setSelected(id);
  }
  function changeStatus(sale, status) {
    setData(current => {
      const record = current.ventas.find(s => s.id === sale.id);
      if (!record || record.canal !== 'LOCAL' || record.estado === 'ANULADA') return current;
      if (status !== 'ANULADA') return { ...current, ventas: current.ventas.map(s => s.id === sale.id ? { ...s, estado: status } : s) };
      let movementId = nextId(current.movimientos);
      const entries = (record.detalles || []).map(line => { const product = current.productos.find(p => p.id === line.producto_id); if (!product) return null; const before = Number(product.existencia); return { id: movementId++, producto_id: product.id, usuario_id: null, tipo: 'ENTRADA', cantidad: Number(line.cantidad), existencia_anterior: before, existencia_nueva: roundQuantity(before + Number(line.cantidad)), motivo: `Anulación ${record.numero}`, fecha: new Date().toISOString() }; }).filter(Boolean);
      return { ...current, ventas: current.ventas.map(s => s.id === sale.id ? { ...s, estado: status } : s), productos: current.productos.map(p => { const line = (record.detalles || []).find(l => l.producto_id === p.id); return line ? { ...p, existencia: roundQuantity(Number(p.existencia) + Number(line.cantidad)) } : p; }), movimientos: [...entries, ...current.movimientos] };
    });
  }
  return <>
    <Header title="Ventas locales" description="Registrá y consultá las ventas realizadas en tienda." action="Nueva venta" onAction={() => { setForm(blankSale()); setLines([]); setProductId(''); setQuantity('1'); setSelected(null); setError(''); }} />
    <p className="ops-note">Demostración local: las ventas y movimientos no se envían ni procesan pagos reales.</p>
    {form && <section className="surface ops-panel"><div className="ops-panel-head"><h2>Nueva venta local</h2><button className="ops-link" type="button" onClick={() => setForm(null)}>Cerrar</button></div><form onSubmit={save}>
      <div className="ops-grid"><Field label="Cliente"><select value={form.usuario_id} onChange={e => update('usuario_id', e.target.value)}><option value="">Cliente ocasional</option>{data.usuarios.filter(u => u.rol === 'CLIENTE' && u.activo).map(u => <option key={u.id} value={u.id}>{nameOf(u)}</option>)}</select></Field><Field label="Método de pago"><select value={form.metodo_pago} onChange={e => update('metodo_pago', e.target.value)}><option value="EFECTIVO">Efectivo</option><option value="TARJETA">Tarjeta</option></select></Field><Field label="Tipo de comprobante"><select value={form.tipo_comprobante} onChange={e => update('tipo_comprobante', e.target.value)}><option value="TIQUETE">Tiquete</option><option value="FACTURA">Factura</option><option value="NOTA_CREDITO">Nota de crédito</option></select></Field><Field label="Número de comprobante"><input maxLength={60} value={form.numero_comprobante} onChange={e => update('numero_comprobante', e.target.value)} /></Field><Field label="Referencia de pago"><input maxLength={120} value={form.referencia_pago} onChange={e => update('referencia_pago', e.target.value)} /></Field><Field label="Estado inicial"><select value={form.estado} onChange={e => update('estado', e.target.value)}><option value="PENDIENTE">Pendiente</option><option value="PAGADA">Pagada</option></select></Field></div>
      <h3>Productos</h3><div className="ops-line-add"><Field label="Producto"><select value={productId} onChange={e => setProductId(e.target.value)}><option value="">Seleccioná un producto</option>{data.productos.filter(p => p.activo && Number(p.existencia) > 0).map(p => <option key={p.id} value={p.id}>{p.nombre} · {money(p.precio_venta)} · {p.existencia} {p.unidad_medida}</option>)}</select></Field><Field label="Cantidad"><input type="number" min="0.001" step="0.001" value={quantity} onChange={e => setQuantity(e.target.value)} /></Field><button type="button" className="ops-secondary" onClick={addLine}>Agregar</button></div>
      <div className="table-scroll"><table><thead><tr><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Total</th><th></th></tr></thead><tbody>{lines.map(line => <tr key={line.producto_id}><td>{data.productos.find(p => p.id === line.producto_id)?.nombre}</td><td>{line.cantidad}</td><td>{money(line.precio_unitario)}</td><td>{money(line.cantidad * line.precio_unitario)}</td><td><button className="ops-link" type="button" onClick={() => setLines(lines.filter(l => l.producto_id !== line.producto_id))}>Quitar</button></td></tr>)}</tbody></table>{!lines.length && <p className="ops-muted">Aún no agregaste productos.</p>}</div>
      <div className="ops-grid ops-totals"><Field label="Descuento (monto)"><input type="number" min="0" step="0.01" value={form.descuento} onChange={e => update('descuento', e.target.value)} /></Field><Field label="Impuesto (monto)"><input type="number" min="0" step="0.01" value={form.impuesto} onChange={e => update('impuesto', e.target.value)} /></Field><Field label="Observaciones" wide><textarea value={form.observaciones} onChange={e => update('observaciones', e.target.value)} /></Field></div><p className="ops-total">Subtotal {money(subtotal)} · Total {money(total)}</p>
      {error && <p className="ops-error" role="alert">{error}</p>}<div className="ops-actions"><button className="primary-action" type="submit">Registrar venta</button><button type="button" className="ops-secondary" onClick={() => setForm(null)}>Cancelar</button></div>
    </form></section>}
    {currentSale && <section className="surface ops-panel"><div className="ops-panel-head"><h2>Venta {currentSale.numero}</h2><button className="ops-link" onClick={() => setSelected(null)}>Cerrar</button></div><p className="ops-muted">{date(currentSale.fecha)} · {nameOf(data.usuarios.find(u => u.id === currentSale.usuario_id))} · {label(currentSale.metodo_pago)} · {label(currentSale.estado)}</p><div className="table-scroll"><table><thead><tr><th>Producto</th><th>Cantidad</th><th>Precio unitario</th><th>Total</th></tr></thead><tbody>{(currentSale.detalles || []).map((line, index) => <tr key={index}><td>{data.productos.find(p => p.id === line.producto_id)?.nombre || 'Producto'}</td><td>{line.cantidad}</td><td>{money(line.precio_unitario)}</td><td>{money(line.total_linea)}</td></tr>)}</tbody></table></div><p className="ops-total">Subtotal {money(currentSale.subtotal)} · Descuento {money(currentSale.descuento)} · Impuesto {money(currentSale.impuesto)} · Total {money(currentSale.total)}</p><p className="ops-muted">Comprobante: {label(currentSale.tipo_comprobante)} {currentSale.numero_comprobante || 'sin número'}{currentSale.referencia_pago ? ` · Referencia: ${currentSale.referencia_pago}` : ''}</p><div className="ops-actions">{currentSale.estado === 'PENDIENTE' && <button className="ops-secondary" onClick={() => changeStatus(currentSale, 'PAGADA')}>Marcar pagada</button>}{currentSale.estado !== 'ANULADA' && <button className="ops-secondary" onClick={() => changeStatus(currentSale, 'ANULADA')}>Anular venta</button>}</div></section>}
    <div className="ops-toolbar"><span>{sales.length} ventas locales</span><input aria-label="Buscar ventas" placeholder="Buscar venta…" value={query} onChange={e => setQuery(e.target.value)} /></div><div className="surface table-scroll"><table><thead><tr><th>Número</th><th>Cliente</th><th>Fecha</th><th>Total</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{sales.map(sale => <tr key={sale.id}><td>{sale.numero}</td><td>{nameOf(data.usuarios.find(u => u.id === sale.usuario_id))}</td><td>{date(sale.fecha)}</td><td>{money(sale.total)}</td><td><span className="status">{label(sale.estado)}</span></td><td><button className="ops-link" onClick={() => { setForm(null); setSelected(sale.id); }}>Ver detalle</button></td></tr>)}</tbody></table>{!sales.length && <p className="empty-state">No se encontraron ventas locales.</p>}</div>
  </>;
}

