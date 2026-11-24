import React, { useMemo, useState } from 'react';
import './Store.css';
import { quantity, amount } from './utils.js';
import Catalogo from './components/Catalogo.jsx';
import DetalleProducto from './components/DetalleProducto.jsx';
import Carrito from './components/Carrito.jsx';
import Checkout from './components/Checkout.jsx';
import Historial from './components/Historial.jsx';
import Chat from './components/Chat.jsx';


export default function Store({ data, customer, feedback, onLogout, page, selectedId, onNavigate, chatOpen, onChatToggle, onBack }) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [cart, setCart] = useState([]);
  const [notice, setNotice] = useState('');
  const products = data.productos || [];
  const categories = data.categorias || [];
  const active = item => item.activo !== false && item.activo !== 0;
  const categoryName = categoryId => categories.find(item => String(item.id) === String(categoryId))?.nombre || 'General';
  const shown = useMemo(() => products.filter(product => active(product) && (!category || String(product.categoria_id) === category) && `${product.nombre} ${product.codigo} ${product.descripcion || ''}`.toLocaleLowerCase('es').includes(query.trim().toLocaleLowerCase('es'))), [products, category, query]);
  const selected = products.find(product => String(product.id) === String(selectedId));
  const cartLines = cart.map(line => ({ ...line, product: products.find(product => String(product.id) === String(line.productId)) }));
  const subtotal = amount(cartLines.reduce((sum, line) => sum + amount(Number(line.product?.precio_venta || 0) * (Number(line.quantity) || 0)), 0));
  const itemCount = quantity(cart.reduce((sum, line) => sum + (Number(line.quantity) || 0), 0));
  const customerSales = (data.ventas || []).filter(sale => sale.canal === 'EN_LINEA' && customer && String(sale.usuario_id) === String(customer.id));

  function navigate(next, productId) {
    onNavigate(next, productId);
    setComment('');
    setNotice('');
    window.scrollTo(0, 0);
  }
  function addToCart(product) {
    const stock = Number(product.existencia) || 0;
    if (stock <= 0) { setNotice('Este producto no tiene existencias disponibles.'); return; }
    const increment = Math.min(1, stock);
    const current = Number(cart.find(item => item.productId === product.id)?.quantity) || 0;
    if (current + increment > stock + 0.00001) { setNotice('La cantidad en el carrito ya alcanza la existencia disponible.'); return; }
    setCart(previous => current ? previous.map(item => item.productId === product.id ? { ...item, quantity: quantity(Number(item.quantity) + increment) } : item) : [...previous, { productId: product.id, quantity: increment }]);
    setNotice(`${product.nombre} se agregó al carrito.`);
  }
  function updateQuantity(productId, value) {
    setCart(previous => previous.map(line => line.productId === productId ? { ...line, quantity: value } : line));
  }
  function normalizeQuantity(productId, value) {
    const product = products.find(item => item.id === productId);
    const n = Number(value);
    setCart(previous => previous.map(line => line.productId === productId ? { ...line, quantity: quantity(Math.min(Math.max(Number.isFinite(n) ? n : 0.001, 0.001), Number(product?.existencia) || 0.001)) } : line));
  }
  return <div className="store">
    <header className="store-header">
      <button className="store-brand" onClick={() => navigate('catalogo')} aria-label="FerreLSA, ir al catálogo"><img src="/assets/emblema-ferrelsa.png" alt="" /><span>Ferre<strong>LSA</strong><small>TIENDA EN LÍNEA</small></span></button>
      <nav className="store-nav" aria-label="Navegación de la tienda">
        <button className={page === 'catalogo' || page === 'detalle' ? 'is-active' : ''} onClick={() => navigate('catalogo')}>Catálogo</button>
        <button className={page === 'historial' ? 'is-active' : ''} onClick={() => navigate('historial')}>Mis pedidos</button>
        <button className={page === 'carrito' || page === 'checkout' ? 'is-active' : ''} onClick={() => navigate('carrito')}>Carrito <span className="store-count">{itemCount}</span></button>
        {customer && <button onClick={onLogout}>Cerrar sesión</button>}
        {onBack && <button className="store-back" onClick={onBack}>Volver al panel</button>}
      </nav>
    </header>
    <main className="store-main">
      {feedback && <p role="status">{feedback}</p>}
      {notice && <div className="store-notice" role="status">{notice}<button aria-label="Cerrar aviso" onClick={() => setNotice('')}>×</button></div>}
      {page === 'catalogo' && <Catalogo shown={shown} query={query} setQuery={setQuery} category={category} setCategory={setCategory} categories={categories} active={active} navigate={navigate} categoryName={categoryName} addToCart={addToCart} />}
      {page === 'detalle' && <DetalleProducto selected={selected} navigate={navigate} categoryName={categoryName} active={active} addToCart={addToCart} />}
      {page === 'carrito' && <Carrito cart={cart} cartLines={cartLines} navigate={navigate} setCart={setCart} updateQuantity={updateQuantity} normalizeQuantity={normalizeQuantity} subtotal={subtotal} />}
      {page === 'checkout' && <Checkout navigate={navigate} cart={cart} />}
      {page === 'historial' && <Historial customer={customer} customerSales={customerSales} products={products} navigate={navigate} />}
    </main>
    <footer className="store-footer">FerreLSA</footer>
    <Chat chatOpen={chatOpen} onToggle={onChatToggle} />
  </div>;
}
