import { create } from 'zustand';
import { login as apiLogin, getMe, logout as apiLogout } from '../api/auth';
import { setToken, clearToken } from '../api/client';

const useAuthStore = create((set, get) => ({
  user: null,
  token: null,
  loading: false,
  error: null,

  /** PIN-based login */
  login: async ({ identifier, phoneNumber, pin }) => {
    set({ loading: true, error: null });
    try {
      const data = await apiLogin({ identifier, phoneNumber, pin });
      const me = await getMe();
      set({ user: me, token: data.access_token, loading: false });
      return me;
    } catch (err) {
      set({ error: err.message, loading: false });
      throw err;
    }
  },

  /** Restore session from stored token */
  restore: async (token) => {
    setToken(token);
    try {
      const me = await getMe();
      set({ user: me, token });
    } catch {
      clearToken();
      set({ user: null, token: null });
    }
  },

  logout: () => {
    apiLogout().catch(() => {});
    clearToken();
    set({ user: null, token: null, error: null });
  },

  isAuthenticated: () => !!get().token,
}));

export default useAuthStore;
