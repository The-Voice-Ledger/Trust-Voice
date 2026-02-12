/**
 * API Client — centralized HTTP layer with JWT auth.
 *
 * Every API call goes through this module so auth headers,
 * base URL, and error handling are consistent.
 */

const BASE = '/api';

let _token = null;

export function setToken(token) {
  _token = token;
}

export function getToken() {
  return _token;
}

export function clearToken() {
  _token = null;
}

async function request(method, path, { body, formData, params } = {}) {
  const url = new URL(`${BASE}${path}`, window.location.origin);
  if (params) {
    Object.entries(params).forEach(([k, v]) => {
      if (v !== undefined && v !== null) url.searchParams.set(k, v);
    });
  }

  const headers = {};
  if (_token) headers['Authorization'] = `Bearer ${_token}`;

  let fetchBody;
  if (formData) {
    fetchBody = formData; // browser sets Content-Type with boundary
  } else if (body) {
    headers['Content-Type'] = 'application/json';
    fetchBody = JSON.stringify(body);
  }

  const res = await fetch(url.toString(), { method, headers, body: fetchBody });

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
