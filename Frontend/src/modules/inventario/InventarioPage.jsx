import React, { useState } from 'react';
import { money, find, Field, PageHeading, Modal, Input, Search, Table } from '../../components/AdminCatalogShared.jsx';

const emptyProduct = { codigo: '', nombre: '', descripcion: '', categoria_id: '', proveedor_id: '', unidad_medida: 'unidad', precio_compra: 0, precio_venta: 0, existencia: 0, stock_minimo: 0, imagen_url: '', activo: true };

export default function InventarioPage({ data, mutate }) {
  const products = data.productos || [], categories = data.categorias || [], suppliers = data.proveedores || [], moves = data.movimientos || [];
  const [query, setQuery] = useState(''), [form, setForm] = useState(null), [movement, setMovement] = useState(null), [error, setError] = useState(''), [showMoves, setShowMoves] = useState(false);
  const filtered = products.filter(p => `${p.codigo} ${p.nombre} ${find(categories, p.categoria_id)?.nombre || ''}`.toLowerCase().includes(query.toLowerCase()));
  async function saveProduct(e) {
    e.preventDefault(); setError('');
    if (!form.codigo.trim() || !form.nombre.trim() || !form.unidad_medida.trim()) return setError('Completá el código, nombre y unidad de medida.');
    if (products.some(p => String(p.id) !== String(form.id) && p.codigo.toLowerCase() === form.codigo.trim().toLowerCase())) return setError('Ya existe un producto con ese código.');
    if (['precio_compra', 'precio_venta', 'stock_minimo'].some(k => form[k] === '' || !Number.isFinite(Number(form[k])) || Number(form[k]) < 0)) return setError('Los precios y las existencias deben ser números iguales o mayores que cero.');
    const { id } = form;
    // Only submit fields accepted by the API, not read-only database columns.
    const product = Object.fromEntries(Object.keys(emptyProduct)
      .filter(key => key !== 'existencia')
      .map(key => [key, form[key]]));
    try {
      await mutate('/admin/productos' + (id ? '/' + id : ''), {
        ...product, categoria_id: product.categoria_id || null, proveedor_id: product.proveedor_id || null,
        imagen_url: product.imagen_url || null, activo: Boolean(product.activo),
      }, id ? 'PATCH' : 'POST');
      setForm(null);
    } catch (error) { setError(error.message); }
  }
  async function saveMovement(e) {
    e.preventDefault(); const product = find(products, movement.producto_id); const qty = Number(movement.cantidad);
    if (!product || movement.cantidad === '' || !Number.isFinite(qty) || (movement.tipo === 'AJUSTE' ? qty < 0 : qty <= 0)) return setError('Seleccioná un producto y una cantidad válida.');
    const previous = Number(product.existencia), current = movement.tipo === 'ENTRADA' ? previous + qty : movement.tipo === 'SALIDA' ? previous - qty : qty;
    if (current < 0) return setError('La salida no puede superar la existencia disponible.');
    if (movement.tipo === 'AJUSTE' && current === previous) return setError('La nueva existencia debe ser diferente de la actual.');
    try {
      await mutate('/inventario/movimientos', movement);
      setMovement(null);
      setError('');
    } catch (error) { setError(error.message); }
  }
  return <><PageHeading title="Inventario" description="Productos, existencias y movimientos de inventario." action="Agregar producto" onAction={() => { setError(''); setForm({ ...emptyProduct }); }} /><div className="ac-toolbar"><button type="button" className="ac-secondary" onClick={() => { setError(''); setMovement({ producto_id: '', tipo: 'ENTRADA', cantidad: '', motivo: '' }); }}>Registrar movimiento</button><button type="button" className="ac-secondary" onClick={() => setShowMoves(!showMoves)}>{showMoves ? 'Ver productos' : 'Ver movimientos'}</button><span>{products.filter(p => Number(p.existencia) <= Number(p.stock_minimo)).length} productos con existencias bajas</span></div>
    {!showMoves ? <><Search value={query} onChange={setQuery} label="Buscar producto o código" /><Table headers={['Código', 'Producto', 'Categoría', 'Precio venta', 'Existencia', 'Estado', 'Acciones']} empty={!filtered.length}>{filtered.map(p => <tr key={p.id}><td>{p.codigo}</td><td>{p.nombre}</td><td>{find(categories,p.categoria_id)?.nombre || 'Sin categoría'}</td><td>{money(p.precio_venta)}</td><td>{p.existencia} {p.unidad_medida}</td><td><span className={p.activo ? "status" : "status status--no-disponible"}>{!p.activo ? 'No disponible' : Number(p.existencia) <= 0 ? 'Agotado' : Number(p.existencia) <= Number(p.stock_minimo) ? 'Stock bajo' : 'Disponible'}</span></td><td><button type="button" className="ac-link" onClick={() => { setError(''); setForm({ ...emptyProduct, ...p }); }}>Editar</button></td></tr>)}</Table></> : <Table headers={['Fecha', 'Producto', 'Tipo', 'Cantidad', 'Antes', 'Después', 'Motivo']} empty={!moves.length}>{moves.map(m => <tr key={m.id}><td>{m.fecha ? new Date(m.fecha).toLocaleString('es-CR') : '—'}</td><td>{find(products,m.producto_id)?.nombre || 'Producto'}</td><td>{m.tipo}</td><td>{m.cantidad}</td><td>{m.existencia_anterior}</td><td>{m.existencia_nueva}</td><td>{m.motivo || '—'}</td></tr>)}</Table>}
    {form && <Modal title={form.id ? 'Editar producto' : 'Agregar producto'} onClose={() => setForm(null)}><form onSubmit={saveProduct} className="ac-form"><div className="ac-grid"><Field label="Código *"><Input form={form} setForm={setForm} name="codigo" maxLength="60" required /></Field><Field label="Nombre *"><Input form={form} setForm={setForm} name="nombre" maxLength="180" required /></Field><Field label="Categoría"><select value={form.categoria_id || ''} onChange={e => setForm({...form,categoria_id:e.target.value})}><option value="">Sin categoría</option>{categories.map(c => <option key={c.id} value={c.id}>{c.nombre}</option>)}</select></Field><Field label="Proveedor"><select value={form.proveedor_id || ''} onChange={e => setForm({...form,proveedor_id:e.target.value})}><option value="">Sin proveedor</option>{suppliers.map(s => <option key={s.id} value={s.id}>{s.nombre}</option>)}</select></Field><Field label="Unidad de medida *"><Input form={form} setForm={setForm} name="unidad_medida" maxLength="30" required /></Field><Field label="Precio de compra"><Input form={form} setForm={setForm} name="precio_compra" type="number" min="0" step="0.01" required /></Field><Field label="Precio de venta"><Input form={form} setForm={setForm} name="precio_venta" type="number" min="0" step="0.01" required /></Field><Field label="Stock mínimo"><Input form={form} setForm={setForm} name="stock_minimo" type="number" min="0" step="0.001" required /></Field><Field label="URL de imagen"><input type="text" placeholder="https://..." value={form.imagen_url || ""} onChange={e => setForm({...form, imagen_url:e.target.value})} /></Field><label className="ac-checkbox"><input type="checkbox" checked={Boolean(form.activo)} onChange={e => setForm({ ...form, activo: e.target.checked })} /> Producto disponible</label><div className="ac-wide"><Field label="Descripción"><textarea value={form.descripcion || ''} onChange={e => setForm({...form,descripcion:e.target.value})} rows="3" /></Field></div></div>{form.imagen_url && <img className="ac-preview" src={form.imagen_url} alt="Vista previa del producto" />}{error && <p className="ac-error" role="alert">{error}</p>}<div className="ac-actions"><button type="button" className="ac-secondary" onClick={() => setForm(null)}>Cancelar</button><button className="primary-action">Guardar producto</button></div></form></Modal>}
    {movement && <Modal title="Registrar movimiento" onClose={() => setMovement(null)}><form className="ac-form" onSubmit={saveMovement}><div className="ac-grid"><Field label="Producto *"><select required value={movement.producto_id} onChange={e => setMovement({...movement,producto_id:e.target.value})}><option value="">Seleccioná un producto</option>{products.map(p => <option key={p.id} value={p.id}>{p.nombre} ({p.existencia} {p.unidad_medida})</option>)}</select></Field><Field label="Tipo"><select value={movement.tipo} onChange={e => setMovement({...movement,tipo:e.target.value})}><option value="ENTRADA">Entrada</option><option value="SALIDA">Salida</option><option value="AJUSTE">Ajuste de existencia</option></select></Field><Field label={movement.tipo === 'AJUSTE' ? 'Nueva existencia *' : 'Cantidad *'}><Input form={movement} setForm={setMovement} name="cantidad" type="number" min={movement.tipo === "AJUSTE" ? "0" : "0.001"} step="0.001" required /></Field><Field label="Motivo"><Input form={movement} setForm={setMovement} name="motivo" maxLength="255" required /></Field></div>{error && <p role="alert" className="ac-error">{error}</p>}<div className="ac-actions"><button type="button" className="ac-secondary" onClick={() => setMovement(null)}>Cancelar</button><button className="primary-action">Guardar movimiento</button></div></form></Modal>}
  </>;
}

