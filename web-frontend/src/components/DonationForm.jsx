import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { createDonation, getDonorByTelegram } from '../api/donations';
import { HiOutlineCheckCircle } from './icons';
import useAuthStore from '../stores/authStore';
import HexIcon from './HexIcon';

const PRESETS_USD = [5, 10, 25, 50, 100];
const CURRENCIES = ['USD', 'KES', 'EUR', 'GBP', 'ETB'];
const METHODS = ['stripe', 'mpesa', 'crypto'];

export default function DonationForm({ 
  campaignId, 
  donorId, 
  onSuccess, 
  onError,
  compact = false,
  presetAmount = null,
  defaultCurrency = 'USD'
}) {
  const { t } = useTranslation();
  const { user } = useAuthStore();
  const [amount, setAmount] = useState(presetAmount || '');
  const [currency, setCurrency] = useState(defaultCurrency);
  const [method, setMethod] = useState('stripe');
  const [message, setMessage] = useState('');
  const [phone, setPhone] = useState('');
  const [anonymous, setAnonymous] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(false);
  const [paymentInitiated, setPaymentInitiated] = useState(false);
  const [checkoutUrl, setCheckoutUrl] = useState('');
  const [donationData, setDonationData] = useState(null);
  const [detectedDonorId, setDetectedDonorId] = useState(donorId);

  // Detect donor ID from logged-in user if not provided
  useEffect(() => {
    const detectDonorId = async () => {
      if (!donorId && user?.telegram_user_id) {
        try {
          const donor = await getDonorByTelegram(user.telegram_user_id);
          setDetectedDonorId(donor.id);
        } catch (err) {
          console.warn('Could not detect donor from logged-in user:', err);
          // Fallback to 1 for demo purposes
          setDetectedDonorId(1);
        }
      }
    };
    
    detectDonorId();
  }, [donorId, user]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      console.log('Creating donation with donor_id:', detectedDonorId);
      console.log('User telegram ID:', user?.telegram_user_id);
      
      const payload = {
        donor_id: detectedDonorId || 1, // use detected donor ID or fallback
        campaign_id: campaignId,
        amount: parseFloat(amount),
        currency,
        payment_method: method,
        donor_message: message || undefined,
        is_anonymous: anonymous,
      };

      if (method === 'mpesa') {
        payload.phone_number = phone;
      }

      // Backend creates checkout session and handles everything
      const result = await createDonation(payload);
      setDonationData(result);
      
      // For Stripe, backend returns direct checkout URL
      if (method === 'stripe' && result.stripe_checkout_url) {
        // Backend provides direct checkout URL for payment completion
        setCheckoutUrl(result.stripe_checkout_url);
        setPaymentInitiated(true);
        // Don't set success yet - wait until after payment
      } else {
        // For M-Pesa and other methods, success is immediate
        setSuccess(true);
        if (onSuccess) onSuccess(result);
      }
    } catch (err) {
      setError(err.message);
      if (onError) onError(err);
    } finally {
      setLoading(false);
    }
  };

  // Payment initiated state (show payment card)
  if (paymentInitiated && method === 'stripe' && checkoutUrl) {
    return (
      <div className="text-center py-8 animate-fadeInUp">
        <div className="rounded-xl bg-gradient-to-br from-emerald-500/15 to-green-600/10 border border-emerald-500/20 p-4">
          <div className="flex items-center gap-2 mb-2">
            <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#10B981" strokeWidth="1.5">
              <rect x="1" y="3" width="14" height="10" rx="2" />
              <path d="M1 7h14" />
            </svg>
            <span className="text-xs font-semibold text-emerald-600">Secure Payment</span>
          </div>
          <p className="text-sm text-gray-700 mb-3">
            <span className="font-bold text-gray-900">${amount ? parseFloat(amount).toFixed(2) : '0.00'} {currency}</span>
            {' '}to complete your donation
          </p>
          <a
            href={checkoutUrl}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-semibold transition-colors shadow-lg shadow-emerald-500/20"
          >
            Complete Payment
            <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M6 1h7v7M13 1L6 8" strokeLinecap="round" />
            </svg>
          </a>
          <p className="text-xs text-gray-500 mt-2">You'll be redirected to secure Stripe checkout</p>
        </div>
      </div>
    );
  }

  // Success state
  if (success) {
    return (
      <div className="text-center py-8 animate-fadeInUp">
        <div className="flex justify-center mb-3">
          <HexIcon Icon={HiOutlineCheckCircle} accent="#059669" size="lg" bespoke="check" />
        </div>
        <p className="text-lg font-semibold text-green-600">{t('fund.success')}</p>
        
        {method === 'mpesa' && (
          <p className="text-sm text-gray-500 mt-2">{t('fund.mpesa_prompt')}</p>
        )}
        
        {method === 'crypto' && (
          <p className="text-sm text-gray-500 mt-2">
            Crypto donation instructions will be sent to your email.
          </p>
        )}
      </div>
    );
  }

  // Form
  return (
    <form onSubmit={handleSubmit} className={`space-y-5 ${compact ? 'space-y-4' : ''}`}>
      {/* Error display */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-sm text-red-600">{error}</p>
        </div>
      )}

      {/* Amount presets */}
      <div>
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('fund.amount')}
        </label>
        <div className="flex gap-2 flex-wrap mb-2">
          {PRESETS_USD.map((v) => (
            <button
              key={v}
              type="button"
              onClick={() => { setAmount(String(v)); setCurrency('USD'); }}
              className={`px-4 py-2 rounded-lg text-sm font-semibold border transition
                ${String(v) === amount && currency === 'USD'
                  ? 'bg-emerald-600 text-white border-emerald-600'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-emerald-300'}`}
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
            className={`flex-1 rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent ${compact ? 'py-2' : 'py-2'}`}
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
        <label className="block text-sm font-medium text-gray-700 mb-2">
          {t('fund.method')}
        </label>
        <div className={`flex gap-2 ${compact ? 'gap-1' : ''}`}>
          {METHODS.map((m) => (
            <button
              key={m}
              type="button"
              onClick={() => setMethod(m)}
              className={`px-4 py-2 rounded-lg text-sm font-semibold border transition capitalize
                ${method === m
                  ? 'bg-emerald-600 text-white border-emerald-600'
                  : 'bg-white text-gray-700 border-gray-200 hover:border-emerald-300'}`}
            >
              {m}
            </button>
          ))}
        </div>
      </div>

      {/* Phone number for M-Pesa */}
      {method === 'mpesa' && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Phone Number
          </label>
          <input
            type="tel"
            required
            value={phone}
            onChange={(e) => setPhone(e.target.value)}
            placeholder="+254712345678"
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Message */}
      {!compact && (
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Message (optional)
          </label>
          <textarea
            value={message}
            onChange={(e) => setMessage(e.target.value)}
            placeholder="Add a message of support..."
            rows={3}
            className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
        </div>
      )}

      {/* Anonymous checkbox */}
      <div className="flex items-center">
        <input
          type="checkbox"
          id="anonymous"
          checked={anonymous}
          onChange={(e) => setAnonymous(e.target.checked)}
          className="rounded border-gray-300 text-emerald-600 focus:ring-emerald-500"
        />
        <label htmlFor="anonymous" className="ml-2 text-sm text-gray-700">
          Donate anonymously
        </label>
      </div>

      {/* Submit button */}
      <button
        type="submit"
        disabled={loading || !amount || (method === 'mpesa' && !phone)}
        className="w-full py-3 rounded-lg bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50 disabled:cursor-not-allowed transition"
      >
        {loading ? t('common.loading') : `Donate ${amount ? `$${amount} ${currency}` : ''}`}
      </button>
    </form>
  );
}
