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

// ── AI Agent endpoints ─────────────────────────────────────────

/**
 * POST /api/voice/agent — unified voice agent (audio input).
 *
 * Sends audio to the AI Agent which transcribes, understands,
 * and executes any command (search, donate, check status, etc.)
 * in a single round-trip.
 *
 * @param {Blob}   audioBlob       Recorded audio blob
 * @param {string} userId          User identifier
 * @param {string} [language]      Language preference ("en" | "am")
 * @param {string} [conversationId] For multi-turn conversations
 * @param {object} [context]       Page context (e.g. { page, selected_campaign })
 */
export function voiceAgent(audioBlob, userId, language, conversationId, context) {
  const fd = new FormData();
  fd.append('audio', audioBlob, `recording.${audioBlob.ext || 'webm'}`);
  fd.append('user_id', userId || 'web_anonymous');
  if (language) fd.append('user_language', language);
  if (conversationId) fd.append('conversation_id', conversationId);
  if (context) fd.append('context', JSON.stringify(context));
  return api.upload('/voice/agent', fd);
}

/**
 * POST /api/voice/agent/text — unified text agent (typed input).
 *
 * Same AI Agent but skips ASR — useful for chat / text input.
 *
 * @param {string} text            User message
 * @param {string} userId          User identifier
 * @param {string} [language]      Language preference
 * @param {string} [conversationId] For multi-turn conversations
 * @param {object} [context]       Page context
 */
export function textAgent(text, userId, language, conversationId, context) {
  return api.post('/voice/agent/text', {
    text,
    user_id: userId || 'web_anonymous',
    user_language: language || 'en',
    conversation_id: conversationId || undefined,
    context: context ? JSON.stringify(context) : undefined,
  });
}
