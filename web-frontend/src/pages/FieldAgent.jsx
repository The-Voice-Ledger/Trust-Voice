import { useState, useEffect, useRef } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate } from 'react-router-dom';
import { uploadPhoto, submitVerification, getPendingCampaigns, getVerificationHistory } from '../api/fieldAgent';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineCheckCircle, HiOutlineXMark, HiOutlineMapPin,
  HiOutlineCamera, HiOutlineSparkles,
} from 'react-icons/hi2';

const STEPS = ['photos', 'location', 'details', 'review'];

export default function FieldAgent() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const userId = user?.telegram_user_id || user?.id || 'web_anonymous';
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  // Form data
  const [photos, setPhotos] = useState([]); // { file, preview, uploadedPath }
  const [gps, setGps] = useState({ lat: '', lng: '', accuracy: null });
  const [campaigns, setCampaigns] = useState([]);
  const [history, setHistory] = useState([]);
  const [form, setForm] = useState({
    campaign_id: '',
    observations: '',
    beneficiary_count: '',
    testimonials: '',
  });

  const fileRef = useRef(null);

  // Auth guard — field agent must be logged in
  if (!user) return <Navigate to="/login" replace />;

  useEffect(() => {
    getPendingCampaigns(userId).then((d) => setCampaigns(Array.isArray(d) ? d : d?.campaigns || [])).catch(() => {});
    getVerificationHistory(userId).then((d) => setHistory(Array.isArray(d) ? d : d?.verifications || [])).catch(() => {});
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
      () => setError(t('field_agent.gps_error')),
      { enableHighAccuracy: true, timeout: 15000 }
    );
  };

  const canNext = () => {
    if (step === 0) return photos.length >= 1;
    if (step === 1) return gps.lat && gps.lng;
    if (step === 2) return form.campaign_id && form.observations.length >= 5;
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      // Upload photos first
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
        <div className="w-20 h-20 mx-auto rounded-full bg-green-100 flex items-center justify-center mb-4">
          <HiOutlineCheckCircle className="w-10 h-10 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('field_agent.success_title')}</h1>
        <p className="text-gray-500 mb-4">{t('field_agent.success_desc')}</p>
        <button onClick={() => { setSuccess(false); setStep(0); setPhotos([]); setForm({ campaign_id: '', observations: '', beneficiary_count: '', testimonials: '' }); }}
          className="px-5 py-2.5 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition">
          {t('field_agent.new_verification')}
        </button>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          {t('field_agent.title')}
          <HiOutlineCamera className="w-6 h-6 text-teal-500" />
        </h1>
        <p className="text-gray-500 text-sm mt-1">{t('field_agent.subtitle')}</p>
      </div>

      {/* Progress */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((_, i) => (
          <div key={i} className={`flex-1 h-2 rounded-full transition ${i <= step ? 'bg-teal-600' : 'bg-gray-200'}`} />
        ))}
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">{t(`field_agent.step_${STEPS[step]}`)}</h2>
        <span className="text-xs text-gray-400">{step + 1}/{STEPS.length}</span>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-6 mb-6">
        {/* Step 1: Photos */}
        {step === 0 && (
          <div>
            <p className="text-sm text-gray-500 mb-4">{t('field_agent.photo_desc')}</p>
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-3 mb-4">
              {photos.map((p, i) => (
                <div key={i} className="relative aspect-square rounded-xl overflow-hidden border border-gray-200">
                  <img src={p.preview} alt={`Photo ${i+1}`} className="w-full h-full object-cover" />
                  <button onClick={() => removePhoto(i)}
                    className="absolute top-1 right-1 w-7 h-7 bg-red-500 text-white rounded-full text-xs flex items-center justify-center hover:bg-red-600">
                    <HiOutlineXMark className="w-4 h-4" />
                  </button>
                </div>
              ))}
              {photos.length < 5 && (
                <button onClick={() => fileRef.current?.click()}
                  className="aspect-square rounded-xl border-2 border-dashed border-gray-300 flex flex-col items-center justify-center text-gray-400 hover:border-teal-400 hover:text-teal-500 transition">
                  <HiOutlineCamera className="w-7 h-7" />
                  <span className="text-xs mt-1">{t('field_agent.add_photo')}</span>
                </button>
              )}
            </div>
            <input ref={fileRef} type="file" accept="image/*" multiple capture="environment"
              onChange={(e) => addPhotos(e.target.files)} className="hidden" />
            <p className="text-xs text-gray-400">{photos.length}/5 {t('field_agent.photos_uploaded')}</p>
          </div>
        )}

        {/* Step 2: GPS */}
        {step === 1 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">{t('field_agent.gps_desc')}</p>
            <button onClick={getLocation}
              className="w-full py-4 rounded-xl border-2 border-dashed border-teal-300 bg-teal-50 text-teal-700 font-semibold hover:bg-teal-100 transition flex items-center justify-center gap-2">
              <HiOutlineMapPin className="w-5 h-5" /> {gps.lat ? t('field_agent.gps_refresh') : t('field_agent.gps_capture')}
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
            <p className="text-xs text-gray-400">{t('field_agent.gps_manual_note')}</p>
            <div className="grid grid-cols-2 gap-3">
              <input value={gps.lat} onChange={(e) => setGps((g) => ({ ...g, lat: e.target.value }))}
                placeholder="Latitude" className="rounded-lg border border-gray-200 px-3 py-2.5 text-sm" />
              <input value={gps.lng} onChange={(e) => setGps((g) => ({ ...g, lng: e.target.value }))}
                placeholder="Longitude" className="rounded-lg border border-gray-200 px-3 py-2.5 text-sm" />
            </div>
          </div>
        )}

        {/* Step 3: Details */}
        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('field_agent.select_campaign')} *</label>
              <select value={form.campaign_id} onChange={(e) => set('campaign_id', e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm">
                <option value="">{t('field_agent.choose_campaign')}</option>
                {campaigns.map((c) => (
                  <option key={c.id} value={c.id}>{c.title} (#{c.id})</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('field_agent.observations')} *</label>
              <textarea value={form.observations} onChange={(e) => set('observations', e.target.value)}
                rows={4} placeholder={t('field_agent.observations_placeholder')}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none focus:ring-2 focus:ring-teal-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('field_agent.beneficiary_count')}</label>
              <input type="number" value={form.beneficiary_count} onChange={(e) => set('beneficiary_count', e.target.value)}
                placeholder="e.g. 150" className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('field_agent.testimonials')}</label>
              <textarea value={form.testimonials} onChange={(e) => set('testimonials', e.target.value)}
                rows={3} placeholder={t('field_agent.testimonials_placeholder')}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none" />
            </div>
          </div>
        )}

        {/* Step 4: Review */}
        {step === 3 && (
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900">{t('field_agent.review_title')}</h3>

            <div className="flex gap-2 overflow-x-auto pb-2">
              {photos.map((p, i) => (
                <img key={i} src={p.preview} alt="" className="w-20 h-20 rounded-lg object-cover flex-shrink-0" />
              ))}
            </div>

            <ReviewRow label="GPS" value={`${gps.lat}, ${gps.lng}`} />
            <ReviewRow label={t('field_agent.select_campaign')}
              value={campaigns.find((c) => String(c.id) === form.campaign_id)?.title || form.campaign_id} />
            <ReviewRow label={t('field_agent.observations')} value={form.observations} />
            <ReviewRow label={t('field_agent.beneficiary_count')} value={form.beneficiary_count || '—'} />

            <div className="bg-teal-50 border border-teal-200 rounded-lg p-3 mt-4">
              <p className="text-sm text-teal-700 font-medium">{t('field_agent.earn_note')}</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}
          className="px-5 py-3 rounded-xl text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 disabled:opacity-30 transition">
          ← {t('common.back')}
        </button>
        {step < STEPS.length - 1 ? (
          <button onClick={() => setStep((s) => s + 1)} disabled={!canNext()}
            className="px-5 py-3 rounded-xl text-sm font-semibold bg-teal-600 text-white hover:bg-teal-700 disabled:opacity-50 transition">
            {t('field_agent.next')} →
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={loading}
            className="px-6 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
            {loading ? t('common.loading') : t('field_agent.submit')}
          </button>
        )}
      </div>

      {/* Past verifications */}
      {history.length > 0 && (
        <div className="mt-12">
          <h3 className="font-semibold text-gray-900 mb-4">{t('field_agent.history_title')}</h3>
          <div className="space-y-3">
            {history.map((v, i) => (
              <div key={i} className="bg-white rounded-xl border border-gray-100 p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                <div>
                  <p className="font-medium text-gray-900">Campaign #{v.campaign_id}</p>
                  <p className="text-xs text-gray-400">{v.created_at ? new Date(v.created_at).toLocaleDateString() : ''}</p>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                  v.status === 'approved' ? 'bg-green-50 text-green-600' :
                  v.status === 'rejected' ? 'bg-red-50 text-red-600' :
                  'bg-yellow-50 text-yellow-600'
                }`}>{v.status || 'pending'}</span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="flex flex-col sm:flex-row sm:justify-between py-2 border-b border-gray-50 last:border-0 gap-0.5">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900 sm:text-right sm:max-w-[60%] line-clamp-2">{value || '—'}</span>
    </div>
  );
}
