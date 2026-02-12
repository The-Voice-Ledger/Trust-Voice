import { api } from './client';

/** GET /api/campaigns?page=&page_size=&status=&category=&search=&sort= */
export function listCampaigns({ page = 1, pageSize = 12, status, category, search, sort } = {}) {
  return api.get('/campaigns/', {
    page,
    page_size: pageSize,
    status: status || undefined,
    category: category || undefined,
    search: search || undefined,
    sort: sort || undefined,
  });
}

/** GET /api/campaigns/:id */
export function getCampaign(id) {
  return api.get(`/campaigns/${id}`);
}

/** GET /api/campaigns/:id/video */
export function getCampaignVideo(id) {
  return api.get(`/campaigns/${id}/video`);
}
