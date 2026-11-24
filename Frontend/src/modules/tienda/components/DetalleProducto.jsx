import React from 'react';
import ProductImage from './ProductImage.jsx';
import { money } from '../utils.js';

export default function DetalleProducto({ selected, navigate, categoryName, active, addToCart }) {
  return (selected ? <>
        <button className="store-link" onClick={() => navigate('catalogo')}>← Volver al catálogo</button>
        <section className="store-detail"><ProductImage key={selected.imagen_url || 'none'} product={selected} /><div><span className="store-product-category">{categoryName(selected.categoria_id)} · {selected.codigo}</span><h1>{selected.nombre}</h1><p>{selected.descripcion || 'Sin descripción disponible.'}</p><strong className="store-price store-price-large">{money(selected.precio_venta)}</strong><p className="store-stock">{Number(selected.existencia) > 0 ? `${selected.existencia} ${selected.unidad_medida || 'unidad'} disponibles` : 'Agotado'}</p><button className="store-button" disabled={!active(selected) || Number(selected.existencia) <= 0} onClick={() => addToCart(selected)}>Agregar al carrito</button></div></section>
        <section className="store-comments"><h2>Comentarios del producto</h2><p>Compartí tu experiencia con este producto.</p><form onSubmit={submitComment}><label htmlFor="store-comment">Tu comentario</label><textarea id="store-comment" value={comment} maxLength={2000} onChange={event => setComment(event.target.value)} placeholder="Escribí tu comentario..." required /><button className="store-button" type="submit">Publicar comentario</button></form>
          {(data.comentarios || []).filter(item => String(item.producto_id) === String(selected.id)).length ? (data.comentarios || []).filter(item => String(item.producto_id) === String(selected.id)).map(item => <article className="store-comment" key={item.id}><strong>{customerName(users.find(user => String(user.id) === String(item.usuario_id)))}</strong><time>{item.fecha ? new Date(item.fecha).toLocaleDateString('es-CR') : ''}</time><p>{item.comentario}</p></article>) : <p className="store-muted">Todavía no hay comentarios para este producto.</p>}
        </section>
      </> : <div className="store-empty">Producto no disponible. <button className="store-link" onClick={() => navigate('catalogo')}>Volver al catálogo</button></div>);
}
