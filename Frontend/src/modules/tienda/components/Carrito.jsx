import React from 'react';
import { money, amount } from '../utils.js';

export default function Carrito({ cart, cartLines, navigate, setCart, updateQuantity, subtotal }) {
  return <><div className="store-page-heading"><span className="store-eyebrow">TU SELECCIÓN</span><h1>Carrito de compras</h1><p>Revisá los productos antes de continuar.</p></div>
        {!cart.length ? <div className="store-empty">Tu carrito está vacío.<br /><button className="store-button" onClick={() => navigate('catalogo')}>Explorar productos</button></div> : <div className="store-checkout-layout"><div className="store-cart-list">{cartLines.map(line => {
          const available = Math.floor(Number(line.product?.existencia) || 0);
          return <article className="store-cart-line" key={line.productId}><div><strong>{line.product?.nombre || 'Producto no disponible'}</strong><small>{money(line.product?.precio_venta)} / {line.product?.unidad_medida || 'unidad'}</small>{available < 1 && <small>Sin unidades disponibles</small>}<button className="store-link store-remove" onClick={() => setCart(previous => previous.filter(item => item.productId !== line.productId))}>Quitar</button></div><label>Cantidad<input aria-label={`Cantidad de ${line.product?.nombre || 'producto'}`} type="number" min="1" max={Math.max(1, available)} step="1" disabled={available < 1} value={line.quantity} onChange={event => updateQuantity(line.productId, event.target.value)} /></label><strong>{money(amount(Number(line.product?.precio_venta || 0) * (Number(line.quantity) || 0)))}</strong></article>;
        })}</div><aside className="store-summary"><h2>Resumen</h2><div><span>Subtotal</span><strong>{money(subtotal)}</strong></div><p>Los impuestos y costos de envío se confirmarán al integrar el sistema.</p><button className="store-button" onClick={() => navigate('checkout')}>Continuar al checkout</button><button className="store-link" onClick={() => navigate('catalogo')}>Seguir comprando</button></aside></div>}
      </>;
}
