/**
 * VideoUploadWidget — dead-simple upload for campaign creators and field agents.
 *
 * Features:
 * - Drag-and-drop or click to select
 * - Category selection (Why / Progress / Completion / Verification)
 * - GPS capture for verification videos
 * - Client-side duration validation (5 min max for progress)
 * - Auto-generated title from date + category when left blank
 * - Upload progress indication
 * - Title & description fields
 *
 * Props:
 *   parentType  - 'campaign' | 'milestone'
 *   parentId    - ID of the parent entity
 *   parentTitle - Title of the parent entity (for auto-title generation)
 *   category    - Pre-set category (optional, hides selector if set)
 *   onUploaded  - Callback when upload succeeds: (videoData) => void
 *   compact     - Smaller variant for inline use
 */
import { useState, useRef, useCallback } from 'react';
import { uploadVideo } from '../api/videos';
import { HiOutlineCamera, HiOutlineXMark, HiOutlineCloudArrowUp } from './icons';

const CATEGORY_LABELS = {
  why:          { label: 'Why We Need This',   color: 'bg-blue-50 text-blue-700 border-blue-200', maxMinutes: 10 },
  progress:     { label: 'Progress Update',    color: 'bg-amber-50 text-amber-700 border-amber-200', maxMinutes: 5 },
  completion:   { label: 'Completion Evidence', color: 'bg-emerald-50 text-emerald-700 border-emerald-200', maxMinutes: 10 },
  verification: { label: 'Field Verification', color: 'bg-purple-50 text-purple-700 border-purple-200', maxMinutes: 5 },
};

const MAX_SIZE_MB = 100;

/**
 * Read video duration from a File object using an off-screen <video> element.
 * @param {File} file
 * @returns {Promise<number>} duration in seconds
 */
function getVideoDuration(file) {
  return new Promise((resolve, reject) => {
    const url = URL.createObjectURL(file);
    const el = document.createElement('video');
    el.preload = 'metadata';
    el.onloadedmetadata = () => {
      URL.revokeObjectURL(url);
      resolve(Math.round(el.duration));
    };
    el.onerror = () => { URL.revokeObjectURL(url); reject(new Error('Cannot read video metadata')); };
    el.src = url;
  });
}

export default function VideoUploadWidget({
  parentType, parentId, parentTitle, category: fixedCategory, onUploaded, compact = false,
}) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [duration, setDuration] = useState(null); // seconds
  const [category, setCategory] = useState(fixedCategory || 'progress');
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [gps, setGps] = useState({ lat: null, lng: null });
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);
  const fileRef = useRef(null);

  const maxMinutes = CATEGORY_LABELS[category]?.maxMinutes || 10;

  const handleFile = useCallback(async (f) => {
    if (!f) return;
    if (f.size > MAX_SIZE_MB * 1024 * 1024) {
      setError(`Video must be under ${MAX_SIZE_MB}MB`);
      return;
    }
    // Read duration client-side
    try {
      const dur = await getVideoDuration(f);
      setDuration(dur);
      const catMax = CATEGORY_LABELS[category]?.maxMinutes || 10;
      if (dur > catMax * 60) {
        setError(`${CATEGORY_LABELS[category]?.label || 'This'} video must be under ${catMax} minutes (yours is ${Math.floor(dur / 60)}:${String(dur % 60).padStart(2, '0')})`);
        return;
      }
    } catch {
      // Non-fatal — server will still check if needed
      setDuration(null);
    }
    setError(null);
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, [category]);

  const captureGps = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setGps({ lat: pos.coords.latitude, lng: pos.coords.longitude }),
      () => setError('Could not capture GPS'),
      { enableHighAccuracy: true, timeout: 10000 },
    );
  };

  const handleUpload = async () => {
    if (!file) return;
    setUploading(true);
    setError(null);
    try {
      const result = await uploadVideo({
        file,
        category,
        parentType,
        parentId,
        title: title || undefined, // server will auto-generate if empty
        description: description || undefined,
        gpsLatitude: gps.lat,
        gpsLongitude: gps.lng,
        durationSeconds: duration,
      });
      // Clean up
      if (preview) URL.revokeObjectURL(preview);
      setFile(null);
      setPreview(null);
      setTitle('');
      setDescription('');
      setDuration(null);
      onUploaded?.(result.video);
    } catch (err) {
      setError(err.message || 'Upload failed');
    } finally {
      setUploading(false);
    }
  };

  const clearFile = () => {
    if (preview) URL.revokeObjectURL(preview);
    setFile(null);
    setPreview(null);
    setDuration(null);
    setError(null);
  };

  return (
    <div className={`rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden ${compact ? 'p-3' : 'p-5'}`}>
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-amber-400 to-transparent" />

      {/* Category selector (hidden if fixed) */}
      {!fixedCategory && (
        <div className="flex flex-wrap gap-2 mb-4">
          {Object.entries(CATEGORY_LABELS).map(([key, { label, color }]) => (
            <button
              key={key}
              onClick={() => setCategory(key)}
              className={`px-3 py-1.5 rounded-full text-xs font-medium border transition
                ${category === key ? color : 'bg-gray-50 text-gray-400 border-gray-200 hover:bg-gray-100'}`}
            >
              {label}
            </button>
          ))}
        </div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-2 mb-3 text-xs text-red-600">{error}</div>
      )}

      {/* Drop zone / Preview */}
      {!file ? (
        <div
          onDragOver={(e) => { e.preventDefault(); e.currentTarget.classList.add('border-emerald-400'); }}
          onDragLeave={(e) => e.currentTarget.classList.remove('border-emerald-400')}
          onDrop={(e) => { e.preventDefault(); e.currentTarget.classList.remove('border-emerald-400'); handleFile(e.dataTransfer.files[0]); }}
          onClick={() => fileRef.current?.click()}
          className={`flex flex-col items-center justify-center border-2 border-dashed border-gray-300 rounded-xl
            text-gray-400 hover:border-emerald-400 hover:text-emerald-500 cursor-pointer transition
            ${compact ? 'py-6' : 'py-10'}`}
        >
          <HiOutlineCamera className="w-8 h-8 mb-2" />
          <span className="text-sm font-medium">Drop video here or click to select</span>
          <span className="text-xs mt-1">MP4, WebM, MOV — max {MAX_SIZE_MB}MB, {maxMinutes} min</span>
        </div>
      ) : (
        <div className="relative rounded-xl overflow-hidden bg-black mb-4">
          <video src={preview} controls playsInline preload="metadata" className="w-full aspect-video" />
          <button
            onClick={clearFile}
            className="absolute top-2 right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600 transition"
          >
            <HiOutlineXMark className="w-4 h-4" />
          </button>
        </div>
      )}

      <input
        ref={fileRef}
        type="file"
        accept="video/*"
        capture="environment"
        onChange={(e) => handleFile(e.target.files?.[0])}
        className="hidden"
      />

      {/* Metadata fields */}
      {file && (
        <div className="space-y-3 mt-4">
          {/* Duration badge */}
          {duration != null && (
            <div className={`flex items-center gap-2 text-xs font-medium px-3 py-1.5 rounded-lg ${
              duration > maxMinutes * 60
                ? 'bg-red-50 text-red-600'
                : 'bg-emerald-50 text-emerald-600'
            }`}>
              ⏱ {Math.floor(duration / 60)}:{String(duration % 60).padStart(2, '0')}
              {duration > maxMinutes * 60
                ? ` (exceeds ${maxMinutes} min limit)`
                : ` / ${maxMinutes} min max`}
            </div>
          )}

          <input
            value={title}
            onChange={(e) => setTitle(e.target.value)}
            placeholder={`Title (auto-generated if blank${parentTitle ? ` — e.g. "Progress Update — ${parentTitle}"` : ''})`}
            className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-emerald-200 focus:border-emerald-400 outline-none"
          />
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            rows={2}
            placeholder="Description (optional)"
            className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm resize-none focus:ring-2 focus:ring-emerald-200 focus:border-emerald-400 outline-none"
          />

          {/* GPS capture (especially for verification) */}
          {(category === 'verification' || category === 'progress') && (
            <div className="flex items-center gap-3">
              <button
                onClick={captureGps}
                className="px-3 py-2 rounded-lg bg-gray-100 text-gray-600 text-xs font-medium hover:bg-gray-200 transition"
              >
                📍 Capture GPS
              </button>
              {gps.lat && (
                <span className="text-xs text-gray-400 font-mono">
                  {gps.lat.toFixed(4)}, {gps.lng.toFixed(4)}
                </span>
              )}
            </div>
          )}

          {/* Upload button */}
          <button
            onClick={handleUpload}
            disabled={uploading || (duration != null && duration > maxMinutes * 60)}
            className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 text-white font-semibold
              hover:from-emerald-700 hover:to-green-700 transition disabled:opacity-50 flex items-center justify-center gap-2 text-sm"
          >
            <HiOutlineCloudArrowUp className="w-4 h-4" />
            {uploading ? 'Uploading…' : 'Upload Video'}
          </button>

          {/* File info */}
          <p className="text-xs text-gray-400 text-center">
            {file.name} — {(file.size / 1024 / 1024).toFixed(1)} MB
          </p>
        </div>
      )}
    </div>
  );
}
