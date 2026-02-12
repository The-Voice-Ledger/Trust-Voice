import { api } from './client';

/** POST /api/donations/ — create donation & initiate payment */
export function createDonation(data) {
  return api.post('/donations/', data);
}

/** GET /api/donations/:id */
export function getDonation(id) {
  return api.get(`/donations/${id}`);
}

/** GET /api/donations/donor/:donorId */
export function getDonorDonations(donorId, { skip = 0, limit = 50 } = {}) {
  return api.get(`/donations/donor/${donorId}`, { skip, limit });
}

/** GET /api/donations/:id/receipt */
export function getReceipt(donationId) {
  return api.get(`/donations/${donationId}/receipt`);
}

/** GET /api/donations/:id/receipt/verify */
export function verifyReceipt(donationId) {
  return api.get(`/donations/${donationId}/receipt/verify`);
}

/** GET /api/donations/tax-year/:year?donor_id= */
export function getTaxSummary(year, donorId) {
  return api.get(`/donations/tax-year/${year}`, { donor_id: donorId });
}
