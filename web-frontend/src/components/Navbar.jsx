import { useState, useRef, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../stores/authStore';
import LanguageToggle from './LanguageToggle';
import {
  HiOutlineGlobeAlt, HiOutlineChartBar, HiOutlineBanknotes,
  HiOutlineBuildingOffice2, HiOutlineCamera,
  HiOutlineCog6Tooth, HiOutlineUser, HiOutlineArrowRightOnRectangle,
  HiOutlineArrowLeftOnRectangle, HiOutlineBars3, HiOutlineXMark,
  HiOutlineWallet, HiOutlineChevronDown, HiOutlineEllipsisHorizontal,
  HiOutlineSparkles, HiOutlineMicrophone, HiOutlineMapPin,
} from './icons';

/* Primary nav — always visible on desktop */
const PRIMARY_ITEMS = [
  { to: '/campaigns', key: 'nav.campaigns', Icon: HiOutlineGlobeAlt },
  { to: '/projects', key: 'nav.projects', Icon: HiOutlineMapPin },
  { to: '/fund', key: 'nav.fund', Icon: HiOutlineBanknotes },
  { to: '/assistant', key: 'nav.assistant', Icon: HiOutlineSparkles },
];

/* Secondary nav — hidden in "More" dropdown on desktop */
const SECONDARY_ITEMS = [
  { to: '/portal', key: 'nav.portal', Icon: HiOutlineCog6Tooth },
  { to: '/analytics', key: 'nav.analytics', Icon: HiOutlineChartBar },
  { to: '/register-ngo', key: 'nav.register_ngo', Icon: HiOutlineBuildingOffice2 },
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
    <nav className="sticky top-0 z-50">
      {/* Gradient accent bar — 3px, visually dominant */}
      <div className="h-[3px] bg-gradient-to-r from-emerald-600 via-green-500 to-amber-500" />
      {/* Glass morphism body */}
      <div className="bg-white/70 backdrop-blur-2xl border-b border-gray-200/40 shadow-lg shadow-gray-200/20">
        <div className="max-w-7xl mx-auto flex items-center justify-between px-4 sm:px-6 h-16">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 font-bold text-lg text-gray-900 flex-shrink-0 group">
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-600 to-green-700 flex items-center justify-center shadow-lg shadow-emerald-300/40 group-hover:shadow-xl group-hover:shadow-amber-400/50 group-hover:scale-105 transition-all">
            <HiOutlineMicrophone className="w-5 h-5 text-white" />
            {/* Animated ring on hover */}
            <div className="absolute inset-0 rounded-xl border-2 border-amber-400/0 group-hover:border-amber-400/40 transition-all scale-100 group-hover:scale-110" />
          </div>
          <div className="hidden sm:flex flex-col leading-none">
            <span className="tracking-tight font-display text-lg">{t('app_name')}</span>
            <span className="text-[10px] font-medium text-emerald-700 tracking-widest uppercase">Transparency</span>
          </div>
        </Link>

        {/* Desktop nav */}
        <div className="hidden lg:flex items-center gap-0.5">
          {PRIMARY_ITEMS.map(({ to, key, Icon }) => (
            <Link
              key={to}
              to={to}
              className={`relative flex items-center gap-1.5 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                isActive(to)
                  ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 shadow-sm shadow-emerald-100/50'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50/80'
              }`}
            >
              <Icon className={`w-4 h-4 ${isActive(to) ? 'text-emerald-600' : ''}`} />
              <span className="font-display">{t(key)}</span>
              {isActive(to) && (
                <span className="absolute bottom-0 left-3 right-3 h-0.5 bg-gradient-to-r from-emerald-500 to-amber-500 rounded-full" />
              )}
            </Link>
          ))}

          {/* "More" dropdown */}
          <div ref={moreRef} className="relative">
            <button
              onClick={() => setMoreOpen((v) => !v)}
              className={`flex items-center gap-1 px-3.5 py-2 rounded-lg text-sm font-medium transition-all ${
                SECONDARY_ITEMS.some((i) => isActive(i.to))
                  ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700'
                  : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50/80'
              }`}
            >
              <HiOutlineEllipsisHorizontal className="w-4 h-4" />
              <span className="font-display">{t('nav.more')}</span>
              <HiOutlineChevronDown className={`w-3 h-3 transition-transform duration-200 ${moreOpen ? 'rotate-180' : ''}`} />
            </button>

            {moreOpen && (
              <div className="absolute top-full right-0 mt-2 w-56 bg-white/95 backdrop-blur-xl rounded-xl shadow-2xl shadow-gray-300/40 border border-gray-100 py-1.5 animate-fadeIn z-50">
                {SECONDARY_ITEMS.map(({ to, key, Icon }) => (
                  <Link
                    key={to}
                    to={to}
                    onClick={() => setMoreOpen(false)}
                    className={`flex items-center gap-2.5 px-4 py-2.5 text-sm transition-all ${
                      isActive(to)
                        ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 font-semibold'
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
                    }`}
                  >
                    <Icon className="w-4.5 h-4.5" />
                    <span className="font-display">{t(key)}</span>
                  </Link>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right side */}
        <div className="flex items-center gap-2">
          {/* LanguageToggle hidden until more languages added */}

          {user ? (
            <div className="hidden sm:flex items-center gap-2">
              <Link
                to="/portal"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium transition-all ${
                  isActive('/portal')
                    ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700'
                    : 'text-gray-500 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                <HiOutlineWallet className="w-4 h-4" />
                <span className="font-display">{t('nav.portal')}</span>
              </Link>
              <div className="flex items-center gap-2 pl-2 border-l border-gray-200/60">
                <span className="flex items-center gap-1.5 text-xs font-medium text-gray-600 bg-gradient-to-r from-gray-50 to-gray-100 px-2.5 py-1.5 rounded-lg border border-gray-200/50">
                  <HiOutlineUser className="w-3.5 h-3.5 text-emerald-500" />
                  {user.full_name || user.telegram_username || 'User'}
                </span>
                <button onClick={logout} className="p-1.5 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all" title={t('nav.logout')}>
                  <HiOutlineArrowRightOnRectangle className="w-4.5 h-4.5" />
                </button>
              </div>
            </div>
          ) : (
            <Link to="/login" className="hidden sm:flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-700 text-white text-sm font-semibold hover:from-emerald-700 hover:to-green-800 transition-all shadow-lg shadow-emerald-300/30 hover:shadow-xl hover:shadow-emerald-400/40 hover:-translate-y-px font-display">
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
      </div>

      {/* Mobile menu */}
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
                className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm transition-all font-display ${
                  isActive(to) ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 font-semibold' : 'text-gray-600 hover:bg-gray-50'
                }`}
              >
                <Icon className="w-5 h-5" />
                {t(key)}
              </Link>
            ))}
            <hr className="border-gray-100 my-2" />
            {user ? (
              <>
                <Link to="/portal"
                  className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-gray-600 hover:bg-gray-50 font-display">
                  <HiOutlineWallet className="w-5 h-5" />
                  {t('nav.portal')}
                </Link>
                <button onClick={logout}
                  className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-red-500 hover:bg-red-50 font-display">
                  <HiOutlineArrowRightOnRectangle className="w-5 h-5" />
                  {t('nav.logout')}
                </button>
              </>
            ) : (
              <Link to="/login"
                className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-emerald-600 font-semibold hover:bg-emerald-50 font-display">
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
