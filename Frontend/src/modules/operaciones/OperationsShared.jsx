import React from 'react';
import './operations.css';

export const money = value => new Intl.NumberFormat('es-CR', { style: 'currency', currency: 'CRC' }).format(Number(value) || 0);
export const roundMoney = value => Math.round((Number(value) + Number.EPSILON) * 100) / 100;
export const roundQuantity = value => Math.round(Number(value) * 1000) / 1000;
export const nameOf = user => user ? [user.nombre, user.apellido].filter(Boolean).join(' ') : 'Cliente ocasional';
export const nextId = list => Math.max(0, ...list.map(item => Number(item.id) || 0)) + 1;
export const label = value => String(value || '').replaceAll('_', ' ').toLowerCase();
export const date = value => value ? new Date(value).toLocaleString('es-CR', { dateStyle: 'medium', timeStyle: 'short' }) : '—';

export function Field({ label: title, children, wide }) {
  return <label className={`ops-field ${wide ? 'ops-field--wide' : ''}`}><span>{title}</span>{children}</label>;
}

export function Header({ title, description, action, onAction }) {
  return <div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line" /> GESTIÓN COMERCIAL</div><h1>{title}<span className="orange-dot">.</span></h1><p>{description}</p></div>{action && <button className="primary-action" type="button" onClick={onAction}><span>＋</span>{action}</button>}</div>;
}

