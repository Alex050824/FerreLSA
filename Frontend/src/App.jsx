import React, { useEffect, useState } from 'react';
import Login from './modules/acceso/Login.jsx';
import Workspace from './layouts/Workspace.jsx';
import Store from './modules/tienda/Store.jsx';
import { api, readSession } from './api.js';

const storePages = new Map([
  ['catalogo', 'catalogo'], ['carrito', 'carrito'], ['checkout', 'checkout'], ['pedidos', 'historial'],
]);
const emptyData = { productos: [], categorias: [], proveedores: [], movimientos: [], compras: [], ventas: [], usuarios: [], comentarios: [] };

export default function App() {
  const [path, setPath] = useState(() => window.location.pathname);
  const [session, setSession] = useState(readSession);
  const [verified, setVerified] = useState(null);
  const [validationError, setValidationError] = useState('');
  const [snapshot, setSnapshot] = useState(null);
  const [load, setLoad] = useState({ pending: true, error: '' });
  const [revision, setRevision] = useState(0);
  const route = path.replace(/\/$/, '');
  const adminRoute = route === '/admin' || route.startsWith('/admin/');
  const storeRoute = route === '/tienda' || route.startsWith('/tienda/');
  const accessArea = adminRoute ? 'admin' : storeRoute ? 'store' : null;
  const token = session?.token;
  const currentUser = token && verified?.token === token && verified.area === accessArea ? verified.user : null;
  const admin = adminRoute && currentUser?.rol === 'ADMIN';
  const store = storeRoute && ['ADMIN', 'CLIENTE'].includes(currentUser?.rol);

  useEffect(() => {
    if (!accessArea) {
      setVerified(null);
      return;
    }
    function redirect(destination) {
      window.history.replaceState(null, '', destination);
      setPath(destination);
    }
    if (!token) {
      redirect('/login');
      return;
    }
    const controller = new AbortController();
    setValidationError('');
    api('/usuarios/me', { token, signal: controller.signal }).then(user => {
      if (controller.signal.aborted) return;
      if (!['ADMIN', 'CLIENTE'].includes(user.rol)) {
        sessionStorage.removeItem('ferrelsa.session');
        setSession(null);
        redirect('/login');
        return;
      }
      if (accessArea === 'admin' && user.rol !== 'ADMIN') {
        redirect('/tienda');
        return;
      }
      setVerified({ token, area: accessArea, user });
    }).catch(error => {
      if (controller.signal.aborted) return;
      if (error.status === 401) {
        sessionStorage.removeItem('ferrelsa.session');
        setSession(null);
        redirect('/login');
      } else {
        setValidationError('No se pudo verificar tu sesión. Recargá la página para volver a intentar.');
      }
    });
    return () => controller.abort();
  }, [accessArea, token]);

  useEffect(() => {
    if (!admin && !store) return;
    const controller = new AbortController();
    const options = { token: session?.token, signal: controller.signal };
    const read = path => api(path, options);
    setLoad({ pending: true, error: '' });
    async function loadData() {
      const paths = admin
        ? { productos: '/admin/productos', categorias: '/admin/categorias', proveedores: '/admin/proveedores',
            movimientos: '/inventario/movimientos', compras: '/compras', ventas: '/ventas', usuarios: '/usuarios',
            comentarios: '/admin/comentarios' }
        : { productos: '/productos', categorias: '/categorias', ...(session && { ventas: '/ventas' }) };
      const entries = await Promise.all(Object.entries(paths).map(async ([key, path]) => [key, await read(path)]));
      const next = { ...emptyData, ...Object.fromEntries(entries) };
      if (admin) {
        const [purchases, localSales] = await Promise.all([
          Promise.all(next.compras.map(row => read('/compras/' + row.id))),
          Promise.all(next.ventas.filter(row => row.canal === 'LOCAL').map(row => read('/ventas/' + row.id))),
        ]);
        const details = new Map(localSales.map(row => [row.id, row]));
        next.compras = purchases;
        next.ventas = next.ventas.map(row => details.get(row.id) ?? row);
      } else if (session) {
        next.ventas = await Promise.all(next.ventas.map(row => read('/ventas/' + row.id)));
      }
      if (!controller.signal.aborted) {
        setSnapshot({ admin, session, data: next });
        setLoad({ pending: false, error: '' });
      }
    }
    loadData().catch(error => {
      if (controller.signal.aborted) return;
      setSnapshot(null);
      setLoad({ pending: false, error: error.message });
      if (error.status === 401 || (admin && error.status === 403)) {
        sessionStorage.removeItem('ferrelsa.session');
        setSession(null);
      }
    });
    return () => controller.abort();
  }, [admin, store, session, revision]);

  useEffect(() => {
    const syncPath = () => setPath(window.location.pathname);
    window.addEventListener('popstate', syncPath);
    return () => window.removeEventListener('popstate', syncPath);
  }, []);

  function navigate(destination, { replace = false, state = null } = {}) {
    if (destination === window.location.pathname && !replace) return;
    const method = replace ? 'replaceState' : 'pushState';
    window.history[method](state, '', destination);
    setPath(destination);
  }

  async function mutate(path, body, method = 'POST') {
    const result = await api(path, { method, body, token: session.token });
    setRevision(value => value + 1);
    return result;
  }

  function logout() {
    if (token) api('/auth/logout', { method: 'POST', token }).catch(() => {});
    sessionStorage.removeItem('ferrelsa.session');
    setSession(null);
    setVerified(null);
    setSnapshot(null);
    navigate('/login', { replace: true });
  }

  const data = snapshot?.admin === admin && snapshot.session === session ? snapshot.data : emptyData;
  const feedback = load.pending ? 'Cargando datos…' : load.error;
  if (accessArea && !admin && !store) {
    return <main className="container"><p role="status">{validationError || 'Verificando acceso…'}</p></main>;
  }
  if (store) {
    const chatOpen = route.endsWith('/chat');
    const storePath = chatOpen ? route.slice(0, -'/chat'.length) : route;
    const productId = /^\/tienda\/productos\/([\w-]+)$/.exec(storePath)?.[1];
    const section = /^\/tienda\/([^/]+)$/.exec(storePath)?.[1];
    const page = productId ? 'detalle' : storePath === '/tienda' ? 'catalogo' : storePages.get(section);
    const adminReturn = window.history.state?.adminReturn;
    const goToStore = destination => navigate(destination, { state: { adminReturn } });
    if (page) {
      return <Store data={data} customer={currentUser} feedback={feedback} page={page}
        selectedId={productId} onLogout={logout}
        onNavigate={(next, id) => {
          const destination = next === 'detalle' ? '/tienda/productos/' + encodeURIComponent(id)
            : next === 'historial' ? '/tienda/pedidos'
            : next === 'catalogo' ? '/tienda' : '/tienda/' + next;
          goToStore(destination + (chatOpen ? '/chat' : ''));
        }}
        chatOpen={chatOpen} onChatToggle={() => goToStore(chatOpen ? storePath : storePath + '/chat')}
        onBack={currentUser.rol === 'ADMIN' && adminReturn ? () => navigate(adminReturn) : undefined} />;
    }
  }
  const adminPage = route === '/admin' ? 'inicio' : /^\/admin\/([^/]+)$/.exec(route)?.[1];
  if (adminPage && admin) {
    return <Workspace data={data} mutate={mutate} page={adminPage} user={verified.user} feedback={feedback}
      onNavigate={page => navigate(page === 'inicio' ? '/admin' : '/admin/' + page)}
      onLogout={logout}
      onStore={() => navigate('/tienda', { state: { adminReturn: route } })} />;
  }
  if (route && route !== '/login' && !adminRoute) {
    return <main className="container">
      <h1>Página no encontrada</h1>
      <button type="button" onClick={() => navigate('/login')}>Volver al inicio</button>
    </main>;
  }
  return <Login onAuthenticated={next => {
    sessionStorage.setItem('ferrelsa.session', JSON.stringify(next));
    setSession(next);
    navigate(next.usuario.rol === 'ADMIN' ? '/admin' : '/tienda');
  }} />;
}
