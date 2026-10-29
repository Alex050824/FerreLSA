import React, { useMemo, useState } from 'react';
import Icon from './components/Icon.jsx';
import { signIn, AuthNotConfiguredError } from './services/auth.js';

const modules = [
  { id: 'inicio', label: 'Panel principal', icon: 'chart' },
  { id: 'ventas', label: 'Ventas', icon: 'cart' },
  { id: 'inventario', label: 'Inventario', icon: 'box' },
  { id: 'compras', label: 'Compras', icon: 'receipt' },
  { id: 'facturacion', label: 'Facturación', icon: 'receipt' },
  { id: 'clientes', label: 'Clientes', icon: 'user' },
  { id: 'proveedores', label: 'Proveedores', icon: 'building' },
  { id: 'administracion', label: 'Administración', icon: 'settings' },
];

const rows = {
  ventas: [
    ['V-1048', 'María Fernanda Rojas', 'Hoy, 10:42 a. m.', '₡184 500', 'Completada'],
    ['V-1047', 'Construcciones Vega', 'Hoy, 9:18 a. m.', '₡926 000', 'Pendiente'],
    ['V-1046', 'Carlos Jiménez', 'Ayer, 3:35 p. m.', '₡76 250', 'Completada'],
    ['V-1045', 'Obras del Valle S. A.', 'Ayer, 11:06 a. m.', '₡1 245 900', 'Completada'],
  ],
  inventario: [
    ['INV-001', 'Cemento gris 50 kg', 'Construcción', '24 sacos', 'Disponible'],
    ['INV-002', 'Tubo PVC 1/2 pulg.', 'Plomería', '8 unidades', 'Stock bajo'],
    ['INV-003', 'Cable THHN #12', 'Electricidad', '120 m', 'Disponible'],
    ['INV-004', 'Pintura blanca 1 galón', 'Pinturas', '0 unidades', 'Agotado'],
  ],
  compras: [
    ['OC-0231', 'Distribuidora El Constructor', 'Hoy, 8:30 a. m.', '₡540 000', 'En tránsito'],
    ['OC-0230', 'Materiales del Norte', 'Ayer, 2:15 p. m.', '₡318 750', 'Recibida'],
    ['OC-0229', 'Pinturas del Valle', '22 oct, 11:00 a. m.', '₡96 000', 'Pendiente'],
  ],
  facturacion: [
    ['FAC-2084', 'María Fernanda Rojas', 'Hoy, 10:43 a. m.', '₡184 500', 'Pagada'],
    ['FAC-2083', 'Construcciones Vega', 'Hoy, 9:19 a. m.', '₡926 000', 'Por cobrar'],
    ['FAC-2082', 'Carlos Jiménez', 'Ayer, 3:36 p. m.', '₡76 250', 'Pagada'],
  ],
  clientes: [
    ['CLI-0142', 'María Fernanda Rojas', 'maria.rojas@email.com', '8888-1200', 'Frecuente'],
    ['CLI-0141', 'Construcciones Vega', 'compras@construevega.cr', '2222-7400', 'Empresa'],
    ['CLI-0140', 'Carlos Jiménez', 'cjimenez@email.com', '8700-6652', 'Regular'],
    ['CLI-0139', 'Obras del Valle S. A.', 'contacto@obrasvalle.cr', '2255-1900', 'Empresa'],
  ],
  proveedores: [
    ['PRO-0038', 'Distribuidora El Constructor', 'ventas@constructor.cr', '2222-1100', 'Activo'],
    ['PRO-0037', 'Materiales del Norte', 'pedidos@matnorte.cr', '2233-4500', 'Activo'],
    ['PRO-0036', 'Pinturas del Valle', 'info@pinturasvalle.cr', '2444-2000', 'Activo'],
  ],
  administracion: [
    ['USR-001', 'Administrador del sistema', 'admin@ferrelsa.cr', 'Administrador', 'Activo'],
    ['USR-002', 'Andrea Vargas', 'andrea@ferrelsa.cr', 'Ventas', 'Activo'],
    ['USR-003', 'Luis Morales', 'luis@ferrelsa.cr', 'Inventario', 'Activo'],
  ],
};

const config = {
  ventas: { title: 'Ventas', desc: 'Consulta y seguimiento de las ventas del negocio.', action: 'Nueva venta', columns: ['N.º venta', 'Cliente', 'Fecha', 'Total', 'Estado'] },
  inventario: { title: 'Inventario', desc: 'Control de existencias y disponibilidad de productos.', action: 'Agregar producto', columns: ['Código', 'Producto', 'Categoría', 'Existencia', 'Estado'] },
  compras: { title: 'Compras', desc: 'Órdenes de compra y recepción de mercadería.', action: 'Nueva orden', columns: ['N.º orden', 'Proveedor', 'Fecha', 'Total', 'Estado'] },
  facturacion: { title: 'Facturación', desc: 'Facturas emitidas y estado de cobro.', action: 'Crear factura', columns: ['N.º factura', 'Cliente', 'Fecha', 'Total', 'Estado'] },
  clientes: { title: 'Clientes', desc: 'Directorio de clientes y sus datos de contacto.', action: 'Nuevo cliente', columns: ['Código', 'Nombre', 'Correo', 'Teléfono', 'Tipo'] },
  proveedores: { title: 'Proveedores', desc: 'Directorio de proveedores y contactos comerciales.', action: 'Nuevo proveedor', columns: ['Código', 'Proveedor', 'Correo', 'Teléfono', 'Estado'] },
  administracion: { title: 'Administración', desc: 'Usuarios y accesos del sistema.', action: 'Invitar usuario', columns: ['Código', 'Usuario', 'Correo', 'Rol', 'Estado'] },
};

function Brand({ onClick }) {
  return <button className="brand" onClick={onClick} aria-label="FerreLSA, ir al panel principal"><span className="brand__symbol"><img src="/assets/emblema-ferrelsa.png" alt="" /></span><span className="brand__identity"><strong>Ferre<span>LSA</span></strong><small>SISTEMA DE GESTIÓN EMPRESARIAL</small></span></button>;
}

function Login({ onPreview }) {
  const [username, setUsername] = useState(''); const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false); const [pending, setPending] = useState(false); const [feedback, setFeedback] = useState(null);
  async function handleSubmit(event) {
    event.preventDefault(); setFeedback(null);
    if (!username.trim() || !password) { setFeedback({ type: 'error', text: 'Ingresá tu usuario y contraseña para continuar.' }); return; }
    setPending(true);
    try { await signIn({ username: username.trim(), password }); setPassword(''); setFeedback({ type: 'success', text: 'Acceso validado. Configurá la ruta del panel para continuar.' }); }
    catch (error) { setFeedback({ type: error instanceof AuthNotConfiguredError ? 'info' : 'error', text: error.message || 'Ocurrió un problema al intentar ingresar.' }); }
    finally { setPending(false); }
  }
  return <><header className="site-header container"><Brand onClick={onPreview}/><div className="header-context"><Icon name="shield" size={16}/><span>Acceso exclusivo para personal autorizado</span></div></header><main className="container main-layout"><section className="login-panel"><div className="login-panel__inner"><div className="eyebrow"><span className="eyebrow__line"/> PORTAL INTERNO · FERRELSA ERP</div><h1>Iniciar sesión<span className="orange-dot">.</span></h1><p className="login-intro">Ingresá tus credenciales para acceder al sistema de gestión empresarial.</p><form className="login-form" onSubmit={handleSubmit} noValidate><div className="field"><label htmlFor="username">Usuario o correo electrónico</label><span className="field__input-wrap"><Icon name="user" size={19}/><input id="username" type="text" placeholder="Ingresá tu usuario" autoComplete="username" value={username} onChange={e=>setUsername(e.target.value)} disabled={pending}/></span></div><div className="field"><label htmlFor="password">Contraseña</label><span className="field__input-wrap"><Icon name="lock" size={19}/><input id="password" type={showPassword?'text':'password'} placeholder="Ingresá tu contraseña" autoComplete="current-password" value={password} onChange={e=>setPassword(e.target.value)} disabled={pending}/><button className="field__visibility" type="button" onClick={()=>setShowPassword(!showPassword)} aria-label={showPassword?'Ocultar contraseña':'Mostrar contraseña'}><Icon name={showPassword?'eyeOff':'eye'} size={20}/></button></span></div>{feedback&&<div className={`form-feedback form-feedback--${feedback.type}`} role="status">{feedback.text}</div>}<button className="submit-button" type="submit" disabled={pending}>{pending?'Verificando acceso…':'Ingresar al sistema'} <Icon name="arrow" size={20}/></button></form><div className="login-panel__help"><Icon name="shield" size={18}/><p><strong>¿Necesitás ayuda para ingresar?</strong><br/>Contactá al administrador del ERP para solicitar o recuperar tu acceso.</p></div><button className="preview-link" onClick={onPreview}>Explorar vista previa del sistema <Icon name="arrow" size={16}/></button></div></section><aside className="identity-panel"><div className="eyebrow"><span className="eyebrow__line"/> NUESTRA IDENTIDAD</div><h2>Lo que nos mueve<span className="orange-dot">.</span></h2><p>Principios que orientan a FerreLSA y su compromiso con una gestión más organizada.</p><article className="identity-card"><span className="identity-card__number">01 / PROPÓSITO</span><h3>Misión</h3><p>Ofrecer herramientas, materiales y suministros para la construcción, reparación y mantenimiento, mediante un servicio organizado y confiable.</p></article><article className="identity-card"><span className="identity-card__number">02 / FUTURO</span><h3>Visión</h3><p>Consolidarnos como una ferretería reconocida por acompañar los proyectos de nuestros clientes con una gestión moderna y eficiente.</p></article></aside></main><footer className="site-footer container"><span>© {new Date().getFullYear()} FerreLSA · Proyecto académico</span><span>Universidad de Costa Rica · Sistema ERP</span></footer></>;
}

function Dashboard({ navigate }) {
  const cards = [{label:'Ventas del mes',value:'₡8 420 500',delta:'+12,8%',icon:'chart',tone:'orange'},{label:'Productos activos',value:'1 284',delta:'En catálogo',icon:'box',tone:'blue'},{label:'Órdenes pendientes',value:'8',delta:'Requieren atención',icon:'receipt',tone:'violet'},{label:'Clientes registrados',value:'342',delta:'+18 este mes',icon:'user',tone:'green'}];
  return <><div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line"/> RESUMEN DEL NEGOCIO</div><h1>Buenos días, equipo<span className="orange-dot">.</span></h1><p>Este es el resumen de actividad de FerreLSA.</p></div><span className="date-chip">Miércoles, 28 de octubre</span></div><div className="stat-grid">{cards.map(c=><article className="stat-card" key={c.label}><span className={`stat-icon ${c.tone}`}><Icon name={c.icon} size={20}/></span><span className="stat-label">{c.label}</span><strong>{c.value}</strong><small>{c.delta}</small></article>)}</div><div className="dashboard-grid"><section className="surface chart-panel"><div className="surface-heading"><div><h2>Actividad de ventas</h2><p>Resumen semanal ilustrativo</p></div><span className="period-select">Esta semana⌄</span></div><div className="chart-area"><div className="chart-y"><span>₡1,2 M</span><span>₡900 mil</span><span>₡600 mil</span><span>₡300 mil</span><span>₡0</span></div><div className="chart-content"><div className="chart-gridlines"><i/><i/><i/><i/><i/></div><div className="bars">{[['Lun',55],['Mar',76],['Mié',62],['Jue',88],['Vie',70],['Sáb',96],['Dom',42]].map(([d,h])=><div className="bar-col" key={d}><span className="bar" style={{height:`${h}%`}}/><small>{d}</small></div>)}</div></div></div></section><section className="surface quick-panel"><div className="surface-heading"><div><h2>Accesos rápidos</h2><p>Ir directamente a un módulo</p></div></div><div className="quick-links">{modules.slice(1,5).map(m=><button key={m.id} onClick={()=>navigate(m.id)}><span><Icon name={m.icon} size={19}/></span>{m.label}<Icon name="arrow" size={16}/></button>)}</div></section></div><section className="surface recent-panel"><div className="surface-heading"><div><h2>Movimientos recientes</h2><p>Últimas operaciones registradas en el sistema</p></div><button className="text-button" onClick={()=>navigate('ventas')}>Ver todas <Icon name="arrow" size={16}/></button></div><DataTable columns={config.ventas.columns} data={rows.ventas.slice(0,3)}/></section></>;
}

function DataTable({ columns, data }) {
  return <div className="table-scroll"><table><thead><tr>{columns.map(c=><th key={c}>{c}</th>)}</tr></thead><tbody>{data.map((row,i)=><tr key={i}>{row.map((v,j)=><td key={j}>{j===row.length-1?<span className={`status status--${v.toLowerCase().replaceAll(' ','-')}`}>{v}</span>:v}</td>)}</tr>)}</tbody></table></div>;
}

function ModulePage({ page, onAction }) {
  const {title,desc,action,columns}=config[page]; const [query,setQuery]=useState('');
  const data=useMemo(()=>rows[page].filter(row=>row.join(' ').toLowerCase().includes(query.toLowerCase())),[page,query]);
  return <><div className="page-heading"><div><div className="eyebrow"><span className="eyebrow__line"/> GESTIÓN COMERCIAL</div><h1>{title}<span className="orange-dot">.</span></h1><p>{desc}</p></div><button className="primary-action" onClick={()=>onAction(action)}><span>＋</span>{action}</button></div><div className="module-summary"><div><strong>{data.length}</strong><span>registros encontrados</span></div><div className="search-box"><Icon name="search" size={18}/><input placeholder={`Buscar en ${title.toLowerCase()}…`} value={query} onChange={e=>setQuery(e.target.value)}/></div></div><section className="surface module-table"><DataTable columns={columns} data={data}/>{data.length===0&&<p className="empty-state">No se encontraron registros con esa búsqueda.</p>}<div className="table-foot">Mostrando {data.length} de {rows[page].length} registros <span>Vista de demostración · datos de ejemplo</span></div></section><p className="demo-note"><Icon name="info" size={16}/> Esta pantalla muestra información ficticia para la vista previa académica.</p></>;
}

function Workspace({ onLogout }) {
  const [page,setPage]=useState('inicio'); const [notice,setNotice]=useState('');
  const active=modules.find(m=>m.id===page);
  function action(label){setNotice(`${label}: esta acción estará disponible cuando se conecte el backend.`);window.setTimeout(()=>setNotice(''),3500);}
  return <div className="workspace"><aside className="sidebar"><Brand onClick={()=>setPage('inicio')}/><div className="nav-caption">ESPACIO DE TRABAJO</div><nav>{modules.map(m=><button key={m.id} className={`nav-item ${page===m.id?'active':''}`} onClick={()=>setPage(m.id)}><Icon name={m.icon} size={19}/><span>{m.label}</span>{m.id==='inventario'&&<i className="nav-badge">2</i>}</button>)}</nav><div className="sidebar-bottom"><div className="user-card"><span className="avatar">SA</span><span><strong>Shirley Araya</strong><small>Administradora</small></span><button aria-label="Cerrar sesión" title="Cerrar sesión" onClick={onLogout}><Icon name="logout" size={17}/></button></div><span className="demo-badge"><i/> MODO DEMOSTRACIÓN</span></div></aside><main className="work-main"><header className="work-topbar"><div className="breadcrumbs">FerreLSA <span>/</span> {active.label}</div><div className="topbar-right"><span className="today-label">28 oct 2026</span><button className="notification-button" aria-label="Notificaciones"><Icon name="bell" size={19}/><i/></button><span className="top-avatar">SA</span></div></header><div className="work-content">{page==='inicio'?<Dashboard navigate={setPage}/>:<ModulePage page={page} onAction={action}/>}</div></main>{notice&&<div className="toast"><Icon name="info" size={18}/>{notice}</div>}</div>;
}

export default function App() {
  const [preview,setPreview]=useState(false);
  return preview?<Workspace onLogout={()=>setPreview(false)}/>:<Login onPreview={()=>setPreview(true)}/>;
}
