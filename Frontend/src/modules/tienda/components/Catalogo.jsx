import React, { useRef } from 'react';
import ProductImage from './ProductImage.jsx';
import CategoryIcon from './CategoryIcon.jsx';
import { stockDescription } from '../utils.js';
import { money } from '../utils.js';

export default function Catalogo({ shown, category, setCategory, categories, active, navigate, categoryName, addToCart, query }) {
  const categoriesRef = useRef(null);
  const moveCategories = direction => categoriesRef.current?.scrollBy({ left: direction * categoriesRef.current.clientWidth * 0.8, behavior: 'smooth' });
  return <>
        {!query && <>
        <section className="store-home-hero" aria-label="Descubrí FerreLSA">
          <article className="store-home-feature store-home-feature--main">
            <img src="/assets/store-home/Imagen1.png" alt="Taller de hogar con herramientas y materiales para renovar" fetchPriority="high" />
            <div className="store-home-feature__copy">
              <span className="store-home-eyebrow">FERRELSA · TODO PARA TU PROYECTO</span>
              <h1>Renová tu<br />hogar.</h1>
              <p>Las herramientas y materiales para convertir tus ideas en realidad.</p>
            </div>
          </article>
          <div className="store-home-feature-stack">
            <article className="store-home-feature store-home-feature--delivery">
              <img src="/assets/store-home/Imagen2.png" alt="Entrega de materiales para proyectos del hogar" loading="lazy" />
              <div className="store-home-feature__copy">
                <span className="store-home-eyebrow">A TU RITMO</span>
                <h2>Tu próximo<br />proyecto empieza aquí.</h2>
              </div>
            </article>
            <article className="store-home-feature store-home-feature--tools">
              <img src="/assets/store-home/Imagen3.png" alt="Ilustración de herramientas, pintura y artículos de ferretería" loading="lazy" />
              <div className="store-home-feature__copy">
                <span className="store-home-eyebrow">IDEAS QUE TOMAN FORMA</span>
                <h2>Manos a la obra.</h2>
              </div>
            </article>
          </div>
        </section>
        </>}
        {categories.filter(active).length > 0 && <section className="store-category-section" aria-labelledby="store-categories-title">
          <div className="store-category-heading"><h2 id="store-categories-title">Explorá por categoría</h2><div className="store-category-controls"><button type="button" aria-label="Desplazar categorías a la izquierda" onClick={() => moveCategories(-1)}>&#8249;</button><button type="button" aria-label="Desplazar categorías a la derecha" onClick={() => moveCategories(1)}>&#8250;</button></div></div>
          <div className="store-category-grid" ref={categoriesRef}>
            <button type="button" className={`store-category ${!category ? 'is-selected' : ''}`} aria-pressed={!category} onClick={() => setCategory('')}>
              <CategoryIcon name="general" /><span>Todas</span><i aria-hidden="true">›</i>
            </button>
            {categories.filter(active).map(item => <button type="button" className={`store-category ${String(category) === String(item.id ?? item.categoria_id) ? 'is-selected' : ''}`} aria-pressed={String(category) === String(item.id ?? item.categoria_id)} key={item.id ?? item.categoria_id} onClick={() => setCategory(String(item.id ?? item.categoria_id))}>
              <CategoryIcon name={item.nombre} /><span>{item.nombre}</span><i aria-hidden="true">›</i>
            </button>)}
          </div>
        </section>}
        <div className="store-section-title catalog-results-heading" id="store-products"><div><h2>Nuestros productos{category ? ` · ${categoryName(category)}` : ''}</h2></div><span>{shown.length} {shown.length === 1 ? 'producto' : 'productos'}</span></div>
        {shown.length ? <div className="store-grid">{shown.map(product => <article className="store-card" key={product.id}>
          <button className="store-card-image" onClick={() => navigate('detalle', product.id)} aria-label={`Ver ${product.nombre}`}><ProductImage key={product.imagen_url || 'none'} product={product} /></button>
          <div className="store-card-body"><span className="store-product-category">{categoryName(product.categoria_id)}</span><button className="store-product-name" onClick={() => navigate('detalle', product.id)}>{product.nombre}</button><p>{product.descripcion || 'Consultá los detalles de este producto.'}</p><strong className="store-price">{money(product.precio_venta)}</strong><span className={`store-stock ${Number(product.existencia) < 1 ? 'is-empty' : ''}`}>{Number(product.existencia) >= 1 ? stockDescription(product) : 'Sin unidades disponibles'}</span><button className="store-button" disabled={Number(product.existencia) < 1} onClick={() => addToCart(product)}>Agregar al carrito</button></div>
        </article>)}</div> : <div className="store-empty">No encontramos productos con esos filtros.</div>}
      </>;
}
