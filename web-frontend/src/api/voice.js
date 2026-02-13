import { api } from './client';

/** POST /api/voice/search-campaigns — voice search */
export function voiceSearchCampaigns(audioBlob, userId, language) {
  const fd = new FormData();
  fd.append('audio', audioBlob, `recording.${audioBlob.ext || 'webm'}`);
  fd.append('user_id', userId || 'web_anonymous');
  if (language) fd.append('user_language', language);
  return api.upload('/voice/search-campaigns', fd);
}

/** POST /api/voice/donate-by-voice */
export function voiceDonate(audioBlob, userId, campaignId, language) {
  const fd = new FormData();
  fd.append('audio', audioBlob, `recording.${audioBlob.ext || 'webm'}`);
  fd.append('user_id', userId || 'web_anonymous');
  if (campaignId) fd.append('campaign_id', String(campaignId));
  if (language) fd.append('user_language', language);
  return api.upload('/voice/donate-by-voice', fd);
}

/** POST /api/voice/tts — text to speech */
export function textToSpeech(text, language = 'en') {
  return api.post('/voice/tts', { text, language });
}

/** POST /api/voice/set-language */
export function setVoiceLanguage(userId, language) {
  return api.post('/voice/set-language', { user_id: userId, language });
}
