import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import VoiceButton from '../components/VoiceButton';
import useAuthStore from '../stores/authStore';

const STEPS = ['basics', 'details', 'funding', 'media', 'review'];
const CATEGORIES = ['water', 'education', 'health', 'infrastructure', 'food', 'environment', 'shelter', 'children'];

export default function CreateCampaign() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    title: '',
    description: '',
    category: 'education',
    goal_amount_usd: '',
    currency: 'USD',
    location_name: '',
    location_gps: '',
    start_date: '',
    end_date: '',
    ngo_id: user?.ngo_id || '',
    video_file: null,
  });

  const set = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const canNext = () => {
    if (step === 0) return form.title.length >= 3;
    if (step === 1) return form.description.length >= 10 && form.category;
    if (step === 2) return form.goal_amount_usd > 0;
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      const payload = {
        title: form.title,
        description: form.description,
        category: form.category,
        goal_amount_usd: parseFloat(form.goal_amount_usd),
        currency: form.currency,
        location_name: form.location_name || undefined,
        location_gps: form.location_gps || undefined,
        start_date: form.start_date || undefined,
        end_date: form.end_date || undefined,
        ngo_id: form.ngo_id || undefined,
      };

      const campaign = await api.post('/campaigns/', payload);

      // Upload video if provided
      if (form.video_file && campaign?.id) {
        const fd = new FormData();
        fd.append('video', form.video_file);
        await api.upload(`/campaigns/${campaign.id}/upload-video`, fd);
      }

      navigate(`/campaign/${campaign.id}`);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Get GPS location
  const getLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => set('location_gps', `${pos.coords.latitude},${pos.coords.longitude}`),
      () => {},
      { enableHighAccuracy: true }
    );
  };

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">{t('create_campaign.title')} 🎤</h1>
        <p className="text-gray-500 text-sm mt-1">{t('create_campaign.subtitle')}</p>
      </div>

      {/* Progress */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((_, i) => (
          <div key={i} className={`flex-1 h-2 rounded-full transition ${i <= step ? 'bg-indigo-600' : 'bg-gray-200'}`} />
        ))}
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">{t(`create_campaign.step_${STEPS[step]}`)}</h2>
        <span className="text-xs text-gray-400">{step + 1}/{STEPS.length}</span>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-6 mb-6">
        {step === 0 && (
          <div className="space-y-4">
            <Field label={t('create_campaign.campaign_title')} required value={form.title}
              onChange={(v) => set('title', v)} placeholder={t('create_campaign.title_placeholder')} />
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-500">{t('create_campaign.or_dictate')}</span>
              <VoiceButton
                apiCall={async (blob) => {
                  const fd = new FormData();
                  fd.append('audio', blob, 'recording.webm');
                  fd.append('user_id', user?.telegram_user_id || 'web_anonymous');
                  const res = await fetch('/api/voice/dictate-text', { method: 'POST', body: fd });
                  return res.json();
                }}
                onResult={(r) => { if (r?.transcription) set('title', r.transcription); }}
                className="!text-xs !py-1.5"
              />
            </div>
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('create_campaign.description')} *</label>
              <textarea value={form.description} onChange={(e) => set('description', e.target.value)}
                rows={5} placeholder={t('create_campaign.desc_placeholder')}
                className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
              <VoiceButton
                apiCall={async (blob) => {
                  const fd = new FormData();
                  fd.append('audio', blob, 'recording.webm');
                  fd.append('user_id', user?.telegram_user_id || 'web_anonymous');
                  const res = await fetch('/api/voice/dictate-text', { method: 'POST', body: fd });
                  return res.json();
                }}
                onResult={(r) => {
                  if (r?.transcription) set('description', (form.description ? form.description + ' ' : '') + r.transcription);
                }}
                className="mt-2 !text-xs !py-1.5"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('create_campaign.category')}</label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((c) => (
                  <button key={c} type="button" onClick={() => set('category', c)}
                    className={`px-3 py-1.5 rounded-full text-xs font-medium border transition capitalize ${
                      form.category === c
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'
                    }`}>
                    {c}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Field label={t('create_campaign.goal_amount')} required type="number"
                  value={form.goal_amount_usd} onChange={(v) => set('goal_amount_usd', v)} placeholder="10000" />
              </div>
              <div className="w-24">
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <select value={form.currency} onChange={(e) => set('currency', e.target.value)}
                  className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm">
                  {['USD', 'EUR', 'GBP', 'KES', 'ETB'].map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <Field label={t('create_campaign.location')} value={form.location_name}
              onChange={(v) => set('location_name', v)} placeholder="e.g. Addis Ababa, Ethiopia" />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('create_campaign.gps')}</label>
              <div className="flex gap-2">
                <input value={form.location_gps} onChange={(e) => set('location_gps', e.target.value)}
                  placeholder="lat,lng" className="flex-1 rounded-lg border border-gray-200 px-3 py-2.5 text-sm" />
                <button type="button" onClick={getLocation}
                  className="px-3 py-2 rounded-lg bg-gray-100 text-sm hover:bg-gray-200 transition">
                  📍 {t('create_campaign.auto_gps')}
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label={t('create_campaign.start_date')} type="date" value={form.start_date}
                onChange={(v) => set('start_date', v)} />
              <Field label={t('create_campaign.end_date')} type="date" value={form.end_date}
                onChange={(v) => set('end_date', v)} />
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">{t('create_campaign.media_desc')}</p>
            <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
              <input
                type="file"
                accept="video/*"
                onChange={(e) => set('video_file', e.target.files?.[0] || null)}
                className="hidden"
                id="video-upload"
              />
              <label htmlFor="video-upload" className="cursor-pointer">
                {form.video_file ? (
                  <div>
                    <span className="text-3xl">🎬</span>
                    <p className="text-sm font-medium text-gray-700 mt-2">{form.video_file.name}</p>
                    <p className="text-xs text-gray-400">{(form.video_file.size / 1024 / 1024).toFixed(1)} MB</p>
                  </div>
                ) : (
                  <div>
                    <span className="text-4xl text-gray-300">🎥</span>
                    <p className="text-sm text-gray-500 mt-2">{t('create_campaign.upload_video')}</p>
                    <p className="text-xs text-gray-400 mt-1">{t('create_campaign.video_note')}</p>
                  </div>
                )}
              </label>
            </div>
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900 mb-3">{t('create_campaign.review_title')}</h3>
            <ReviewRow label={t('create_campaign.campaign_title')} value={form.title} />
            <ReviewRow label={t('create_campaign.category')} value={form.category} />
            <ReviewRow label={t('create_campaign.description')} value={form.description} />
            <ReviewRow label={t('create_campaign.goal_amount')} value={`${form.goal_amount_usd} ${form.currency}`} />
            <ReviewRow label={t('create_campaign.location')} value={form.location_name || '—'} />
            <ReviewRow label={t('create_campaign.gps')} value={form.location_gps || '—'} />
            <ReviewRow label={t('create_campaign.start_date')} value={form.start_date || '—'} />
            <ReviewRow label={t('create_campaign.end_date')} value={form.end_date || '—'} />
            <ReviewRow label="Video" value={form.video_file?.name || 'No video'} />
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button onClick={() => setStep((s) => Math.max(0, s - 1))} disabled={step === 0}
          className="px-5 py-2.5 rounded-xl text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 disabled:opacity-30 transition">
          ← {t('common.back')}
        </button>
        {step < STEPS.length - 1 ? (
          <button onClick={() => setStep((s) => s + 1)} disabled={!canNext()}
            className="px-5 py-2.5 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition">
            {t('create_campaign.next')} →
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={loading}
            className="px-6 py-2.5 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
            {loading ? t('common.loading') : t('create_campaign.publish')}
          </button>
        )}
      </div>
    </div>
  );
}

function Field({ label, required, value, onChange, placeholder, type = 'text' }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label} {required && '*'}</label>
      <input type={type} required={required} value={value} onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-200 px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
    </div>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="flex justify-between py-2 border-b border-gray-50 last:border-0">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900 text-right max-w-[60%] line-clamp-2">{value || '—'}</span>
    </div>
  );
}
