import './sales.css';
import React, { useState } from 'react';
import DropdownSelect from '../../components/DropdownSelect.jsx';
import { Field, Header, money, roundMoney, roundQuantity, nameOf, label, date } from '../operaciones/OperationsShared.jsx';

const blankSale = () => ({ usuario_id: '', metodo_pago: 'EFECTIVO', tipo_comprobante: 'TIQUETE', observaciones: '' });
const formatStatus = value => { const text = String(value || '').replaceAll('_', ' ').toLocaleLowerCase('es-CR'); return text ? text[0].toLocaleUpperCase('es-CR') + text.slice(1) : ''; };

export default function Sales({ data, mutate }) {
  const [form, setForm] = useState(null);
  const [lines, setLines] = useState([]);
  const [productId, setProductId] = useState('');
  const [quantity, setQuantity] = useState('1');
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState('');
  const availableProducts = data.productos.filter(p => p.activo && Number(p.existencia) > 0);
  const subtotal = roundMoney(lines.reduce((sum, line) => sum + roundMoney(line.cantidad * line.precio_unitario), 0));
  const sales = data.ventas.filter(s => s.canal === 'LOCAL' && `${s.numero} ${s.estado} ${nameOf(data.usuarios.find(u => u.id === s.usuario_id))}`.toLowerCase().includes(query.toLowerCase()));
  const currentSale = data.ventas.find(s => s.id === selected);
  const update = (key, value) => setForm(current => ({ ...current, [key]: value }));
  function addLine() {
    const product = availableProducts.find(p => String(p.id) === productId);
    const qty = Number(quantity);
    if (!product || !Number.isFinite(qty) || qty <= 0 || Math.abs(Math.round(qty * 1000) - qty * 1000) > 0.000001) return setError('Seleccioná un producto y una cantidad positiva de hasta tres decimales.');
    const existing = lines.find(line => line.producto_id === product.id)?.cantidad || 0;
    if (roundQuantity(qty + existing) > Number(product.existencia)) return setError('La cantidad supera la existencia disponible.');
    setLines(current => existing ? current.map(line => line.producto_id === product.id ? { ...line, cantidad: roundQuantity(line.cantidad + qty) } : line) : [...current, { producto_id: product.id, cantidad: qty, precio_unitario: Number(product.precio_venta), descuento: 0 }]);
    setError(''); setProductId(''); setQuantity('1');
  }
  async function save(event) {
    event.preventDefault();
    if (!lines.length) return setError('Agregá al menos un producto.');
    setError('');
    try {
      const sale = await mutate('/ventas', {
        numero: 'V-' + crypto.randomUUID(), canal: 'LOCAL',
        metodo_pago: form.metodo_pago, tipo_comprobante: form.tipo_comprobante,
        ...(form.usuario_id && { usuario_id: form.usuario_id }),
        observaciones: form.observaciones,
        detalles: lines.map(({ producto_id, cantidad }) => ({ producto_id, cantidad })),
      });
      setForm(null);
      setLines([]);
      setSelected(sale.id);
    } catch (error) { setError(error.message); }
  }

  async function refund(sale) {
    setError('');
    try {
      await mutate('/ventas/' + sale.id + '/nota-credito');
    } catch (error) { setError(error.message); }
  }
  return <>
    <Header title="Ventas locales" description="Registrá y consultá las ventas realizadas en tienda." action="Nueva venta" onAction={() => { setForm(blankSale()); setLines([]); setProductId(''); setQuantity('1'); setSelected(null); setError(''); }} />
    {!form && error && <p role="alert">{error}</p>}
    {form && <section className="surface ops-panel"><div className="ops-panel-head"><h2>Nueva venta local</h2><button className="ops-link" type="button" onClick={() => setForm(null)}>Cerrar</button></div><form onSubmit={save}>
      <div className="ops-grid"><Field label="Cliente"><DropdownSelect value={form.usuario_id} onChange={e => update('usuario_id', e.target.value)}><option value="">Cliente ocasional</option>{data.usuarios.filter(u => u.rol === 'CLIENTE' && u.activo).map(u => <option key={u.id} value={u.id}>{nameOf(u)}</option>)}</DropdownSelect></Field><Field label="Método de pago"><DropdownSelect value={form.metodo_pago} onChange={e => update('metodo_pago', e.target.value)}><option value="EFECTIVO">Efectivo</option><option value="TARJETA">Tarjeta</option></DropdownSelect></Field><Field label="Tipo de comprobante"><DropdownSelect value={form.tipo_comprobante} onChange={e => update('tipo_comprobante', e.target.value)}><option value="TIQUETE">Tiquete</option><option value="FACTURA">Factura</option></DropdownSelect></Field></div>
      <h3>Productos</h3><div className="ops-line-add"><Field label="Producto"><DropdownSelect value={productId} onChange={e => setProductId(e.target.value)}><option value="">{availableProducts.length ? "Seleccioná un producto" : "Sin productos disponibles"}</option>{availableProducts.map(p => <option key={p.id} value={p.id}>{p.nombre} · {money(p.precio_venta)} · {p.existencia} {p.unidad_medida}</option>)}</DropdownSelect></Field><Field label="Cantidad"><input type="number" min="0.001" step="0.001" value={quantity} onChange={e => setQuantity(e.target.value)} /></Field><button type="button" className="ops-secondary" onClick={addLine} disabled={!productId || !availableProducts.length}>Agregar</button></div>{!availableProducts.length && <p className="ops-muted">Para vender un producto, marcá «Producto disponible» en Inventario y verificá que tenga existencias.</p>}
      <div className="table-scroll"><table><thead><tr><th>Producto</th><th>Cantidad</th><th>Precio</th><th>Total</th><th></th></tr></thead><tbody>{lines.map(line => <tr key={line.producto_id}><td>{data.productos.find(p => p.id === line.producto_id)?.nombre}</td><td>{line.cantidad}</td><td>{money(line.precio_unitario)}</td><td>{money(line.cantidad * line.precio_unitario)}</td><td><button className="ops-link" type="button" onClick={() => setLines(lines.filter(l => l.producto_id !== line.producto_id))}>Quitar</button></td></tr>)}</tbody></table>{!lines.length && <p className="ops-muted">Aún no agregaste productos.</p>}</div>
      <div className="ops-grid ops-totals"><Field label="Observaciones" wide><textarea value={form.observaciones} onChange={e => update('observaciones', e.target.value)} /></Field></div><p className="ops-total">Subtotal {money(subtotal)}</p>
      {error && <p className="ops-error" role="alert">{error}</p>}<div className="ops-actions"><button className="primary-action" type="submit">Registrar venta</button><button type="button" className="ops-secondary" onClick={() => setForm(null)}>Cancelar</button></div>
    </form></section>}
    {currentSale && <section className="surface ops-panel"><div className="ops-panel-head"><h2>Venta {currentSale.numero}</h2><button className="ops-link" onClick={() => setSelected(null)}>Cerrar</button></div><p className="ops-muted">{date(currentSale.fecha)} · {nameOf(data.usuarios.find(u => u.id === currentSale.usuario_id))} · {label(currentSale.metodo_pago)} · {formatStatus(currentSale.estado)}</p><div className="table-scroll"><table><thead><tr><th>Producto</th><th>Cantidad</th><th>Precio unitario</th><th>Total</th></tr></thead><tbody>{(currentSale.detalles || []).map((line, index) => <tr key={index}><td>{data.productos.find(p => p.id === line.producto_id)?.nombre || 'Producto'}</td><td>{line.cantidad}</td><td>{money(line.precio_unitario)}</td><td>{money(line.total_linea)}</td></tr>)}</tbody></table></div><p className="ops-total">Subtotal {money(currentSale.subtotal)} · Descuento {money(currentSale.descuento)} · Impuesto {money(currentSale.impuesto)} · Total {money(currentSale.total)}</p><p className="ops-muted">Comprobante: {label(currentSale.tipo_comprobante)} {currentSale.numero_comprobante || 'sin número'}{currentSale.referencia_pago ? ` · Referencia: ${currentSale.referencia_pago}` : ''}</p><div className="ops-actions">{currentSale.estado === 'PAGADA' && <button className="ops-secondary" onClick={() => refund(currentSale)}>Emitir nota de crédito</button>}</div></section>}
    <div className="ops-toolbar"><span>{sales.length} ventas locales</span><input aria-label="Buscar ventas" placeholder="Buscar venta…" value={query} onChange={e => setQuery(e.target.value)} /></div><div className="surface table-scroll"><table><thead><tr><th>Número</th><th>Cliente</th><th>Fecha</th><th>Total</th><th>Estado</th><th>Acción</th></tr></thead><tbody>{sales.map(sale => <tr key={sale.id}><td>{sale.numero}</td><td>{nameOf(data.usuarios.find(u => u.id === sale.usuario_id))}</td><td>{date(sale.fecha)}</td><td>{money(sale.total)}</td><td><span className="status">{formatStatus(sale.estado)}</span></td><td className="table-actions"><button className="table-action" onClick={() => { setForm(null); setSelected(sale.id); }}>Ver detalle</button></td></tr>)}</tbody></table>{!sales.length && <p className="empty-state">No se encontraron ventas locales.</p>}</div>
  </>;
}

