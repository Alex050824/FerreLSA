import React, { useMemo, useState } from 'react';
import Icon from '../components/Icon.jsx';
import DataTable from '../components/DataTable.jsx';
import { config, rows } from '../modules/index.js';
export default function ModulePage({
  page,
  onAction
}) {
  const {
    title,
    desc,
    action,
    columns
  } = config[page];
  const [query, setQuery] = useState('');
  const data = useMemo(() => rows[page].filter(row => row.join(' ').toLowerCase().includes(query.toLowerCase())), [page, query]);
  return <>
    <div className="page-heading">
      <div>
        <div className="eyebrow">
          <span className="eyebrow__line" /> GESTIÓN COMERCIAL</div>
        <h1>
          {title}
          <span className="orange-dot">.</span>
        </h1>
        <p>
          {desc}
        </p>
      </div>
      <button className="primary-action" onClick={() => onAction(action)}>
        <span>＋</span>
        {action}
      </button>
    </div>
    <div className="module-summary">
      <div>
        <strong>
          {data.length}
        </strong>
        <span>registros encontrados</span>
      </div>
      <div className="search-box">
        <Icon name="search" size={18} />
        <input placeholder={`Buscar en ${title.toLowerCase()}…`} value={query} onChange={e => setQuery(e.target.value)} />
      </div>
    </div>
    <section className="surface module-table">
      <DataTable columns={columns} data={data} />
      {data.length === 0 && <p className="empty-state">No se encontraron registros con esa búsqueda.</p>}
      <div className="table-foot">Mostrando {data.length} de {rows[page].length} registros <span></span>
      </div>
    </section>
  </>;
}
