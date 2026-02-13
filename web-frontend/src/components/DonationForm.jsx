import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { createDonation } from '../api/donations';
import { HiOutlineCheckCircle } from 'react-icons/hi2';

const PRESETS_USD = [5, 10, 25, 50, 100];
const CURRENCIES = ['USD', 'KES', 'EUR', 'GBP', 'ETB'];
const METHODS = ['stripe', 'mpesa', 'crypto'];

export default function DonationForm({ campaignId, donorId, onSuccess }) {
  const { t } = useTranslation();
  const [amount, setAmount] = useState('');
  const [currency, setCurrency] = useState('USD');
  const [method, setMethod] = useState('stripe');
  const [phone, setPhone] = useState('');
  const [message, setMessage] = useState('');
  const [anonymous, setAnonymous] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const payload = {
        donor_id: donorId || 1, // fallback for demo
        campaign_id: campaignId,
        amount: parseFloat(amount),
        currency,
        payment_method: method,
        donor_message: message || undefined,
        is_anonymous: anonymous,
      };
      if (method === 'mpesa') payload.phone_number = phone;

      const result = await createDonation(payload);
      setSuccess(true);
      if (onSuccess) onSuccess(result);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  if (success) {
    return (
      <div className="text-center py-8 animate-fadeInUp">
        <div className="w-16 h-16 mx-auto rounded-full bg-green-50 flex items-center justify-center mb-3">
          <HiOutlineCheckCircle className="w-10 h-10 text-green-500" />
        </div>
        <p className="text-lg font-semibold text-green-600">{t('donate.success')}</p>
        {method === 'mpesa' && (
          <p className="text-sm text-gray-500 mt-2">{t('donate.mpesa_prompt')}</p>
        )}
      </div>
    );
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-5">
      {/* Amount presets */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">{t('donate.amount')}</label>
        <div className="flex gap-2 flex-wrap mb-2">
          {PRESETS_USD.map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => { setAmount(String(v)); setCurrency('USD'); }}
              className={`px-4 py-2 rounded-lg text-sm font-semibold border transition
                ${String(v) === amount && currency === 'USD'
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-indigo-300'}`}
            >
              ${v}
            </button>
          ))}
        </div>
        <div className="flex gap-2">
          <input
            type="number"
            min="1"
            step="any"
            required
            value={amount}
            onChange={(e) => setAmount(e.target.value)}
            placeholder="0.00"
            className="flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <select
            value={currency}
            onChange={(e) => setCurrency(e.target.value)}
            className="rounded-lg border border-gray-200 px-3 py-2 text-sm"
          >
            {CURRENCIES.map((c) => <option key={c} value={c}>{c}</option>)}
          </select>
        </div>
      </div>

      {/* Payment method */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">{t('donate.method')}</label>
        <div className="flex gap-2">
          {METHODS.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMethod(m)}
              className={`flex-1 py-2 rounded-lg text-sm font-medium border transition
                ${m === method
                  ? 'bg-indigo-600 text-white border-indigo-600'
                  : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'}`}
            >
              {t(`donate.method_${m}`)}
            </button>
          ))}
        </div>
      </div>

      {/* M-Pesa phone */}
      {method === 'mpesa' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('donate.phone_label')}</label>
          <input
            type="tel"
            required
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+254712345678"
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Message */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-1">{t('donate.message_label')}</label>
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          rows={2}
          maxLength={500}
          className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
        />
      </div>

      {/* Anonymous */}
      <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
        <input
          type="checkbox"
          checked={anonymous}
          onChange={(e) => setAnonymous(e.target.checked)}
          className="rounded border-gray-300 text-indigo-600 focus:ring-indigo-500"
        />
        {t('donate.anonymous')}
      </label>

      {error && <p className="text-sm text-red-500">{error}</p>}

      <button
        type="submit"
        disabled={loading || !amount}
        className="w-full py-3 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
      >
        {loading ? t('donate.processing') : t('donate.submit')}
      </button>
    </form>
  );
}
