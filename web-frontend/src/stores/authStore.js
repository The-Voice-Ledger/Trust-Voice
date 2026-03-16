import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { login as apiLogin, getMe, logout as apiLogout } from '../api/auth';

const useAuthStore = create(
  persist(
    (set, get) => ({
      user: null,
      token: null,
      loading: false,
      error: null,

      /** PIN-based login */
      login: async ({ identifier, phoneNumber, pin, token, user }) => {
        set({ loading: true, error: null });
        try {
          // If token and user provided, use them directly (from API response)
          if (token && user) {
            set({ user, token, loading: false });
            return user;
          }
          
          const data = await apiLogin({ identifier, phoneNumber, pin });
          const me = await getMe();  // Get user data in same call
          set({ user: me, token: data.access_token, loading: false });
          return me;
        } catch (err) {
          set({ error: err.message, loading: false });
          throw err;
        }
      },

      /** Restore session from stored token */
      restore: async (token) => {
        try {
          const me = await getMe();
          set({ user: me, token });
        } catch {
          set({ user: null, token: null });
        }
      },

      logout: () => {
        apiLogout().catch(() => {});
        set({ user: null, token: null, error: null });
      },

      isAuthenticated: () => {
      const state = get();
      return !!(state.user && state.token);  // Only authenticated if both user and token exist
    },
    }),
    {
      name: 'auth-storage', // localStorage key
      partialize: (state) => ({ 
        token: state.token, 
        user: state.user 
      }), // Only persist token and user
    }
  )
);

export default useAuthStore;
