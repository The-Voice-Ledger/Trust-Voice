import { api } from './client';

/* ── Admin Auth ────────────────────────────── */

/** POST /api/admin/login */
export function adminLogin({ email, password }) {
  return api.post('/admin/login', { email, password });
}

/** GET /api/admin/me */
export function adminMe() {
  return api.get('/admin/me');
}

/** POST /api/admin/users — create admin user (super_admin only) */
export function createAdminUser(data) {
  return api.post('/admin/users', data);
}

/** GET /api/admin/users */
export function listAdminUsers() {
  return api.get('/admin/users');
}

/* ── NGO Registrations (admin) ────────────── */

/** GET /api/ngo-registrations/?status=&limit= */
export function listNgoRegistrations({ status, limit = 50 } = {}) {
  return api.get('/ngo-registrations/', { status, limit });
}

/** GET /api/ngo-registrations/:id */
export function getNgoRegistration(id) {
  return api.get(`/ngo-registrations/${id}`);
}

/** POST /api/ngo-registrations/:id/approve */
export function approveNgoRegistration(id, adminNotes) {
  return api.post(`/ngo-registrations/${id}/approve`, { admin_notes: adminNotes });
}

/** POST /api/ngo-registrations/:id/reject */
export function rejectNgoRegistration(id, reason) {
  return api.post(`/ngo-registrations/${id}/reject`, { rejection_reason: reason });
}

/** POST /api/ngo-registrations/:id/request-info */
export function requestNgoInfo(id, message) {
  return api.post(`/ngo-registrations/${id}/request-info`, {}, { message });
}

/* ── User Registrations (admin) ───────────── */

/** GET /api/registrations/?status=&role=&skip=&limit= */
export function listUserRegistrations({ status = 'pending', role, skip = 0, limit = 50 } = {}) {
  return api.get('/registrations/', { status, role, skip, limit });
}

/** GET /api/registrations/stats */
export function getRegistrationStats() {
  return api.get('/registrations/stats');
}

/** GET /api/registrations/:id */
export function getUserRegistration(id) {
  return api.get(`/registrations/${id}`);
}

/** POST /api/registrations/:id/approve */
export function approveUserRegistration(id, adminNotes) {
  return api.post(`/registrations/${id}/approve`, { admin_notes: adminNotes });
}

/** POST /api/registrations/:id/reject */
export function rejectUserRegistration(id, reason) {
  return api.post(`/registrations/${id}/reject`, { reason });
}

/* ── Payouts (admin) ──────────────────────── */

/** GET /api/payouts/?status=&ngo_id=&skip=&limit= */
export function listPayouts({ status, ngo_id, skip = 0, limit = 50 } = {}) {
  return api.get('/payouts/', { status, ngo_id, skip, limit });
}

/** GET /api/payouts/:id */
export function getPayout(id) {
  return api.get(`/payouts/${id}`);
}

/** POST /api/payouts/:id/approve */
export function approvePayout(id) {
  return api.post(`/payouts/${id}/approve`, {});
}

/** POST /api/payouts/:id/reject */
export function rejectPayout(id, reason) {
  return api.post(`/payouts/${id}/reject`, { rejection_reason: reason });
}

/* ── NGOs (CRUD) ──────────────────────────── */

/** GET /api/ngos/?skip=&limit= */
export function listNgos({ skip = 0, limit = 50 } = {}) {
  return api.get('/ngos/', { skip, limit });
}

/** GET /api/ngos/:id */
export function getNgo(id) {
  return api.get(`/ngos/${id}`);
}
