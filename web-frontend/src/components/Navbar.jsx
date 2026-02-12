import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../stores/authStore';
import LanguageToggle from './LanguageToggle';
import {
  HiOutlineGlobeAlt, HiOutlineChartBar, HiOutlineHeart,
  HiOutlineBuildingOffice2, HiOutlinePlusCircle, HiOutlineCamera,
  HiOutlineCog6Tooth, HiOutlineUser, HiOutlineArrowRightOnRectangle,
  HiOutlineArrowLeftOnRectangle, HiOutlineBars3, HiOutlineXMark,
  HiOutlineWallet,
} from 'react-icons/hi2';
import { HiOutlineMicrophone } from 'react-icons/hi';

const NAV_ITEMS = [
  { to: '/campaigns', key: 'nav.campaigns', Icon: HiOutlineGlobeAlt },
  { to: '/analytics', key: 'nav.analytics', Icon: HiOutlineChartBar },
  { to: '/donate', key: 'nav.donate', Icon: HiOutlineHeart },
  { to: '/register-ngo', key: 'nav.register_ngo', Icon: HiOutlineBuildingOffice2 },
  { to: '/create-campaign', key: 'nav.create_campaign', Icon: HiOutlinePlusCircle },
  { to: '/field-agent', key: 'nav.field_agent', Icon: HiOutlineCamera },
  { to: '/admin', key: 'nav.admin', Icon: HiOutlineCog6Tooth },
];

export default function Navbar() {
  const { t } = useTranslation();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [mobileOpen, setMobileOpen] = useState(false);

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200/60 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 sm:px-6 h-16">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-gray-900 flex-shrink-0 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md shadow-indigo-200/50 group-hover:shadow-lg group-hover:shadow-indigo-300/50 transition-shadow">
            <HiOutlineMicrophone className="w-5 h-5 text-white" />
          </div>
          <span className="hidden sm:inline tracking-tight">{t('app_name')}</span>
        </Link>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-1">
          {NAV_ITEMS.map(({ to, key, Icon }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all ${
                isActive(to)
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {t(key)}
            </Link>
          ))}
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <LanguageToggle />

          {user ? (
            <div className="hidden sm:flex items-center gap-2">
              <Link
                to="/dashboard"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-[13px] font-medium transition-all ${
                  isActive('/dashboard')
                    ? 'bg-indigo-50 text-indigo-700'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <HiOutlineWallet className="w-4 h-4" />
                {t('nav.dashboard')}
              </Link>
              <div className="flex items-center gap-2 pl-2 border-l border-gray-200">
                <span className="flex items-center gap-1.5 text-xs font-medium text-gray-600 bg-gray-100 px-2.5 py-1.5 rounded-lg">
                  <HiOutlineUser className="w-3.5 h-3.5" />
                  {user.full_name || user.telegram_username || 'User'}
                </span>
                <button onClick={logout} className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all" title={t('nav.logout')}>
                  <HiOutlineArrowRightOnRectangle className="w-4.5 h-4.5" />
                </button>
              </div>
            </div>
          ) : (
            <Link to="/login" className="hidden sm:flex items-center gap-1.5 px-4 py-2 rounded-lg bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-colors shadow-sm">
              <HiOutlineArrowLeftOnRectangle className="w-4 h-4" />
              {t('nav.login')}
            </Link>
          )}

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen(!mobileOpen)}
            className="lg:hidden p-2 rounded-lg hover:bg-gray-100 transition text-gray-600"
            aria-label="Menu"
          >
            {mobileOpen ? <HiOutlineXMark className="w-5 h-5" /> : <HiOutlineBars3 className="w-5 h-5" />}
          </button>
        </div>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="lg:hidden border-t border-gray-100 bg-white/95 backdrop-blur-xl shadow-lg">
          <div className="max-w-7xl mx-auto px-4 py-3 space-y-1">
            {NAV_ITEMS.map(({ to, key, Icon }) => (
              <Link
                key={to}
                to={to}
                onClick={() => setMobileOpen(false)}
                className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm transition-all ${
                  isActive(to) ? 'bg-indigo-50 text-indigo-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-5 h-5" />
                {t(key)}
              </Link>
            ))}
            <hr className="border-gray-100 my-2" />
            {user ? (
              <>
                <Link to="/dashboard" onClick={() => setMobileOpen(false)}
                  className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-600 hover:bg-gray-50">
                  <HiOutlineWallet className="w-5 h-5" />
                  {t('nav.dashboard')}
                </Link>
                <button onClick={() => { logout(); setMobileOpen(false); }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50">
                  <HiOutlineArrowRightOnRectangle className="w-5 h-5" />
                  {t('nav.logout')}
                </button>
              </>
            ) : (
              <Link to="/login" onClick={() => setMobileOpen(false)}
                className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-indigo-600 font-semibold hover:bg-indigo-50">
                <HiOutlineArrowLeftOnRectangle className="w-5 h-5" />
                {t('nav.login')}
              </Link>
            )}
          </div>
        </div>
      )}
    </nav>
  );
}
