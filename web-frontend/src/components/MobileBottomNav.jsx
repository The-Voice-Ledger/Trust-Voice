import { Link, useLocation } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  HiOutlineGlobeAlt, HiOutlineHeart, HiOutlineCamera, HiOutlineUser,
  HiOutlineSparkles,
} from 'react-icons/hi2';
import useAuthStore from '../stores/authStore';

const NAV_ITEMS = [
  { to: '/campaigns', key: 'nav.campaigns', Icon: HiOutlineGlobeAlt },
  { to: '/donate', key: 'nav.donate', Icon: HiOutlineHeart },
  { to: '/assistant', key: 'nav.assistant', Icon: HiOutlineSparkles, isHome: true },
  { to: '/field-agent', key: 'nav.field_agent', Icon: HiOutlineCamera },
  { to: '/dashboard', key: 'nav.dashboard', Icon: HiOutlineUser, authOnly: true },
];

export default function MobileBottomNav() {
  const { t } = useTranslation();
  const location = useLocation();
  const user = useAuthStore((s) => s.user);

  const isActive = (path, isHome) => {
    if (isHome) return location.pathname === path;
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  // Replace dashboard with login if not authenticated
  const items = NAV_ITEMS.map((item) => {
    if (item.authOnly && !user) {
      return { to: '/login', key: 'nav.login', Icon: HiOutlineUser };
    }
    return item;
  });

  return (
    <nav className="sm:hidden fixed bottom-0 inset-x-0 z-50 bg-white/95 backdrop-blur-xl border-t border-gray-200/60 shadow-[0_-2px_10px_rgba(0,0,0,0.06)]">
      <div className="flex items-center justify-around h-16 px-1 max-w-lg mx-auto">
        {items.map(({ to, key, Icon, isHome }) => {
          const active = isActive(to, isHome);
          return (
            <Link
              key={to + key}
              to={to}
              className={`flex flex-col items-center justify-center gap-0.5 min-w-[56px] py-1 px-2 rounded-xl transition-all ${
                active
                  ? 'text-indigo-600'
                  : 'text-gray-400 hover:text-gray-600 active:text-gray-700'
              }`}
            >
              {isHome ? (
                <div className={`w-10 h-10 -mt-4 rounded-full flex items-center justify-center shadow-lg ${
                  active
                    ? 'bg-indigo-600 text-white shadow-indigo-200/60'
                    : 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-indigo-200/40'
                }`}>
                  <Icon className="w-5 h-5" />
                </div>
              ) : (
                <Icon className={`w-6 h-6 ${active ? 'scale-110' : ''} transition-transform`} />
              )}
              <span className={`text-[10px] font-medium leading-tight ${isHome ? 'mt-0.5' : ''}`}>
                {t(key)}
              </span>
            </Link>
          );
        })}
      </div>
      {/* Safe area for iPhones with home indicator */}
      <div className="h-[env(safe-area-inset-bottom)]" />
    </nav>
  );
}
