import React from 'react';
import ProductImage from './ProductImage.jsx';
import { money } from '../utils.js';

export default function Catalogo({ shown, query, setQuery, category, setCategory, categories, active, navigate, categoryName, addToCart }) {
  return <>
        <section className="store-hero"><div><span className="store-eyebrow">FERRELSA · TIENDA EN LÍNEA</span><h1>Todo para tu próximo proyecto<span>.</span></h1><p>Explorá nuestros materiales y herramientas desde un solo lugar.</p></div><div className="store-hero-mark" aria-hidden="true">✳</div></section>
        <div className="store-section-title"><div><span className="store-eyebrow">ENCONTRÁ LO QUE NECESITÁS</span><h2>Nuestros productos</h2></div><span>{shown.length} {shown.length === 1 ? 'producto' : 'productos'}</span></div>
        <div className="store-filters"><label><span className="store-sr-only">Buscar productos</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar producto o código..." /></label><label><span className="store-sr-only">Categoría</span><select value={category} onChange={event => setCategory(event.target.value)}><option value="">Todas las categorías</option>{categories.filter(active).map(item => <option key={item.id} value={String(item.id)}>{item.nombre}</option>)}</select></label></div>
        {shown.length ? <div className="store-grid">{shown.map(product => <article className="store-card" key={product.id}>
          <button className="store-card-image" onClick={() => navigate('detalle', product.id)} aria-label={`Ver ${product.nombre}`}><ProductImage key={product.imagen_url || 'none'} product={product} /></button>
          <div className="store-card-body"><span className="store-product-category">{categoryName(product.categoria_id)}</span><button className="store-product-name" onClick={() => navigate('detalle', product.id)}>{product.nombre}</button><p>{product.descripcion || 'Consultá los detalles de este producto.'}</p><strong className="store-price">{money(product.precio_venta)}</strong><span className={`store-stock ${Number(product.existencia) <= 0 ? 'is-empty' : ''}`}>{Number(product.existencia) > 0 ? `${product.existencia} ${product.unidad_medida || 'unidad'} disponibles` : 'Agotado'}</span><button className="store-button" disabled={Number(product.existencia) <= 0} onClick={() => addToCart(product)}>Agregar al carrito</button></div>
        </article>)}</div> : <div className="store-empty">No encontramos productos con esos filtros.</div>}
      </>;
}
