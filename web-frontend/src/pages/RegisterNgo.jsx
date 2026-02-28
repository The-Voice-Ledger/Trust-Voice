import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { submitNgoRegistration } from '../api/ngoRegistrations';
import { api } from '../api/client';
import VoiceButton from '../components/VoiceButton';
import useAuthStore from '../stores/authStore';
import { HiOutlineCheckCircle } from 'react-icons/hi2';
import { HiOutlineMicrophone } from 'react-icons/hi';

const STEPS = ['org_info', 'contact', 'mission', 'banking', 'review'];
const ORG_TYPES = ['ngo', 'foundation', 'charity', 'cooperative', 'social_enterprise', 'community_group'];
const FOCUS_AREAS = ['water', 'education', 'health', 'infrastructure', 'food', 'environment', 'shelter', 'children', 'women', 'elderly'];

export default function RegisterNgo() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState(null);

  const [form, setForm] = useState({
    organization_name: '',
    registration_number: '',
    organization_type: 'ngo',
    contact_person_name: '',
    contact_email: '',
    phone_number: '',
    country: '',
    city: '',
    address: '',
    mission_statement: '',
    focus_areas: [],
    year_established: '',
    website_url: '',
    bank_name: '',
    bank_account_number: '',
    bank_branch: '',
    mpesa_paybill: '',
    telegram_user_id: user?.telegram_user_id || '',
  });

  const set = (field, value) => setForm((prev) => ({ ...prev, [field]: value }));

  const toggleFocus = (area) => {
    setForm((prev) => ({
      ...prev,
      focus_areas: prev.focus_areas.includes(area)
        ? prev.focus_areas.filter((a) => a !== area)
        : [...prev.focus_areas, area],
    }));
  };

  const canNext = () => {
    if (step === 0) return form.organization_name && form.registration_number && form.organization_type;
    if (step === 1) return form.contact_person_name && form.contact_email && form.phone_number;
    if (step === 2) return form.mission_statement && form.focus_areas.length > 0;
    if (step === 3) return true; // banking optional
    return true;
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError(null);
    try {
      await submitNgoRegistration(form);
      setSuccess(true);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  // Voice dictation handler — fills the active field
  const handleVoiceDictation = (result) => {
    if (result?.transcription) {
      // Auto-fill the first empty field in current step
      const txt = result.transcription;
      if (step === 0 && !form.organization_name) set('organization_name', txt);
      else if (step === 2 && !form.mission_statement) set('mission_statement', txt);
    }
  };

  if (success) {
    return (
      <div className="max-w-lg mx-auto px-4 py-20 text-center">
        <div className="w-20 h-20 mx-auto rounded-full bg-green-100 flex items-center justify-center mb-4">
          <HiOutlineCheckCircle className="w-10 h-10 text-green-600" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900 mb-2">{t('ngo_reg.success_title')}</h1>
        <p className="text-gray-500">{t('ngo_reg.success_desc')}</p>
      </div>
    );
  }

  return (
    <div className="max-w-2xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          {t('ngo_reg.title')}
          <HiOutlineMicrophone className="w-6 h-6 text-indigo-500" />
        </h1>
        <p className="text-gray-500 text-sm mt-1">{t('ngo_reg.subtitle')}</p>
      </div>

      {/* Progress bar */}
      <div className="flex gap-1 mb-8">
        {STEPS.map((s, i) => (
          <div
            key={s}
            className={`flex-1 h-2 rounded-full transition ${i <= step ? 'bg-indigo-600' : 'bg-gray-200'}`}
          />
        ))}
      </div>

      {/* Step label */}
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-lg font-semibold text-gray-900">
          {t(`ngo_reg.step_${STEPS[step]}`)}
        </h2>
        <span className="text-xs text-gray-400">{step + 1}/{STEPS.length}</span>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>
      )}

      {/* Step content */}
      <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-6 mb-6">
        {step === 0 && (
          <div className="space-y-4">
            <Field label={t('ngo_reg.org_name')} required value={form.organization_name}
              onChange={(v) => set('organization_name', v)} />
            <Field label={t('ngo_reg.reg_number')} required value={form.registration_number}
              onChange={(v) => set('registration_number', v)} placeholder="e.g. NGO/2024/001" />
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('ngo_reg.org_type')}</label>
              <select value={form.organization_type} onChange={(e) => set('organization_type', e.target.value)}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm">
                {ORG_TYPES.map((o) => <option key={o} value={o}>{o.replace(/_/g, ' ')}</option>)}
              </select>
            </div>
            <Field label={t('ngo_reg.year_established')} value={form.year_established}
              onChange={(v) => set('year_established', v)} placeholder="e.g. 2015" type="number" />
          </div>
        )}

        {step === 1 && (
          <div className="space-y-4">
            <Field label={t('ngo_reg.contact_name')} required value={form.contact_person_name}
              onChange={(v) => set('contact_person_name', v)} />
            <Field label={t('ngo_reg.contact_email')} required value={form.contact_email}
              onChange={(v) => set('contact_email', v)} type="email" />
            <Field label={t('ngo_reg.phone')} required value={form.phone_number}
              onChange={(v) => set('phone_number', v)} placeholder="+254..." type="tel" />
            <Field label={t('ngo_reg.country')} value={form.country} onChange={(v) => set('country', v)} />
            <Field label={t('ngo_reg.city')} value={form.city} onChange={(v) => set('city', v)} />
            <Field label={t('ngo_reg.address')} value={form.address} onChange={(v) => set('address', v)} />
            <Field label={t('ngo_reg.website')} value={form.website_url}
              onChange={(v) => set('website_url', v)} placeholder="https://..." />
          </div>
        )}

        {step === 2 && (
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">{t('ngo_reg.mission')} *</label>
              <textarea value={form.mission_statement} onChange={(e) => set('mission_statement', e.target.value)}
                rows={4} placeholder={t('ngo_reg.mission_placeholder')}
                className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm resize-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent" />
              <div className="mt-2">
                <VoiceButton
                  apiCall={async (blob) => {
                    // Use dictate-text voice endpoint
                    const fd = new FormData();
                    fd.append('audio', blob, `recording.${blob.ext || 'webm'}`);
                    fd.append('user_id', user?.telegram_user_id || 'web_anonymous');
                    return api.upload('/voice/dictate-text', fd);
                  }}
                  onResult={(r) => {
                    if (r?.transcription) set('mission_statement', (form.mission_statement ? form.mission_statement + ' ' : '') + r.transcription);
                  }}
                  className="!text-xs !py-1.5"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">{t('ngo_reg.focus_areas')}</label>
              <div className="flex flex-wrap gap-2">
                {FOCUS_AREAS.map((a) => (
                  <button key={a} type="button" onClick={() => toggleFocus(a)}
                    className={`px-4 py-2 rounded-full text-xs font-medium border transition capitalize ${
                      form.focus_areas.includes(a)
                        ? 'bg-indigo-600 text-white border-indigo-600'
                        : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'
                    }`}>
                    {a}
                  </button>
                ))}
              </div>
            </div>
          </div>
        )}

        {step === 3 && (
          <div className="space-y-4">
            <p className="text-sm text-gray-500 mb-2">{t('ngo_reg.banking_note')}</p>
            <Field label={t('ngo_reg.bank_name')} value={form.bank_name}
              onChange={(v) => set('bank_name', v)} />
            <Field label={t('ngo_reg.bank_account')} value={form.bank_account_number}
              onChange={(v) => set('bank_account_number', v)} />
            <Field label={t('ngo_reg.bank_branch')} value={form.bank_branch}
              onChange={(v) => set('bank_branch', v)} />
            <Field label={t('ngo_reg.mpesa_paybill')} value={form.mpesa_paybill}
              onChange={(v) => set('mpesa_paybill', v)} placeholder="e.g. 123456" />
          </div>
        )}

        {step === 4 && (
          <div className="space-y-4">
            <h3 className="font-semibold text-gray-900 mb-3">{t('ngo_reg.review_title')}</h3>
            <ReviewRow label={t('ngo_reg.org_name')} value={form.organization_name} />
            <ReviewRow label={t('ngo_reg.reg_number')} value={form.registration_number} />
            <ReviewRow label={t('ngo_reg.org_type')} value={form.organization_type} />
            <ReviewRow label={t('ngo_reg.contact_name')} value={form.contact_person_name} />
            <ReviewRow label={t('ngo_reg.contact_email')} value={form.contact_email} />
            <ReviewRow label={t('ngo_reg.phone')} value={form.phone_number} />
            <ReviewRow label={t('ngo_reg.country')} value={`${form.country} ${form.city}`} />
            <ReviewRow label={t('ngo_reg.mission')} value={form.mission_statement} />
            <ReviewRow label={t('ngo_reg.focus_areas')} value={form.focus_areas.join(', ')} />
            <ReviewRow label={t('ngo_reg.bank_name')} value={form.bank_name || '-'} />
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="flex justify-between">
        <button
          onClick={() => setStep((s) => Math.max(0, s - 1))}
          disabled={step === 0}
          className="px-5 py-3 rounded-xl text-sm font-medium text-gray-600 bg-gray-100 hover:bg-gray-200 disabled:opacity-30 transition"
        >
          ← {t('common.back')}
        </button>

        {step < STEPS.length - 1 ? (
          <button
            onClick={() => setStep((s) => s + 1)}
            disabled={!canNext()}
            className="px-5 py-3 rounded-xl text-sm font-semibold bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition"
          >
            {t('ngo_reg.next')} →
          </button>
        ) : (
          <button
            onClick={handleSubmit}
            disabled={loading}
            className="px-6 py-3 rounded-xl text-sm font-semibold bg-green-600 text-white hover:bg-green-700 disabled:opacity-50 transition"
          >
            {loading ? t('common.loading') : t('ngo_reg.submit')}
          </button>
        )}
      </div>
    </div>
  );
}

/* ── Shared ──────────────────────────────── */
function Field({ label, required, value, onChange, placeholder, type = 'text' }) {
  return (
    <div>
      <label className="block text-sm font-medium text-gray-700 mb-1">
        {label} {required && '*'}
      </label>
      <input
        type={type}
        required={required}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="w-full rounded-lg border border-gray-200 px-3 py-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
      />
    </div>
  );
}

function ReviewRow({ label, value }) {
  return (
    <div className="flex flex-col sm:flex-row sm:justify-between py-2 border-b border-gray-50 last:border-0 gap-0.5">
      <span className="text-sm text-gray-500">{label}</span>
      <span className="text-sm font-medium text-gray-900 sm:text-right sm:max-w-[60%]">{value || '-'}</span>
    </div>
  );
}
