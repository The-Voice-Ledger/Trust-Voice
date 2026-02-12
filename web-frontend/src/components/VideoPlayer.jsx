/**
 * VideoPlayer — plays campaign transparency videos.
 * Supports IPFS CID-based videos, direct URLs, and alternative gateways.
 */
export default function VideoPlayer({ videoData, className = '' }) {
  if (!videoData) return null;

  // Build video URL — support multiple field names
  const videoUrl = videoData.video_url
    || videoData.url
    || (videoData.ipfs_cid ? `https://gateway.pinata.cloud/ipfs/${videoData.ipfs_cid}` : null)
    || (videoData.cid ? `https://gateway.pinata.cloud/ipfs/${videoData.cid}` : null);

  if (!videoUrl) return null;

  const sources = [
    videoUrl,
    ...(videoData.alternative_urls || []),
  ];

  return (
    <div className={`rounded-2xl overflow-hidden bg-black shadow-lg ${className}`}>
      <video
        controls
        playsInline
        preload="metadata"
        className="w-full aspect-video"
        poster={videoData.thumbnail_url || undefined}
      >
        {sources.map((src, i) => (
          <source key={i} src={src} type={videoData.content_type || 'video/mp4'} />
        ))}
        Your browser does not support video playback.
      </video>

      {/* Metadata bar */}
      {(videoData.upload_date || videoData.uploaded_at || videoData.location_verified || videoData.ipfs_cid) && (
        <div className="px-4 py-2 bg-gray-900 text-gray-400 text-xs flex items-center justify-between">
          <span>
            {videoData.upload_date || videoData.uploaded_at
              ? `Uploaded ${new Date(videoData.upload_date || videoData.uploaded_at).toLocaleDateString()}`
              : ''}
          </span>
          <div className="flex items-center gap-3">
            {videoData.location_verified && (
              <span className="text-green-400 font-medium">✓ Location Verified</span>
            )}
            {videoData.file_size_mb && <span>{videoData.file_size_mb.toFixed(1)} MB</span>}
            {videoData.ipfs_cid && (
              <span className="font-mono truncate max-w-[120px]" title={videoData.ipfs_cid}>
                IPFS: {videoData.ipfs_cid.slice(0, 12)}…
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
