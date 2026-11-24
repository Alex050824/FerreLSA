/**
 * Punto de integración con el backend real del ERP.
 * Definí VITE_LOGIN_ENDPOINT en tu archivo .env para habilitar el POST.
 * No hay usuarios de prueba, credenciales falsas ni inicio de sesión simulado.
 *
 * IMPORTANTE: el contrato { username, password } debe adaptarse al endpoint real.
 * En producción usá HTTPS y preferentemente cookies HttpOnly gestionadas por el servidor.
 */
export class AuthNotConfiguredError extends Error {
  constructor() {
    super('La pantalla está lista, pero el inicio de sesión todavía no está conectado al backend del ERP.');
    this.name = 'AuthNotConfiguredError';
  }
}

export async function signIn({ username, password }) {
  const endpoint = import.meta.env.VITE_LOGIN_ENDPOINT?.trim();
  if (!endpoint) throw new AuthNotConfiguredError();

  let response;
  try {
    response = await fetch(endpoint, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      credentials: 'include',
      body: JSON.stringify({ username, password }),
    });
  } catch {
    throw new Error('No se pudo conectar con el servidor. Verificá que el backend esté disponible.');
  }

  if (!response.ok) {
    if (response.status === 401 || response.status === 403) {
      throw new Error('Usuario o contraseña incorrectos.');
    }
    throw new Error('No fue posible completar el ingreso. Intentá nuevamente.');
  }
  return true;
}
