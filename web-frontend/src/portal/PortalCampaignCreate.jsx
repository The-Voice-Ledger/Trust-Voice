/**
 * PortalCampaignCreate — campaign creation wizard inside the portal.
 *
 * 5-step wizard: basics → details → funding → media → review.
 * Gated on the user having a verified NGO (ngo_id).
 * After creation, navigates to the campaign editor for further setup.
 */
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { api } from '../api/client';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineMapPin, HiOutlineFilm, HiOutlineVideoCameraSlash,
  HiOutlineRocketLaunch, HiOutlineCheckCircle, HiOutlineArrowLeft,
} from '../components/icons';

const STEPS = ['basics', 'details', 'funding', 'media', 'review'];
const CATEGORIES = ['water', 'education', 'health', 'infrastructure', 'food', 'environment', 'shelter', 'children'];

export default function PortalCampaignCreate() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

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
    video_url: '',
  });

  // Gate: must have ngo_id
  if (!user?.ngo_id) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <HiOutlineRocketLaunch className="w-12 h-12 text-gray-300 mx-auto mb-4" />
        <h1 className="text-xl font-bold text-gray-900 mb-2">NGO account required</h1>
        <p className="text-gray-500 text-sm mb-4">
          Only verified NGOs can create campaigns. If you represent an NGO,{' '}
          <Link to="/register-ngo" className="text-emerald-600 hover:underline">register your organisation</Link>{' '}
          first and wait for admin approval.
        </p>
      </div>
    );
  }

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

      setSuccess(campaign);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getLocation = () => {
    if (!navigator.geolocation) return;
    navigator.geolocation.getCurrentPosition(
      (pos) => set('location_gps', `${pos.coords.latitude},${pos.coords.longitude}`),
      () => {},
      { enableHighAccuracy: true }
    );
  };

  // Success state
  if (success) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <div className="w-16 h-16 rounded-full bg-green-100 flex items-center justify-center mx-auto mb-4">
          <HiOutlineCheckCircle className="w-8 h-8 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('create_campaign.success_title') || 'Campaign Created!'}</h1>
        <p className="text-gray-500 text-sm mb-6">Your campaign is live. Add milestones, videos, and updates to build trust with funders.</p>
        <div className="flex flex-col sm:flex-row gap-3 justify-center">
          <Link to={`/portal/projects/${success.id}/edit`}
            className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition text-sm">
            Edit Campaign
          </Link>
          <Link to={`/portal/projects/${success.id}/milestones`}
            className="px-5 py-2.5 rounded-xl bg-green-50 text-green-700 font-semibold hover:bg-green-100 transition text-sm border border-green-100">
            Add Milestones
          </Link>
          <Link to="/portal/projects"
            className="px-5 py-2.5 rounded-xl bg-gray-100 text-gray-700 font-semibold hover:bg-gray-200 transition text-sm">
            My Projects
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-6">
        <Link to="/portal/projects" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition mb-3">
          <HiOutlineArrowLeft className="w-4 h-4" /> Back to projects
        </Link>
        <h1 className="text-2xl font-bold text-gray-900">Create Campaign</h1>
        <p className="text-sm text-gray-500 mt-1">Launch a new campaign for your organisation</p>
      </div>

      {/* Progress */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((_, i) => (
          <div key={i} className={`flex-1 h-2 rounded-full transition ${i <= step ? 'bg-emerald-600' : 'bg-gray-200'}`} />
        ))}
      </div>

      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900 capitalize">{STEPS[step]}</h2>
        <span className="text-xs text-gray-400">{step + 1}/{STEPS.length}</span>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      {/* Form card */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />

        {/* Step 1: Basics */}
        {step === 0 && (
          <div className="space-y-4">
            <Field label="Campaign Title" required value={form.title}
              onChange={(v) => set('title', v)} placeholder="e.g. Clean Water for Kibera Community" />
          </div>
        )}

        {/* Step 2: Details */}
        {step === 1 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">Description *</label>
              <textarea value={form.description} onChange={(e) => set('description', e.target.value)}
                rows={5} placeholder="Describe the campaign's goals, who it helps, and why it matters…"
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none focus:ring-2 focus:ring-emerald-500 focus:border-transparent" />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
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

        {/* Step 3: Funding */}
        {step === 2 && (
          <div className="space-y-4">
            <div className="flex gap-3">
              <div className="flex-1">
                <Field label="Goal Amount" required type="number"
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
            <Field label="Location" value={form.location_name}
              onChange={(v) => set('location_name', v)} placeholder="e.g. Addis Ababa, Ethiopia" />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">GPS Coordinates</label>
              <div className="flex flex-col sm:flex-row gap-2">
                <input value={form.location_gps} onChange={(e) => set('location_gps', e.target.value)}
                  placeholder="lat,lng" className="flex-1 rounded-lg border border-gray-200 px-3 py-3 text-sm" />
                <button type="button" onClick={getLocation}
                  className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-lg bg-gray-100 text-sm hover:bg-gray-200 transition">
                  <HiOutlineMapPin className="w-4 h-4" /> Auto-detect
                </button>
              </div>
            </div>
            <div className="grid grid-cols-2 gap-3">
              <Field label="Start Date" type="date" value={form.start_date} onChange={(v) => set('start_date', v)} />
              <Field label="End Date" type="date" value={form.end_date} onChange={(v) => set('end_date', v)} />
            </div>
          </div>
        )}

        {/* Step 4: Media */}
        {step === 3 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500">Add a transparency video to build trust with funders.</p>
            <div className="border-2 border-dashed border-gray-200 rounded-xl p-8 text-center">
              <input type="file" accept="video/*" onChange={(e) => set('video_file', e.target.files?.[0] || null)}
                className="hidden" id="portal-video-upload" />
              <label htmlFor="portal-video-upload" className="cursor-pointer">
                {form.video_file ? (
                  <div className="flex flex-col items-center">
                    <HiOutlineFilm className="w-10 h-10 text-emerald-500" />
                    <p className="text-sm font-medium text-gray-700 mt-2">{form.video_file.name}</p>
                    <p className="text-xs text-gray-400">{(form.video_file.size / 1024 / 1024).toFixed(1)} MB</p>
                  </div>
                ) : (
                  <div className="flex flex-col items-center">
                    <HiOutlineVideoCameraSlash className="w-12 h-12 text-gray-300" />
                    <p className="text-sm text-gray-500 mt-2">Click to upload a video</p>
                    <p className="text-xs text-gray-400 mt-1">MP4, MOV, WebM - max 100 MB</p>
                  </div>
                )}
              </label>
            </div>
            <div className="flex items-center gap-3">
              <div className="flex-1 h-px bg-gray-200" />
              <span className="text-xs text-gray-400 uppercase tracking-wide">or</span>
              <div className="flex-1 h-px bg-gray-200" />
            </div>
            <Field label="Video URL (YouTube, Vimeo, etc.)" value={form.video_url}
              onChange={(v) => set('video_url', v)} placeholder="https://youtube.com/watch?v=..." />
          </div>
        )}

        {/* Step 5: Review */}
        {step === 4 && (
          <div className="space-y-3">
            <h3 className="font-semibold text-gray-900 mb-3">Review & publish</h3>
            <ReviewRow label="Title" value={form.title} />
            <ReviewRow label="Category" value={form.category} />
            <ReviewRow label="Description" value={form.description} />
            <ReviewRow label="Goal" value={`${form.goal_amount_usd} ${form.currency}`} />
            <ReviewRow label="Location" value={form.location_name || '-'} />
            <ReviewRow label="GPS" value={form.location_gps || '-'} />
            <ReviewRow label="Start" value={form.start_date || '-'} />
            <ReviewRow label="End" value={form.end_date || '-'} />
            <ReviewRow label="Video" value={form.video_file?.name || form.video_url || 'No video'} />
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
            className="px-5 py-3 rounded-xl text-sm font-semibold bg-emerald-600 text-white hover:bg-emerald-700 disabled:opacity-50 transition">
            Next →
          </button>
        ) : (
          <button onClick={handleSubmit} disabled={loading}
            className="px-6 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition">
            {loading ? 'Publishing…' : 'Publish Campaign'}
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
