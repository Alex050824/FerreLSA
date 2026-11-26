import React, { useEffect, useState } from 'react';
import { api } from '../../api.js';
import './power-bi-report.css';

export default function PowerBIReport({ token }) {
  const [report, setReport] = useState({ pending: true, url: '', message: '' });

  useEffect(() => {
    const controller = new AbortController();
    api('/admin/reportes/power-bi', { token, signal: controller.signal })
      .then(config => {
        if (controller.signal.aborted) return;
        setReport(config.configured
          ? { pending: false, url: config.url, message: '' }
          : { pending: false, url: '', message: config.invalid
            ? 'La URL configurada no es un enlace de inserción válido de Power BI.'
            : 'El informe de Power BI todavía no está configurado. Definí POWER_BI_REPORT_URL en el archivo .env de la raíz y reiniciá el sistema.' });
      })
      .catch(error => {
        if (controller.signal.aborted) return;
        setReport({ pending: false, url: '', message: error.message });
      });
    return () => controller.abort();
  }, [token]);

  return <section className="power-bi-page" aria-labelledby="power-bi-title">
    <header className="page-heading">
      <div>
        <h1 id="power-bi-title">Estadísticas y reportes</h1>
        <p>Explorá los indicadores interactivos de FerreLSA.</p>
      </div>
    </header>
    {report.pending
      ? <p className="power-bi-message" role="status">Cargando el informe…</p>
      : report.url
        ? <div className="power-bi-frame-wrap">
          <iframe className="power-bi-frame" src={report.url} title="Informe de Power BI" allowFullScreen />
        </div>
        : <div className="power-bi-message" role="status"><strong>Informe no disponible</strong><p>{report.message}</p></div>}
  </section>;
}
