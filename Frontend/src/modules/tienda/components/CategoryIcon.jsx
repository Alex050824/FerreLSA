import React from 'react';

const drawings = {
  general: <><rect x="3.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="3.5" width="7" height="7" rx="1.5" /><rect x="3.5" y="13.5" width="7" height="7" rx="1.5" /><rect x="13.5" y="13.5" width="7" height="7" rx="1.5" /></>,
  tools: <><path d="m14.2 4.1 2.1-2.1 5.7 5.7-2.1 2.1-2-1.2-2.4 2.4-3-3 2.4-2.4zM12.5 8l3.5 3.5-8.6 8.6a2.5 2.5 0 0 1-3.5-3.5z" /><path d="m5.5 18.5.1-.1" /></>,
  adhesives: <><path d="M8 8V6h8v2l1.5 2v9a2 2 0 0 1-2 2h-7a2 2 0 0 1-2-2v-9zM10 6V4h4v2M11 4l1-2 1 2" /><path d="M7 11h10M9.5 15h5M9.5 17.5h3" /></>,
  paint: <><rect x="3" y="3" width="14" height="6" rx="1.5" /><path d="M17 5h2a2 2 0 0 1 2 2v3a2 2 0 0 1-2 2h-7v2M10 14h4v6a2 2 0 0 1-4 0z" /></>,
  building: <><rect x="3" y="4" width="18" height="16" rx="1" /><path d="M3 9.5h18M3 14.5h18M9 4v5.5M16 9.5v5M9 14.5V20" /></>,
  electricity: <><rect x="5" y="3" width="14" height="18" rx="2.5" /><path d="M9 8v2M15 8v2M10 15a2 2 0 0 1 4 0v1h-4z" /></>,
  hardware: <><path d="M14.6 4.1a5 5 0 0 0-6.2 6.5l-4.6 4.6a2.6 2.6 0 0 0 3.7 3.7l4.6-4.6a5 5 0 0 0 6.5-6.2l-3.1 3.1-3-3z" /><circle cx="5.7" cy="17.3" r=".5" /></>,
  plumbing: <><path d="M3 8h8V6h4v2h2a3 3 0 0 1 3 3v1M3 12h8v2h4v-2h2v2M18 14h4v3h-4zM7 8V5M5 5h4" /><path d="M20 19v1" /></>,
  lighting: <><path d="M8.5 16a6 6 0 1 1 7 0c-.7.5-1 1.1-1 2h-5c0-.9-.3-1.5-1-2ZM9.5 20h5M11 22h2" /><path d="M12 7v4M10 9h4" /></>,
  outdoors: <><path d="M12 3a9 9 0 0 0-9 7h18a9 9 0 0 0-9-7ZM12 3v17M8 21h8M6 10c.7-4 2.8-7 6-7s5.3 3 6 7" /></>,
  garden: <><path d="M12 14V9M12 11C8 11 5 9 5 5c4 0 7 2 7 6ZM12 9c0-3.5 2.4-5.5 6-5.5 0 3.8-2.3 6-6 6Z" /><path d="M6 14h12l-1.2 6H7.2zM5 14h14" /></>,
  bath: <><path d="M3 13h18v2a5 5 0 0 1-5 5H8a5 5 0 0 1-5-5zM6 20v1.5M18 20v1.5M6 13V6a3 3 0 0 1 6 0v1" /><path d="M10 7h4M11 10h.01M13.5 10h.01" /></>,
  kitchen: <><path d="M3 12h18v2a6 6 0 0 1-6 6H9a6 6 0 0 1-6-6zM7 12V7a4 4 0 0 1 8 0v1M13 8h4M17 8v2" /><path d="M6 21h12" /></>,
  floors: <><rect x="3" y="3" width="18" height="18" rx="1" /><path d="M12 3v18M3 12h18" /><path d="m5.5 8 2-2M14.5 18l2-2" /></>,
  automotive: <><path d="m5 10 1.4-4.2A2 2 0 0 1 8.3 4.5h7.4a2 2 0 0 1 1.9 1.3L19 10M4 10h16l1 2v5H3v-5zM5 17v2h2v-2M17 17v2h2v-2" /><path d="M6 13h2M16 13h2M9.5 15h5" /></>,
  cleaning: <><path d="M10 6V4h5l2 2-2 2h-5M10 7 7 9v2M8 10h8l2 3v6a2 2 0 0 1-2 2H8a2 2 0 0 1-2-2v-6z" /><path d="M9 15h6M9 18h4M18 5h2M19 8h2" /></>,
  furniture: <><rect x="4" y="3" width="16" height="17" rx="1" /><path d="M4 9h16M4 15h16M12 3v6M12 15v5M6 20v1.5M18 20v1.5" /><path d="M7 6h2M15 18h2" /></>,
  security: <><path d="M12 3 20 6v5c0 4.5-2.8 7.7-8 10-5.2-2.3-8-5.5-8-10V6z" /><path d="m8.8 11.8 2.1 2.1 4.5-4.5" /></>,
};

const categories = [
  ['adhesives', ['adhesivo', 'sellador', 'silicona', 'pegamento']],
  ['building', ['construccion', 'materiales de construccion', 'obra']],
  ['electricity', ['electricidad', 'electrico', 'electrica', 'cable', 'iluminacion electrica']],
  ['hardware', ['ferreteria general', 'ferreteria']], ['tools', ['herramienta', 'taladro', 'herramientas']],
  ['garden', ['jardineria', 'jardin', 'riego', 'plantas']], ['paint', ['pintura', 'pinturas', 'rodillo']],
  ['plumbing', ['plomeria', 'fontaneria', 'tuberia', 'griferia']],
  ['security', ['seguridad', 'cerradura', 'candado', 'proteccion']],
  ['lighting', ['lampara', 'lámpara', 'iluminacion', 'iluminación']], ['outdoors', ['exterior', 'jardin', 'jardín']],
  ['bath', ['baño', 'bano', 'sanitario']], ['kitchen', ['cocina']],
  ['floors', ['piso', 'ceramica', 'cerámica']], ['automotive', ['automotriz', 'auto', 'vehiculo', 'vehículo']],
  ['cleaning', ['limpieza']], ['furniture', ['mueble', 'organizacion', 'organización']],
];

export default function CategoryIcon({ name = '' }) {
  const normalized = String(name).normalize('NFD').replace(/[\u0300-\u036f]/g, '').toLocaleLowerCase();
  const match = name === 'general' ? ['general'] : categories.find(([, terms]) => terms.some(term => normalized.includes(term.normalize('NFD').replace(/[\u0300-\u036f]/g, ''))));
  return <svg className="store-category-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.45" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{drawings[match?.[0] || 'general']}</svg>;
}
