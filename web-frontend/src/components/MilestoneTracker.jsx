/**
 * MilestoneTracker — visual timeline of milestone-gated funding.
 *
 * Shows each milestone as a step in a vertical pipeline with status
 * indicators, amounts, progress, evidence submitted by the NGO,
 * and field-agent verification details.  Used on CampaignDetail
 * and DonateCheckout pages.
 */

import { useState, useEffect } from 'react';
import { getCampaignMilestones } from '../api/campaigns';
import {
  HiOutlineCheckCircle,
  HiOutlineClock,
  HiOutlineShieldCheck,
  HiOutlineLockClosed,
  HiOutlineDocumentText,
  HiOutlineCamera,
  HiOutlineMapPin,
} from '../components/icons';

/* ── Status config ──────────────────────────────────── */

const STATUS_MAP = {
  active:             { label: 'Raising',          color: 'text-emerald-600', bg: 'bg-emerald-50',  border: 'border-emerald-200', icon: HiOutlineClock,      ring: 'ring-emerald-400' },
  pending:            { label: 'Upcoming',         color: 'text-gray-400',   bg: 'bg-gray-50',    border: 'border-gray-200',   icon: HiOutlineLockClosed, ring: 'ring-gray-300' },
  evidence_submitted: { label: 'Evidence Sent',    color: 'text-amber-600',  bg: 'bg-amber-50',   border: 'border-amber-200',  icon: HiOutlineDocumentText, ring: 'ring-amber-400' },
  under_review:       { label: 'Under Review',     color: 'text-amber-600',  bg: 'bg-amber-50',   border: 'border-amber-200',  icon: HiOutlineShieldCheck,ring: 'ring-amber-400' },
  verified:           { label: 'Verified',         color: 'text-green-600',  bg: 'bg-green-50',   border: 'border-green-200',  icon: HiOutlineShieldCheck,ring: 'ring-green-400' },
  released:           { label: 'Funds Released',   color: 'text-emerald-600',bg: 'bg-emerald-50', border: 'border-emerald-200',icon: HiOutlineCheckCircle,ring: 'ring-emerald-400' },
  failed:             { label: 'Failed',           color: 'text-red-500',    bg: 'bg-red-50',     border: 'border-red-200',    icon: HiOutlineLockClosed, ring: 'ring-red-400' },
};

const DEFAULT_STATUS = STATUS_MAP.pending;

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

/* ── Component ──────────────────────────────────────── */

export default function MilestoneTracker({ campaignId, compact = false }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!campaignId) return;
    setLoading(true);
    getCampaignMilestones(campaignId)
      .then((d) => setData(d))
      .catch(() => setData(null))
      .finally(() => setLoading(false));
  }, [campaignId]);

  if (loading) return null;
  if (!data || !data.milestones?.length) return null;

  const milestones = data.milestones;
  const total = data.total_target_usd || 0;
  const released = data.total_released_usd || 0;
  const progressPct = total > 0 ? Math.min(100, (released / total) * 100) : 0;

  /* Compact mode: just the summary bar */
  if (compact) {
    const activeMs = milestones.find((m) => m.status === 'active') || milestones[0];
    const completedCount = milestones.filter(
      (m) => m.status === 'released' || m.status === 'verified'
    ).length;
    return (
      <div className="flex items-center gap-2 text-xs text-gray-500 mt-1">
        <span className="inline-flex items-center gap-1 text-emerald-600 font-medium">
          <HiOutlineShieldCheck className="w-3.5 h-3.5" />
          Milestone-gated
        </span>
        <span className="text-gray-300">|</span>
        <span>{completedCount}/{milestones.length} complete</span>
        {activeMs && (
          <>
            <span className="text-gray-300">|</span>
            <span>Now: {activeMs.title}</span>
          </>
        )}
      </div>
    );
  }

  return (
    <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-emerald-500 to-transparent" />

      {/* Bespoke corner SVG */}
      <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
        <rect x="45" y="10" width="24" height="30" rx="3" stroke="#059669" strokeWidth="0.5" opacity="0.05" />
        <path d="M50 18 L64 18" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
        <path d="M50 24 L60 24" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
        <circle cx="57" cy="46" r="1.5" fill="#059669" opacity="0.06" />
      </svg>

      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <HiOutlineShieldCheck className="w-5 h-5 text-emerald-600" />
          <h3 className="font-semibold text-gray-900 text-sm">Milestone Funding</h3>
        </div>
        <span className="text-xs text-gray-400">
          ${fmt(released)} / ${fmt(total)} released
        </span>
      </div>

      {/* Overall progress bar */}
      <div className="h-2 bg-gray-100 rounded-full overflow-hidden mb-5">
        <div
          className="h-full bg-gradient-to-r from-emerald-500 to-emerald-500 rounded-full transition-all duration-700 ease-out"
          style={{ width: `${progressPct}%` }}
        />
      </div>

      {/* Milestone timeline */}
      <div className="space-y-0">
        {milestones.map((m, idx) => {
          const cfg = STATUS_MAP[m.status] || DEFAULT_STATUS;
          const Icon = cfg.icon;
          const isLast = idx === milestones.length - 1;
          const pct =
            m.target_amount_usd > 0
              ? Math.min(100, ((m.released_amount_usd || 0) / m.target_amount_usd) * 100)
              : 0;

          const hasEvidence = !!m.evidence_notes || (m.evidence_ipfs_hashes?.length > 0);
          const verifications = m.verifications || [];
          const approvedV = verifications.filter((v) => v.status === 'approved');
          const avgTrust = approvedV.length > 0
            ? Math.round(approvedV.reduce((s, v) => s + v.trust_score, 0) / approvedV.length)
            : null;

          return (
            <div key={m.id} className="relative flex gap-3">
              {/* Vertical connector line */}
              {!isLast && (
                <div className="absolute left-[15px] top-[32px] bottom-0 w-px bg-gray-200" />
              )}

              {/* Step circle */}
              <div className={`relative z-10 flex-shrink-0 w-[30px] h-[30px] rounded-full flex items-center justify-center ${cfg.bg} border ${cfg.border} ring-2 ring-offset-1 ${cfg.ring}`}>
                <Icon className={`w-4 h-4 ${cfg.color}`} />
              </div>

              {/* Content */}
              <div className={`flex-1 pb-5 ${isLast ? 'pb-0' : ''}`}>
                <div className="flex items-center justify-between">
                  <h4 className="text-sm font-medium text-gray-900">
                    {m.title}
                  </h4>
                  <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${cfg.bg} ${cfg.color} border ${cfg.border}`}>
                    {cfg.label}
                  </span>
                </div>

                <p className="text-xs text-gray-500 mt-0.5 line-clamp-2">
                  {m.description}
                </p>

                {/* Amount bar */}
                <div className="mt-2 flex items-center gap-2">
                  <div className="flex-1 h-1.5 bg-gray-100 rounded-full overflow-hidden">
                    <div
                      className={`h-full rounded-full transition-all duration-500 ${
                        m.status === 'released'
                          ? 'bg-emerald-500'
                          : m.status === 'active'
                          ? 'bg-emerald-500'
                          : 'bg-gray-200'
                      }`}
                      style={{ width: `${m.status === 'released' ? 100 : pct}%` }}
                    />
                  </div>
                  <span className="text-xs font-medium text-gray-600 whitespace-nowrap">
                    ${fmt(m.target_amount_usd)}
                  </span>
                </div>

                {/* ── Evidence from project owner ── */}
                {hasEvidence && (
                  <div className="mt-3 bg-emerald-50/60 border border-emerald-100 rounded-xl px-3 py-2.5">
                    <div className="flex items-center gap-1.5 mb-1">
                      <HiOutlineDocumentText className="w-3.5 h-3.5 text-emerald-500" />
                      <span className="text-[11px] font-semibold text-emerald-600 uppercase tracking-wide">Project Evidence</span>
                      {!approvedV.length && (
                        <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded-full bg-amber-100 text-amber-700 font-medium">Unverified</span>
                      )}
                      {approvedV.length > 0 && (
                        <span className="ml-auto text-[10px] px-1.5 py-0.5 rounded-full bg-green-100 text-green-700 font-medium flex items-center gap-0.5">
                          <HiOutlineShieldCheck className="w-3 h-3" /> Verified
                        </span>
                      )}
                    </div>
                    {m.evidence_notes && (
                      <p className="text-xs text-gray-600 line-clamp-3">{m.evidence_notes}</p>
                    )}
                    {m.evidence_ipfs_hashes?.length > 0 && (
                      <div className="flex items-center gap-1.5 mt-1.5 flex-wrap">
                        <HiOutlineCamera className="w-3 h-3 text-gray-400" />
                        {m.evidence_ipfs_hashes.map((hash, i) => (
                          <a key={i} href={`https://gateway.pinata.cloud/ipfs/${hash}`} target="_blank" rel="noreferrer"
                            className="text-[10px] text-emerald-600 hover:underline font-mono bg-white/60 px-1.5 py-0.5 rounded">
                            Doc {i + 1}
                          </a>
                        ))}
                      </div>
                    )}
                    {m.evidence_submitted_at && (
                      <p className="text-[10px] text-gray-400 mt-1">
                        Submitted {new Date(m.evidence_submitted_at).toLocaleDateString()}
                      </p>
                    )}
                  </div>
                )}

                {/* ── Field agent verification(s) ── */}
                {verifications.length > 0 && (
                  <div className="mt-2 space-y-2">
                    {verifications.map((v) => (
                      <div key={v.id} className={`rounded-xl px-3 py-2.5 border ${
                        v.status === 'approved' ? 'bg-green-50/60 border-green-100' :
                        v.status === 'rejected' ? 'bg-red-50/60 border-red-100' :
                        'bg-amber-50/60 border-amber-100'
                      }`}>
                        <div className="flex items-center gap-1.5 mb-1">
                          <HiOutlineShieldCheck className={`w-3.5 h-3.5 ${
                            v.status === 'approved' ? 'text-green-500' :
                            v.status === 'rejected' ? 'text-red-500' :
                            'text-amber-500'
                          }`} />
                          <span className="text-[11px] font-semibold uppercase tracking-wide" style={{
                            color: v.status === 'approved' ? '#059669' : v.status === 'rejected' ? '#dc2626' : '#d97706'
                          }}>
                            Field Verification: {v.status === 'approved' ? 'Approved' : v.status === 'rejected' ? 'Rejected' : 'Pending Review'}
                          </span>
                          {v.trust_score != null && (
                            <span className={`ml-auto text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                              v.trust_score >= 70 ? 'bg-green-100 text-green-700' :
                              v.trust_score >= 40 ? 'bg-amber-100 text-amber-700' :
                              'bg-red-100 text-red-700'
                            }`}>
                              Trust: {v.trust_score}/100
                            </span>
                          )}
                        </div>
                        {v.agent_notes && <p className="text-xs text-gray-600 line-clamp-2">{v.agent_notes}</p>}
                        <div className="flex items-center gap-3 mt-1 text-[10px] text-gray-400 flex-wrap">
                          {v.agent_name && <span>Agent: {v.agent_name}</span>}
                          {v.gps_latitude && v.gps_longitude && (
                            <span className="flex items-center gap-0.5">
                              <HiOutlineMapPin className="w-3 h-3" />
                              {Number(v.gps_latitude).toFixed(4)}, {Number(v.gps_longitude).toFixed(4)}
                            </span>
                          )}
                          {v.photos?.length > 0 && (
                            <span className="flex items-center gap-0.5">
                              <HiOutlineCamera className="w-3 h-3" />
                              {v.photos.length} photo{v.photos.length !== 1 ? 's' : ''}
                            </span>
                          )}
                          {v.created_at && <span>{new Date(v.created_at).toLocaleDateString()}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* ── Trust score summary badge ── */}
                {avgTrust != null && (
                  <div className="mt-2 flex items-center gap-1.5 text-xs">
                    <div className={`w-2 h-2 rounded-full ${avgTrust >= 70 ? 'bg-green-500' : avgTrust >= 40 ? 'bg-amber-500' : 'bg-red-500'}`} />
                    <span className="text-gray-500">
                      Avg Trust Score: <span className="font-semibold text-gray-700">{avgTrust}/100</span> from {approvedV.length} verification{approvedV.length !== 1 ? 's' : ''}
                    </span>
                  </div>
                )}

                {/* ── On-chain TX ── */}
                {m.chain_tx_hash && (
                  <a href={`https://sepolia.basescan.org/tx/${m.chain_tx_hash}`} target="_blank" rel="noreferrer"
                    className="inline-flex items-center gap-1 mt-2 text-[10px] text-emerald-600 hover:underline font-mono">
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path d="M13.5 6H5.25A2.25 2.25 0 003 8.25v10.5A2.25 2.25 0 005.25 21h10.5A2.25 2.25 0 0018 18.75V10.5m-10.5 6L21 3m0 0h-5.25M21 3v5.25" strokeLinecap="round" strokeLinejoin="round" /></svg>
                    On-chain: {m.chain_tx_hash.slice(0, 10)}…{m.chain_tx_hash.slice(-6)}
                  </a>
                )}
              </div>
            </div>
          );
        })}
      </div>

      {/* On-chain badge */}
      <div className="mt-4 pt-3 border-t border-gray-100 flex items-center gap-1.5 text-xs text-gray-400">
        <svg className="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
          <path d="M21 12a9 9 0 01-9 9m9-9a9 9 0 00-9-9m9 9H3m9 9a9 9 0 01-9-9m9 9c1.657 0 3-4.03 3-9s-1.343-9-3-9m0 18c-1.657 0-3-4.03-3-9s1.343-9 3-9m-9 9a9 9 0 019-9" strokeLinecap="round" strokeLinejoin="round" />
        </svg>
        Every milestone release is recorded on-chain for full transparency
      </div>
    </div>
  );
}
