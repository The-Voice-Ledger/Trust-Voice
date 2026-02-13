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
} from 'react-icons/hi2';

const TABS = ['pending_ngos', 'pending_users', 'ngos', 'payouts', 'stats'];

export default function AdminPanel() {
  const { t } = useTranslation();
  const [tab, setTab] = useState('pending_ngos');

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">{t('admin.title')}</h1>
        <p className="text-gray-500 text-sm mt-1">{t('admin.subtitle')}</p>
      </div>

      {/* Tab bar */}
      <div className="flex gap-1 bg-gray-100 rounded-xl p-1 mb-8 overflow-x-auto scrollbar-hide">
        {TABS.map((tb) => (
          <button
            key={tb}
            onClick={() => setTab(tb)}
            className={`flex-shrink-0 px-4 py-2.5 rounded-lg text-sm font-medium transition whitespace-nowrap ${
              tab === tb ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'
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
          <div key={reg.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-900">{reg.organization_name || reg.org_name}</h3>
                <p className="text-sm text-gray-500 mt-0.5">
                  {reg.contact_email} · {reg.phone_number || '—'}
                </p>
                <p className="text-xs text-gray-400 mt-1">
                  Reg #{reg.registration_number || '—'} · Type: {reg.organization_type || '—'}
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
          <div key={reg.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-900">{reg.full_name || reg.telegram_username || `User #${reg.id}`}</h3>
                <p className="text-sm text-gray-500">
                  Role: <span className="font-medium text-indigo-600">{reg.requested_role || reg.role}</span>
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
          <div key={ngo.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2">
              <div>
                <h3 className="font-semibold text-gray-900">{ngo.name}</h3>
                <p className="text-sm text-gray-500">{ngo.description || '—'}</p>
                {ngo.website_url && (
                  <a href={ngo.website_url} target="_blank" rel="noreferrer" className="text-xs text-indigo-600 hover:underline">
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
          <div key={p.id} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-5">
            <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div>
                <h3 className="font-semibold text-gray-900">
                  {p.amount} {p.currency} → {p.recipient_name}
                </h3>
                <p className="text-sm text-gray-500">
                  {p.payment_method} · Campaign #{p.campaign_id || '—'}
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
        <div key={key} className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-5 text-center">
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
  '✅': HiOutlineCheckCircle,
  '🏛️': HiOutlineBuildingOffice2,
  '💸': HiOutlineBanknotes,
  '📊': HiOutlineChartBarSquare,
};

function EmptyState({ icon, message }) {
  const IconComp = EMPTY_ICONS[icon] || HiOutlineCheckCircle;
  return (
    <div className="text-center py-16">
      <div className="w-14 h-14 mx-auto rounded-2xl bg-gray-100 flex items-center justify-center mb-3">
        <IconComp className="w-7 h-7 text-gray-400" />
      </div>
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
