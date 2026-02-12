import { api } from './client';

/** POST /api/ngo-registrations/ — submit new NGO registration */
export function submitNgoRegistration(data) {
  return api.post('/ngo-registrations/', data);
}

/** GET /api/ngo-registrations/my-application?telegram_user_id= */
export function getMyApplication(telegramUserId) {
  return api.get('/ngo-registrations/my-application', { telegram_user_id: telegramUserId });
}
