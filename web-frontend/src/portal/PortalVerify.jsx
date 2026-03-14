/**
 * PortalVerify — field agent verification wizard inside the portal.
 *
 * 5-step wizard: photos → video → location → details → review → submit.
 * Adapted from FieldAgent.jsx for the portal sidebar layout.
 * Now includes video evidence upload (Act: verification).
 */
import { useState, useEffect, useRef } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { uploadPhoto, submitVerification, getPendingCampaigns } from '../api/fieldAgent';
import { uploadVideo } from '../api/videos';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineCheckCircle, HiOutlineXMark, HiOutlineMapPin,
  HiOutlineCamera, HiOutlineArrowLeft, HiOutlineFilm,
} from '../components/icons';

const STEPS = ['photos', 'video', 'location', 'details', 'review'];

export default function PortalVerify() {
  const { t } = useTranslation();
  const [searchParams] = useSearchParams();
  const user = useAuthStore((s) => s.user);
  const userId = user?.telegram_user_id || user?.id || 'web_anonymous';
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Form data
  const [photos, setPhotos] = useState([]);
  const [videoFile, setVideoFile] = useState(null);
  const [videoPreview, setVideoPreview] = useState(null);
  const [videoUploaded, setVideoUploaded] = useState(false);
  const [gps, setGps] = useState({ lat: '', lng: '', accuracy: null });
  const [campaigns, setCampaigns] = useState([]);
  const [form, setForm] = useState({
    campaign_id: searchParams.get('campaign') || '',
    observations: '',
    beneficiary_count: '',
    testimonials: '',
  });

  const fileRef = useRef(null);
  const videoRef = useRef(null);

  useEffect(() => {
    getPendingCampaigns(userId)
      .then((d) => setCampaigns(Array.isArray(d) ? d : d?.campaigns || []))
      .catch(() => {});
  }, [userId]);

  const set = (f, v) => setForm((p) => ({ ...p, [f]: v }));

  // Photo handling
  const addPhotos = (files) => {
    const newPhotos = Array.from(files).slice(0, 5 - photos.length).map((file) => ({
      file,
      preview: URL.createObjectURL(file),
      uploadedPath: null,
    }));
    setPhotos((prev) => [...prev, ...newPhotos].slice(0, 5));
  };

  const removePhoto = (i) => {
    setPhotos((prev) => {
      URL.revokeObjectURL(prev[i].preview);
      return prev.filter((_, idx) => idx !== i);
    });
  };

  // GPS
  const getLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => setGps({ lat: pos.coords.latitude.toFixed(6), lng: pos.coords.longitude.toFixed(6), accuracy: Math.round(pos.coords.accuracy) }),
      () => setError('Could not get GPS location. Please enter coordinates manually.'),
      { enableHighAccuracy: true, timeout: 15000 }
    );
  };

  const canNext = () => {
    if (step === 0) return photos.length >= 1;
    if (step === 1) return true; // video is optional
    if (step === 2) return gps.lat && gps.lng;
    if (step === 3) return form.campaign_id && form.observations.length >= 5;
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const photoPaths = [];
      for (const photo of photos) {
        if (!photo.uploadedPath) {
          const result = await uploadPhoto(userId, photo.file);
          photoPaths.push(result.photo_id || '');
        } else {
          photoPaths.push(photo.uploadedPath);
        }
      }

      await submitVerification({
        telegram_user_id: userId,
        campaign_id: form.campaign_id,
        photo_ids: photoPaths,
        gps_latitude: parseFloat(gps.lat),
        gps_longitude: parseFloat(gps.lng),
        gps_accuracy: gps.accuracy,
        description: form.observations,
        beneficiary_count: form.beneficiary_count ? parseInt(form.beneficiary_count) : undefined,
        testimonials: form.testimonials || undefined,
      });

      // Upload verification video if provided (best-effort, non-blocking)
      if (videoFile && !videoUploaded) {
        try {
          await uploadVideo({
            file: videoFile,
            category: 'verification',
            parentType: 'campaign',
            parentId: parseInt(form.campaign_id),
            title: `Field verification: ${form.observations.slice(0, 80)}`,
            description: form.observations,
            gpsLatitude: parseFloat(gps.lat) || undefined,
            gpsLongitude: parseFloat(gps.lng) || undefined,
          });
        } catch (videoErr) {
          console.warn('Video upload failed (verification still submitted):', videoErr);
        }
      }

      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <HiOutlineCheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">Verification Submitted!</h1>
        <p className="text-gray-500 text-sm mb-6">Your field report has been recorded. It will be reviewed and linked to the campaign.</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <button onClick={() => { setSuccess(false); setStep(0); setPhotos([]); setVideoFile(null); setVideoPreview(null); setVideoUploaded(false); setForm({ campaign_id: '', observations: '', beneficiary_count: '', testimonials: '' }); setGps({ lat: '', lng: '', accuracy: null }); }}
            className="px-5 py-2.5 rounded-xl bg-green-600 text-white font-semibold hover:bg-green-700 transition text-sm">
            New Verification
          </button>
          <Link to="/portal"
            className="px-5 py-2.5 rounded-xl bg-gray-100 text-gray-700 font-semibold hover:bg-gray-200 transition text-sm">
            Back to Dashboard
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <Link to="/portal" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition mb-3">
        <HiOutlineArrowLeft className="w-4 h-4" /> Back to dashboard
      </Link>
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Field Verification</h1>
        <p className="text-sm text-gray-500 mt-1">Document on-the-ground impact with photos, GPS, and observations</p>
      </div>

      {/* Progress */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((_, i) => (
          <div key={i} className={`flex-1 h-2 rounded-full transition ${i <= step ? 'bg-green-600' : 'bg-gray-200'}`} />
        ))}
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 capitalize">{STEPS[step]}</h2>
        <span className="text-xs text-gray-400">{step + 1}/{STEPS.length}</span>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      {/* Form card */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-emerald-500 to-transparent" />

        {/* Step 1: Photos */}
        {step === 0 && (
          <div>
            <p className="text-sm text-gray-500 mb-4">Take or upload at least 1 photo showing the project site, beneficiaries, or progress.</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
              {photos.map((p, i) => (
                <div key={i} className="relative aspect-square rounded-xl overflow-hidden border border-gray-200">
                  <img src={p.preview} alt={`Photo ${i + 1}`} className="w-full h-full object-cover" />
                  <button onClick={() => removePhoto(i)}
                    className="absolute top-1 right-1 w-7 h-7 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600">
                    <HiOutlineXMark className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {photos.length < 5 && (
                <button onClick={() => fileRef.current?.click()}
                  className="aspect-square rounded-xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center text-gray-400 hover:border-green-400 hover:text-green-500 transition">
                  <HiOutlineCamera className="w-7 h-7" />
                  <span className="text-xs mt-1">Add Photo</span>
                </button>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/*" multiple capture="environment"
              onChange={(e) => addPhotos(e.target.files)} className="hidden" />
            <p className="text-xs text-gray-400">{photos.length}/5 photos</p>
          </div>
        )}

        {/* Step 2: Video (optional) */}
        {step === 1 && (
          <div>
            <p className="text-sm text-gray-500 mb-4">
              Record or upload a short video showing the project site. This provides powerful visual evidence. <span className="text-gray-400">(Optional — you can skip this step)</span>
            </p>
            {!videoFile ? (
              <button
                onClick={() => videoRef.current?.click()}
                className="w-full py-10 rounded-xl border-2 border-dashed border-purple-300 bg-purple-50 text-purple-600 font-semibold hover:bg-purple-100 transition flex flex-col items-center justify-center gap-2"
              >
                <HiOutlineFilm className="w-8 h-8" />
                <span>Record or Select Video</span>
                <span className="text-xs font-normal text-purple-400">MP4, WebM, MOV — max 100MB</span>
              </button>
            ) : (
              <div className="relative rounded-xl overflow-hidden bg-black mb-3">
                <video src={videoPreview} controls playsInline preload="metadata" className="w-full aspect-video" />
                <button
                  onClick={() => { if (videoPreview) URL.revokeObjectURL(videoPreview); setVideoFile(null); setVideoPreview(null); }}
                  className="absolute top-2 right-2 w-8 h-8 bg-red-500 text-white rounded-full flex items-center justify-center hover:bg-red-600"
                >
                  <HiOutlineXMark className="w-4 h-4" />
                </button>
              </div>
            )}
            {videoFile && (
              <p className="text-xs text-gray-400">{videoFile.name} — {(videoFile.size / 1024 / 1024).toFixed(1)} MB</p>
            )}
            <input
              ref={videoRef}
              type="file"
              accept="video/*"
              capture="environment"
              onChange={(e) => {
                const f = e.target.files?.[0];
                if (f) {
                  setVideoFile(f);
                  setVideoPreview(URL.createObjectURL(f));
                }
              }}
              className="hidden"
            />
          </div>
        )}

        {/* Step 3: GPS */}
        {step === 2 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">Capture or enter your current GPS location for verification.</p>
            <button onClick={getLocation}
              className="w-full py-4 rounded-xl border-2 border-dashed border-green-300 bg-green-50 text-green-700 font-semibold hover:bg-green-100 transition flex items-center justify-center gap-2">
              <HiOutlineMapPin className="w-5 h-5" /> {gps.lat ? 'Refresh Location' : 'Capture GPS'}
            </button>
            {gps.lat && (
              <div className="bg-gray-50 rounded-lg p-4 text-sm">
                <div className="grid grid-cols-2 gap-3">
                  <div>
                    <span className="text-gray-400">Latitude</span>
                    <p className="font-mono text-gray-700">{gps.lat}</p>
                  </div>
                  <div>
                    <span className="text-gray-400">Longitude</span>
                    <p className="font-mono text-gray-700">{gps.lng}</p>
                  </div>
                </div>
                {gps.accuracy && (
                  <p className="text-xs text-gray-400 mt-2">Accuracy: ±{gps.accuracy}m</p>
                )}
              </div>
            )}
            <p className="text-xs text-gray-400">Or enter coordinates manually:</p>
            <div className="grid grid-cols-2 gap-3">
              <input value={gps.lat} onChange={(e) => setGps((g) => ({ ...g, lat: e.target.value }))}
                placeholder="Latitude" className="rounded-lg border border-gray-200 px-3 py-2.5 text-sm" />
              <input value={gps.lng} onChange={(e) => setGps((g) => ({ ...g, lng: e.target.value }))}
                placeholder="Longitude" className="rounded-lg border border-gray-200 px-3 py-2.5 text-sm" />
            </div>
          </div>
        )}

        {/* Step 4: Details */}
        {step === 3 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Campaign *</label>
              <select value={form.campaign_id} onChange={(e) => set('campaign_id', e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm">
                <option value="">Choose a campaign…</option>
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>{c.title} (#{c.id})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Observations *</label>
              <textarea value={form.observations} onChange={(e) => set('observations', e.target.value)}
                rows={4} placeholder="Describe what you observed on site…"
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none focus:ring-2 focus:ring-green-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Beneficiary Count</label>
              <input type="number" value={form.beneficiary_count} onChange={(e) => set('beneficiary_count', e.target.value)}
                placeholder="e.g. 150" className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Testimonials</label>
              <textarea value={form.testimonials} onChange={(e) => set('testimonials', e.target.value)}
                rows={3} placeholder="Direct quotes from beneficiaries…"
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none" />
            </div>
          </div>
        )}

        {/* Step 5: Review */}
        {step === 4 && (
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">Review your verification</h3>
            <div className="flex gap-2 overflow-x-auto pb-2">
              {photos.map((p, i) => (
                <img key={i} src={p.preview} alt="" className="w-20 h-20 rounded-lg object-cover flex-shrink-0" />
              ))}
            </div>
            <ReviewRow label="GPS" value={`${gps.lat}, ${gps.lng}`} />
            <ReviewRow label="Video" value={videoFile ? `${videoFile.name} (${(videoFile.size / 1024 / 1024).toFixed(1)} MB)` : 'None'} />
            <ReviewRow label="Campaign" value={campaigns.find((c) => String(c.id) === form.campaign_id)?.title || form.campaign_id} />
            <ReviewRow label="Observations" value={form.observations} />
            <ReviewRow label="Beneficiaries" value={form.beneficiary_count || '-'} />
            <div className="bg-green-50 border border-green-200 rounded-lg p-3 mt-4">
              <p className="text-sm text-green-700 font-medium">Your verification builds trust and may earn you rewards.</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}
          className="px-5 py-3 rounded-xl text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 disabled:opacity-30 transition">
          ← Back
        </button>
        {step < STEPS.length - 1 ? (
          <button onClick={() => setStep((s) => s + 1)} disabled={!canNext()}
            className="px-5 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
            Next →
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={loading}
            className="px-6 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
            {loading ? 'Submitting…' : 'Submit Verification'}
          </button>
        )}
      </div>
    </div>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="flex flex-col sm:flex-row sm:justify-between py-2 border-b border-gray-50 last:border-0 gap-0.5">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900 sm:text-right sm:max-w-[60%] line-clamp-2">{value || '-'}</span>
    </div>
  );
}
