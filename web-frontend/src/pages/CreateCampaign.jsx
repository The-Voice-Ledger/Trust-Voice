import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import useAuthStore from '../stores/authStore';
import { HiOutlineMapPin, HiOutlineFilm, HiOutlineVideoCameraSlash, HiOutlineRocketLaunch } from '../components/icons';
import { PageBg, PageHeader } from '../components/SvgDecorations';

const STEPS = ['basics', 'details', 'funding', 'media', 'review'];
const CATEGORIES = ['water', 'education', 'health', 'infrastructure', 'food', 'environment', 'shelter', 'children'];

export default function CreateCampaign() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Gate: must be logged in with an approved NGO
  if (!user) {
    return (
      <PageBg pattern="isometric" colorA="#0D9488" colorB="#10B981">
        <div className="max-w-lg mx-auto px-4 py-20 text-center">
          <h1 className="text-xl font-bold text-gray-900 mb-2">Sign in required</h1>
          <p className="text-gray-500 text-sm mb-4">You need to be logged in to create a campaign.</p>
          <a href="/login" className="text-emerald-600 text-sm hover:underline">Go to Login</a>
        </div>
      </PageBg>
    );
  }

  const isAdmin = ['SYSTEM_ADMIN', 'SUPER_ADMIN'].includes((user.role || '').toUpperCase());

  if (!user.ngo_id && !isAdmin) {
    return (
      <PageBg pattern="isometric" colorA="#0D9488" colorB="#10B981">
        <div className="max-w-lg mx-auto px-4 py-20 text-center">
          <h1 className="text-xl font-bold text-gray-900 mb-2">NGO account required</h1>
          <p className="text-gray-500 text-sm mb-4">
            Only approved NGOs can create campaigns. If you represent an NGO,{' '}
            <a href="/register-ngo" className="text-emerald-600 hover:underline">register your organisation</a>{' '}
            first and wait for admin approval.
          </p>
        </div>
      </PageBg>
    );
  }

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
    video_url: '',       // alternative: paste a YouTube/external video link
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
    <PageBg pattern="isometric" colorA="#0D9488" colorB="#10B981">
    <div className="max-w-2xl mx-auto px-4 py-8">
      <PageHeader icon={HiOutlineRocketLaunch} title={t('create_campaign.title')} subtitle={t('create_campaign.subtitle')} accentColor="green" bespoke="rocket" />

      {/* Progress */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((_, i) => (
          <div key={i} className={`flex-1 h-2 rounded-full transition ${i <= step ? 'bg-emerald-600' : 'bg-gray-200'}`} />
        ))}
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">{t(`create_campaign.step_${STEPS[step]}`)}</h2>
        <span className="text-xs text-gray-400">{step + 1}/{STEPS.length}</span>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-green-500 to-transparent" />
        <svg className="absolute top-2 right-2 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
          <circle cx="65" cy="28" r="20" stroke="#0D9488" strokeWidth="0.5" opacity="0.05" />
          <path d="M55 28 L65 18 L75 28" stroke="#0D9488" strokeWidth="0.4" opacity="0.04" />
          <path d="M60 32 L65 28 L70 32" stroke="#0D9488" strokeWidth="0.3" opacity="0.03" />
          <circle cx="65" cy="18" r="2" fill="#0D9488" opacity="0.05" />
        </svg>
        <svg className="absolute bottom-1 left-1 w-10 h-10 pointer-events-none" viewBox="0 0 40 40" fill="none">
          <path d="M0 40V25" stroke="#10B981" strokeWidth="0.5" opacity="0.04" />
          <path d="M0 40H15" stroke="#10B981" strokeWidth="0.5" opacity="0.04" />
          <circle cx="0" cy="40" r="1.5" fill="#10B981" opacity="0.05" />
        </svg>
        {step === 0 && (
          <div className="space-y-4">
            <Field label={t('create_campaign.campaign_title')} required value={form.title}
              onChange={(v) => set('title', v)} placeholder={t('create_campaign.title_placeholder')} />
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('create_campaign.description')} *</label>
              <textarea value={form.description} onChange={(e) => set('description', e.target.value)}
                rows={5} placeholder={t('create_campaign.desc_placeholder')}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('create_campaign.category')}</label>
              <div className="flex flex-wrap gap-2">
                {CATEGORIES.map((c) => (
                  <button key={c} type="button" onClick={() => set('category', c)}
                    className={`px-4 py-2 rounded-full text-xs font-medium border transition capitalize ${
                      form.category === c
                        ? 'bg-emerald-600 text-white border-emerald-600'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-emerald-300'
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
                  className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm">
                  {['USD', 'EUR', 'GBP', 'KES', 'ETB'].map((c) => <option key={c}>{c}</option>)}
                </select>
              </div>
            </div>
            <Field label={t('create_campaign.location')} value={form.location_name}
              onChange={(v) => set('location_name', v)} placeholder="e.g. Addis Ababa, Ethiopia" />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('create_campaign.gps')}</label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input value={form.location_gps} onChange={(e) => set('location_gps', e.target.value)}
                  placeholder="lat,lng" className="flex-1 rounded-lg border border-gray-200 px-3 py-3 text-sm" />
                <button type="button" onClick={getLocation}
                  className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg bg-gray-100 text-sm hover:bg-gray-200 transition">
                  <HiOutlineMapPin className="w-4 h-4" /> {t('create_campaign.auto_gps')}
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

            {/* Option 1: Upload video file */}
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
                  <div className="flex flex-col items-center">
                    <HiOutlineFilm className="w-10 h-10 text-emerald-500" />
                    <p className="text-sm font-medium text-gray-700 mt-2">{form.video_file.name}</p>
                    <p className="text-xs text-gray-400">{(form.video_file.size / 1024 / 1024).toFixed(1)} MB</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <HiOutlineVideoCameraSlash className="w-12 h-12 text-gray-300" />
                    <p className="text-sm text-gray-500 mt-2">{t('create_campaign.upload_video')}</p>
                    <p className="text-xs text-gray-400 mt-1">{t('create_campaign.video_note')}</p>
                  </div>
                )}
              </label>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-gray-200" />
              <span className="text-xs text-gray-400 uppercase tracking-wide">or</span>
              <div className="flex-1 h-px bg-gray-200" />
            </div>

            {/* Option 2: Paste video URL */}
            <Field
              label="Video URL (YouTube, Vimeo, etc.)"
              value={form.video_url}
              onChange={(v) => set('video_url', v)}
              placeholder="https://youtube.com/watch?v=..."
            />
          </div>
        )}

        {step === 4 && (
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900 mb-3">{t('create_campaign.review_title')}</h3>
            <ReviewRow label={t('create_campaign.campaign_title')} value={form.title} />
            <ReviewRow label={t('create_campaign.category')} value={form.category} />
            <ReviewRow label={t('create_campaign.description')} value={form.description} />
            <ReviewRow label={t('create_campaign.goal_amount')} value={`${form.goal_amount_usd} ${form.currency}`} />
            <ReviewRow label={t('create_campaign.location')} value={form.location_name || '-'} />
            <ReviewRow label={t('create_campaign.gps')} value={form.location_gps || '-'} />
            <ReviewRow label={t('create_campaign.start_date')} value={form.start_date || '-'} />
            <ReviewRow label={t('create_campaign.end_date')} value={form.end_date || '-'} />
            <ReviewRow label="Video" value={form.video_file?.name || form.video_url || 'No video'} />
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
            className="px-5 py-3 rounded-xl text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 transition">
            {t('create_campaign.next')} →
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={loading}
            className="px-6 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
            {loading ? t('common.loading') : t('create_campaign.publish')}
          </button>
        )}
      </div>
    </div>
    </PageBg>
  );
}

function Field({ label, required, value, onChange, placeholder, type = 'text' }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">{label} {required && '*'}</label>
      <input type={type} required={required} value={value} onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
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
