/**
 * VideoTimeline — three-act transparency video feed for a campaign.
 *
 * Displays all videos organized by act:
 *   Act 1: "Why We Need This" — campaign pitch
 *   Act 2: "What We Are Doing" — progress stream
 *   Act 3: "What We Did" — completion evidence
 *   + Field Agent Verifications
 *
 * Props:
 *   campaignId - Campaign ID to load timeline for
 *   compact    - Smaller variant (default: false)
 */
import { useState, useEffect } from 'react';
import { getCampaignTimeline, verifyVideoIntegrity, getVideoStreamUrl } from '../api/videos';
import VideoPlayer from './VideoPlayer';
import {
  HiOutlineCheckCircle, HiOutlineShieldCheck, HiOutlinePlay,
  HiOutlineFilm, HiOutlineFlag,
} from './icons';

const ACTS = [
  { key: 'act_1_why',       label: 'Why We Need This',   icon: HiOutlineFlag,         accent: 'blue' },
  { key: 'act_2_progress',  label: 'What We Are Doing',  icon: HiOutlinePlay,         accent: 'amber' },
  { key: 'act_3_completion',label: 'What We Did',         icon: HiOutlineCheckCircle,  accent: 'emerald' },
  { key: 'verifications',   label: 'Field Verifications', icon: HiOutlineShieldCheck,  accent: 'purple' },
];

const ACCENT_CLASSES = {
  blue:    { bg: 'bg-blue-50',    text: 'text-blue-700',    border: 'border-blue-200',    ring: 'ring-blue-400' },
  amber:   { bg: 'bg-amber-50',   text: 'text-amber-700',   border: 'border-amber-200',   ring: 'ring-amber-400' },
  emerald: { bg: 'bg-emerald-50', text: 'text-emerald-700', border: 'border-emerald-200', ring: 'ring-emerald-400' },
  purple:  { bg: 'bg-purple-50',  text: 'text-purple-700',  border: 'border-purple-200',  ring: 'ring-purple-400' },
};

export default function VideoTimeline({ campaignId, compact = false }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeAct, setActiveAct] = useState(null);
  const [playingVideo, setPlayingVideo] = useState(null);
  const [verifyResult, setVerifyResult] = useState({});

  useEffect(() => {
    if (!campaignId) return;
    setLoading(true);
    getCampaignTimeline(campaignId)
      .then((d) => {
        setData(d);
        // Auto-select first non-empty act
        for (const act of ACTS) {
          if (d[act.key]?.length > 0) { setActiveAct(act.key); break; }
        }
      })
      .catch((e) => setError(e.message))
      .finally(() => setLoading(false));
  }, [campaignId]);

  const handleVerify = async (videoId) => {
    try {
      const result = await verifyVideoIntegrity(videoId);
      setVerifyResult((prev) => ({ ...prev, [videoId]: result }));
    } catch {
      setVerifyResult((prev) => ({ ...prev, [videoId]: { verified: false, error: true } }));
    }
  };

  if (loading) return <div className="text-center py-12 text-gray-400 text-sm">Loading timeline…</div>;
  if (error) return <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-sm text-red-600">{error}</div>;
  if (!data || data.total_videos === 0) {
    return (
      <div className="text-center py-12">
        <HiOutlineFilm className="w-10 h-10 text-gray-300 mx-auto mb-2" />
        <p className="text-gray-400 text-sm">No transparency videos yet</p>
      </div>
    );
  }

  const activeVideos = data[activeAct] || [];

  return (
    <div>
      {/* Act tabs */}
      <div className="flex gap-2 overflow-x-auto pb-2 mb-4 scrollbar-none">
        {ACTS.map((act) => {
          const count = data[act.key]?.length || 0;
          if (count === 0 && compact) return null;
          const colors = ACCENT_CLASSES[act.accent];
          const isActive = activeAct === act.key;
          const Icon = act.icon;

          return (
            <button
              key={act.key}
              onClick={() => { setActiveAct(act.key); setPlayingVideo(null); }}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-full text-xs font-medium border whitespace-nowrap transition
                ${isActive ? `${colors.bg} ${colors.text} ${colors.border}` : 'bg-gray-50 text-gray-400 border-gray-200 hover:bg-gray-100'}`}
            >
              <Icon className="w-3.5 h-3.5" />
              {act.label}
              {count > 0 && (
                <span className={`ml-1 w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold
                  ${isActive ? `${colors.bg} ${colors.text}` : 'bg-gray-200 text-gray-500'}`}>
                  {count}
                </span>
              )}
            </button>
          );
        })}
      </div>

      {/* Currently playing */}
      {playingVideo && (
        <div className="mb-4">
          <VideoPlayer
            videoData={{
              video_url: playingVideo.storage_url,
              thumbnail_url: playingVideo.thumbnail_url,
              ipfs_hash: playingVideo.ipfs_cid,
              upload_date: playingVideo.created_at,
              file_size_mb: playingVideo.file_size_mb,
              location_verified: playingVideo.gps_latitude != null,
            }}
          />
          <div className="mt-2 flex items-center justify-between">
            <div>
              <h4 className="text-sm font-medium text-gray-900">{playingVideo.title || 'Untitled'}</h4>
              {playingVideo.description && (
                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{playingVideo.description}</p>
              )}
              <p className="text-xs text-gray-400 mt-1">
                By {playingVideo.uploader_name || 'Unknown'} · {playingVideo.created_at ? new Date(playingVideo.created_at).toLocaleDateString() : ''}
                {playingVideo.view_count > 0 && ` · ${playingVideo.view_count} views`}
              </p>
            </div>

            {/* Verify integrity button */}
            <div className="flex items-center gap-2">
              {verifyResult[playingVideo.id] ? (
                <span className={`text-xs font-medium px-2 py-1 rounded-full ${verifyResult[playingVideo.id].verified
                  ? 'bg-green-50 text-green-600' : 'bg-red-50 text-red-600'}`}>
                  {verifyResult[playingVideo.id].verified ? '✓ Verified' : '✗ Mismatch'}
                </span>
              ) : (
                <button
                  onClick={() => handleVerify(playingVideo.id)}
                  className="text-xs text-gray-400 hover:text-emerald-600 transition"
                  title="Verify file integrity"
                >
                  <HiOutlineShieldCheck className="w-4 h-4" />
                </button>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Video grid */}
      {activeVideos.length === 0 ? (
        <div className="text-center py-8 text-gray-400 text-xs">No videos in this category yet</div>
      ) : (
        <div className={`grid gap-3 ${compact ? 'grid-cols-1 sm:grid-cols-2' : 'grid-cols-1 sm:grid-cols-2 lg:grid-cols-3'}`}>
          {activeVideos.map((v) => (
            <button
              key={v.id}
              onClick={() => setPlayingVideo(v)}
              className={`text-left group rounded-xl overflow-hidden border transition hover:shadow-md
                ${playingVideo?.id === v.id ? 'border-emerald-400 ring-2 ring-emerald-200' : 'border-gray-200 hover:border-gray-300'}`}
            >
              {/* Thumbnail / placeholder */}
              <div className="relative aspect-video bg-gray-900 flex items-center justify-center">
                {v.thumbnail_url ? (
                  <img src={v.thumbnail_url} alt="" className="w-full h-full object-cover" />
                ) : (
                  <HiOutlinePlay className="w-10 h-10 text-gray-500 group-hover:text-white transition" />
                )}
                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/20 transition flex items-center justify-center">
                  <div className="w-10 h-10 rounded-full bg-white/80 flex items-center justify-center opacity-0 group-hover:opacity-100 transition">
                    <HiOutlinePlay className="w-5 h-5 text-gray-900 ml-0.5" />
                  </div>
                </div>

                {/* Duration badge */}
                {v.duration_seconds && (
                  <span className="absolute bottom-1 right-1 bg-black/70 text-white text-[10px] px-1.5 py-0.5 rounded">
                    {Math.floor(v.duration_seconds / 60)}:{String(v.duration_seconds % 60).padStart(2, '0')}
                  </span>
                )}

                {/* GPS badge */}
                {v.gps_latitude && (
                  <span className="absolute top-1 left-1 bg-green-600/80 text-white text-[10px] px-1.5 py-0.5 rounded flex items-center gap-0.5">
                    📍 GPS
                  </span>
                )}
              </div>

              {/* Info */}
              <div className="p-2.5">
                <h5 className="text-xs font-medium text-gray-900 line-clamp-1">{v.title || 'Untitled video'}</h5>
                <p className="text-[11px] text-gray-400 mt-0.5">
                  {v.uploader_name || 'Unknown'} · {v.created_at ? new Date(v.created_at).toLocaleDateString() : ''}
                </p>
                {v.content_hash_sha256 && (
                  <p className="text-[10px] text-gray-300 font-mono mt-1 truncate" title={v.content_hash_sha256}>
                    SHA-256: {v.content_hash_sha256.slice(0, 16)}…
                  </p>
                )}
              </div>
            </button>
          ))}
        </div>
      )}

      {/* Transparency footer */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-1.5 text-[11px] text-gray-400">
        <HiOutlineShieldCheck className="w-3.5 h-3.5" />
        {data.total_videos} video{data.total_videos !== 1 ? 's' : ''} · Every file is SHA-256 hashed for tamper-proof verification
      </div>
    </div>
  );
}
