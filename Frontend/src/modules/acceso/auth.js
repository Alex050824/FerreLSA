export async function signIn({ username, password }) {
  const endpoint = import.meta.env.VITE_LOGIN_ENDPOINT?.trim() || '/api/auth/login';

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
  const session = await response.json().catch(() => null);
  if (!session?.token || !['ADMIN', 'CLIENTE'].includes(session.usuario?.rol)) {
    throw new Error('El servidor devolvió una respuesta de inicio de sesión inválida.');
  }
  return session;
}
