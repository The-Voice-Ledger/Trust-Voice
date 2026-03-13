/**
 * AdminDashboard — portal landing for SUPER_ADMIN / SYSTEM_ADMIN.
 *
 * Shows pending approval counts, platform-wide stats, and quick links
 * to each admin action area.  Designed for the portal sidebar layout.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import {
  listNgoRegistrations, listUserRegistrations, getRegistrationStats,
  listPayouts,
} from '../api/admin';
import {
  HiOutlineBuildingOffice2, HiOutlineUserGroup, HiOutlineBanknotes,
  HiOutlineShieldCheck, HiOutlineChartBarSquare, HiOutlineArrowRight,
} from '../components/icons';

export default function AdminDashboard({ user }) {
  const [pendingNgos, setPendingNgos] = useState(0);
  const [pendingUsers, setPendingUsers] = useState(0);
  const [pendingPayouts, setPendingPayouts] = useState(0);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      listNgoRegistrations({ status: 'pending' }).then((d) => (Array.isArray(d) ? d : d?.registrations || []).length).catch(() => 0),
      listUserRegistrations({ status: 'pending' }).then((d) => (Array.isArray(d) ? d : d?.registrations || []).length).catch(() => 0),
      listPayouts({ status: 'pending' }).then((d) => (Array.isArray(d) ? d : d?.payouts || []).length).catch(() => 0),
      getRegistrationStats().catch(() => null),
    ]).then(([ngo, usr, pay, st]) => {
      setPendingNgos(ngo);
      setPendingUsers(usr);
      setPendingPayouts(pay);
      setStats(st);
    }).finally(() => setLoading(false));
  }, []);

  const actions = [
    { to: '/portal/admin/ngos', icon: HiOutlineBuildingOffice2, label: 'NGO Approvals', count: pendingNgos, accent: '#6366F1', desc: 'Review and approve NGO registration applications' },
    { to: '/portal/admin/users', icon: HiOutlineUserGroup, label: 'User Approvals', count: pendingUsers, accent: '#A855F7', desc: 'Manage pending user role requests' },
    { to: '/portal/admin/payouts', icon: HiOutlineBanknotes, label: 'Payouts', count: pendingPayouts, accent: '#D97706', desc: 'Review and release payout requests' },
    { to: '/portal/admin/milestones', icon: HiOutlineShieldCheck, label: 'Milestones', count: null, accent: '#059669', desc: 'Verify milestones and release on-chain funds' },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Platform Administration</h1>
        <p className="text-sm text-gray-500">Welcome, {user.full_name || 'Admin'}. Manage approvals, payouts, and governance.</p>
      </div>

      {/* Pending action cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-10">
        {actions.map(({ to, icon: Icon, label, count, accent, desc }) => (
          <Link key={to} to={to}
            className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-5 overflow-hidden transition-all hover:shadow-lg hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(to right, ${accent}, ${accent}80)` }} />
            <svg className="absolute -top-1 -right-1 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
              <circle cx="68" cy="28" r="22" stroke={accent} strokeWidth="0.5" opacity="0.06" />
              <circle cx="68" cy="28" r="10" stroke={accent} strokeWidth="0.3" strokeDasharray="2 3" opacity="0.04" />
            </svg>
            <svg className="absolute bottom-1 left-1 w-12 h-12 pointer-events-none" viewBox="0 0 50 50" fill="none">
              <path d="M0 50V30" stroke={accent} strokeWidth="0.5" opacity="0.04" />
              <path d="M0 50H20" stroke={accent} strokeWidth="0.5" opacity="0.04" />
              <circle cx="0" cy="50" r="1.5" fill={accent} opacity="0.06" />
            </svg>

            <div className="relative flex items-start justify-between">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${accent}15` }}>
                  <Icon className="w-5 h-5" style={{ color: accent }} />
                </div>
                <div>
                  <h3 className="font-semibold text-gray-900 text-sm">{label}</h3>
                  <p className="text-xs text-gray-400 mt-0.5 line-clamp-1">{desc}</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {count != null && count > 0 && (
                  <span className="inline-flex items-center justify-center min-w-[24px] h-6 px-1.5 rounded-full text-xs font-bold text-white" style={{ background: accent }}>
                    {count}
                  </span>
                )}
                <HiOutlineArrowRight className="w-4 h-4 text-gray-300 group-hover:text-gray-500 transition" />
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Platform stats */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Platform Stats</h2>
      {loading ? (
        <p className="text-center py-10 text-gray-400">Loading stats…</p>
      ) : stats ? (
        <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
          {Object.entries(stats).map(([key, value]) => (
            <div key={key} className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden transition-all hover:shadow-md hover:border-transparent">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-violet-500 to-transparent" />
              <svg className="absolute -top-1 -right-1 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
                <circle cx="45" cy="20" r="14" stroke="#6366F1" strokeWidth="0.5" opacity="0.05" />
                <circle cx="45" cy="20" r="6" stroke="#6366F1" strokeWidth="0.3" strokeDasharray="2 2" opacity="0.04" />
              </svg>
              <p className="text-sm text-gray-400 capitalize">{key.replace(/_/g, ' ')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900 mt-1 truncate">
                {typeof value === 'object' ? JSON.stringify(value) : String(value)}
              </p>
            </div>
          ))}
        </div>
      ) : (
        <div className="text-center py-10">
          <HiOutlineChartBarSquare className="w-10 h-10 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-400 text-sm">Stats unavailable</p>
        </div>
      )}
    </div>
  );
}
