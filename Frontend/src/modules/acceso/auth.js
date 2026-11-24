import { api } from '../../api.js';

export function registerCustomer({ nombre, correo, password }) {
  return api('/auth/registro', { method: 'POST', body: { nombre, correo, password } });
}

export async function signIn({ username, password }) {
  let session;
  try {
    session = await api('/auth/login', {
      method: 'POST',
      body: { username, password },
    });
  } catch (error) {
    if (error.status === 401 || error.status === 403) {
      throw new Error('Correo o contraseña incorrectos.');
    }
    throw error;
  }
  if (!session?.token || !['ADMIN', 'CLIENTE'].includes(session.usuario?.rol)) {
    throw new Error('El servidor devolvió una respuesta de inicio de sesión inválida.');
  }
  return session;
}
