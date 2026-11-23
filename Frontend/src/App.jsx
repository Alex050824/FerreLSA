import React, { useState } from 'react';
import Login from './modules/acceso/Login.jsx';
import Workspace from './layouts/Workspace.jsx';
import Store from './modules/tienda/Store.jsx';
import { initialData } from './data/demoData.js';

export default function App() {
  const [screen, setScreen] = useState('login');
  const [storeReturn, setStoreReturn] = useState('login');
  // El estado es compartido entre vistas y dura mientras la aplicación esté abierta.
  const [data, setData] = useState(() => structuredClone(initialData));
  const openStore = from => { setStoreReturn(from); setScreen('store'); };
  if (screen === 'store') return <Store data={data} setData={setData} onBack={() => setScreen(storeReturn)} backLabel={storeReturn === 'admin' ? 'Volver al panel' : 'Volver al inicio'} />;
  if (screen === 'admin') return <Workspace data={data} setData={setData} onLogout={() => setScreen('login')} onStore={() => openStore('admin')} />;
  return <Login onPreview={() => setScreen('admin')} onStore={() => openStore('login')} onAuthenticated={() => setScreen('admin')} />;
}
