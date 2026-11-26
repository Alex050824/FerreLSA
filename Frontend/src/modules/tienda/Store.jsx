import React, { useEffect, useMemo, useRef, useState } from 'react';
import Icon from '../../components/Icon.jsx';
import './Store.css';
import { quantity, amount } from './utils.js';
import Catalogo from './components/Catalogo.jsx';
import DetalleProducto from './components/DetalleProducto.jsx';
import Carrito from './components/Carrito.jsx';
import Checkout from './components/Checkout.jsx';
import Historial from './components/Historial.jsx';
import Chat from './components/Chat.jsx';
import Profile from './Profile.jsx';

function LoginRequiredDialog({ onClose, onLogin }) {
  const dialogRef = useRef(null);

  useEffect(() => {
    const dialog = dialogRef.current;
    dialog.showModal();
    return () => { if (dialog.open) dialog.close(); };
  }, []);

  return <dialog ref={dialogRef} className="store-login-dialog" aria-modal="true" aria-labelledby="store-login-title"
    aria-describedby="store-login-description" onCancel={event => { event.preventDefault(); onClose(); }}>
    <h2 id="store-login-title">Iniciá sesión</h2>
    <p id="store-login-description">Necesitás iniciar sesión para agregar productos al carrito.</p>
    <div className="store-login-dialog__actions">
      <button className="store-login-dialog__cancel" type="button" onClick={onClose} autoFocus>Seguir explorando</button>
      <button className="store-button" type="button" onClick={onLogin}>Iniciar sesión</button>
    </div>
  </dialog>;
}


export default function Store({ data, customer, token, verifyingSession, feedback, cart, setCart, onLogin, onLogout, onSaveProfile, page, selectedId, onNavigate, chatOpen, onChatToggle, onBack, onPaid }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [notice, setNotice] = useState('');
  const [loginRequired, setLoginRequired] = useState(false);
  const products = data.productos || [];
  const categories = data.categorias || [];
  const active = item => item.activo !== false && item.activo !== 0;
  const categoryName = categoryId => categories.find(item => String(item.id ?? item.categoria_id) === String(categoryId))?.nombre || 'General';
  const normalizeCategory = value => String(value || '').normalize('NFD').replace(/[\u0300-\u036f]/g, '').trim().toLocaleLowerCase('es');
  const shown = useMemo(() => products.filter(product => {
    if (!active(product)) return false;
    if (category) {
      const selectedCategory = categories.find(item => String(item.id ?? item.categoria_id) === String(category));
      const productCategoryId = product.categoria_id ?? product.category_id ?? product.categoria?.id ?? product.category?.id;
      const productCategoryName = typeof product.categoria === 'string' ? product.categoria : product.categoria?.nombre ?? product.category?.name ?? product.categoria_nombre ?? product.category_name;
      const categoryMatches = String(productCategoryId ?? '') === String(category) ||
        Boolean(selectedCategory?.nombre && productCategoryName && normalizeCategory(productCategoryName) === normalizeCategory(selectedCategory.nombre));
      if (!categoryMatches) return false;
    }
    return `${product.nombre} ${product.codigo} ${product.descripcion || ''}`.toLocaleLowerCase('es').includes(query.trim().toLocaleLowerCase('es'));
  }), [products, categories, category, query]);
  const selected = products.find(product => String(product.id) === String(selectedId));
  const cartLines = cart.map(line => ({ ...line, product: products.find(product => String(product.id) === String(line.productId)) }));
  const subtotal = amount(cartLines.reduce((sum, line) => sum + amount(Number(line.product?.precio_venta || 0) * (Number(line.quantity) || 0)), 0));
  const itemCount = quantity(cart.reduce((sum, line) => sum + (Number(line.quantity) || 0), 0));
  const customerSales = (data.ventas || []).filter(sale => sale.canal === 'EN_LINEA' && customer && String(sale.usuario_id) === String(customer.id));

  useEffect(() => {
    setCart(previous => {
      let changed = false;
      const next = previous.map(line => {
        const product = products.find(item => String(item.id) === String(line.productId));
        const max = Math.floor(Number(product?.existencia) || 0);
        const value = Math.max(1, Math.floor(Number(line.quantity) || 1));
        const quantity = max >= 1 ? Math.min(value, max) : value;
        if (quantity === line.quantity) return line;
        changed = true;
        return { ...line, quantity };
      });
      return changed ? next : previous;
    });
  }, [products]);

  function navigate(next, productId) {
    onNavigate(next, productId);
    setNotice('');
    window.scrollTo(0, 0);
  }
  function requireCustomer() {
    if (customer) return true;
    if (verifyingSession) setNotice('Estamos verificando tu sesión. Intentá de nuevo en un momento.');
    else setLoginRequired(true);
    return false;
  }
  function addToCart(product) {
    if (!requireCustomer()) return;
    const stock = Number(product.existencia) || 0;
    if (stock < 1) { setNotice('Este producto no tiene una unidad disponible.'); return; }
    const current = Number(cart.find(item => item.productId === product.id)?.quantity) || 0;
    if (current + 1 > stock) { setNotice('La cantidad en el carrito ya alcanza la existencia disponible.'); return; }
    setCart(previous => current ? previous.map(item => item.productId === product.id ? { ...item, quantity: Number(item.quantity) + 1 } : item) : [...previous, { productId: product.id, quantity: 1 }]);
    setNotice(`${product.nombre} se agregó al carrito.`);
  }
  function updateQuantity(productId, value) {
    const product = products.find(item => String(item.id) === String(productId));
    const max = Math.floor(Number(product?.existencia) || 0);
    const n = Number(value);
    const next = Math.min(Math.max(1, max), Math.max(1, Number.isFinite(n) ? Math.floor(n) : 1));
    const current = cart.find(line => line.productId === productId);
    if (current && next > Number(current.quantity) && !requireCustomer()) return;
    setCart(previous => previous.map(line => line.productId === productId ? { ...line, quantity: next } : line));
  }
  return <div className={`store store--${page}`}>
    <header className="store-header store-header--reworked">
      <div className="store-header-main"><button className="store-brand" onClick={() => navigate('catalogo')} aria-label="FerreLSA, ir al catálogo"><img src="/assets/emblema-ferrelsa.png" alt="" /><span>Ferre<strong>LSA</strong><small>TIENDA EN LÍNEA</small></span></button>
        {page === 'catalogo' && <label className="store-search"><span className="store-sr-only">Buscar productos</span><input type="search" value={query} onChange={event => setQuery(event.target.value)} placeholder="Buscar por producto o c&#243;digo" /><span aria-hidden="true" /></label>}
      <nav className="store-nav store-nav--header" aria-label="Navegación de la tienda">
        <button className={page === 'catalogo' || page === 'detalle' ? 'is-active' : ''} onClick={() => navigate('catalogo')}>Catálogo</button>
        <button className={page === 'historial' ? 'is-active' : ''} onClick={() => navigate('historial')}>Mis pedidos</button>
        <button className={`store-cart-action ${page === 'carrito' || page === 'checkout' ? 'is-active' : ''}`} onClick={() => navigate('carrito')} aria-label={`Carrito, ${itemCount} artículos`} title="Carrito"><Icon name="cart" size={22} /><span className="store-sr-only">Carrito</span><span className="store-count">{itemCount}</span></button>
        {customer ? <>
          <button className={`store-profile-action ${page === 'perfil' ? 'is-active' : ''}`} onClick={() => navigate('perfil')} aria-label="Mi perfil" title="Mi perfil"><Icon name="user" size={20} /><span>Perfil</span></button>
          <button className="store-logout-action" onClick={onLogout} aria-label="Cerrar sesión" title="Cerrar sesión"><Icon name="logout" size={20} /><span className="store-sr-only">Cerrar sesión</span></button>
        </> : <button onClick={onLogin}>Iniciar sesión</button>}
        {onBack && <button className="store-back" onClick={onBack}><Icon name="arrow" size={17} /><span>Volver al panel</span></button>}
      </nav>
      </div>
    </header>
    <main className={`store-main store-main--${page}`}>
      {feedback && <p role="status">{feedback}</p>}
      {notice && <div className="store-notice" role="status">{notice}<button aria-label="Cerrar aviso" onClick={() => setNotice('')}>×</button></div>}
      {!feedback && <>
        {page === 'catalogo' && <Catalogo shown={shown} category={category} setCategory={setCategory} categories={categories} active={active} navigate={navigate} categoryName={categoryName} addToCart={addToCart} query={query} />}
        {page === 'detalle' && <DetalleProducto key={selectedId} selected={selected} token={token} customer={customer} verifyingSession={verifyingSession} onLogin={onLogin} navigate={navigate} categoryName={categoryName} active={active} addToCart={addToCart} />}
        {page === 'carrito' && <Carrito cart={cart} cartLines={cartLines} navigate={navigate} setCart={setCart} updateQuantity={updateQuantity} subtotal={subtotal} />}
        {page === 'checkout' && (
 <Checkout
    navigate={navigate}
    cart={cart}
    cartLines={cartLines}
    token={token}
    setCart={setCart}
    subtotal={subtotal}
    onPaid={onPaid}
  />
)}
        {page === 'historial' && <Historial customer={customer} customerSales={customerSales} products={products} navigate={navigate} onLogin={onLogin} />}
        {page === 'perfil' && <Profile customer={customer} onSave={onSaveProfile} onLogin={onLogin} />}
      </>}
    </main>
    <footer className="store-footer"><div className="store-footer-brand"><img src="/assets/emblema-ferrelsa.png" alt="" /><strong>Ferre<span>LSA</span></strong></div><span>Tienda en l&#237;nea</span></footer>
    <Chat key={customer?.id ?? 'invitado'} chatOpen={chatOpen} onToggle={onChatToggle} />
    {loginRequired && <LoginRequiredDialog onClose={() => setLoginRequired(false)} onLogin={onLogin} />}
  </div>;
}
