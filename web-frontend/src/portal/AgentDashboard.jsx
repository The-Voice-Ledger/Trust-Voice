/**
 * AgentDashboard — portal landing for FIELD_AGENT role.
 *
 * Shows verification queue, recent history, earnings snapshot,
 * and a quick-start verify button.  Designed for the portal sidebar layout.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getPendingCampaigns, getVerificationHistory } from '../api/fieldAgent';
import {
  HiOutlineCamera, HiOutlineShieldCheck, HiOutlineCheckCircle,
  HiOutlineClock, HiOutlineDocumentText,
} from '../components/icons';

export default function AgentDashboard({ user }) {
  const userId = user?.telegram_user_id || user?.id || 'web_anonymous';
  const [campaigns, setCampaigns] = useState([]);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      getPendingCampaigns(userId).then((d) => (Array.isArray(d) ? d : d?.campaigns || [])).catch(() => []),
      getVerificationHistory(userId).then((d) => (Array.isArray(d) ? d : d?.verifications || [])).catch(() => []),
    ]).then(([c, h]) => {
      setCampaigns(c);
      setHistory(h);
    }).finally(() => setLoading(false));
  }, [userId]);

  const approved = history.filter((v) => v.status === 'approved').length;
  const pending = history.filter((v) => v.status === 'pending').length;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Field Agent Dashboard</h1>
          <p className="text-sm text-gray-500">Verify milestones, earn rewards, build trust</p>
        </div>
        <Link to="/portal/verify"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-violet-600 to-purple-600 text-white text-sm font-semibold hover:from-violet-700 hover:to-purple-700 transition shadow-lg shadow-violet-300/30">
          <HiOutlineCamera className="w-4 h-4" /> New Verification
        </Link>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <Stat accent="#6366F1" icon={HiOutlineDocumentText} label="Assignments" value={campaigns.length} />
        <Stat accent="#059669" icon={HiOutlineCheckCircle} label="Approved" value={approved} />
        <Stat accent="#D97706" icon={HiOutlineClock} label="Pending" value={pending} />
      </div>

      {/* Pending queue */}
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Verification Queue</h2>
      {loading ? (
        <p className="text-center py-10 text-gray-400">Loading…</p>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-12">
          <HiOutlineShieldCheck className="w-10 h-10 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-400 text-sm">No pending assignments right now</p>
        </div>
      ) : (
        <div className="space-y-3 mb-10">
          {campaigns.map((c) => (
            <Link key={c.id} to={`/portal/verify?campaign=${c.id}`}
              className="group relative block rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-violet-500/30 via-emerald-500/30 to-transparent" />
              <svg className="absolute bottom-0 right-0 w-12 h-12 pointer-events-none" viewBox="0 0 50 50" fill="none">
                <path d="M50 0v50H0" stroke="#A855F7" strokeWidth="0.5" opacity="0.04" />
                <circle cx="50" cy="50" r="1.5" fill="#A855F7" opacity="0.06" />
              </svg>
              <div className="flex items-center justify-between">
                <div>
                  <p className="font-medium text-gray-900 text-sm">{c.title}</p>
                  <p className="text-xs text-gray-400 mt-0.5">Campaign #{c.id}</p>
                </div>
                <span className="text-xs px-3 py-1.5 rounded-lg bg-violet-50 text-violet-700 font-semibold group-hover:bg-violet-100 transition">
                  Verify →
                </span>
              </div>
            </Link>
          ))}
        </div>
      )}

      {/* Recent history */}
      {history.length > 0 && (
        <>
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-lg font-semibold text-gray-900">Recent Activity</h2>
            <Link to="/portal/history" className="text-sm text-indigo-600 hover:underline">View all →</Link>
          </div>
          <div className="space-y-3">
            {history.slice(0, 5).map((v, i) => (
              <div key={i} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 overflow-hidden transition-all hover:shadow-sm">
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-violet-500/20 via-emerald-500/20 to-transparent" />
                <div>
                  <p className="font-medium text-gray-900 text-sm">Campaign #{v.campaign_id}</p>
                  <p className="text-xs text-gray-400">{v.created_at ? new Date(v.created_at).toLocaleDateString() : ''}</p>
                </div>
                <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                  v.status === 'approved' ? 'bg-green-50 text-green-600' :
                  v.status === 'rejected' ? 'bg-red-50 text-red-600' :
                  'bg-yellow-50 text-yellow-600'
                }`}>{v.status || 'pending'}</span>
              </div>
            ))}
          </div>
        </>
      )}
    </div>
  );
}

function Stat({ accent, icon: Icon, label, value }) {
  return (
    <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden transition-all hover:shadow-md hover:border-transparent">
      <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(to right, ${accent}, ${accent}80)` }} />
      <svg className="absolute -top-2 -right-2 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
        <circle cx="55" cy="25" r="20" stroke={accent} strokeWidth="0.5" opacity="0.08" />
        <circle cx="55" cy="25" r="10" stroke={accent} strokeWidth="0.3" strokeDasharray="2 3" opacity="0.05" />
      </svg>
      {Icon && <Icon className="w-5 h-5 mx-auto mb-1" style={{ color: accent }} />}
      <p className="text-sm text-gray-400">{label}</p>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
