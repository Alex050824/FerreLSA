import React, { useState } from 'react';
import { Field, Header, nameOf } from '../operaciones/OperationsShared.jsx';

const blankUser = () => ({ nombre: '', apellido: '', identificacion: '', correo: '', telefono: '', rol: 'CLIENTE', provincia: '', canton: '', distrito: '', direccion_exacta: '', activo: true, password: '' });

export default function Users({ data, mutate, currentUser }) {
  const [query, setQuery] = useState('');
  const [form, setForm] = useState(null);
  const [error, setError] = useState('');
  const [removing, setRemoving] = useState(null);
  const [removalError, setRemovalError] = useState('');
  const users = data.usuarios.filter(u => `${u.nombre} ${u.apellido || ''} ${u.correo} ${u.identificacion || ''} ${u.rol}`.toLowerCase().includes(query.toLowerCase()));
  const edit = user => { setForm(user ? { ...blankUser(), ...user } : blankUser()); setError(''); };
  const update = (key, value) => setForm(current => ({ ...current, [key]: value }));
  async function save(event) {
    event.preventDefault();
    setError('');
    const { id, password, ...user } = form;
    try {
      await mutate('/usuarios' + (id ? '/' + id : ''), {
        ...user, activo: Boolean(user.activo), ...((password || !id) && { password }),
      }, id ? 'PATCH' : 'POST');
      setForm(null);
    } catch (error) { setError(error.message); }
  }
  async function remove(user) {
    const permanent = !user.activo;
    const action = permanent ? 'eliminar definitivamente' : 'desactivar';
    if (!window.confirm(`¿Querés ${action} la cuenta de ${nameOf(user)}?`)) return;
    setRemoving(user.id);
    setRemovalError('');
    try {
      await mutate('/usuarios/' + user.id + (permanent ? '?permanente=1' : ''), undefined, 'DELETE');
      setForm(previous => previous?.id === user.id ? null : previous);
    } catch (error) {
      setRemovalError(error.message);
    } finally {
      setRemoving(null);
    }
  }

  return <>
    <Header title="Usuarios" description="Administrá los perfiles y sus datos de contacto." action="Nuevo usuario" onAction={() => edit(null)} />
    {form && <section className="ops-panel surface"><div className="ops-panel-head"><h2>{form.id ? 'Editar usuario' : 'Nuevo usuario'}</h2><button type="button" className="ops-link" onClick={() => setForm(null)}>Cerrar</button></div>
      <form onSubmit={save}><div className="ops-grid">
        <Field label="Nombre *"><input required maxLength={255} value={form.nombre} onChange={e => update('nombre', e.target.value)} /></Field>
        <Field label="Apellido"><input maxLength={255} value={form.apellido || ''} onChange={e => update('apellido', e.target.value)} /></Field>
        <Field label={form.id ? "Nueva contraseña (opcional)" : "Contraseña *"}><input type="password" autoComplete="new-password" minLength={8} maxLength={128} required={!form.id} value={form.password} onChange={e => update("password", e.target.value)} /></Field>
        <Field label="Correo *"><input type="email" required maxLength={255} value={form.correo} onChange={e => update('correo', e.target.value)} /></Field>
        <Field label="Identificación"><input maxLength={30} value={form.identificacion || ''} onChange={e => update('identificacion', e.target.value)} /></Field>
        <Field label="Teléfono"><input type="tel" maxLength={30} value={form.telefono || ''} onChange={e => update('telefono', e.target.value)} /></Field>
        <Field label="Rol"><select value={form.rol} onChange={e => update('rol', e.target.value)}><option value="CLIENTE">Cliente</option><option value="ADMIN">Administrador</option></select></Field>
        <Field label="Provincia"><input maxLength={80} value={form.provincia || ''} onChange={e => update('provincia', e.target.value)} /></Field>
        <Field label="Cantón"><input maxLength={80} value={form.canton || ''} onChange={e => update('canton', e.target.value)} /></Field>
        <Field label="Distrito"><input maxLength={80} value={form.distrito || ''} onChange={e => update('distrito', e.target.value)} /></Field>
        <Field label="Estado"><select value={form.activo ? '1' : '0'} onChange={e => update('activo', e.target.value === '1')}><option value="1">Activo</option><option value="0">Inactivo</option></select></Field>
        <Field label="Dirección exacta" wide><textarea maxLength={500} value={form.direccion_exacta || ''} onChange={e => update('direccion_exacta', e.target.value)} /></Field>
      </div>{error && <p className="ops-error" role="alert">{error}</p>}<div className="ops-actions"><button className="primary-action" type="submit">Guardar usuario</button><button type="button" className="ops-secondary" onClick={() => setForm(null)}>Cancelar</button></div></form>
    </section>}
    <div className="ops-toolbar"><span>{users.length} usuarios</span><input aria-label="Buscar usuarios" placeholder="Buscar usuario…" value={query} onChange={e => setQuery(e.target.value)} /></div>
    {removalError && <p className="ops-error" role="alert">{removalError}</p>}
    <div className="surface table-scroll">
      <table>
        <thead><tr><th>Nombre</th><th>Correo</th><th>Teléfono</th><th>Rol</th><th>Estado</th><th>Acciones</th></tr></thead>
        <tbody>{users.map(user => <tr key={user.id}>
          <td>{nameOf(user)}</td><td>{user.correo}</td><td>{user.telefono || '—'}</td>
          <td>{user.rol === 'ADMIN' ? 'Administrador' : 'Cliente'}</td>
          <td><span className={user.activo ? 'status' : 'status ops-status-inactive'}>{user.activo ? 'Activo' : 'Inactivo'}</span></td>
          <td className="ops-user-actions">
            <button type="button" className="ops-link" onClick={() => edit(user)}>Editar</button>
            <button type="button" className="ops-link ops-link-danger"
              disabled={removing !== null || user.id === currentUser.id}
              onClick={() => remove(user)}>Eliminar</button>
          </td>
        </tr>)}</tbody>
      </table>
      {!users.length && <p className="empty-state">No se encontraron usuarios.</p>}
    </div>
  </>;
}

