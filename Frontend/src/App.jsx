import React, { useState } from 'react';
import Icon from './components/Icon.jsx';
import { signIn, AuthNotConfiguredError } from './services/auth.js';

function Brand() {
  return (
    <a className="brand" href="#acceso" aria-label="FerreLSA ERP, ir al inicio de sesión">
      <span className="brand__symbol"><img src="/assets/emblema-ferrelsa.png" alt="" /></span>
      <span className="brand__identity">
        <strong>Ferre<span>LSA</span></strong>
        <small>SISTEMA DE GESTIÓN EMPRESARIAL</small>
      </span>
    </a>
  );
}

function Header() {
  return (
    <header className="site-header">
      <div className="site-header__inner container">
        <Brand />
        <div className="header-context"><Icon name="shield" size={16} /><span>Acceso exclusivo para personal autorizado</span></div>
      </div>
    </header>
  );
}

function LoginForm() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState(null);

  async function handleSubmit(event) {
    event.preventDefault();
    setFeedback(null);
    if (!username.trim() || !password) {
      setFeedback({ type: 'error', text: 'Ingresá tu usuario y contraseña para continuar.' });
      return;
    }
    setPending(true);
    try {
      await signIn({ username: username.trim(), password });
      setPassword('');
      const nextPath = import.meta.env.VITE_AFTER_LOGIN_PATH?.trim();
      if (nextPath && nextPath.startsWith('/') && !nextPath.startsWith('//')) {
        window.location.assign(nextPath);
        return;
      }
      setFeedback({ type: 'success', text: 'Acceso validado. Para abrir el panel, configurá la ruta posterior al inicio de sesión.' });
    } catch (error) {
      setFeedback({
        type: error instanceof AuthNotConfiguredError ? 'info' : 'error',
        text: error.message || 'Ocurrió un problema al intentar ingresar.',
      });
    } finally {
      setPending(false);
    }
  }

  return (
    <section className="login-panel" id="acceso" aria-labelledby="login-heading">
      <div className="login-panel__inner">
        <div className="login-panel__heading">
          <div className="eyebrow"><span className="eyebrow__line"/> PORTAL INTERNO · FERRELSA ERP</div>
          <h1 id="login-heading">Iniciar sesión<span className="orange-dot">.</span></h1>
          <p>Ingresá tus credenciales para acceder al sistema de gestión empresarial.</p>
        </div>

        <form className="login-form" onSubmit={handleSubmit} noValidate>
          <div className="field">
            <label htmlFor="username">Usuario o correo electrónico</label>
            <span className="field__input-wrap">
              <Icon name="user" size={19}/>
              <input id="username" name="username" type="text" placeholder="Ingresá tu usuario"
                autoComplete="username" required value={username}
                onChange={(event) => setUsername(event.target.value)} disabled={pending} />
            </span>
          </div>
          <div className="field">
            <label htmlFor="password">Contraseña</label>
            <span className="field__input-wrap">
              <Icon name="lock" size={19}/>
              <input id="password" name="password" type={showPassword ? 'text' : 'password'}
                placeholder="Ingresá tu contraseña" autoComplete="current-password" required
                value={password} onChange={(event) => setPassword(event.target.value)} disabled={pending} />
              <button className="field__visibility" type="button"
                onClick={() => setShowPassword((value) => !value)}
                aria-label={showPassword ? 'Ocultar contraseña' : 'Mostrar contraseña'}
                aria-pressed={showPassword} disabled={pending}>
                <Icon name={showPassword ? 'eyeOff' : 'eye'} size={20}/>
              </button>
            </span>
          </div>
          {feedback && (
            <div className={`form-feedback form-feedback--${feedback.type}`} role="status" aria-live="polite">
              <Icon name={feedback.type === 'success' ? 'check' : 'info'} size={18}/>
              <span>{feedback.text}</span>
            </div>
          )}
          <button className="submit-button" type="submit" disabled={pending}>
            {pending ? 'Verificando acceso…' : 'Ingresar al sistema'}
            {!pending && <Icon name="arrow" size={20}/>}
          </button>
        </form>

        <div className="login-panel__help">
          <div className="login-panel__help-icon"><Icon name="shield" size={18}/></div>
          <p><strong>¿Necesitás ayuda para ingresar?</strong><br />Contactá al administrador del ERP para solicitar o recuperar tu acceso.</p>
        </div>
      </div>
      <div className="login-panel__foot"><span>FERRELSA ERP</span><span>ACCESO SEGURO</span></div>
    </section>
  );
}

function MissionVision() {
  return (
    <aside className="identity-panel" aria-labelledby="identity-heading">
      <div className="identity-panel__intro">
        <div className="eyebrow"><span className="eyebrow__line"/> NUESTRA IDENTIDAD</div>
        <h2 id="identity-heading">Lo que nos mueve<span className="orange-dot">.</span></h2>
        <p>Conocé los principios que orientan a FerreLSA y su compromiso con una gestión más organizada.</p>
      </div>

      <div className="identity-values">
        <article className="identity-card">
          <div className="identity-card__header">
            <span className="identity-card__icon identity-card__icon--mission"><Icon name="target" size={21}/></span>
            <span className="identity-card__number">01 / PROPÓSITO</span>
          </div>
          <h3>Misión</h3>
          <p>Ofrecer herramientas, materiales y suministros para la construcción, reparación y mantenimiento, atendiendo las necesidades de clientes particulares y profesionales mediante un servicio organizado y confiable.</p>
        </article>
        <article className="identity-card">
          <div className="identity-card__header">
            <span className="identity-card__icon identity-card__icon--vision"><Icon name="compass" size={21}/></span>
            <span className="identity-card__number">02 / FUTURO</span>
          </div>
          <h3>Visión</h3>
          <p>Consolidarnos como una ferretería reconocida por acompañar los proyectos de nuestros clientes, impulsando una gestión moderna, eficiente y apoyada en herramientas tecnológicas.</p>
        </article>
      </div>
      <p className="identity-panel__note">Misión y visión propuestas a partir del anteproyecto académico de FerreLSA.</p>
    </aside>
  );
}

function Footer() {
  return (
    <footer className="site-footer container">
      <span>© {new Date().getFullYear()} FerreLSA · Proyecto académico</span>
      <span>Universidad de Costa Rica · Sistema ERP</span>
    </footer>
  );
}

export default function App() {
  return (
    <>
      <Header />
      <main className="container main-layout">
        <LoginForm />
        <MissionVision />
      </main>
      <Footer />
    </>
  );
}
