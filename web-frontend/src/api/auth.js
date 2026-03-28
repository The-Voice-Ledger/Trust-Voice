import { api, setTokenGetter } from './client';
import useAuthStore from '../stores/authStore';

/** POST /api/auth/login */
export async function login({ identifier, phoneNumber, pin }) {
  const body = { pin };
  if (identifier) body.username = identifier.replace(/^@/, '');
  if (phoneNumber) body.phone = phoneNumber;
  
  const data = await api.post('/auth/login', body);
  
  if (data.access_token) {
    // Set token directly in store with API response
    const { login: loginAction } = useAuthStore.getState();
    await loginAction({ 
      identifier, 
      phoneNumber, 
      pin,
      // Pass the token and user data from API response
      token: data.access_token,
      user: data.user || null
    });
  }
  
  return data;
}

/** GET /api/auth/me */
export function getMe() {
  return api.get('/auth/me');
}

/** POST /api/auth/refresh */
export function refreshToken() {
  return api.post('/auth/refresh');
}

/** POST /api/auth/logout */
export function logout() {
  return api.post('/auth/logout', {});
}
