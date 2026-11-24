import React, { useEffect, useState } from 'react';
import { api } from '../../../api.js';
import ProductImage from './ProductImage.jsx';
import { money, stockDescription } from '../utils.js';

export default function DetalleProducto({ selected, token, navigate, categoryName, active, addToCart }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const productId = selected?.id;

  useEffect(() => {
    setComments([]);
    setError('');
    if (!productId) return;
    const controller = new AbortController();
    setLoading(true);
    api(`/productos/${productId}/comentarios`, { token, signal: controller.signal })
      .then(setComments)
      .catch(error => { if (!controller.signal.aborted) setError(error.message); })
      .finally(() => { if (!controller.signal.aborted) setLoading(false); });
    return () => controller.abort();
  }, [productId, token]);

  return (selected ? <>
    <button className="store-link" onClick={() => navigate('catalogo')}>← Volver al catálogo</button>
    <section className="store-detail"><ProductImage key={selected.imagen_url || 'none'} product={selected} /><div><span className="store-product-category">{categoryName(selected.categoria_id)} · {selected.codigo}</span><h1>{selected.nombre}</h1><p>{selected.descripcion || 'Sin descripción disponible.'}</p><strong className="store-price store-price-large">{money(selected.precio_venta)}</strong><p className="store-stock">{Number(selected.existencia) >= 1 ? stockDescription(selected) : 'Sin unidades disponibles'}</p><button className="store-button" disabled={!active(selected) || Number(selected.existencia) < 1} onClick={() => addToCart(selected)}>Agregar al carrito</button></div></section>
    <section className="store-comments"><h2>Comentarios del producto</h2><p>La publicación de comentarios aún no está disponible.</p>
      {error && <p role="alert">{error}</p>}
      {loading ? <p role="status">Cargando comentarios…</p> : comments.length ? comments.map(item => <article className="store-comment" key={item.id}><strong>{`${item.nombre || ''} ${item.apellido || ''}`.trim() || 'Cliente'}</strong><time>{item.fecha ? new Date(item.fecha).toLocaleDateString('es-CR') : ''}</time><p>{item.comentario}</p></article>) : !error && <p className="store-muted">Todavía no hay comentarios para este producto.</p>}
    </section>
  </> : <div className="store-empty">Producto no disponible. <button className="store-link" onClick={() => navigate('catalogo')}>Volver al catálogo</button></div>);
}
