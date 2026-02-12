import { api, setToken, clearToken } from './client';

/** POST /api/auth/login */
export async function login({ identifier, phoneNumber, pin }) {
  const body = { pin };
  if (identifier) body.telegram_username = identifier;
  if (phoneNumber) body.phone_number = phoneNumber;
  const data = await api.post('/auth/login', body);
  if (data.access_token) setToken(data.access_token);
  return data;
}

/** GET /api/auth/me */
export function getMe() {
  return api.get('/auth/me');
}

/** POST /api/auth/logout */
export function logout() {
  clearToken();
  return api.post('/auth/logout', {});
}
