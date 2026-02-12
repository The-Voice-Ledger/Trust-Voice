import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../stores/authStore';
import LanguageToggle from './LanguageToggle';

const NAV_ITEMS = [
  { to: '/campaigns', key: 'nav.campaigns', icon: '🔍' },
  { to: '/analytics', key: 'nav.analytics', icon: '📊' },
  { to: '/donate', key: 'nav.donate', icon: '💝' },
  { to: '/register-ngo', key: 'nav.register_ngo', icon: '🏛️' },
  { to: '/create-campaign', key: 'nav.create_campaign', icon: '✨' },
  { to: '/field-agent', key: 'nav.field_agent', icon: '📸' },
  { to: '/admin', key: 'nav.admin', icon: '⚙️' },
];

export default function Navbar() {
  const { t } = useTranslation();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path) => location.pathname === path;
  const linkCls = (path) =>
    `text-sm font-medium transition-colors whitespace-nowrap ${isActive(path)
      ? 'text-indigo-600'
      : 'text-gray-500 hover:text-gray-900'}`;

  return (
    <nav className="sticky top-0 z-40 bg-white/80 backdrop-blur-lg border-b border-gray-100">
      <div className="max-w-6xl mx-auto flex items-center justify-between px-4 h-14">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-bold text-lg text-gray-900 flex-shrink-0">
          <span className="text-2xl">🎙️</span>
          <span className="hidden sm:inline">{t('app_name')}</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-3">
          {NAV_ITEMS.map((item) => (
            <Link key={item.to} to={item.to} className={linkCls(item.to)}>
              {t(item.key)}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-3">
          {user ? (
            <>
              <Link to="/dashboard" className={`hidden sm:inline ${linkCls('/dashboard')}`}>
                {t('nav.dashboard')}
              </Link>
              <button onClick={logout} className="hidden sm:inline text-sm text-gray-400 hover:text-red-500 transition-colors">
                {t('nav.logout')}
              </button>
              <span className="text-xs bg-indigo-50 text-indigo-600 px-2 py-0.5 rounded-full">
                {user.full_name || user.telegram_username || 'User'}
              </span>
            </>
          ) : (
            <Link to="/login" className={`hidden sm:inline ${linkCls('/login')}`}>{t('nav.login')}</Link>
          )}

          <LanguageToggle />

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-1.5 rounded-lg hover:bg-gray-100 transition"
            aria-label="Menu"
          >
            <svg className="w-5 h-5 text-gray-600" fill="none" stroke="currentColor" strokeWidth="2" viewBox="0 0 24 24">
              {mobileOpen
                ? <path strokeLinecap="round" d="M6 18L18 6M6 6l12 12" />
                : <path strokeLinecap="round" d="M4 6h16M4 12h16M4 18h16" />
              }
            </svg>
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-gray-100 bg-white">
          <div className="max-w-6xl mx-auto px-4 py-3 space-y-1">
            {NAV_ITEMS.map((item) => (
              <Link
                key={item.to}
                to={item.to}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm transition ${
                  isActive(item.to) ? 'bg-indigo-50 text-indigo-600 font-medium' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <span>{item.icon}</span>
                {t(item.key)}
              </Link>
            ))}
            <hr className="border-gray-100" />
            {user ? (
              <>
                <Link to="/dashboard" onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-gray-600 hover:bg-gray-50">
                  📋 {t('nav.dashboard')}
                </Link>
                <button onClick={() => { logout(); setMobileOpen(false); }}
                  className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-red-500 hover:bg-red-50">
                  🚪 {t('nav.logout')}
                </button>
              </>
            ) : (
              <Link to="/login" onClick={() => setMobileOpen(false)}
                className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm text-indigo-600 font-medium hover:bg-indigo-50">
                🔐 {t('nav.login')}
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
