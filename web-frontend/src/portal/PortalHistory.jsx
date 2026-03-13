/**
 * PortalHistory — full verification history for field agents.
 *
 * Shows all past verifications (not just the last 5 shown on the dashboard).
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getVerificationHistory } from '../api/fieldAgent';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineArrowLeft, HiOutlineDocumentText, HiOutlineShieldCheck,
} from '../components/icons';

export default function PortalHistory() {
  const user = useAuthStore((s) => s.user);
  const userId = user?.telegram_user_id || user?.id || 'web_anonymous';
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    getVerificationHistory(userId)
      .then((d) => setHistory(Array.isArray(d) ? d : d?.verifications || []))
      .catch(() => setHistory([]))
      .finally(() => setLoading(false));
  }, [userId]);

  const approved = history.filter((v) => v.status === 'approved').length;
  const pending = history.filter((v) => v.status === 'pending').length;
  const rejected = history.filter((v) => v.status === 'rejected').length;

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <Link to="/portal" className="inline-flex items-center gap-1 text-sm text-gray-500 hover:text-gray-700 transition mb-4">
        <HiOutlineArrowLeft className="w-4 h-4" /> Back to dashboard
      </Link>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Verification History</h1>
        <p className="text-sm text-gray-500 mt-1">All your past field verification submissions</p>
      </div>

      {/* Summary stats */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        <StatCard accent="#059669" label="Approved" value={approved} />
        <StatCard accent="#D97706" label="Pending" value={pending} />
        <StatCard accent="#DC2626" label="Rejected" value={rejected} />
      </div>

      {/* History list */}
      {loading ? (
        <p className="text-center py-16 text-gray-400">Loading…</p>
      ) : history.length === 0 ? (
        <div className="text-center py-16">
          <HiOutlineShieldCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-400 text-sm">No verifications yet</p>
          <Link to="/portal/verify" className="text-indigo-600 text-sm hover:underline mt-2 inline-block">
            Start your first verification →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {history.map((v, i) => (
            <div key={i} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 overflow-hidden transition-all hover:shadow-sm">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-violet-500/20 via-emerald-500/20 to-transparent" />
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-violet-50 flex items-center justify-center flex-shrink-0">
                  <HiOutlineDocumentText className="w-4 h-4 text-violet-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900 text-sm">Campaign #{v.campaign_id}</p>
                  <p className="text-xs text-gray-400">{v.created_at ? new Date(v.created_at).toLocaleDateString() : ''}</p>
                </div>
              </div>
              <span className={`text-xs px-2.5 py-1 rounded-full font-medium ${
                v.status === 'approved' ? 'bg-green-50 text-green-600' :
                v.status === 'rejected' ? 'bg-red-50 text-red-600' :
                'bg-yellow-50 text-yellow-600'
              }`}>{v.status || 'pending'}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ accent, label, value }) {
  return (
    <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 text-center overflow-hidden">
      <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(to right, ${accent}, ${accent}80)` }} />
      <p className="text-sm text-gray-400">{label}</p>
      <p className="text-xl font-bold text-gray-900">{value}</p>
    </div>
  );
}
