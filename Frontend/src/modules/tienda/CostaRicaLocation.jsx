import React, { useEffect, useState } from 'react';
import DropdownSelect from '../../components/DropdownSelect.jsx';

const API = 'https://ubicaciones-cr.ryze-cr.workers.dev';
const PROVINCES = ['San José', 'Alajuela', 'Cartago', 'Heredia', 'Guanacaste', 'Puntarenas', 'Limón'];

function normalize(payload, keys) {
  const source = keys.map(key => payload?.[key]).find(value => value != null) ?? payload;
  if (Array.isArray(source)) return source.map((item, index) => ({
    id: String(item?.id ?? item?.codigo ?? item?.codigo_postal ?? index + 1),
    name: String(typeof item === 'string' ? item : item?.nombre ?? item?.name ?? item?.title ?? item?.distrito ?? item?.canton ?? item?.provincia ?? ''),
  })).filter(item => item.name);
  if (source && typeof source === 'object') return Object.entries(source).map(([id, value]) => ({
    id: String(id),
    name: String(typeof value === 'string' ? value : value?.nombre ?? value?.name ?? value?.title ?? ''),
  })).filter(item => item.name);
  return [];
}

async function getOptions(path, keys, cacheKey) {
  try {
    const response = await fetch(`${API}${path}`);
    if (!response.ok) throw new Error('No se pudo cargar el catálogo de ubicaciones.');
    const payload = await response.json();
    try { localStorage.setItem(cacheKey, JSON.stringify(payload)); } catch { /* almacenamiento opcional */ }
    return normalize(payload, keys);
  } catch (error) {
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) return normalize(JSON.parse(cached), keys);
    } catch { /* almacenamiento opcional */ }
    throw error;
  }
}

function LocationSelect({ label, value, options, placeholder, disabled, onChange, loading, fieldClass }) {
  const selectedExists = options.some(option => option.name === value);
  return <label className={fieldClass}>
    <span>{label}</span>
    <DropdownSelect value={value || ''} disabled={disabled || loading} onChange={event => onChange(event.target.value)}>
      <option value="">{loading ? 'Cargando…' : placeholder}</option>
      {value && !selectedExists && <option value={value}>{value}</option>}
      {options.map(option => <option key={option.id} value={option.name}>{option.name}</option>)}
    </DropdownSelect>
  </label>;
}

export default function CostaRicaLocation({ form, setForm, fieldClass = 'store-profile-field' }) {
  const [provinceOptions, setProvinceOptions] = useState(PROVINCES.map((name, index) => ({ id: String(index + 1), name })));
  const [cantonOptions, setCantonOptions] = useState([]);
  const [districtOptions, setDistrictOptions] = useState([]);
  const [loading, setLoading] = useState({ provinces: false, cantons: false, districts: false });
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    setLoading(current => ({ ...current, provinces: true }));
    getOptions('/provincias.json', ['provincias', 'data'], 'ferrelsa.cr.provincias')
      .then(options => { if (!cancelled && options.length) setProvinceOptions(options); })
      .catch(() => { if (!cancelled) setError('No se pudieron actualizar las provincias. Se muestran las guardadas en la aplicación.'); })
      .finally(() => { if (!cancelled) setLoading(current => ({ ...current, provinces: false })); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    const province = provinceOptions.find(option => option.name === form.provincia);
    setCantonOptions([]);
    setDistrictOptions([]);
    if (!province) return;
    let cancelled = false;
    setLoading(current => ({ ...current, cantons: true }));
    setError('');
    getOptions(`/provincia/${province.id}/cantones.json`, ['cantones', 'data'], `ferrelsa.cr.cantones.${province.id}`)
      .then(options => { if (!cancelled) setCantonOptions(options); })
      .catch(() => { if (!cancelled) setError('No se pudieron cargar los cantones. Revisá tu conexión e intentá de nuevo.'); })
      .finally(() => { if (!cancelled) setLoading(current => ({ ...current, cantons: false })); });
    return () => { cancelled = true; };
  }, [form.provincia, provinceOptions]);

  useEffect(() => {
    const province = provinceOptions.find(option => option.name === form.provincia);
    const canton = cantonOptions.find(option => option.name === form.canton);
    setDistrictOptions([]);
    if (!province || !canton) return;
    let cancelled = false;
    setLoading(current => ({ ...current, districts: true }));
    getOptions(`/provincia/${province.id}/canton/${canton.id}/distritos.json`, ['distritos', 'data'], `ferrelsa.cr.distritos.${province.id}.${canton.id}`)
      .then(options => { if (!cancelled) setDistrictOptions(options); })
      .catch(() => { if (!cancelled) setError('No se pudieron cargar los distritos. Revisá tu conexión e intentá de nuevo.'); })
      .finally(() => { if (!cancelled) setLoading(current => ({ ...current, districts: false })); });
    return () => { cancelled = true; };
  }, [form.provincia, form.canton, provinceOptions, cantonOptions]);

  const update = (key, value, reset = []) => setForm(previous => ({ ...previous, [key]: value, ...Object.fromEntries(reset.map(field => [field, ''])) }));
  return <>
    <LocationSelect fieldClass={fieldClass} label="Provincia" value={form.provincia} options={provinceOptions} loading={loading.provinces}
      placeholder="Seleccioná una provincia" onChange={value => update('provincia', value, ['canton', 'distrito'])} />
    <LocationSelect fieldClass={fieldClass} label="Cantón" value={form.canton} options={cantonOptions} loading={loading.cantons}
      disabled={!form.provincia} placeholder="Seleccioná un cantón" onChange={value => update('canton', value, ['distrito'])} />
    <LocationSelect fieldClass={fieldClass} label="Distrito" value={form.distrito} options={districtOptions} loading={loading.districts}
      disabled={!form.canton} placeholder="Seleccioná un distrito" onChange={value => update('distrito', value)} />
    {error && <p className={fieldClass === 'ops-field' ? 'ops-error ops-field--wide' : 'store-profile-location-error'} role="status">{error}</p>}
  </>;
}
