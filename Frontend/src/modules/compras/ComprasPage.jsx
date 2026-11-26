import React, { useState } from 'react';
import DropdownSelect from '../../components/DropdownSelect.jsx';
import { money, find, numeric, today, Field, PageHeading, Modal, Input, Search, Table } from '../../components/AdminCatalogShared.jsx';

const emptyOrder = () => ({ numero: '', proveedor_id: '', fecha: today(), observaciones: '', detalles: [{ producto_id: '', cantidad: 1, costo_unitario: 0 }] });
const displayOrderNumber = value => String(value || '').replace(/^SEED-/i, '');
const displayOrderNotes = value => /semilla inicial/i.test(value || '') ? 'Orden de compra registrada en el sistema.' : value;
const formatStatus = value => { const text = String(value || '').replaceAll('_', ' ').toLocaleLowerCase('es-CR'); return text ? text[0].toLocaleUpperCase('es-CR') + text.slice(1) : ''; };

export default function ComprasPage({data,mutate}) {
  const orders = data.compras || [], products = data.productos || [], suppliers = data.proveedores || [];
  const [query,setQuery] = useState(''), [form,setForm] = useState(null), [detail,setDetail] = useState(null), [error,setError] = useState('');
  const filtered = orders.filter(o => `${o.numero} ${find(suppliers,o.proveedor_id)?.nombre || ''} ${o.estado}`.toLowerCase().includes(query.toLowerCase()));
  const subtotal = form?.detalles.reduce((sum,line) => sum + numeric(line.cantidad) * numeric(line.costo_unitario),0) || 0;
  function changeLine(index,key,value) { setForm({...form,detalles:form.detalles.map((line,i) => i === index ? {...line,[key]:value,...(key === 'producto_id' ? {costo_unitario:find(products,value)?.precio_compra || 0} : {})} : line)}); }
  async function save(event) {
    event.preventDefault();
    setError('');
    const { numero, proveedor_id, fecha, observaciones, detalles } = form;
    try {
      await mutate('/compras', { numero, proveedor_id, fecha, observaciones, detalles });
      setForm(null);
    } catch (error) { setError(error.message); }
  }

  async function status(order, estado) {
    setError('');
    try {
      await mutate('/compras/' + order.id + (estado === 'RECIBIDA' ? '/recibir' : '/cancelar'));
    } catch (error) { setError(error.message); }
  }
  return <><PageHeading title="Compras" description="Órdenes de compra y seguimiento a proveedores." action="Nueva orden" onAction={() => {setError('');setForm(emptyOrder());}} /><Search value={query} onChange={setQuery} label="Buscar orden o proveedor" /><Table headers={['N.º orden','Proveedor','Fecha','Total','Estado','Acciones']} empty={!filtered.length}>{filtered.map(o => <tr key={o.id}><td>{displayOrderNumber(o.numero)}</td><td>{find(suppliers,o.proveedor_id)?.nombre || '—'}</td><td>{o.fecha}</td><td>{money(o.total)}</td><td><span className="status">{formatStatus(o.estado)}</span></td><td className="table-actions"><button type="button" className="table-action" onClick={() => setDetail(o)}>Ver detalle</button>{o.estado === 'PENDIENTE' && <><button type="button" className="table-action table-action--success" onClick={() => status(o,'RECIBIDA')}>Marcar recibida</button><button type="button" className="table-action table-action--danger" onClick={() => status(o,'CANCELADA')}>Cancelar orden</button></>}</td></tr>)}</Table>{!form && error && <p role="alert">{error}</p>}
    {detail && <Modal title={`Orden ${displayOrderNumber(detail.numero)}`} onClose={() => setDetail(null)}><div className="ac-form"><p>Proveedor: {find(suppliers,detail.proveedor_id)?.nombre || '—'} · Estado: {formatStatus(detail.estado)}</p><Table headers={['Producto','Cantidad','Costo','Total']} empty={!detail.detalles?.length}>{(detail.detalles || []).map((l,i)=><tr key={i}><td>{find(products,l.producto_id)?.nombre || 'Producto'}</td><td>{l.cantidad}</td><td>{money(l.costo_unitario)}</td><td>{money(l.total_linea ?? numeric(l.cantidad)*numeric(l.costo_unitario))}</td></tr>)}</Table><p>Subtotal: {money(detail.subtotal)} · Impuesto: {money(detail.impuesto)} · <strong>Total: {money(detail.total)}</strong></p><p>Observaciones: {displayOrderNotes(detail.observaciones) || '—'}</p></div></Modal>}
    {form && <Modal title="Nueva orden de compra" onClose={() => setForm(null)}><form className="ac-form" onSubmit={save}><div className="ac-grid"><Field label="Número *"><Input form={form} setForm={setForm} name="numero" maxLength="40" required /></Field><Field label="Proveedor *"><DropdownSelect required value={form.proveedor_id} onChange={e=>setForm({...form,proveedor_id:e.target.value})}><option value="">Seleccioná proveedor</option>{suppliers.filter(s=>s.activo).map(s=><option key={s.id} value={s.id}>{s.nombre}</option>)}</DropdownSelect></Field><Field label="Fecha *"><Input form={form} setForm={setForm} name="fecha" type="date" required /></Field></div><h3>Productos</h3>{form.detalles.map((line,i)=><div className="ac-line" key={i}><Field label="Producto"><DropdownSelect required value={line.producto_id} onChange={e=>changeLine(i,'producto_id',e.target.value)}><option value="">Seleccioná producto</option>{products.filter(p=>p.activo).map(p=><option value={p.id} key={p.id}>{p.nombre}</option>)}</DropdownSelect></Field><Field label="Cantidad"><input required type="number" min="0.001" step="0.001" value={line.cantidad} onChange={e=>changeLine(i,'cantidad',e.target.value)} /></Field><Field label="Costo unitario"><input required type="number" min="0" step="0.01" value={line.costo_unitario} onChange={e=>changeLine(i,'costo_unitario',e.target.value)} /></Field><button type="button" className="ac-link" disabled={form.detalles.length===1} onClick={()=>setForm({...form,detalles:form.detalles.filter((_,j)=>j!==i)})}>Quitar</button></div>)}<button type="button" className="ac-secondary" onClick={()=>setForm({...form,detalles:[...form.detalles,{producto_id:'',cantidad:1,costo_unitario:0}]})}>＋ Agregar producto</button><p>Subtotal: {money(subtotal)}</p><Field label="Observaciones"><textarea rows="3" value={form.observaciones || ''} onChange={e=>setForm({...form,observaciones:e.target.value})} /></Field>{error && <p className="ac-error" role="alert">{error}</p>}<div className="ac-actions"><button type="button" className="ac-secondary" onClick={()=>setForm(null)}>Cancelar</button><button className="primary-action">Guardar orden</button></div></form></Modal>}
  </>;
}

