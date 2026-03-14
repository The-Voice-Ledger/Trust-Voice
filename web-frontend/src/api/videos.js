import { api } from './client';

// ── Upload ──────────────────────────────────────────────────────

/**
 * Upload a transparency video.
 * @param {Object} opts
 * @param {File}   opts.file        - Video file
 * @param {string} opts.category    - 'why' | 'progress' | 'completion' | 'verification'
 * @param {string} opts.parentType  - 'campaign' | 'milestone'
 * @param {number} opts.parentId    - Campaign or milestone ID
 * @param {string} [opts.title]
 * @param {string} [opts.description]
 * @param {number} [opts.gpsLatitude]
 * @param {number} [opts.gpsLongitude]
 * @param {number} [opts.durationSeconds] - Client-measured duration (seconds)
 * @param {boolean} [opts.pinToIpfs=false]
 */
export function uploadVideo({
  file, category, parentType, parentId,
  title, description, gpsLatitude, gpsLongitude, durationSeconds, pinToIpfs = false,
}) {
  const fd = new FormData();
  fd.append('video', file);
  fd.append('category', category);
  fd.append('parent_type', parentType);
  fd.append('parent_id', String(parentId));
  if (title) fd.append('title', title);
  if (description) fd.append('description', description);
  if (gpsLatitude != null) fd.append('gps_latitude', String(gpsLatitude));
  if (gpsLongitude != null) fd.append('gps_longitude', String(gpsLongitude));
  if (durationSeconds != null) fd.append('duration_seconds', String(durationSeconds));
  if (pinToIpfs) fd.append('pin_to_ipfs', 'true');
  return api.upload('/videos/upload', fd);
}

// ── Retrieval ───────────────────────────────────────────────────

/** Get all videos for a parent entity (campaign or milestone). */
export function getParentVideos(parentType, parentId, category) {
  const params = {};
  if (category) params.category = category;
  return api.get(`/videos/parent/${parentType}/${parentId}`, params);
}

/** Get the full three-act timeline for a campaign (includes milestone videos). */
export function getCampaignTimeline(campaignId) {
  return api.get(`/videos/campaign/${campaignId}/timeline`);
}

/** Get a single video by ID. */
export function getVideo(videoId) {
  return api.get(`/videos/${videoId}`);
}

// ── Integrity ──────────────────────────────────────────────────

/** Verify video integrity via SHA-256 hash. */
export function verifyVideoIntegrity(videoId) {
  return api.get(`/videos/${videoId}/verify`);
}

// ── Moderation ─────────────────────────────────────────────────

/** Flag a video for review. */
export function flagVideo(videoId, reason) {
  const fd = new FormData();
  fd.append('reason', reason);
  return api.upload(`/videos/${videoId}/flag`, fd);
}

/** Delete a video (uploader or admin only). */
export function deleteVideo(videoId) {
  return api.del(`/videos/${videoId}`);
}

/** Get stream URL for a video. */
export function getVideoStreamUrl(videoId) {
  return `/api/videos/${videoId}/stream`;
}
