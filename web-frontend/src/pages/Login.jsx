import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { useNavigate, Link } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import { HiOutlineLockClosed, HiOutlineInformationCircle } from '../components/icons';
import HexIcon from '../components/HexIcon';
import { PageBg } from '../components/SvgDecorations';

export default function Login() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const { login, loading, error, isAuthenticated } = useAuthStore();
  const [identifier, setIdentifier] = useState('');
  const [pin, setPin] = useState('');

  // Get auth state for redirect check
  const user = useAuthStore((s) => s.user);
  const token = useAuthStore((s) => s.token);

  // Redirect authenticated users away from login page
  useEffect(() => {
    // Only redirect if both user and token exist
    if (user && token) {
      navigate('/portal');
    }
  }, [user, token, navigate]);

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
    <PageBg pattern="hex" colorA="#10B981" colorB="#14B8A6">
    <div className="max-w-sm mx-auto px-4 py-8 sm:py-16">
      {/* Bespoke login card */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden p-6 sm:p-8 shadow-xl shadow-gray-200/30">
        {/* Top gradient accent */}
        <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: 'linear-gradient(to right, #10B981, #14B8A6)' }} />

        {/* Decorative SVG */}
        <svg className="absolute -top-4 -right-4 w-40 h-40 pointer-events-none" viewBox="0 0 160 160" fill="none">
          <circle cx="120" cy="40" r="50" stroke="#10B981" strokeWidth="0.5" opacity="0.06" />
          <circle cx="120" cy="40" r="30" stroke="#10B981" strokeWidth="0.3" strokeDasharray="3 4" opacity="0.04" />
          <polygon points="120,10 135,18 135,34 120,42 105,34 105,18" stroke="#14B8A6" strokeWidth="0.5" opacity="0.06" />
        </svg>
        <svg className="absolute bottom-0 left-0 w-24 h-24 pointer-events-none" viewBox="0 0 100 100" fill="none">
          <path d="M0 100V40" stroke="#10B981" strokeWidth="0.5" opacity="0.06" />
          <path d="M0 100H60" stroke="#14B8A6" strokeWidth="0.5" opacity="0.06" />
          <circle cx="0" cy="100" r="2" fill="#10B981" opacity="0.08" />
        </svg>

      <div className="relative text-center mb-8">
        <div className="flex justify-center mb-4">
          <HexIcon Icon={HiOutlineLockClosed} accent="#10B981" size="lg" bespoke="lock" gradient gradientTo="#14B8A6" />
        </div>
        <h1 className="page-header-accent text-2xl text-gray-900">{t('auth.sign_in')}</h1>
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
            className="w-full rounded-xl border border-gray-200 px-3 py-3 text-sm focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
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
            className="w-full rounded-xl border border-gray-200 px-3 py-3 text-sm tracking-[0.5em] text-center focus:ring-2 focus:ring-emerald-500 focus:border-transparent"
          />
          <p className="text-xs text-gray-400 mt-1">{t('auth.pin_help')}</p>
        </div>

        {error && (
          <p className="text-sm text-red-500 bg-red-50 rounded-lg p-2">{error}</p>
        )}

        <button
          type="submit"
          disabled={loading || pin.length < 4}
          className="w-full py-3 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 disabled:opacity-50 transition"
        >
          {loading ? t('common.loading') : t('auth.submit')}
        </button>
      </form>

      {/* Demo quick-login buttons */}
      <div className="mt-6 p-3.5 bg-emerald-50/60 border border-emerald-100 rounded-xl">
        <div className="flex items-start gap-2 mb-3">
          <HiOutlineInformationCircle className="w-4 h-4 text-emerald-500 mt-0.5 flex-shrink-0" />
          <p className="text-xs font-semibold text-emerald-700">Demo Logins <span className="font-normal text-emerald-400">(PIN 1234)</span></p>
        </div>
        <div className="grid grid-cols-2 gap-2">
          {[
            { user: 'demo_user',  label: 'Funder',      color: 'emerald' },
            { user: 'demo_ngo',   label: 'NGO Admin',    color: 'emerald' },
            { user: 'demo_admin', label: 'Platform Admin', color: 'green' },
            { user: 'demo_agent', label: 'Field Agent',  color: 'amber' },
          ].map(({ user: u, label, color }) => (
            <button
              key={u}
              type="button"
              disabled={loading}
              onClick={async () => {
                setIdentifier(u);
                setPin('1234');
                try {
                  await login({ identifier: u, pin: '1234' });
                  navigate('/portal');
                } catch { /* error shown by store */ }
              }}
              className={`text-xs font-medium px-2.5 py-2 rounded-lg border transition-all
                bg-${color}-50 border-${color}-200 text-${color}-700
                hover:bg-${color}-100 disabled:opacity-50`}
            >
              {label}
              <span className="block text-[10px] font-mono opacity-60">@{u}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Register link */}
      <p className="text-center text-sm text-gray-400 mt-5">
        New here?{' '}
        <Link to="/register-ngo" className="text-emerald-600 font-medium hover:underline">
          Register your NGO
        </Link>
      </p>
      </div>{/* end bespoke card */}
    </div>
    </PageBg>
  );
}
