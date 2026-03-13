/**
 * PortalAdminSection — renders the correct admin content based on the URL.
 *
 * /portal/admin/ngos       → Pending NGO registrations with approve/reject
 * /portal/admin/users      → Pending user registrations with approve/reject
 * /portal/admin/payouts    → Pending payout requests with approve/reject
 * /portal/admin/milestones → Milestone oversight (links to milestone manager)
 *
 * Consolidates the CRUD functionality from the old AdminPanel into the portal.
 */
import { useState, useEffect, useCallback } from 'react';
import { useLocation, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import {
  listNgoRegistrations, approveNgoRegistration, rejectNgoRegistration,
  listUserRegistrations, approveUserRegistration, rejectUserRegistration,
  listPayouts, approvePayout, rejectPayout,
  listNgos,
} from '../api/admin';
import {
  HiOutlineCheckCircle, HiOutlineCheck, HiOutlineXMark,
  HiOutlineBuildingOffice2, HiOutlineUserGroup, HiOutlineBanknotes,
  HiOutlineShieldCheck, HiOutlineArrowLeft,
} from '../components/icons';

const SECTION_META = {
  ngos:       { title: 'NGO Approvals',   desc: 'Review and approve NGO registration applications', icon: HiOutlineBuildingOffice2, accent: '#6366F1' },
  users:      { title: 'User Approvals',   desc: 'Manage pending user role requests',                icon: HiOutlineUserGroup,       accent: '#A855F7' },
  payouts:    { title: 'Payouts',          desc: 'Review and release payout requests',               icon: HiOutlineBanknotes,       accent: '#D97706' },
  milestones: { title: 'Milestones',       desc: 'Verify milestones and release on-chain funds',     icon: HiOutlineShieldCheck,     accent: '#059669' },
};

export default function PortalAdminSection() {
  const location = useLocation();
  const section = location.pathname.split('/').pop(); // ngos | users | payouts | milestones

  const meta = SECTION_META[section] || SECTION_META.ngos;
  const Icon = meta.icon;

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <Link to="/portal" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition mb-4">
        <HiOutlineArrowLeft className="w-4 h-4" /> Back to dashboard
      </Link>
      <div className="flex items-center gap-3 mb-8">
        <div className="w-10 h-10 rounded-xl flex items-center justify-center" style={{ background: `${meta.accent}15` }}>
          <Icon className="w-5 h-5" style={{ color: meta.accent }} />
        </div>
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{meta.title}</h1>
          <p className="text-sm text-gray-500">{meta.desc}</p>
        </div>
      </div>

      {/* Section content */}
      {section === 'ngos' && <PendingNgos />}
      {section === 'users' && <PendingUsers />}
      {section === 'payouts' && <PayoutList />}
      {section === 'milestones' && <MilestoneSection />}
    </div>
  );
}

/* ── Pending NGO Registrations ───────────── */
function PendingNgos() {
  const { t } = useTranslation();
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
    if (!confirm('Approve this NGO registration?')) return;
    await approveNgoRegistration(id, 'Approved via portal');
    load();
  };

  const handleReject = async (id) => {
    const reason = prompt('Rejection reason (min 10 chars):');
    if (!reason || reason.length < 10) return alert('Please provide a reason with at least 10 characters.');
    await rejectNgoRegistration(id, reason);
    load();
  };

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState message="No pending NGO registrations" />
      ) : (
        items.map((reg) => (
          <div key={reg.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-violet-500 to-transparent" />
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
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
              <div className="flex gap-2 flex-shrink-0">
                <button onClick={() => handleApprove(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition">
                  <HiOutlineCheck className="w-4 h-4" /> Approve
                </button>
                <button onClick={() => handleReject(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition">
                  <HiOutlineXMark className="w-4 h-4" /> Reject
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
function PendingUsers() {
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
    if (!confirm('Approve this user registration?')) return;
    await approveUserRegistration(id, 'Approved via portal');
    load();
  };

  const handleReject = async (id) => {
    const reason = prompt('Rejection reason:');
    if (!reason) return;
    await rejectUserRegistration(id, reason);
    load();
  };

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState message="No pending user registrations" />
      ) : (
        items.map((reg) => (
          <div key={reg.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-purple-500 to-transparent" />
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-gray-900">{reg.full_name || reg.telegram_username || `User #${reg.id}`}</h3>
                <p className="text-sm text-gray-500">
                  Role: <span className="font-medium text-indigo-600">{reg.requested_role || reg.role}</span>
                </p>
                <p className="text-xs text-gray-400">
                  {reg.phone_number || ''} · {reg.telegram_username ? `@${reg.telegram_username}` : ''}
                </p>
              </div>
              <div className="flex gap-2 flex-shrink-0">
                <button onClick={() => handleApprove(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition">
                  <HiOutlineCheck className="w-4 h-4" /> Approve
                </button>
                <button onClick={() => handleReject(reg.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition">
                  <HiOutlineXMark className="w-4 h-4" /> Reject
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ── Payout List ─────────────────────────── */
function PayoutList() {
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
    if (!confirm('Approve this payout?')) return;
    await approvePayout(id);
    load();
  };

  const handleReject = async (id) => {
    const reason = prompt('Rejection reason:');
    if (!reason) return;
    await rejectPayout(id, reason);
    load();
  };

  if (loading) return <LoadingState />;

  return (
    <div className="space-y-4">
      {items.length === 0 ? (
        <EmptyState message="No pending payout requests" />
      ) : (
        items.map((p) => (
          <div key={p.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-amber-500 via-orange-500 to-transparent" />
            <div className="relative flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
              <div className="flex-1 min-w-0">
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
              <div className="flex gap-2 flex-shrink-0">
                <button onClick={() => handleApprove(p.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-green-600 text-white text-sm font-medium hover:bg-green-700 transition">
                  <HiOutlineCheck className="w-4 h-4" /> Approve
                </button>
                <button onClick={() => handleReject(p.id)}
                  className="flex items-center gap-1.5 px-4 py-2 rounded-lg bg-red-50 text-red-600 text-sm font-medium hover:bg-red-100 transition">
                  <HiOutlineXMark className="w-4 h-4" /> Reject
                </button>
              </div>
            </div>
          </div>
        ))
      )}
    </div>
  );
}

/* ── Milestone Section ───────────────────── */
function MilestoneSection() {
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Milestones are managed per-campaign. List all campaigns with active milestones.
    listNgos()
      .then(() => {
        // For now, show a prompt to navigate to the milestone manager per project.
        // A full milestone admin view could be built later.
      })
      .catch(() => {})
      .finally(() => setLoading(false));
  }, []);

  return (
    <div className="text-center py-16">
      <HiOutlineShieldCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
      <h3 className="font-semibold text-gray-900 mb-2">Milestone Verification</h3>
      <p className="text-gray-500 text-sm max-w-md mx-auto mb-6">
        Milestones are managed per-campaign. Navigate to a specific project to review and verify its milestones, 
        or ask a field agent to submit ground-truth verification.
      </p>
      <Link to="/portal/projects" className="px-5 py-2.5 rounded-xl bg-emerald-600 text-white font-semibold hover:bg-emerald-700 transition text-sm">
        View All Projects
      </Link>
    </div>
  );
}

/* ── Shared components ───────────────────── */
function LoadingState() {
  return <p className="text-center py-16 text-gray-400">Loading…</p>;
}

function EmptyState({ message }) {
  return (
    <div className="text-center py-16">
      <HiOutlineCheckCircle className="w-10 h-10 text-green-400 mx-auto mb-2" />
      <p className="text-gray-400">{message}</p>
    </div>
  );
}
