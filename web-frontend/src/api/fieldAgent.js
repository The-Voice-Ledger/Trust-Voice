import { api } from './client';

/** POST /api/field-agent/photos/upload — multipart form (telegram_user_id, photo) */
export function uploadPhoto(telegramUserId, photoFile) {
  const fd = new FormData();
  fd.append('telegram_user_id', telegramUserId);
  fd.append('photo', photoFile);
  return api.upload('/field-agent/photos/upload', fd);
}

/** POST /api/field-agent/verifications/submit */
export function submitVerification(data) {
  return api.post('/field-agent/verifications/submit', data);
}

/** GET /api/field-agent/campaigns/pending?telegram_user_id= */
export function getPendingCampaigns(telegramUserId) {
  return api.get('/field-agent/campaigns/pending', { telegram_user_id: telegramUserId });
}

/** GET /api/field-agent/verifications/history?telegram_user_id= */
export function getVerificationHistory(telegramUserId) {
  return api.get('/field-agent/verifications/history', { telegram_user_id: telegramUserId });
}

/** GET /api/field-agent/session?telegram_user_id= */
export function getSession(telegramUserId) {
  return api.get('/field-agent/session', { telegram_user_id: telegramUserId });
}

/** POST /api/field-agent/session */
export function saveSession(data) {
  return api.upload('/field-agent/session', (() => {
    const fd = new FormData();
    Object.entries(data).forEach(([k, v]) => fd.append(k, typeof v === 'object' ? JSON.stringify(v) : String(v)));
    return fd;
  })());
}

/** DELETE /api/field-agent/session?telegram_user_id= */
export function clearSession(telegramUserId) {
  return api.del(`/field-agent/session?telegram_user_id=${telegramUserId}`);
}
