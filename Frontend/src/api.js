export async function api(path, { token, method = 'GET', body, signal } = {}) {
  const response = await fetch('/api' + path, {
    method, signal,
    headers: {
      ...(token && { Authorization: 'Bearer ' + token }),
      ...(body !== undefined && { 'Content-Type': 'application/json' }),
    },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  if (response.status === 204) return null;
  const result = await response.json().catch(() => null);
  if (!response.ok || result === null) {
    const error = new Error(result?.error || 'No se pudo completar la solicitud.');
    error.status = response.status;
    throw error;
  }
  return result;
}

export function readSession() {
  try {
    return JSON.parse(sessionStorage.getItem('ferrelsa.session'));
  } catch {
    return null;
  }
}
