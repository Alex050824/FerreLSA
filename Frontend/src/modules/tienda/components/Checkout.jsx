import React from 'react';

export default function Checkout({ navigate, cart }) {
  return <>
    <button className="store-link" onClick={() => navigate('carrito')}>← Volver al carrito</button>
    <div className="store-page-heading"><h1>Finalizar pedido</h1></div>
    <p className="store-empty">{cart.length ? 'El pago en línea aún no está disponible.' : 'Tu carrito está vacío.'}</p>
  </>;
}
