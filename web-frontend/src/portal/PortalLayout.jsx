/**
 * PortalLayout — role-based sidebar + content area for authenticated users.
 *
 * Each stakeholder (Funder, NGO/Project Owner, Platform Admin, Field Agent)
 * sees ONLY the nav items relevant to their role.  The sidebar collapses to a
 * bottom bar on mobile and a narrow icon-strip on tablet.
 */
import { useState, useEffect } from 'react';
import { Link, Outlet, useLocation, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineArrowLeft, HiOutlineArrowRightOnRectangle, HiOutlineUser,
  HiOutlineBars3, HiOutlineXMark, HiOutlineMicrophone,
  /* Funder */
  HiOutlineWallet, HiOutlineBanknotes, HiOutlineDocumentText,
  /* NGO */
  HiOutlinePlusCircle, HiOutlineCog6Tooth, HiOutlineCheckCircle,
  HiOutlineChartBar, HiOutlineShieldCheck,
  /* Admin */
  HiOutlineBuildingOffice2, HiOutlineUserGroup, HiOutlineChartBarSquare,
  /* Field Agent */
  HiOutlineCamera, HiOutlineMapPin,
  /* Shared */
  HiOutlineSparkles,
} from '../components/icons';

/* ─── Role → nav items mapping ──────────────────────── */

const FUNDER_NAV = [
  { to: '/portal',              icon: HiOutlineWallet,       label: 'Dashboard',     end: true },
  { to: '/portal/donations',    icon: HiOutlineBanknotes,    label: 'My Donations'         },
  { to: '/portal/receipts',     icon: HiOutlineDocumentText, label: 'Tax Receipts'         },
];

const NGO_NAV = [
  { to: '/portal',              icon: HiOutlineChartBar,     label: 'Overview',      end: true },
  { to: '/portal/projects',     icon: HiOutlineDocumentText, label: 'My Projects'          },
  { to: '/portal/create',       icon: HiOutlinePlusCircle,   label: 'New Campaign'         },
  { to: '/portal/ngo-profile',  icon: HiOutlineBuildingOffice2, label: 'NGO Profile'       },
];

const ADMIN_NAV = [
  { to: '/portal',              icon: HiOutlineChartBarSquare, label: 'Dashboard',   end: true },
  { to: '/portal/admin/ngos',   icon: HiOutlineBuildingOffice2, label: 'NGO Approvals'     },
  { to: '/portal/admin/users',  icon: HiOutlineUserGroup,    label: 'User Approvals'       },
  { to: '/portal/admin/payouts', icon: HiOutlineBanknotes,   label: 'Payouts'              },
  { to: '/portal/admin/milestones', icon: HiOutlineShieldCheck, label: 'Milestones'        },
];

const AGENT_NAV = [
  { to: '/portal',              icon: HiOutlineCamera,       label: 'Dashboard',     end: true },
  { to: '/portal/verify',       icon: HiOutlineShieldCheck,  label: 'Verify'               },
  { to: '/portal/history',      icon: HiOutlineDocumentText, label: 'History'              },
];

function getNavForRole(role) {
  if (!role) return FUNDER_NAV;
  const r = role.toUpperCase();
  if (r === 'SUPER_ADMIN' || r === 'SYSTEM_ADMIN') return ADMIN_NAV;
  if (r === 'NGO_ADMIN' || r === 'CAMPAIGN_CREATOR') return NGO_NAV;
  if (r === 'FIELD_AGENT') return AGENT_NAV;
  return FUNDER_NAV; // DONOR, VIEWER
}

function getRoleLabel(role) {
  if (!role) return 'Funder';
  const r = role.toUpperCase();
  if (r === 'SUPER_ADMIN' || r === 'SYSTEM_ADMIN') return 'Admin';
  if (r === 'NGO_ADMIN') return 'NGO Admin';
  if (r === 'CAMPAIGN_CREATOR') return 'Project Owner';
  if (r === 'FIELD_AGENT') return 'Field Agent';
  return 'Funder';
}

export default function PortalLayout() {
  const { t } = useTranslation();
  const location = useLocation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const logout = useAuthStore((s) => s.logout);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useEffect(() => { setSidebarOpen(false); }, [location.pathname]);

  // Auth guard
  if (!user) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="text-center">
          <p className="text-gray-500 mb-4">Sign in to access your portal</p>
          <Link to="/login" className="px-6 py-3 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition">
            Sign In
          </Link>
        </div>
      </div>
    );
  }

  const navItems = getNavForRole(user.role);
  const roleLabel = getRoleLabel(user.role);
  const isActive = (path, end) => end ? location.pathname === path : location.pathname.startsWith(path);

  const handleLogout = () => { logout(); navigate('/'); };

  return (
    <div className="min-h-screen bg-gray-50 flex">
      {/* ── Sidebar (desktop) ─────────────── */}
      <aside className="hidden lg:flex flex-col w-64 bg-white border-r border-gray-200/60 fixed inset-y-0 z-40">
        {/* Brand bar */}
        <div className="h-16 flex items-center gap-2.5 px-5 border-b border-gray-100">
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-green-700 flex items-center justify-center shadow-md shadow-emerald-300/40 group-hover:shadow-lg transition-all">
              <HiOutlineMicrophone className="w-4 h-4 text-white" />
            </div>
            <div className="leading-none">
              <span className="font-bold text-gray-900 text-sm tracking-tight">VBV</span>
              <span className="block text-[9px] font-semibold text-emerald-700 tracking-widest uppercase">Portal</span>
            </div>
          </Link>
        </div>

        {/* Role badge */}
        <div className="px-5 py-3">
          <div className="flex items-center gap-2 bg-gradient-to-r from-emerald-50 to-green-50 rounded-xl px-3 py-2.5 border border-emerald-100/60">
            <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center">
              <HiOutlineUser className="w-4 h-4 text-emerald-600" />
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-xs font-semibold text-gray-900 truncate">{user.full_name || user.telegram_username || 'User'}</p>
              <p className="text-[10px] text-emerald-600 font-medium">{roleLabel}</p>
            </div>
          </div>
        </div>

        {/* Nav items */}
        <nav className="flex-1 px-3 py-1 space-y-0.5 overflow-y-auto">
          {navItems.map(({ to, icon: Icon, label, end }) => (
            <Link
              key={to}
              to={to}
              className={`flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all ${
                isActive(to, end)
                  ? 'bg-gradient-to-r from-emerald-50 to-green-50 text-emerald-700 shadow-sm border border-emerald-100/60'
                  : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'
              }`}
            >
              <Icon className={`w-[18px] h-[18px] ${isActive(to, end) ? 'text-emerald-600' : 'text-gray-400'}`} />
              {label}
            </Link>
          ))}
        </nav>

        {/* Bottom */}
        <div className="px-3 py-4 border-t border-gray-100 space-y-1">
          <Link to="/" className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-gray-500 hover:bg-gray-50 hover:text-gray-700 transition">
            <HiOutlineArrowLeft className="w-[18px] h-[18px]" /> Back to VBV
          </Link>
          <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm text-red-500 hover:bg-red-50 transition">
            <HiOutlineArrowRightOnRectangle className="w-[18px] h-[18px]" /> Sign Out
          </button>
        </div>
      </aside>

      {/* ── Mobile top bar ────────────────── */}
      <div className="lg:hidden fixed top-0 inset-x-0 z-50">
        <div className="h-[3px] bg-gradient-to-r from-emerald-600 via-green-500 to-amber-500" />
        <div className="h-14 bg-white/90 backdrop-blur-xl border-b border-gray-200/40 flex items-center justify-between px-4">
          <div className="flex items-center gap-2">
            <button onClick={() => setSidebarOpen((v) => !v)} className="p-2 -ml-2 rounded-lg hover:bg-gray-100 transition">
              {sidebarOpen ? <HiOutlineXMark className="w-5 h-5" /> : <HiOutlineBars3 className="w-5 h-5" />}
            </button>
            <span className="font-bold text-sm text-gray-900">Portal</span>
            <span className="text-[10px] font-semibold text-emerald-700 px-1.5 py-0.5 bg-emerald-50 rounded-full">{roleLabel}</span>
          </div>
          <Link to="/" className="text-xs text-gray-400 hover:text-gray-600">← VBV</Link>
        </div>
      </div>

      {/* ── Mobile sidebar overlay ────────── */}
      {sidebarOpen && (
        <div className="lg:hidden fixed inset-0 z-40 flex">
          <div className="absolute inset-0 bg-black/20 backdrop-blur-sm" onClick={() => setSidebarOpen(false)} />
          <div className="relative w-72 bg-white shadow-2xl flex flex-col">
            <div className="px-5 py-4 border-b border-gray-100 flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-600 to-green-700 flex items-center justify-center">
                <HiOutlineMicrophone className="w-4 h-4 text-white" />
              </div>
              <div className="leading-none">
                <span className="font-bold text-gray-900 text-sm">VBV</span>
                <span className="block text-[9px] font-semibold text-emerald-700 tracking-widest uppercase">Portal</span>
              </div>
            </div>
            <div className="px-5 py-3">
              <div className="flex items-center gap-2 bg-emerald-50 rounded-xl px-3 py-2.5">
                <HiOutlineUser className="w-4 h-4 text-emerald-600" />
                <div>
                  <p className="text-xs font-semibold text-gray-900 truncate">{user.full_name || user.telegram_username || 'User'}</p>
                  <p className="text-[10px] text-emerald-600 font-medium">{roleLabel}</p>
                </div>
              </div>
            </div>
            <nav className="flex-1 px-3 py-1 space-y-0.5 overflow-y-auto">
              {navItems.map(({ to, icon: Icon, label, end }) => (
                <Link key={to} to={to}
                  className={`flex items-center gap-3 px-3 py-3 rounded-xl text-sm font-medium transition-all ${
                    isActive(to, end) ? 'bg-emerald-50 text-emerald-700' : 'text-gray-600 hover:bg-gray-50'
                  }`}>
                  <Icon className="w-5 h-5" /> {label}
                </Link>
              ))}
            </nav>
            <div className="px-3 py-4 border-t border-gray-100 space-y-1">
              <Link to="/" className="flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-gray-500 hover:bg-gray-50">
                <HiOutlineArrowLeft className="w-5 h-5" /> Back to VBV
              </Link>
              <button onClick={handleLogout} className="w-full flex items-center gap-3 px-3 py-3 rounded-xl text-sm text-red-500 hover:bg-red-50">
                <HiOutlineArrowRightOnRectangle className="w-5 h-5" /> Sign Out
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ── Main content ──────────────────── */}
      <main className="flex-1 lg:ml-64 pt-[calc(3px+3.5rem)] lg:pt-0 min-h-screen">
        <Outlet />
      </main>
    </div>
  );
}
