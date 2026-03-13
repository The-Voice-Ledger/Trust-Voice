import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import {
  listNgoRegistrations, approveNgoRegistration, rejectNgoRegistration,
  listUserRegistrations, approveUserRegistration, rejectUserRegistration, getRegistrationStats,
  listPayouts, approvePayout, rejectPayout,
  listNgos,
} from '../api/admin';
import {
  HiOutlineCheckCircle, HiOutlineXCircle, HiOutlineCheck, HiOutlineXMark,
  HiOutlineBuildingOffice2, HiOutlineBanknotes, HiOutlineChartBarSquare,
} from '../components/icons';
import { PageBg, PageHeader } from '../components/SvgDecorations';
import HexIcon from '../components/HexIcon';

const TABS = ['pending_ngos', 'pending_users', 'ngos', 'payouts', 'stats'];

export default function AdminPanel() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('pending_ngos');

  return (
    <PageBg pattern="blueprint" colorA="#10B981" colorB="#14B8A6">
    <div className="max-w-6xl mx-auto px-4 py-8">
      <PageHeader icon={HiOutlineChartBarSquare} title={t('admin.title')} subtitle={t('admin.subtitle')} accentColor="blue" bespoke="gear" />

      {/* Tab bar */}
      <div className="flex gap-1 bg-white/60 backdrop-blur-sm rounded-xl p-1 mb-8 overflow-x-auto scrollbar-hide border border-gray-200/50 shadow-sm">
        {TABS.map((tb) => (
          <button
            key={tb}
            onClick={() => setTab(tb)}
            className={`flex-shrink-0 px-4 py-2.5 rounded-lg text-sm font-medium transition whitespace-nowrap ${
              tab === tb ? 'bg-white shadow text-emerald-600' : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {t(`admin.tab_${tb}`)}
          </button>
        ))}
      </div>

      {/* Tab content */}
      {tab === 'pending_ngos' && <PendingNgos t={t} />}
      {tab === 'pending_users' && <PendingUsers t={t} />}
      {tab === 'ngos' && <NgoList t={t} />}
      {tab === 'payouts' && <PayoutList t={t} />}
      {tab === 'stats' && <DashboardStats t={t} />}
    </div>
    </PageBg>
  );
}

/* ── Pending NGO Registrations ───────────── */
function PendingNgos({ t }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    listNgoRegistrations({ status: 'pending' })
      .then((d) => setItems(Array.isArray(d) ? d : d?.registrations || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (id) => {
    if (!confirm(t('admin.confirm_approve'))) return;
    await approveNgoRegistration(id, 'Approved via web admin');
    load();
  };

  const handleReject = async (id) => {
    const reason = prompt(t('admin.reject_reason'));
    if (!reason || reason.length < 10) return alert(t('admin.reject_min'));
    await rejectNgoRegistration(id, reason);
    load();
  };

  if (loading) return <Loading t={t} />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState icon="✅" message={t('admin.no_pending_ngos')} />
      ) : (
        items.map((reg) => (
          <div key={reg.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />
            <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
              <rect x="45" y="10" width="24" height="30" rx="3" stroke="#10B981" strokeWidth="0.5" opacity="0.05" />
              <path d="M50 20 L64 20" stroke="#10B981" strokeWidth="0.4" opacity="0.04" />
              <path d="M50 26 L60 26" stroke="#10B981" strokeWidth="0.4" opacity="0.04" />
              <circle cx="57" cy="45" r="1.5" fill="#10B981" opacity="0.06" />
            </svg>
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-900">{reg.organization_name || reg.org_name}</h3>
                <p className="text-sm text-gray-500 mt-0.5">
                  {reg.contact_email} · {reg.phone_number || '-'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Reg #{reg.registration_number || '-'} · Type: {reg.organization_type || '-'}
                </p>
                {reg.mission_statement && (
                  <p className="text-sm text-gray-600 mt-2 line-clamp-2">{reg.mission_statement}</p>
                )}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition"
                >
                  <HiOutlineCheck className="w-4 h-4" /> {t('admin.approve')}
                </button>
                <button
                  onClick={() => handleReject(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition"
                >
                  <HiOutlineXMark className="w-4 h-4" /> {t('admin.reject')}
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ── Pending User Registrations ──────────── */
function PendingUsers({ t }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    listUserRegistrations({ status: 'pending' })
      .then((d) => setItems(Array.isArray(d) ? d : d?.registrations || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (id) => {
    if (!confirm(t('admin.confirm_approve'))) return;
    await approveUserRegistration(id, 'Approved via web admin');
    load();
  };

  const handleReject = async (id) => {
    const reason = prompt(t('admin.reject_reason'));
    if (!reason) return;
    await rejectUserRegistration(id, reason);
    load();
  };

  if (loading) return <Loading t={t} />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState icon="✅" message={t('admin.no_pending_users')} />
      ) : (
        items.map((reg) => (
          <div key={reg.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-green-500 to-transparent" />
            <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
              <circle cx="55" cy="22" r="10" stroke="#0D9488" strokeWidth="0.5" opacity="0.05" />
              <path d="M55 12 L55 6" stroke="#0D9488" strokeWidth="0.4" opacity="0.04" />
              <circle cx="55" cy="22" r="4" stroke="#0D9488" strokeWidth="0.3" opacity="0.04" />
              <path d="M48 32 L62 32" stroke="#0D9488" strokeWidth="0.4" opacity="0.04" />
            </svg>
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-900">{reg.full_name || reg.telegram_username || `User #${reg.id}`}</h3>
                <p className="text-sm text-gray-500">
                  Role: <span className="font-medium text-emerald-600">{reg.requested_role || reg.role}</span>
                </p>
                <p className="text-xs text-gray-400">
                  {reg.phone_number || ''} · {reg.telegram_username ? `@${reg.telegram_username}` : ''}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition"
                >
                  <HiOutlineCheck className="w-4 h-4" /> {t('admin.approve')}
                </button>
                <button
                  onClick={() => handleReject(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition"
                >
                  <HiOutlineXMark className="w-4 h-4" /> {t('admin.reject')}
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ── NGO List ────────────────────────────── */
function NgoList({ t }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    listNgos()
      .then((d) => setItems(Array.isArray(d) ? d : d?.ngos || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading t={t} />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState icon="🏛️" message={t('admin.no_ngos')} />
      ) : (
        items.map((ngo) => (
          <div key={ngo.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />
            <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
              <path d="M50 35 L57 15 L64 35" stroke="#059669" strokeWidth="0.5" opacity="0.05" />
              <path d="M47 35 L67 35" stroke="#059669" strokeWidth="0.4" opacity="0.05" />
              <rect x="53" y="22" width="8" height="8" stroke="#059669" strokeWidth="0.3" opacity="0.04" />
            </svg>
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h3 className="font-semibold text-gray-900">{ngo.name}</h3>
                <p className="text-sm text-gray-500">{ngo.description || '-'}</p>
                {ngo.website_url && (
                  <a href={ngo.website_url} target="_blank" rel="noreferrer" className="text-xs text-emerald-600 hover:underline">
                    {ngo.website_url}
                  </a>
                )}
              </div>
              <StatusBadge status={ngo.status || 'active'} />
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ── Payout List ─────────────────────────── */
function PayoutList({ t }) {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(() => {
    setLoading(true);
    listPayouts({ status: 'pending' })
      .then((d) => setItems(Array.isArray(d) ? d : d?.payouts || []))
      .catch(() => setItems([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => { load(); }, [load]);

  const handleApprove = async (id) => {
    if (!confirm(t('admin.confirm_approve'))) return;
    await approvePayout(id);
    load();
  };

  const handleReject = async (id) => {
    const reason = prompt(t('admin.reject_reason'));
    if (!reason) return;
    await rejectPayout(id, reason);
    load();
  };

  if (loading) return <Loading t={t} />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState icon="💸" message={t('admin.no_pending_payouts')} />
      ) : (
        items.map((p) => (
          <div key={p.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-amber-500 via-orange-500 to-transparent" />
            <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
              <circle cx="57" cy="22" r="12" stroke="#D97706" strokeWidth="0.5" opacity="0.05" />
              <path d="M52 22 L57 17 L62 22 L57 27 Z" stroke="#D97706" strokeWidth="0.4" opacity="0.05" />
              <path d="M57 10 L57 6" stroke="#D97706" strokeWidth="0.3" opacity="0.04" />
              <path d="M69 22 L73 22" stroke="#D97706" strokeWidth="0.3" opacity="0.04" />
            </svg>
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-900">
                  {p.amount} {p.currency} → {p.recipient_name}
                </h3>
                <p className="text-sm text-gray-500">
                  {p.payment_method} · Campaign #{p.campaign_id || '-'}
                </p>
                <p className="text-xs text-gray-400">
                  {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}
                </p>
              </div>
              <div className="flex gap-2">
                <button
                  onClick={() => handleApprove(p.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition"
                >
                  <HiOutlineCheck className="w-4 h-4" /> {t('admin.approve')}
                </button>
                <button
                  onClick={() => handleReject(p.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition"
                >
                  <HiOutlineXMark className="w-4 h-4" /> {t('admin.reject')}
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ── Dashboard Stats ─────────────────────── */
function DashboardStats({ t }) {
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getRegistrationStats()
      .then(setStats)
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <Loading t={t} />;

  if (!stats) return <EmptyState icon="📊" message={t('admin.stats_unavailable')} />;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
      {Object.entries(stats).map(([key, value]) => (
        <div key={key} className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden transition-all hover:shadow-md hover:border-transparent">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />
          <svg className="absolute -top-1 -right-1 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
            <circle cx="45" cy="20" r="14" stroke="#10B981" strokeWidth="0.5" opacity="0.05" />
            <circle cx="45" cy="20" r="6" stroke="#10B981" strokeWidth="0.3" strokeDasharray="2 2" opacity="0.04" />
          </svg>
          <p className="text-sm text-gray-400 capitalize">{key.replace(/_/g, ' ')}</p>
          <p className="text-xl sm:text-2xl font-bold text-gray-900 mt-1 truncate">
            {typeof value === 'object' ? JSON.stringify(value) : String(value)}
          </p>
        </div>
      ))}
    </div>
  );
}

/* ── Shared components ───────────────────── */
function Loading({ t }) {
  return <div className="text-center py-16 text-gray-400">{t('common.loading')}</div>;
}

const EMPTY_ICONS = {
  '✅': { Icon: HiOutlineCheckCircle, accent: '#059669', bespoke: 'check' },
  '🏛️': { Icon: HiOutlineBuildingOffice2, accent: '#10B981', bespoke: 'building' },
  '💸': { Icon: HiOutlineBanknotes, accent: '#D97706', bespoke: 'money' },
  '📊': { Icon: HiOutlineChartBarSquare, accent: '#0D9488', bespoke: 'chart' },
};

function EmptyState({ icon, message }) {
  const cfg = EMPTY_ICONS[icon] || { Icon: HiOutlineCheckCircle, accent: '#059669', bespoke: 'check' };
  return (
    <div className="text-center py-16">
      <HexIcon Icon={cfg.Icon} accent={cfg.accent} bespoke={cfg.bespoke} size="md" className="mx-auto mb-3" />
      <p className="text-gray-400">{message}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    active: 'bg-green-50 text-green-600',
    pending: 'bg-yellow-50 text-yellow-600',
    suspended: 'bg-red-50 text-red-600',
  };
  return (
    <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${colors[status] || 'bg-gray-50 text-gray-600'}`}>
      {status}
    </span>
  );
}
