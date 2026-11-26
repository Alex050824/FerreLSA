import React, { useEffect, useState } from 'react';
import CostaRicaLocation from './CostaRicaLocation.jsx';

const fields = [
  ['nombre', 'Nombre', true], ['apellido', 'Apellido'],
  ['correo', 'Correo electrónico', true], ['identificacion', 'Identificación'],
  ['telefono', 'Teléfono'],
];
const profileKeys = [...fields.map(([key]) => key), 'provincia', 'canton', 'distrito', 'direccion_exacta'];

export default function Profile({ customer, onSave, onLogin }) {
  const [form, setForm] = useState({});
  const [password, setPassword] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);

  useEffect(() => {
    setForm(Object.fromEntries(profileKeys.map(key => [key, customer?.[key] || ''])));
  }, [customer]);

  async function submit(event) {
    event.preventDefault();
    setMessage('');
    setError('');
    setSaving(true);
    try {
      await onSave({ ...form, ...(password ? { password } : {}) });
      setPassword('');
      setMessage('Tus datos se guardaron correctamente.');
    } catch (err) {
      setError(err.message || 'No se pudieron guardar los cambios.');
    } finally {
      setSaving(false);
    }
  }

  return <section className="store-profile-page">
    <div className="store-page-heading">
      <span className="store-eyebrow">TU CUENTA</span>
      <h1>Mi perfil</h1>
      <p>Actualizá tus datos de contacto y acceso.</p>
    </div>
    {customer ? <form className="store-profile-form" onSubmit={submit}>
      <div className="store-profile-grid">
        {fields.map(([key, label, required]) => <label key={key}>
          <span>{label}{required ? ' *' : ''}</span>
          <input name={key} type={key === 'correo' ? 'email' : 'text'} value={form[key] || ''} required={required}
            maxLength={key === 'direccion_exacta' ? 500 : key === 'telefono' ? 30 : key === 'identificacion' ? 30 : 255}
            onChange={event => setForm(previous => ({ ...previous, [key]: event.target.value }))} />
        </label>)}
        <CostaRicaLocation form={form} setForm={setForm} />
        <label className="store-profile-grid__wide">
          <span>Dirección exacta</span>
          <input name="direccion_exacta" type="text" value={form.direccion_exacta || ''} maxLength={500}
            onChange={event => setForm(previous => ({ ...previous, direccion_exacta: event.target.value }))} />
        </label>
        <label className="store-profile-grid__wide">
          <span>Nueva contraseña <small>(opcional)</small></span>
          <input type="password" autoComplete="new-password" minLength="8" maxLength="128" value={password}
            placeholder="Dejá este campo vacío para mantenerla"
            onChange={event => setPassword(event.target.value)} />
        </label>
      </div>
      {message && <p className="store-profile-message" role="status">{message}</p>}
      {error && <p className="store-profile-error" role="alert">{error}</p>}
      <div className="store-profile-actions"><button className="store-button" type="submit" disabled={saving}>{saving ? 'Guardando…' : 'Guardar cambios'}</button></div>
    </form> : <section className="store-profile-guest"><p>Iniciá sesión para ver y actualizar tu perfil.</p><button className="store-button" type="button" onClick={onLogin}>Iniciar sesión</button></section>}
  </section>;
}
