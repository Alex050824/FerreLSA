import React, { useEffect, useState } from 'react';
import { api } from '../../../api.js';
import ProductImage from './ProductImage.jsx';
import { money, stockDescription } from '../utils.js';

function commentName(person) {
  return `${person?.nombre || ''} ${person?.apellido || ''}`.trim() || 'Cliente';
}

function CommentAvatar({ person }) {
  const initials = commentName(person).split(/\s+/).slice(0, 2).map(part => Array.from(part)[0]).join('').toLocaleUpperCase('es');
  return <span className="store-comment-avatar" aria-hidden="true">{initials}</span>;
}

export default function DetalleProducto({ selected, token, customer, verifyingSession, onLogin, navigate, categoryName, active, addToCart }) {
  const [comments, setComments] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [comment, setComment] = useState('');
  const [sending, setSending] = useState(false);
  const [submitError, setSubmitError] = useState('');
  const [notice, setNotice] = useState('');
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

  async function submitComment(event) {
    event.preventDefault();
    const trimmed = comment.trim();
    if (!trimmed) {
      setSubmitError('Escribí un comentario antes de publicarlo.');
      return;
    }
    setSending(true);
    setSubmitError('');
    setNotice('');
    try {
      await api(`/productos/${productId}/comentarios`, { token, method: 'POST', body: { comentario: trimmed } });
      setComment('');
      setNotice('Tu comentario se publicó correctamente.');
      try {
        const updated = await api(`/productos/${productId}/comentarios`, { token });
        setComments(updated);
        setError('');
      } catch {
        setError('Tu comentario se guardó, pero no se pudo actualizar la lista. Recargá la página para verlo.');
      }
    } catch (error) {
      setSubmitError(error.message);
    } finally {
      setSending(false);
    }
  }

  return (selected ? <>
    <button className="store-link" onClick={() => navigate('catalogo')}>← Volver al catálogo</button>
    <section className="store-detail"><ProductImage key={selected.imagen_url || 'none'} product={selected} /><div><span className="store-product-category">{categoryName(selected.categoria_id)} · {selected.codigo}</span><h1>{selected.nombre}</h1><p>{selected.descripcion || 'Sin descripción disponible.'}</p><strong className="store-price store-price-large">{money(selected.precio_venta)}</strong><p className="store-stock">{Number(selected.existencia) >= 1 ? stockDescription(selected) : 'Sin unidades disponibles'}</p><button className="store-button" disabled={!active(selected) || Number(selected.existencia) < 1} onClick={() => addToCart(selected)}>Agregar al carrito</button></div></section>
    <section className="store-comments" aria-labelledby="product-comments-title">
      <div className="store-comments-heading">
        <div><h2 id="product-comments-title">Comentarios del producto</h2><p>Compartí tu experiencia con otros clientes.</p></div>
        {!loading && !error && <span className="store-comments-count">{comments.length} {comments.length === 1 ? 'comentario' : 'comentarios'}</span>}
      </div>
      {customer?.rol === 'CLIENTE' ? <form className="store-comment-form" onSubmit={submitComment}>
        <CommentAvatar person={customer} />
        <div className="store-comment-compose">
          <label className="store-sr-only" htmlFor="product-comment">Compartí tu opinión sobre este producto</label>
          <textarea id="product-comment" placeholder="Escribí un comentario sobre este producto…" value={comment} onChange={event => setComment(event.target.value)} maxLength={1000} required disabled={sending} />
          <div className="store-comment-actions"><span>{comment.length}/1000 caracteres</span><button className="store-button" type="submit" disabled={sending || loading || !comment.trim()}>{sending ? 'Publicando…' : 'Publicar comentario'}</button></div>
          {submitError && <p className="store-comment-feedback is-error" role="alert">{submitError}</p>}
          {notice && <p className="store-comment-feedback is-success" role="status">{notice}</p>}
        </div>
      </form> : verifyingSession ? <p className="store-comment-prompt" role="status">Estamos verificando tu sesión…</p> : !customer ? <p className="store-comment-prompt">¿Querés compartir tu experiencia? <button className="store-link" type="button" onClick={onLogin}>Iniciá sesión para comentar</button>.</p> : <p className="store-comment-prompt">Los comentarios están disponibles para clientes.</p>}
      {error && <p className="store-comment-feedback is-error" role="alert">{error}</p>}
      <div className="store-comment-list">
        {loading ? <p className="store-muted" role="status">Cargando comentarios…</p> : comments.length ? comments.map(item => <article className="store-comment" key={item.id}>
          <CommentAvatar person={item} />
          <div className="store-comment-content"><div className="store-comment-bubble"><strong>{commentName(item)}</strong><p>{item.comentario}</p></div>{item.fecha && <time dateTime={item.fecha}>{new Date(item.fecha).toLocaleDateString('es-CR', { day: 'numeric', month: 'short', year: 'numeric' })}</time>}</div>
        </article>) : !error && <p className="store-comment-empty">Todavía no hay comentarios. ¡Sé la primera persona en compartir su experiencia!</p>}
      </div>
    </section>
  </> : <div className="store-empty">Producto no disponible. <button className="store-link" onClick={() => navigate('catalogo')}>Volver al catálogo</button></div>);
}
