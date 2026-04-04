/**
 * API Client — centralized HTTP layer with JWT auth.
 *
 * Every API call goes through this module so auth headers,
 * base URL, and error handling are consistent.
 */

const BASE = '/api';

// Track if refresh is in progress to prevent infinite loops
let isRefreshing = false;
let refreshPromise = null; // Track ongoing refresh promise

// Get token from Zustand store
let _getToken = null;
export function setTokenGetter(getter) {
  _getToken = getter;
}

async function request(method, path, { body, formData, params } = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, v);
    });
  }

  const headers = {};
  const token = _getToken ? _getToken() : null;
  if (token) headers['Authorization'] = `Bearer ${token}`;

  let fetchBody;
  if (formData) {
    fetchBody = formData; // browser sets Content-Type with boundary
  } else if (body) {
    headers['Content-Type'] = 'application/json';
    fetchBody = JSON.stringify(body);
  }

  const res = await fetch(url.toString(), { method, headers, body: fetchBody });

  // Handle 401 Unauthorized - try token refresh (but not for refresh endpoint itself)
  if (res.status === 401 && path !== '/auth/refresh' && !isRefreshing) {
    console.log('Token expired, attempting refresh...');
    isRefreshing = true; // Set flag to prevent multiple refresh attempts
    
    try {
      // If refresh is already in progress, wait for it
      if (refreshPromise) {
        const refreshData = await refreshPromise;
        if (refreshData && refreshData.access_token) {
          console.log('Using existing refresh result...');
          
          // Retry with new token from existing refresh
          const newHeaders = { ...headers };
          newHeaders['Authorization'] = `Bearer ${refreshData.access_token}`;
          
          const retryRes = await fetch(url.toString(), { method, headers: newHeaders, body: fetchBody });
          
          if (!retryRes.ok) {
            const err = await retryRes.json().catch(() => ({ detail: retryRes.statusText }));
            const e = new Error(err.detail || 'Request failed');
            e.status = retryRes.status;
            e.data = err;
            throw e;
          }
          
          if (retryRes.status === 204) return null;
          return retryRes.json();
        }
      }
      
      // Start new refresh
      refreshPromise = (async () => {
        const { refreshToken } = await import('./auth');
        return await refreshToken();
      })();
      
      const refreshData = await refreshPromise;
      
      if (refreshData && refreshData.access_token) {
        console.log('Token refreshed successfully, retrying request...');
        
        // Update auth store with new token
        try {
          const authStore = await import('../stores/authStore');
          const store = authStore.default.getState();
          if (store.user) {
            authStore.default.setState({ 
              token: refreshData.access_token, 
              user: refreshData.user 
            });
          }
        } catch (storeError) {
          console.warn('Could not update auth store:', storeError);
        }
        
        // Retry with new token
        const newHeaders = { ...headers };
        newHeaders['Authorization'] = `Bearer ${refreshData.access_token}`;
        
        const retryRes = await fetch(url.toString(), { method, headers: newHeaders, body: fetchBody });
        
        if (!retryRes.ok) {
          const err = await retryRes.json().catch(() => ({ detail: retryRes.statusText }));
          const e = new Error(err.detail || 'Request failed');
          e.status = retryRes.status;
          e.data = err;
          throw e;
        }
        
        if (retryRes.status === 204) return null;
        return retryRes.json();
      } else {
        console.log('Token refresh failed, logging out...');
        throw new Error('Session expired. Please login again.');
      }
    } catch (refreshError) {
      console.error('Token refresh failed:', refreshError);
      throw new Error('Session expired. Please login again.');
    } finally {
      isRefreshing = false; // Reset flag
      refreshPromise = null; // Clear promise
    }
  }

  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    const e = new Error(err.detail || 'Request failed');
    e.status = res.status;
    e.data = err;
    throw e;
  }

  if (res.status === 204) return null;
  return res.json();
}

// Convenience methods
export const api = {
  get: (path, params) => request('GET', path, { params }),
  post: (path, body) => request('POST', path, { body }),
  patch: (path, body) => request('PATCH', path, { body }),
  del: (path) => request('DELETE', path),
  upload: (path, formData) => request('POST', path, { formData }),
};
