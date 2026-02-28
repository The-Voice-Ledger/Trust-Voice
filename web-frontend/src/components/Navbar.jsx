import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../stores/authStore';
import LanguageToggle from './LanguageToggle';
import {
  HiOutlineGlobeAlt, HiOutlineChartBar, HiOutlineHeart,
  HiOutlineBuildingOffice2, HiOutlinePlusCircle, HiOutlineCamera,
  HiOutlineCog6Tooth, HiOutlineUser, HiOutlineArrowRightOnRectangle,
  HiOutlineArrowLeftOnRectangle, HiOutlineBars3, HiOutlineXMark,
  HiOutlineWallet, HiOutlineChevronDown, HiOutlineEllipsisHorizontal,
  HiOutlineSparkles,
} from 'react-icons/hi2';
import { HiOutlineMicrophone } from 'react-icons/hi';

/* Primary nav — always visible on desktop */
const PRIMARY_ITEMS = [
  { to: '/campaigns', key: 'nav.campaigns', Icon: HiOutlineGlobeAlt },
  { to: '/donate', key: 'nav.donate', Icon: HiOutlineHeart },
  { to: '/assistant', key: 'nav.assistant', Icon: HiOutlineSparkles },
  { to: '/analytics', key: 'nav.analytics', Icon: HiOutlineChartBar },
];

/* Secondary nav — hidden in "More" dropdown on desktop */
const SECONDARY_ITEMS = [
  { to: '/register-ngo', key: 'nav.register_ngo', Icon: HiOutlineBuildingOffice2 },
  { to: '/create-campaign', key: 'nav.create_campaign', Icon: HiOutlinePlusCircle },
  { to: '/field-agent', key: 'nav.field_agent', Icon: HiOutlineCamera },
  { to: '/admin', key: 'nav.admin', Icon: HiOutlineCog6Tooth },
];

const ALL_ITEMS = [...PRIMARY_ITEMS, ...SECONDARY_ITEMS];

export default function Navbar() {
  const { t } = useTranslation();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [mobileOpen, setMobileOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const moreRef = useRef(null);

  const isActive = (path) => location.pathname === path || location.pathname.startsWith(path + '/');

  // Close "More" dropdown on outside click
  useEffect(() => {
    const handler = (e) => {
      if (moreRef.current && !moreRef.current.contains(e.target)) setMoreOpen(false);
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, []);

  // Close menus on route change
  useEffect(() => { setMobileOpen(false); setMoreOpen(false); }, [location.pathname]);

  return (
    <nav className="sticky top-0 z-50 bg-white/80 backdrop-blur-xl border-b border-gray-200/60 shadow-sm">
      <div className="max-w-7xl mx-auto flex items-center justify-between px-4 sm:px-6 h-16">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-gray-900 flex-shrink-0 group">
          <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md shadow-indigo-200/50 group-hover:shadow-lg group-hover:shadow-indigo-300/50 group-hover:scale-105 transition-all">
            <HiOutlineMicrophone className="w-5 h-5 text-white" />
          </div>
          <span className="hidden sm:inline tracking-tight">{t('app_name')}</span>
        </Link>

        {/* Desktop nav — clean: 3 primary + More */}
        <div className="hidden lg:flex items-center gap-1">
          {PRIMARY_ITEMS.map(({ to, key, Icon }) => (
            <Link
              key={to}
              to={to}
              className={`relative flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive(to)
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <Icon className="w-4 h-4" />
              {t(key)}
            </Link>
          ))}

          {/* "More" dropdown */}
          <div ref={moreRef} className="relative">
            <button
              onClick={() => setMoreOpen((v) => !v)}
              className={`flex items-center gap-1 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                SECONDARY_ITEMS.some((i) => isActive(i.to))
                  ? 'bg-indigo-50 text-indigo-700'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
              }`}
            >
              <HiOutlineEllipsisHorizontal className="w-4 h-4" />
              {t('nav.more')}
              <HiOutlineChevronDown className={`w-3 h-3 transition-transform duration-200 ${moreOpen ? 'rotate-180' : ''}`} />
            </button>

            {moreOpen && (
              <div className="absolute top-full right-0 mt-2 w-56 bg-white rounded-xl shadow-xl shadow-gray-200/60 border border-gray-100 py-1.5 animate-fadeIn z-50">
                {SECONDARY_ITEMS.map(({ to, key, Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    onClick={() => setMoreOpen(false)}
                    className={`flex items-center gap-2.5 px-4 py-2.5 text-sm transition-all ${
                      isActive(to)
                        ? 'bg-indigo-50 text-indigo-700 font-semibold'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4.5 h-4.5" />
                    {t(key)}
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          <LanguageToggle />

          {user ? (
            <div className="hidden sm:flex items-center gap-2">
              <Link
                to="/dashboard"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
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
            <Link to="/login" className="hidden sm:flex items-center gap-1.5 px-4 py-2 rounded-xl bg-indigo-600 text-white text-sm font-medium hover:bg-indigo-700 transition-all shadow-sm shadow-indigo-200/50 hover:shadow-md hover:shadow-indigo-300/50 hover:-translate-y-px">
              <HiOutlineArrowLeftOnRectangle className="w-4 h-4" />
              {t('nav.login')}
            </Link>
          )}

          {/* Mobile hamburger */}
          <button
            onClick={() => setMobileOpen((v) => !v)}
            className="lg:hidden p-2.5 -mr-1 rounded-lg hover:bg-gray-100 transition text-gray-600"
            aria-label="Menu"
          >
            {mobileOpen ? <HiOutlineXMark className="w-6 h-6" /> : <HiOutlineBars3 className="w-6 h-6" />}
          </button>
        </div>
      </div>

      {/* Mobile menu — animated slide */}
      <div
        className={`lg:hidden transition-all duration-300 ease-out overflow-hidden ${
          mobileOpen ? 'max-h-[80vh] opacity-100' : 'max-h-0 opacity-0'
        }`}
      >
        <div className="border-t border-gray-100 bg-white/95 backdrop-blur-xl shadow-lg overflow-y-auto overscroll-contain">
          <div className="max-w-7xl mx-auto px-4 py-3 space-y-1">
            {ALL_ITEMS.map(({ to, key, Icon }) => (
              <Link
                key={to}
                to={to}
                className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition-all ${
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
                <Link to="/dashboard"
                  className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-gray-600 hover:bg-gray-50">
                  <HiOutlineWallet className="w-5 h-5" />
                  {t('nav.dashboard')}
                </Link>
                <button onClick={logout}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-red-500 hover:bg-red-50">
                  <HiOutlineArrowRightOnRectangle className="w-5 h-5" />
                  {t('nav.logout')}
                </button>
              </>
            ) : (
              <Link to="/login"
                className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-indigo-600 font-semibold hover:bg-indigo-50">
                <HiOutlineArrowLeftOnRectangle className="w-5 h-5" />
                {t('nav.login')}
              </Link>
            )}
          </div>
        </div>
      </div>
    </nav>
  );
}
