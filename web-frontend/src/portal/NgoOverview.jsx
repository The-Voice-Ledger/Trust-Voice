/**
 * NgoOverview — portal landing for NGO_ADMIN / CAMPAIGN_CREATOR roles.
 *
 * Shows an overview of the user's campaigns, milestone status, funding
 * totals, and quick action links.  Designed for the portal layout.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { listCampaigns, getCampaignMilestones, getCampaignTreasury } from '../api/campaigns';
import ProgressBar from '../components/ProgressBar';
import {
  HiOutlinePlusCircle, HiOutlineDocumentText, HiOutlineBanknotes,
  HiOutlineCheckCircle, HiOutlineChartBar, HiOutlineShieldCheck,
  HiOutlineCog6Tooth,
} from '../components/icons';

const fmt = (n) => (n == null ? '0' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 }));

export default function NgoOverview({ user }) {
  const [campaigns, setCampaigns] = useState([]);
  const [milestones, setMilestones] = useState({});
  const [treasuries, setTreasuries] = useState({});
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const params = {};
        if (user.ngo_id) params.ngoId = user.ngo_id;
        else params.creatorUserId = user.id;
        const res = await listCampaigns({ ...params, pageSize: 50 });
        const items = res.items || res;
        setCampaigns(items);

        const msMap = {}, trMap = {};
        await Promise.all(items.map(async (c) => {
          try { msMap[c.id] = await getCampaignMilestones(c.id); } catch { /* */ }
          try { trMap[c.id] = await getCampaignTreasury(c.id); } catch { /* */ }
        }));
        setMilestones(msMap);
        setTreasuries(trMap);
      } catch { /* */ }
      setLoading(false);
    })();
  }, [user]);

  // Aggregate stats
  const totalRaised = campaigns.reduce((s, c) => s + (c.current_usd_total || c.raised_amount_usd || 0), 0);
  const totalGoal = campaigns.reduce((s, c) => s + (c.goal_amount_usd || 0), 0);
  const allMs = Object.values(milestones).flatMap((d) => d?.milestones || []);
  const completedMs = allMs.filter((m) => ['verified', 'released'].includes(m.status?.toLowerCase())).length;
  const totalReleased = Object.values(treasuries).reduce((s, t) => s + (t?.total_released_usd || 0), 0);

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="flex items-start justify-between mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900 mb-1">Project Overview</h1>
          <p className="text-sm text-gray-500">Manage campaigns, milestones, and financials</p>
        </div>
        <Link to="/portal/create"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 text-white text-sm font-semibold hover:from-emerald-700 hover:to-green-700 transition shadow-lg shadow-emerald-300/30">
          <HiOutlinePlusCircle className="w-4 h-4" /> New Campaign
        </Link>
      </div>

      {/* Aggregate stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Stat accent="#10B981" icon={HiOutlineDocumentText} label="Campaigns" value={campaigns.length} />
        <Stat accent="#059669" icon={HiOutlineBanknotes} label="Total Raised" value={`$${fmt(totalRaised)}`} sub={`of $${fmt(totalGoal)}`} />
        <Stat accent="#14B8A6" icon={HiOutlineCheckCircle} label="Milestones" value={`${completedMs}/${allMs.length}`} sub="completed" />
        <Stat accent="#0D9488" icon={HiOutlineShieldCheck} label="Released" value={`$${fmt(totalReleased)}`} sub="to projects" />
      </div>

      {loading ? (
        <p className="text-center py-16 text-gray-400">Loading your projects…</p>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-20">
          <HiOutlineDocumentText className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">You haven't created any campaigns yet.</p>
          <Link to="/portal/create" className="text-emerald-600 font-semibold hover:underline">Create your first campaign →</Link>
        </div>
      ) : (
        <div className="space-y-4">
          {campaigns.map((c) => {
            const pct = c.goal_amount_usd > 0 ? Math.min(100, ((c.current_usd_total || c.raised_amount_usd || 0) / c.goal_amount_usd) * 100) : 0;
            const ms = milestones[c.id]?.milestones || [];
            const tr = treasuries[c.id];
            const doneMs = ms.filter((m) => ['verified', 'released'].includes(m.status?.toLowerCase())).length;
            const statusCfg = {
              active: { label: 'Active', cls: 'bg-emerald-50 text-emerald-700 ring-emerald-200' },
              paused: { label: 'Paused', cls: 'bg-amber-50 text-amber-700 ring-amber-200' },
              completed: { label: 'Completed', cls: 'bg-gray-100 text-gray-600 ring-gray-200' },
            };
            const badge = statusCfg[c.status] || statusCfg.active;

            return (
              <div key={c.id} className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden hover:shadow-lg transition-shadow">
                <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />
                <svg className="absolute top-2 right-2 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
                  <path d="M45 35 L57 10 L69 35" stroke="#10B981" strokeWidth="0.5" opacity="0.04" />
                  <circle cx="57" cy="10" r="2" fill="#10B981" opacity="0.04" />
                </svg>

                <div className="p-4 sm:p-5">
                  {/* Header */}
                  <div className="flex items-start justify-between gap-3 mb-3">
                    <div className="min-w-0 flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <span className={`inline-flex items-center px-2 py-0.5 text-[10px] font-semibold rounded-full ring-1 ${badge.cls}`}>{badge.label}</span>
                        {c.category && <span className="bg-emerald-50 text-emerald-600 text-[10px] font-semibold px-2 py-0.5 rounded-full capitalize">{c.category}</span>}
                      </div>
                      <Link to={`/campaign/${c.id}`} className="text-lg font-bold text-gray-900 hover:text-emerald-600 transition line-clamp-1">{c.title}</Link>
                      {c.ngo_name && <p className="text-xs text-gray-400 mt-0.5">by {c.ngo_name}</p>}
                    </div>
                  </div>

                  {/* Stats row */}
                  <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                    <MiniStat icon={HiOutlineBanknotes} label="Raised" value={`$${fmt(c.current_usd_total || c.raised_amount_usd)}`} sub={`of $${fmt(c.goal_amount_usd)}`} />
                    <MiniStat icon={HiOutlineCheckCircle} label="Milestones" value={`${doneMs}/${ms.length || '-'}`} sub="completed" />
                    <MiniStat icon={HiOutlineShieldCheck} label="Released" value={`$${fmt(tr?.total_released_usd)}`} sub="to project" />
                    <MiniStat icon={HiOutlineChartBar} label="Donors" value={c.donation_count || 0} sub="supporters" />
                  </div>

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
                    <Link to={`/portal/projects/${c.id}/edit`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition">
                      <HiOutlineCog6Tooth className="w-3.5 h-3.5" /> Edit
                    </Link>
                    <Link to={`/portal/projects/${c.id}/milestones`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-green-50 text-green-700 text-xs font-semibold hover:bg-green-100 transition">
                      <HiOutlineCheckCircle className="w-3.5 h-3.5" /> Milestones
                    </Link>
                    <Link to={`/portal/projects/${c.id}/financials`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-emerald-50 text-emerald-700 text-xs font-semibold hover:bg-emerald-100 transition">
                      <HiOutlineBanknotes className="w-3.5 h-3.5" /> Financials
                    </Link>
                    <Link to={`/portal/projects/${c.id}/updates`} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-blue-50 text-blue-700 text-xs font-semibold hover:bg-blue-100 transition">
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
  );
}

/* ── Sub-components ─────────────── */

function Stat({ accent, icon: Icon, label, value, sub }) {
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
      {sub && <p className="text-[10px] text-gray-400">{sub}</p>}
    </div>
  );
}

function MiniStat({ icon: Icon, label, value, sub }) {
  return (
    <div className="bg-gray-50 rounded-xl p-3">
      <div className="flex items-center gap-1.5 text-xs text-gray-500 mb-1">
        <Icon className="w-3.5 h-3.5" /> {label}
      </div>
      <p className="text-base font-bold text-gray-900">{value}</p>
      {sub && <p className="text-[10px] text-gray-400">{sub}</p>}
    </div>
  );
}
