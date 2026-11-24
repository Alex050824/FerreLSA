import React from 'react';
import './AdminCatalogShared.css';

export const money = value => new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC' }).format(Number(value) || 0);
export const nextId = list => Math.max(0, ...list.map(item => Number(item.id) || 0)) + 1;
export const find = (list, id) => list.find(item => String(item.id) === String(id));
export const numeric = value => Number(value) || 0;
export const today = () => new Date().toISOString().slice(0, 10);

export function Field({ label, children }) { return <label className="ac-field"><span>{label}</span>{children}</label>; }
export function PageHeading({ title, description, action, onAction }) { return <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line" />GESTIÓN COMERCIAL</div><h1>{title}<span className="orange-dot">.</span></h1><p>{description}</p></div>{action && <button type="button" className="primary-action" onClick={onAction}>＋ {action}</button>}</div>; }
export function Modal({ title, children, onClose }) { return <div className="ac-overlay" onMouseDown={e => { if (e.target === e.currentTarget) onClose(); }}><section className="ac-modal" role="dialog" aria-modal="true" aria-label={title}><header><h2>{title}</h2><button type="button" className="ac-close" aria-label="Cerrar" onClick={onClose}>×</button></header>{children}</section></div>; }
export function Input({ form, setForm, name, ...props }) { return <input {...props} value={form[name] ?? ''} onChange={e => setForm({ ...form, [name]: e.target.value })} />; }
export function Search({ value, onChange, label }) { return <div className="module-summary"><div className="search-box"><input aria-label={label} placeholder={label} value={value} onChange={e => onChange(e.target.value)} /></div></div>; }
export function Table({ headers, children, empty }) { return <section className="surface module-table"><div className="table-scroll"><table><thead><tr>{headers.map(x => <th key={x}>{x}</th>)}</tr></thead><tbody>{children}</tbody></table></div>{empty && <p className="empty-state">No hay registros para mostrar.</p>}</section>; }

