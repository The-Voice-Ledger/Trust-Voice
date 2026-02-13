import { api } from './client';

/** GET /api/analytics/conversation-metrics?days=&user_id= */
export function getConversationMetrics({ days = 7, userId } = {}) {
  return api.get('/analytics/conversation-metrics', { days, user_id: userId });
}

/** GET /api/analytics/events?limit=&event_type= */
export function getConversationEvents({ limit = 20, eventType } = {}) {
  return api.get('/analytics/events', { limit, event_type: eventType });
}

/** GET /api/analytics/funnel?conversation_type=&days= */
export function getFunnel({ conversation_type = 'donating', days = 30 } = {}) {
  return api.get('/analytics/funnel', { conversation_type, days });
}

/** GET /api/analytics/summary?days= */
export function getAnalyticsSummary({ days = 7 } = {}) {
  return api.get('/analytics/summary', { days });
}
