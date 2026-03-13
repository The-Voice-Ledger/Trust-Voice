/**
 * MilestoneManager — full milestone lifecycle management for project owners.
 *
 * /portal/projects/:id/milestones
 *
 * Capabilities:
 * - View all milestones with status, amounts, descriptions
 * - Create new milestones (if none exist)
 * - Submit evidence for active milestones
 * - Track verification and release status
 * - See on-chain verification badges
 */
import { useState, useEffect, useCallback } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getCampaign, getCampaignMilestones, getCampaignTreasury,
  createMilestones, submitMilestoneEvidence,
} from '../api/campaigns';
import {
  HiOutlineArrowLeft, HiOutlineCheckCircle, HiOutlineClock,
  HiOutlineShieldCheck, HiOutlineLockClosed, HiOutlinePlusCircle,
  HiOutlineDocumentText, HiOutlineXMark,
} from '../components/icons';

const STATUS_MAP = {
  active:             { label: 'Raising',       color: 'text-indigo-600', bg: 'bg-indigo-50',  border: 'border-indigo-200', icon: HiOutlineClock,        ring: 'ring-indigo-400' },
  pending:            { label: 'Upcoming',      color: 'text-gray-400',   bg: 'bg-gray-50',    border: 'border-gray-200',   icon: HiOutlineLockClosed,   ring: 'ring-gray-300' },
  evidence_submitted: { label: 'Evidence Sent', color: 'text-amber-600',  bg: 'bg-amber-50',   border: 'border-amber-200',  icon: HiOutlineClock,        ring: 'ring-amber-400' },
  under_review:       { label: 'Under Review',  color: 'text-amber-600',  bg: 'bg-amber-50',   border: 'border-amber-200',  icon: HiOutlineShieldCheck,  ring: 'ring-amber-400' },
  verified:           { label: 'Verified',      color: 'text-green-600',  bg: 'bg-green-50',   border: 'border-green-200',  icon: HiOutlineShieldCheck,  ring: 'ring-green-400' },
  released:           { label: 'Released',      color: 'text-emerald-600',bg: 'bg-emerald-50', border: 'border-emerald-200',icon: HiOutlineCheckCircle,  ring: 'ring-emerald-400' },
  failed:             { label: 'Failed',        color: 'text-red-500',    bg: 'bg-red-50',     border: 'border-red-200',    icon: HiOutlineLockClosed,   ring: 'ring-red-400' },
};
const DEFAULT_STATUS = STATUS_MAP.pending;
const fmt = (n) => n == null ? '0' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });

export default function MilestoneManager() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [data, setData] = useState(null);
  const [treasury, setTreasury] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Creation form
  const [showCreate, setShowCreate] = useState(false);
  const [newMilestones, setNewMilestones] = useState([{ title: '', description: '', target_amount_usd: '' }]);
  const [creating, setCreating] = useState(false);

  // Evidence form
  const [evidenceFor, setEvidenceFor] = useState(null); // milestone id
  const [evidenceNotes, setEvidenceNotes] = useState('');
  const [submittingEvidence, setSubmittingEvidence] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [c, ms, tr] = await Promise.all([
        getCampaign(id),
        getCampaignMilestones(id).catch(() => null),
        getCampaignTreasury(id).catch(() => null),
      ]);
      setCampaign(c);
      setData(ms);
      setTreasury(tr);
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  }, [id]);

  useEffect(() => { load(); }, [load]);

  const milestones = data?.milestones || [];
  const totalTarget = data?.total_target_usd || 0;
  const totalReleased = data?.total_released_usd || 0;
  const progressPct = totalTarget > 0 ? Math.min(100, (totalReleased / totalTarget) * 100) : 0;

  /* ── Create milestones ─── */
  const addRow = () => setNewMilestones((p) => [...p, { title: '', description: '', target_amount_usd: '' }]);
  const removeRow = (i) => setNewMilestones((p) => p.filter((_, idx) => idx !== i));
  const updateRow = (i, field, value) => setNewMilestones((p) => p.map((r, idx) => idx === i ? { ...r, [field]: value } : r));

  const handleCreate = async () => {
    setCreating(true); setError(null);
    try {
      await createMilestones({
        campaign_id: parseInt(id),
        milestones: newMilestones.map((m, i) => ({
          title: m.title,
          description: m.description,
          target_amount_usd: parseFloat(m.target_amount_usd) || 0,
          order_index: i,
        })),
      });
      setShowCreate(false);
      setNewMilestones([{ title: '', description: '', target_amount_usd: '' }]);
      await load();
    } catch (err) { setError(err.message); }
    finally { setCreating(false); }
  };

  /* ── Submit evidence ─── */
  const handleEvidence = async () => {
    setSubmittingEvidence(true); setError(null);
    try {
      await submitMilestoneEvidence({
        milestone_id: evidenceFor,
        evidence_notes: evidenceNotes,
      });
      setEvidenceFor(null);
      setEvidenceNotes('');
      await load();
    } catch (err) { setError(err.message); }
    finally { setSubmittingEvidence(false); }
  };

  if (loading) return <div className="text-center py-20 text-gray-400">Loading…</div>;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      {/* Back + title */}
      <div className="flex items-center justify-between mb-6">
        <Link to="/portal/projects" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline">
          <HiOutlineArrowLeft className="w-4 h-4" /> My Projects
        </Link>
        {campaign && <Link to={`/campaign/${id}`} className="text-xs text-gray-400 hover:text-gray-600">View public page →</Link>}
      </div>

      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Milestone Manager</h1>
        <p className="text-sm text-gray-500 mt-0.5">{campaign?.title}</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      {/* Summary bar */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-5 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-indigo-500 to-transparent" />
        <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
          <rect x="45" y="10" width="24" height="30" rx="3" stroke="#059669" strokeWidth="0.5" opacity="0.05" />
          <path d="M50 18 L64 18" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
          <circle cx="57" cy="46" r="1.5" fill="#059669" opacity="0.06" />
        </svg>

        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center gap-2">
            <HiOutlineShieldCheck className="w-5 h-5 text-emerald-600" />
            <span className="font-semibold text-gray-900 text-sm">Milestone Funding</span>
          </div>
          <span className="text-xs text-gray-400">${fmt(totalReleased)} / ${fmt(totalTarget)} released</span>
        </div>
        <div className="h-2 bg-gray-100 rounded-full overflow-hidden">
          <div className="h-full bg-gradient-to-r from-emerald-500 to-indigo-500 rounded-full transition-all duration-700" style={{ width: `${progressPct}%` }} />
        </div>
        <div className="flex items-center justify-between mt-2 text-xs text-gray-400">
          <span>{milestones.length} milestones</span>
          <span>{milestones.filter((m) => ['verified', 'released'].includes(m.status)).length} completed</span>
        </div>
      </div>

      {/* Milestones list or create prompt */}
      {milestones.length === 0 && !showCreate ? (
        <div className="text-center py-16">
          <HiOutlineShieldCheck className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-500 mb-4">No milestones defined for this campaign yet.</p>
          <button onClick={() => setShowCreate(true)}
            className="inline-flex items-center gap-2 px-5 py-3 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white font-semibold hover:from-indigo-700 hover:to-violet-700 transition text-sm">
            <HiOutlinePlusCircle className="w-4 h-4" /> Create Milestones
          </button>
        </div>
      ) : (
        <>
          {/* Timeline */}
          <div className="space-y-0 mb-8">
            {milestones.map((m, idx) => {
              const cfg = STATUS_MAP[m.status] || DEFAULT_STATUS;
              const Icon = cfg.icon;
              const isLast = idx === milestones.length - 1;
              const pct = m.target_amount_usd > 0 ? Math.min(100, ((m.released_amount_usd || 0) / m.target_amount_usd) * 100) : 0;
              const canSubmitEvidence = m.status === 'active';

              return (
                <div key={m.id} className="relative flex gap-3">
                  {!isLast && <div className="absolute left-[15px] top-[32px] bottom-0 w-px bg-gray-200" />}
                  <div className={`relative z-10 flex-shrink-0 w-[30px] h-[30px] rounded-full flex items-center justify-center ${cfg.bg} border ${cfg.border} ring-2 ring-offset-1 ${cfg.ring}`}>
                    <Icon className={`w-4 h-4 ${cfg.color}`} />
                  </div>
                  <div className={`flex-1 ${isLast ? 'pb-0' : 'pb-6'}`}>
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-medium text-gray-900">{m.title}</h4>
                      <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.bg} ${cfg.color} border ${cfg.border}`}>{cfg.label}</span>
                    </div>
                    <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">{m.description}</p>

                    {/* Amount bar */}
                    <div className="mt-2 flex items-center gap-2">
                      <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                        <div className={`h-full rounded-full transition-all duration-500 ${m.status === 'released' ? 'bg-emerald-500' : m.status === 'active' ? 'bg-indigo-500' : 'bg-gray-200'}`}
                          style={{ width: `${m.status === 'released' ? 100 : pct}%` }} />
                      </div>
                      <span className="text-xs font-medium text-gray-600 whitespace-nowrap">${fmt(m.target_amount_usd)}</span>
                    </div>

                    {/* Evidence submission for active milestone */}
                    {canSubmitEvidence && (
                      <div className="mt-3">
                        {evidenceFor === m.id ? (
                          <div className="bg-indigo-50/50 border border-indigo-100 rounded-xl p-3 space-y-3">
                            <textarea
                              value={evidenceNotes}
                              onChange={(e) => setEvidenceNotes(e.target.value)}
                              rows={3}
                              placeholder="Describe the evidence, progress made, photos taken…"
                              className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm resize-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none"
                            />
                            <div className="flex gap-2">
                              <button onClick={handleEvidence} disabled={submittingEvidence || !evidenceNotes.trim()}
                                className="px-4 py-2 rounded-lg bg-indigo-600 text-white text-xs font-semibold hover:bg-indigo-700 transition disabled:opacity-50">
                                {submittingEvidence ? 'Submitting…' : 'Submit Evidence'}
                              </button>
                              <button onClick={() => { setEvidenceFor(null); setEvidenceNotes(''); }}
                                className="px-3 py-2 rounded-lg bg-gray-100 text-gray-600 text-xs font-medium hover:bg-gray-200 transition">
                                Cancel
                              </button>
                            </div>
                          </div>
                        ) : (
                          <button onClick={() => setEvidenceFor(m.id)}
                            className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-indigo-50 text-indigo-700 text-xs font-semibold hover:bg-indigo-100 transition">
                            <HiOutlineDocumentText className="w-3.5 h-3.5" /> Submit Evidence
                          </button>
                        )}
                      </div>
                    )}

                    {/* Evidence note if already submitted */}
                    {m.evidence_notes && m.status !== 'active' && (
                      <div className="mt-2 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2 text-xs text-amber-700">
                        <span className="font-medium">Evidence:</span> {m.evidence_notes}
                      </div>
                    )}

                    {/* On-chain TX link */}
                    {m.blockchain_tx && (
                      <a href={m.blockchain_tx} target="_blank" rel="noreferrer"
                        className="inline-block mt-2 text-xs text-indigo-600 hover:underline font-mono">
                        On-chain: {m.blockchain_tx.slice(0, 20)}…
                      </a>
                    )}
                  </div>
                </div>
              );
            })}
          </div>

          {/* On-chain footer */}
          <div className="pt-3 border-t border-gray-100 flex items-center gap-1.5 text-xs text-gray-400 mb-6">
            <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
              <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" strokeLinecap="round" strokeLinejoin="round" />
            </svg>
            Every milestone release is recorded on Base Sepolia for full transparency
          </div>
        </>
      )}

      {/* Create milestones form */}
      {showCreate && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-5 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-indigo-500 to-transparent" />
          <div className="flex items-center justify-between mb-4">
            <h3 className="font-semibold text-gray-900 text-sm">Create Milestones</h3>
            <button onClick={() => setShowCreate(false)} className="text-gray-400 hover:text-gray-600 p-1">
              <HiOutlineXMark className="w-5 h-5" />
            </button>
          </div>

          <div className="space-y-4">
            {newMilestones.map((m, i) => (
              <div key={i} className="bg-gray-50 rounded-xl p-4 space-y-3 relative">
                {newMilestones.length > 1 && (
                  <button onClick={() => removeRow(i)} className="absolute top-2 right-2 text-gray-400 hover:text-red-500">
                    <HiOutlineXMark className="w-4 h-4" />
                  </button>
                )}
                <div className="flex items-center gap-2 mb-2">
                  <span className="w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold flex items-center justify-center">{i + 1}</span>
                  <span className="text-xs font-medium text-gray-500">Milestone {i + 1}</span>
                </div>
                <input type="text" value={m.title} onChange={(e) => updateRow(i, 'title', e.target.value)} placeholder="Milestone title"
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none" />
                <textarea rows={2} value={m.description} onChange={(e) => updateRow(i, 'description', e.target.value)} placeholder="What will be accomplished?"
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm resize-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none" />
                <input type="number" min={1} value={m.target_amount_usd} onChange={(e) => updateRow(i, 'target_amount_usd', e.target.value)} placeholder="Target amount (USD)"
                  className="w-full px-3 py-2 rounded-lg border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none" />
              </div>
            ))}
          </div>

          <div className="flex items-center justify-between mt-4">
            <button onClick={addRow} className="inline-flex items-center gap-1.5 text-sm text-indigo-600 font-medium hover:underline">
              <HiOutlinePlusCircle className="w-4 h-4" /> Add milestone
            </button>
            <button onClick={handleCreate} disabled={creating || newMilestones.some((m) => !m.title || !m.target_amount_usd)}
              className="px-5 py-2.5 rounded-xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-semibold hover:from-indigo-700 hover:to-violet-700 transition disabled:opacity-50">
              {creating ? 'Creating…' : 'Create Milestones'}
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
