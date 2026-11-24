import React, { useState } from 'react';
import { Field, PageHeading, Modal, Input, Search, Table } from '../../components/AdminCatalogShared.jsx';

const emptySupplier = { nombre: '', identificacion: '', correo: '', telefono: '', direccion: '', contacto: '', activo: true };

export default function ProveedoresPage({data,mutate}) {
  const suppliers = data.proveedores || [];
  const [query,setQuery] = useState(''), [form,setForm] = useState(null), [error,setError] = useState('');
  const filtered = suppliers.filter(p => `${p.nombre} ${p.identificacion || ''} ${p.correo || ''}`.toLowerCase().includes(query.toLowerCase()));
  async function save(event) {
    event.preventDefault();
    setError('');
    const { id, ...supplier } = form;
    try {
      await mutate('/admin/proveedores' + (id ? '/' + id : ''), { ...supplier, activo: Boolean(supplier.activo) }, id ? 'PATCH' : 'POST');
      setForm(null);
    } catch (error) { setError(error.message); }
  }
  return <><PageHeading title="Proveedores" description="Directorio y contactos comerciales." action="Nuevo proveedor" onAction={() => {setError('');setForm({...emptySupplier});}} /><Search value={query} onChange={setQuery} label="Buscar proveedor" /><Table headers={['Proveedor','Identificación','Correo','Teléfono','Estado','Acciones']} empty={!filtered.length}>{filtered.map(p => <tr key={p.id}><td>{p.nombre}</td><td>{p.identificacion || '—'}</td><td>{p.correo || '—'}</td><td>{p.telefono || '—'}</td><td><span className={p.activo ? "status" : "status status--no-disponible"}>{p.activo ? 'Activo' : 'Inactivo'}</span></td><td><button type="button" className="ac-link" onClick={() => {setError('');setForm({...emptySupplier,...p});}}>Editar</button></td></tr>)}</Table>{form && <Modal title={form.id ? 'Editar proveedor' : 'Nuevo proveedor'} onClose={() => setForm(null)}><form className="ac-form" onSubmit={save}><div className="ac-grid"><Field label="Nombre *"><Input form={form} setForm={setForm} name="nombre" maxLength="160" required /></Field><Field label="Identificación"><Input form={form} setForm={setForm} name="identificacion" maxLength="30" /></Field><Field label="Correo"><Input form={form} setForm={setForm} name="correo" type="email" maxLength="180" /></Field><Field label="Teléfono"><Input form={form} setForm={setForm} name="telefono" maxLength="30" /></Field><Field label="Contacto"><Input form={form} setForm={setForm} name="contacto" maxLength="120" /></Field><Field label="Dirección"><Input form={form} setForm={setForm} name="direccion" maxLength="500" /></Field><label className="ac-checkbox"><input type="checkbox" checked={Boolean(form.activo)} onChange={e=>setForm({...form,activo:e.target.checked})} /> Proveedor activo</label></div>{error && <p className="ac-error" role="alert">{error}</p>}<div className="ac-actions"><button type="button" className="ac-secondary" onClick={() => setForm(null)}>Cancelar</button><button className="primary-action">Guardar proveedor</button></div></form></Modal>}</>;
}

