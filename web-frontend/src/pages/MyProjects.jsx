import { useState, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listCampaigns, getCampaignMilestones, getCampaignTreasury } from '../api/campaigns';
import useAuthStore from '../stores/authStore';
import ProgressBar from '../components/ProgressBar';
import {
  HiOutlineArrowLeft, HiOutlinePlusCircle, HiOutlineDocumentText,
  HiOutlineBanknotes, HiOutlineCog6Tooth, HiOutlineCheckCircle,
  HiOutlineChartBar, HiOutlineClock, HiOutlineMapPin,
  HiOutlineShieldCheck,
} from '../components/icons';
import { PageBg, PageHeader } from '../components/SvgDecorations';

const STATUS_BADGE = {
  active:    { label: 'Active', bg: 'bg-emerald-50', text: 'text-emerald-700', ring: 'ring-emerald-200' },
  paused:    { label: 'Paused', bg: 'bg-amber-50', text: 'text-amber-700', ring: 'ring-amber-200' },
  completed: { label: 'Completed', bg: 'bg-gray-100', text: 'text-gray-600', ring: 'ring-gray-200' },
};

export default function MyProjects() {
  const { t } = useTranslation();
  const navigate = useNavigate();
  const user = useAuthStore((s) => s.user);
  const [campaigns, setCampaigns] = useState([]);
  const [milestones, setMilestones] = useState({});
  const [treasuries, setTreasuries] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!user) { navigate('/login'); return; }
    (async () => {
      setLoading(true);
      try {
        // Admins see ALL campaigns; others see only their own
        const params = {};
        const role = (user.role || '').toUpperCase();
        const isAdmin = role === 'SYSTEM_ADMIN' || role === 'SUPER_ADMIN';
        if (!isAdmin) {
          if (user.ngo_id) params.ngoId = user.ngo_id;
          else params.creatorUserId = user.id;
        }
        const res = await listCampaigns({ ...params, pageSize: 50 });
        const items = res.items || res;
        setCampaigns(items);

        // Fetch milestones and treasury for each
        const msMap = {}, trMap = {};
        await Promise.all(items.map(async (c) => {
          try { msMap[c.id] = await getCampaignMilestones(c.id); } catch { /* none */ }
          try { trMap[c.id] = await getCampaignTreasury(c.id); } catch { /* none */ }
        }));
        setMilestones(msMap);
        setTreasuries(trMap);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [user]);

  if (!user) return null;

  const fmt = (n) => n == null ? '0' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });

  return (
    <PageBg pattern="blueprint" colorA="#10B981" colorB="#3B82F6">
    <div className="max-w-5xl mx-auto px-4 py-6">
      <PageHeader icon={HiOutlineDocumentText} title="My Projects" subtitle="Manage your campaigns, milestones, and financials" accentColor="blue" bespoke="blueprint" />

      {/* Action bar */}
      <div className="flex items-center justify-between mb-6">
        <Link to="/campaigns" className="inline-flex items-center gap-1 text-sm text-emerald-600 hover:underline">
          <HiOutlineArrowLeft className="w-4 h-4" /> All Campaigns
        </Link>
        <Link
          to="/create-campaign"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 text-white text-sm font-semibold hover:from-emerald-700 hover:to-green-700 transition shadow-lg shadow-emerald-300/30"
        >
          <HiOutlinePlusCircle className="w-4 h-4" /> New Campaign
        </Link>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      {loading ? (
        <div className="text-center py-20 text-gray-400">Loading your projects…</div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-20">
          <HiOutlineDocumentText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">You haven't created any campaigns yet.</p>
          <Link to="/create-campaign" className="text-emerald-600 font-semibold hover:underline">Create your first campaign →</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns.map((c) => {
            const pct = c.goal_amount_usd > 0 ? Math.min(100, ((c.current_usd_total || c.raised_amount_usd) / c.goal_amount_usd) * 100) : 0;
            const ms = milestones[c.id] || [];
            const tr = treasuries[c.id];
            const badge = STATUS_BADGE[c.status] || STATUS_BADGE.active;
            const completedMs = ms.filter(m => ['verified', 'released'].includes(m.status?.toLowerCase())).length;

            return (
              <div key={c.id} className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow">
                {/* Accent line */}
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />
                {/* Corner SVG */}
                <svg className="absolute top-2 right-2 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
                  <path d="M45 35 L57 10 L69 35" stroke="#10B981" strokeWidth="0.5" opacity="0.04" />
                  <circle cx="57" cy="10" r="2" fill="#10B981" opacity="0.04" />
                  <path d="M10 70 L25 60 L40 70" stroke="#10B981" strokeWidth="0.4" opacity="0.03" />
                </svg>

                <div className="p-4 sm:p-5">
                  {/* Header row */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded-full ring-1 ${badge.bg} ${badge.text} ${badge.ring}`}>
                          {badge.label}
                        </span>
                        {c.category && (
                          <span className="inline-block bg-emerald-50 text-emerald-600 text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize">{c.category}</span>
                        )}
                      </div>
                      <Link to={`/campaign/${c.id}`} className="text-lg font-bold text-gray-900 hover:text-emerald-600 transition line-clamp-1">
                        {c.title}
                      </Link>
                      {c.ngo_name && <p className="text-xs text-gray-400 mt-0.5">by {c.ngo_name}</p>}
                    </div>
                  </div>

                  {/* Stats row */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                    <div className="bg-gray-50 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
                        <HiOutlineBanknotes className="w-3.5 h-3.5" /> Raised
                      </div>
                      <p className="text-base font-bold text-gray-900">${fmt(c.current_usd_total || c.raised_amount_usd)}</p>
                      <p className="text-[10px] text-gray-400">of ${fmt(c.goal_amount_usd)}</p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
                        <HiOutlineCheckCircle className="w-3.5 h-3.5" /> Milestones
                      </div>
                      <p className="text-base font-bold text-gray-900">{completedMs}/{ms.length || '-'}</p>
                      <p className="text-[10px] text-gray-400">completed</p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
                        <HiOutlineShieldCheck className="w-3.5 h-3.5" /> Released
                      </div>
                      <p className="text-base font-bold text-gray-900">${fmt(tr?.total_released_usd)}</p>
                      <p className="text-[10px] text-gray-400">to project</p>
                    </div>
                    <div className="bg-gray-50 rounded-xl p-3">
                      <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
                        <HiOutlineChartBar className="w-3.5 h-3.5" /> Donors
                      </div>
                      <p className="text-base font-bold text-gray-900">{c.donation_count || 0}</p>
                      <p className="text-[10px] text-gray-400">supporters</p>
                    </div>
                  </div>

                  {/* Progress bar */}
                  <ProgressBar percentage={pct} className="mb-4" />

                  {/* Milestone mini-timeline */}
                  {ms.length > 0 && (
                    <div className="flex gap-1 mb-4">
                      {ms.map((m, i) => {
                        const s = m.status?.toLowerCase();
                        const color = s === 'released' ? 'bg-emerald-500' : s === 'verified' ? 'bg-blue-500' : s === 'active' ? 'bg-emerald-400' : s === 'evidence_submitted' || s === 'under_review' ? 'bg-amber-400' : 'bg-gray-200';
                        return (
                          <div key={i} className="flex-1 group relative">
                            <div className={`h-2 rounded-full ${color} transition`} />
                            <div className="absolute bottom-full mb-1 left-1/2 -translate-x-1/2 bg-gray-900 text-white text-[10px] px-2 py-0.5 rounded whitespace-nowrap opacity-0 group-hover:opacity-100 transition pointer-events-none">
                              {m.title}: {m.status}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  )}

                  {/* Action buttons */}
                  <div className="flex flex-wrap gap-2">
                    <Link to={`/campaign/${c.id}/edit`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition">
                      <HiOutlineCog6Tooth className="w-3.5 h-3.5" /> Edit
                    </Link>
                    <Link to={`/campaign/${c.id}/milestones`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-green-50 text-green-700 text-xs font-semibold hover:bg-green-100 transition">
                      <HiOutlineCheckCircle className="w-3.5 h-3.5" /> Milestones
                    </Link>
                    <Link to={`/campaign/${c.id}/financials`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition">
                      <HiOutlineBanknotes className="w-3.5 h-3.5" /> Financials
                    </Link>
                    <Link to={`/campaign/${c.id}/updates`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 transition">
                      <HiOutlineDocumentText className="w-3.5 h-3.5" /> Updates
                    </Link>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
    </PageBg>
  );
}
