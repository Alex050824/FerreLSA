import React from 'react';
export default function Brand({
  onClick
}) {
  return <button className="brand" onClick={onClick} aria-label="FerreLSA, ir al panel principal">
    <span className="brand__symbol">
      <img src="/assets/emblema-ferrelsa.png" alt="" />
    </span>
    <span className="brand__identity">
      <strong>Ferre<span>LSA</span>
      </strong>
      <small>SISTEMA DE GESTIÓN EMPRESARIAL</small>
    </span>
  </button>;
}
