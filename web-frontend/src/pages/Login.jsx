import { useState } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import { HiOutlineLockClosed, HiOutlineInformationCircle } from 'react-icons/hi2';

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
    <div className="max-w-sm mx-auto px-4 py-8 sm:py-16">
      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-200/50 mb-4">
          <HiOutlineLockClosed className="w-8 h-8 text-white" />
        </div>
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
            className="w-full rounded-xl border border-gray-200 px-3 py-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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
            className="w-full rounded-xl border border-gray-200 px-3 py-3 text-sm tracking-[0.5em] text-center focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
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

      {/* Demo hint */}
      <div className="mt-6 p-3.5 bg-indigo-50/60 border border-indigo-100 rounded-xl">
        <div className="flex items-start gap-2">
          <HiOutlineInformationCircle className="w-4 h-4 text-indigo-500 mt-0.5 flex-shrink-0" />
          <div>
            <p className="text-xs font-semibold text-indigo-700 mb-1">Demo Credentials</p>
            <p className="text-xs text-indigo-500">
              Username: <span className="font-mono bg-indigo-100 px-1 rounded">@demo_user</span> · PIN: <span className="font-mono bg-indigo-100 px-1 rounded">1234</span>
            </p>
          </div>
        </div>
      </div>

      {/* Register link */}
      <p className="text-center text-sm text-gray-400 mt-5">
        New here?{' '}
        <Link to="/register-ngo" className="text-indigo-600 font-medium hover:underline">
          Register your NGO
        </Link>
      </p>
    </div>
  );
}
