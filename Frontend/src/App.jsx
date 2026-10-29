import React, { useState } from 'react';
import Login from './pages/Login.jsx';
import Workspace from './layouts/Workspace.jsx';
export default function App() {
  const [preview, setPreview] = useState(false);
  return preview ? <Workspace onLogout={() => setPreview(false)} /> : <Login onPreview={() => setPreview(true)} />;
}
