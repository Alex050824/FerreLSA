import './sentiments.css';
import React, { useMemo, useState } from 'react';
import DropdownSelect from '../../components/DropdownSelect.jsx';
import { Header, nameOf, label, date } from '../operaciones/OperationsShared.jsx';

export default function Sentiments({ data }) {
  const [filter, setFilter] = useState('TODOS');
  const [query, setQuery] = useState('');
  const comments = useMemo(() => data.comentarios.filter(c => {
    const product = data.productos.find(p => p.id === c.producto_id);
    const user = data.usuarios.find(u => u.id === c.usuario_id);
    return (filter === 'TODOS' || c.sentimiento === filter) && `${product?.nombre || ''} ${nameOf(user)} ${c.comentario}`.toLowerCase().includes(query.toLowerCase());
  }), [data, filter, query]);
  return <><Header title="Sentimientos" description="Revisá los comentarios de productos y su clasificación." /><div className="ops-toolbar"><span>{comments.length} comentarios</span><div className="ops-filter"><DropdownSelect aria-label="Filtrar por sentimiento" value={filter} onChange={e => setFilter(e.target.value)}><option value="TODOS">Todos los sentimientos</option><option value="POSITIVO">Positivo</option><option value="NEUTRAL">Neutral</option><option value="NEGATIVO">Negativo</option></DropdownSelect><input aria-label="Buscar comentarios" placeholder="Buscar comentario…" value={query} onChange={e => setQuery(e.target.value)} /></div></div><div className="surface table-scroll"><table><thead><tr><th>Producto</th><th>Cliente</th><th>Comentario</th><th>Fecha</th><th>Sentimiento</th></tr></thead><tbody>{comments.map(c => <tr key={c.id}><td>{data.productos.find(p => p.id === c.producto_id)?.nombre || 'Producto'}</td><td>{nameOf(data.usuarios.find(u => u.id === c.usuario_id))}</td><td className="ops-comment">{c.comentario}</td><td>{date(c.fecha)}</td><td><span className={`ops-sentiment ops-sentiment--${String(c.sentimiento).toLowerCase()}`}>{label(c.sentimiento)}</span></td></tr>)}</tbody></table>{!comments.length && <p className="empty-state">No hay comentarios para mostrar.</p>}</div></>;
}

