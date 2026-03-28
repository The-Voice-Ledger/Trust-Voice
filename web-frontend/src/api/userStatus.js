import { api } from './client';

/** GET /api/users/me/ngo-status — check if user has approved NGO */
export function getUserNgoStatus() {
  return api.get('/users/me/ngo-status');
}
