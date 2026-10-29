
import React, { useState } from 'react';

import Brand from '../components/Brand.jsx';
import Icon from '../components/Icon.jsx';
import {
  signIn,
  AuthNotConfiguredError,
} from '../services/auth.js';

export default function Login({ onPreview }) {
  // ==========================================
  // ESTADOS
  // ==========================================

  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [pending, setPending] = useState(false);
  const [feedback, setFeedback] = useState(null);

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

    setPending(true);

    try {
      await signIn({
        username: username.trim(),
        password,
      });

      setPassword('');

      setFeedback({
        type: 'success',
        text: 'Acceso validado. Configurá la ruta del panel para continuar.',
      });
    } catch (error) {
      setFeedback({
        type:
          error instanceof AuthNotConfiguredError
            ? 'info'
            : 'error',
        text:
          error.message ||
          'Ocurrió un problema al intentar ingresar.',
      });
    } finally {
      setPending(false);
    }
  }

  // ==========================================
  // INTERFAZ DEL LOGIN
  // ==========================================

  return (
    <>
      {/* HEADER */}
      <header className="site-header container">
        <Brand onClick={onPreview} />

        <div className="header-context">
          <Icon name="shield" size={16} />

          <span>
            Acceso exclusivo para personal autorizado
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
              PORTAL INTERNO · FERRELSA ERP
            </div>

            {/* TÍTULO */}
            <h1>
              Iniciar sesión
              <span className="orange-dot">.</span>
            </h1>

            <p className="login-intro">
              Ingresá tus credenciales para acceder
              al sistema de gestión empresarial.
            </p>

            {/* FORMULARIO */}
            <form
              className="login-form"
              onSubmit={handleSubmit}
              noValidate
            >

              {/* CAMPO USUARIO */}
              <div className="field">
                <label htmlFor="username">
                  Usuario o correo electrónico
                </label>

                <span className="field__input-wrap">
                  <Icon name="user" size={19} />

                  <input
                    id="username"
                    type="text"
                    placeholder="Ingresá tu usuario"
                    autoComplete="username"
                    value={username}
                    onChange={(e) =>
                      setUsername(e.target.value)
                    }
                    disabled={pending}
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
                    autoComplete="current-password"
                    value={password}
                    onChange={(e) =>
                      setPassword(e.target.value)
                    }
                    disabled={pending}
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
                  ? 'Verificando acceso…'
                  : 'Ingresar al sistema'}

                <Icon name="arrow" size={20} />
              </button>
            </form>

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

            {/* ACCESO A VISTA PREVIA */}
            <button
              className="preview-link"
              type="button"
              onClick={onPreview}
            >
              Explorar vista previa del sistema

              <Icon name="arrow" size={16} />
            </button>
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
