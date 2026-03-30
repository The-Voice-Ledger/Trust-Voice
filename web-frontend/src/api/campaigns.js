import { api } from './client';

/** POST /api/campaigns/ — create new campaign */
export function createCampaign(data) {
  return api.post('/campaigns/', data);
}

/** GET /api/campaigns?page=&page_size=&status=&category=&search=&sort=&creator_user_id= */
export function listCampaigns({ page = 1, pageSize = 12, status, category, search, sort, creatorUserId, ngoId } = {}) {
  return api.get('/campaigns/', {
    page,
    page_size: pageSize,
    status: status || undefined,
    category: category || undefined,
    search: search || undefined,
    sort: sort || undefined,
    creator_user_id: creatorUserId || undefined,
    ngo_id: ngoId || undefined,
  });
}

/** GET /api/campaigns/:id */
export function getCampaign(id) {
  return api.get(`/campaigns/${id}`);
}

/** PATCH /api/campaigns/:id */
export function updateCampaign(id, data) {
  return api.patch(`/campaigns/${id}`, data);
}

/** DELETE /api/campaigns/:id */
export function deleteCampaign(id) {
  return api.del(`/campaigns/${id}`);
}

/** POST /api/campaigns/:id/upload-video */
export function uploadCampaignVideo(id, formData) {
  return api.upload(`/campaigns/${id}/upload-video`, formData);
}

/** DELETE /api/campaigns/:id/video */
export function deleteCampaignVideo(id) {
  return api.del(`/campaigns/${id}/video`);
}

/** GET /api/campaigns/:id/video */
export function getCampaignVideo(id) {
  return api.get(`/campaigns/${id}/video`);
}

/** GET /api/milestones/campaign/:id — milestone breakdown */
export function getCampaignMilestones(campaignId) {
  return api.get(`/milestones/campaign/${campaignId}`);
}

/** GET /api/milestones/treasury/:id — treasury overview */
export function getCampaignTreasury(campaignId) {
  return api.get(`/milestones/treasury/${campaignId}`);
}

/** POST /api/milestones/create */
export function createMilestones(data) {
  return api.post('/milestones/create', data);
}

/** POST /api/milestones/evidence */
export function submitMilestoneEvidence(data) {
  return api.post('/milestones/evidence', data);
}

/** POST /api/milestones/verify */
export function verifyMilestone(data) {
  return api.post('/milestones/verify', data);
}

/** POST /api/milestones/release */
export function releaseMilestoneFunds(data) {
  return api.post('/milestones/release', data);
}

/** GET /api/donations/campaign/:id */
export function getCampaignDonations(campaignId, { skip = 0, limit = 50 } = {}) {
  return api.get(`/donations/campaign/${campaignId}`, { skip, limit });
}

/** GET /api/payouts/campaign/:id */
export function getCampaignPayouts(campaignId) {
  return api.get(`/payouts/campaign/${campaignId}`);
}

/** POST /api/payouts/ */
export function createPayout(data) {
  return api.post('/payouts/', data);
}

/** GET /api/project-updates/campaign/:id */
export function getProjectUpdates(campaignId, { skip = 0, limit = 20 } = {}) {
  return api.get(`/project-updates/campaign/${campaignId}`, { skip, limit });
}

/** POST /api/project-updates/ */
export function createProjectUpdate(data) {
  return api.post('/project-updates/', data);
}

/** DELETE /api/project-updates/:id */
export function deleteProjectUpdate(id) {
  return api.del(`/project-updates/${id}`);
}

/** GET /api/ngos/:id */
export function getNgo(id) {
  return api.get(`/ngos/${id}`);
}

/** GET /api/ngos/:id/campaigns */
export function getNgoCampaigns(id) {
  return api.get(`/ngos/${id}/campaigns`);
}

/** PATCH /api/ngos/:id */
export function updateNgo(id, data) {
  return api.patch(`/ngos/${id}`, data);
}

/** GET /api/ngo-registrations/my-application */
export function getMyNgoApplication() {
  return api.get('/ngo-registrations/my-application');
}
