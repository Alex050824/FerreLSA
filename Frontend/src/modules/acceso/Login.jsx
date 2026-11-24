
import React, { useState } from 'react';

import Brand from '../../components/Brand.jsx';
import Icon from '../../components/Icon.jsx';
import { registerCustomer, signIn } from './auth.js';

export default function Login({ onAuthenticated }) {
  // ==========================================
  // ESTADOS
  // ==========================================

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState(null);
  const [registering, setRegistering] = useState(false);
  const [name, setName] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');

  // ==========================================
  // MANEJAR INICIO DE SESIÓN
  // ==========================================

  async function handleSubmit(event) {
    event.preventDefault();
    setFeedback(null);

    // Validar campos
    if (!username.trim() || !password) {
      setFeedback({
        type: 'error',
        text: 'Ingresá tu usuario y contraseña para continuar.',
      });
      return;
    }

    if (registering && !name.trim()) {
      setFeedback({ type: 'error', text: 'Ingresá tu nombre para crear tu cuenta.' });
      return;
    }
    if (registering && password.length < 8) {
      setFeedback({ type: 'error', text: 'La contraseña debe tener al menos 8 caracteres.' });
      return;
    }
    if (registering && password !== confirmPassword) {
      setFeedback({ type: 'error', text: 'Las contraseñas no coinciden.' });
      return;
    }

    setPending(true);

    try {
      if (registering) {
        await registerCustomer({ nombre: name.trim(), correo: username.trim(), password });
        setRegistering(false);
        setName('');
        setPassword('');
        setConfirmPassword('');
        setShowPassword(false);
        setFeedback({ type: 'info', text: 'Cuenta creada. Iniciá sesión con tu correo y contraseña.' });
        return;
      }
      const session = await signIn({
        username: username.trim(),
        password,
      });

      setPassword('');

      onAuthenticated(session);
    } catch (error) {
      setFeedback({
        type: 'error',
        text:
          error.message ||
          'Ocurrió un problema al intentar ingresar.',
      });
    } finally {
      setPending(false);
    }
  }

  function toggleRegistration() {
    setRegistering(value => !value);
    setPassword('');
    setConfirmPassword('');
    setShowPassword(false);
    setFeedback(null);
  }

  // ==========================================
  // INTERFAZ DEL LOGIN
  // ==========================================

  return (
    <>
      {/* HEADER */}
      <header className="site-header container">
        <Brand />

        <div className="header-context">
          <Icon name="shield" size={16} />

          <span>
            Acceso a FerreLSA
          </span>
        </div>
      </header>

      {/* CONTENIDO PRINCIPAL */}
      <main className="container main-layout">

        {/* PANEL DE INICIO DE SESIÓN */}
        <section className="login-panel">
          <div className="login-panel__inner">

            {/* ETIQUETA SUPERIOR */}
            <div className="eyebrow">
              <span className="eyebrow__line" />
              {registering ? 'CUENTA DE CLIENTE · FERRELSA' : 'BIENVENIDO A FERRELSA'}
            </div>

            {/* TÍTULO */}
            <h1>
              {registering ? 'Crear cuenta' : 'Iniciar sesión'}
              <span className="orange-dot">.</span>
            </h1>

            <p className="login-intro">
              {registering
                ? 'Registrate para acceder a la tienda en línea.'
                : 'Ingresá tus credenciales para acceder a tu cuenta.'}
            </p>

            {/* FORMULARIO */}
            <form
              className="login-form"
              onSubmit={handleSubmit}
            >

              {registering && <div className="field">
                <label htmlFor="customer-name">Nombre</label>
                <span className="field__input-wrap">
                  <Icon name="user" size={19} />
                  <input id="customer-name" type="text" autoComplete="given-name" maxLength={255}
                    placeholder="Ingresá tu nombre" value={name} onChange={event => setName(event.target.value)}
                    disabled={pending} required />
                </span>
              </div>}

              {/* CAMPO USUARIO */}
              <div className="field">
                <label htmlFor="username">
                  Correo electrónico
                </label>

                <span className="field__input-wrap">
                  <Icon name="user" size={19} />

                  <input
                    id="username"
                    type="email"
                    placeholder="Ingresá tu correo electrónico"
                    autoComplete="username"
                    value={username}
                    onChange={(e) =>
                      setUsername(e.target.value)
                    }
                    disabled={pending}
                    maxLength={255}
                    required
                  />
                </span>
              </div>

              {/* CAMPO CONTRASEÑA */}
              <div className="field">
                <label htmlFor="password">
                  Contraseña
                </label>

                <span className="field__input-wrap">
                  <Icon name="lock" size={19} />

                  <input
                    id="password"
                    type={
                      showPassword
                        ? 'text'
                        : 'password'
                    }
                    placeholder="Ingresá tu contraseña"
                    autoComplete={registering ? 'new-password' : 'current-password'}
                    value={password}
                    onChange={(e) =>
                      setPassword(e.target.value)
                    }
                    disabled={pending}
                    minLength={registering ? 8 : undefined}
                    maxLength={128}
                    required
                  />

                  {/* MOSTRAR / OCULTAR CONTRASEÑA */}
                  <button
                    className="field__visibility"
                    type="button"
                    onClick={() =>
                      setShowPassword(!showPassword)
                    }
                    aria-label={
                      showPassword
                        ? 'Ocultar contraseña'
                        : 'Mostrar contraseña'
                    }
                  >
                    <Icon
                      name={
                        showPassword
                          ? 'eyeOff'
                          : 'eye'
                      }
                      size={20}
                    />
                  </button>
                </span>
              </div>

              {registering && <div className="field">
                <label htmlFor="confirm-password">Confirmar contraseña</label>
                <span className="field__input-wrap">
                  <Icon name="lock" size={19} />
                  <input id="confirm-password" type="password" autoComplete="new-password" maxLength={128}
                    placeholder="Repetí tu contraseña" value={confirmPassword}
                    onChange={event => setConfirmPassword(event.target.value)} disabled={pending} required />
                </span>
              </div>}

              {/* MENSAJES DEL FORMULARIO */}
              {feedback && (
                <div
                  className={`form-feedback form-feedback--${feedback.type}`}
                  role="status"
                >
                  {feedback.text}
                </div>
              )}

              {/* BOTÓN INICIAR SESIÓN */}
              <button
                className="submit-button"
                type="submit"
                disabled={pending}
              >
                {pending
                  ? (registering ? 'Creando cuenta…' : 'Verificando acceso…')
                  : (registering ? 'Crear cuenta de cliente' : 'Ingresar al sistema')}

                <Icon name="arrow" size={20} />
              </button>
            </form>

            <p className="login-panel__register">
              {registering ? '¿Ya tenés una cuenta?' : '¿No tenés una cuenta?'}{' '}
              <button type="button" onClick={toggleRegistration} disabled={pending}>
                {registering ? 'Iniciá sesión' : 'Registrate como cliente'}
              </button>
            </p>

            {/* AYUDA DE ACCESO */}
            <div className="login-panel__help">
              <Icon name="shield" size={18} />

              <p>
                <strong>
                  ¿Necesitás ayuda para ingresar?
                </strong>

                <br />

                Contactá al administrador del ERP
                para solicitar o recuperar tu acceso.
              </p>
            </div>

          </div>
        </section>

        {/* PANEL DE IDENTIDAD EMPRESARIAL */}
        <aside className="identity-panel">

          <div className="eyebrow">
            <span className="eyebrow__line" />
            NUESTRA IDENTIDAD
          </div>

          <h2>
            Lo que nos mueve
            <span className="orange-dot">.</span>
          </h2>

          <p>
            Principios que orientan a FerreLSA
            y su compromiso con una gestión
            más organizada.
          </p>

          {/* MISIÓN */}
          <article className="identity-card">
            <span className="identity-card__number">
              PROPÓSITO
            </span>

            <h3>Misión</h3>

            <p>
              Ofrecer herramientas, materiales y
              suministros para la construcción,
              reparación y mantenimiento,
              mediante un servicio organizado
              y confiable.
            </p>
          </article>

          {/* VISIÓN */}
          <article className="identity-card">
            <span className="identity-card__number">
              FUTURO
            </span>

            <h3>Visión</h3>

            <p>
              Consolidarnos como una ferretería
              reconocida por acompañar los
              proyectos de nuestros clientes
              con una gestión moderna y eficiente.
            </p>
          </article>
        </aside>
      </main>

      {/* FOOTER */}
      <footer className="site-footer container">
        <span>
          © {new Date().getFullYear()} FerreLSA
        </span>
      </footer>
    </>
  );
}
