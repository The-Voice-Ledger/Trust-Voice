import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate } from 'react-router-dom';
import useAuthStore from '../stores/authStore';

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login, loading, error } = useAuthStore();
  const [identifier, setIdentifier] = useState('');
  const [pin, setPin] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      // Detect if input is phone number or username
      const isPhone = /^\+?\d+$/.test(identifier);
      await login({
        identifier: isPhone ? undefined : identifier,
        phoneNumber: isPhone ? (identifier.startsWith('+') ? identifier : `+${identifier}`) : undefined,
        pin,
      });
      navigate('/dashboard');
    } catch {
      // error is set in store
    }
  };

  return (
    <div className="max-w-sm mx-auto px-4 py-16">
      <div className="text-center mb-8">
        <div className="text-5xl mb-3">🔐</div>
        <h1 className="text-2xl font-bold text-gray-900">{t('auth.sign_in')}</h1>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('auth.username_label')}
          </label>
          <input
            type="text"
            required
            value={identifier}
            onChange={(e) => setIdentifier(e.target.value)}
            placeholder="@username or +254…"
            className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            {t('auth.pin_label')}
          </label>
          <input
            type="password"
            inputMode="numeric"
            maxLength={4}
            pattern="\d{4}"
            required
            value={pin}
            onChange={(e) => setPin(e.target.value.replace(/\D/g, '').slice(0, 4))}
            placeholder="••••"
            className="w-full rounded-xl border border-gray-200 px-3 py-2.5 text-sm tracking-[0.5em] text-center focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-400 mt-1">{t('auth.pin_help')}</p>
        </div>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 rounded-lg p-2">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading || pin.length < 4}
          className="w-full py-3 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 disabled:opacity-50 transition"
        >
          {loading ? t('common.loading') : t('auth.submit')}
        </button>
      </form>
    </div>
  );
}
