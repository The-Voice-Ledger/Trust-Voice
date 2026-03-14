/**
 * ActionCards — Renders visual action cards pushed by the voice agent
 * via LiveKit text stream (topic: "vbv.action").
 *
 * Card types:
 *   payment_link     – Clickable Stripe checkout button
 *   donation_receipt  – M-Pesa / pending donation confirmation
 *   donation_history  – List of past donations
 *   campaign_card     – Single campaign info card
 *   campaign_list     – Search results (multiple campaigns)
 *   milestone_update  – Milestone status change
 *   payout_status     – Payout approved/rejected
 *   error             – Error message
 */

// ── Individual card renderers ──────────────────────────────────

function PaymentLinkCard({ data }) {
  return (
    <div className="rounded-xl bg-gradient-to-br from-emerald-500/15 to-green-600/10 border border-emerald-500/20 p-4">
      <div className="flex items-center gap-2 mb-2">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none" stroke="#10B981" strokeWidth="1.5">
          <rect x="1" y="3" width="14" height="10" rx="2" />
          <path d="M1 7h14" />
        </svg>
        <span className="text-xs font-semibold text-emerald-400">Secure Payment</span>
      </div>
      <p className="text-sm text-white/80 mb-3">
        <span className="font-bold text-white">${data.amount?.toFixed(2)} {data.currency}</span>
        {' '}to {data.campaign_title}
      </p>
      {data.url && (
        <a
          href={data.url}
          target="_blank"
          rel="noopener noreferrer"
          className="inline-flex items-center gap-2 px-4 py-2.5 rounded-lg bg-emerald-500 hover:bg-emerald-400 text-white text-sm font-semibold transition-colors shadow-lg shadow-emerald-500/20"
        >
          <svg width="14" height="14" viewBox="0 0 14 14" fill="none" stroke="currentColor" strokeWidth="1.5">
            <path d="M6 1h7v7M13 1L6 8" strokeLinecap="round" />
          </svg>
          Complete Payment
        </a>
      )}
    </div>
  );
}

function DonationReceiptCard({ data }) {
  const isPending = data.status === 'pending';
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-4">
      <div className="flex items-center gap-2 mb-2">
        <div className={`w-2 h-2 rounded-full ${isPending ? 'bg-yellow-400 animate-pulse' : 'bg-emerald-400'}`} />
        <span className="text-xs font-semibold text-white/60">
          {isPending ? 'Payment Pending' : 'Donation Confirmed'}
        </span>
      </div>
      <p className="text-sm text-white/80">
        <span className="font-bold text-white">${data.amount?.toFixed(2)} {data.currency}</span>
        {' '}→ {data.campaign_title}
      </p>
      {data.payment_method === 'mpesa' && isPending && (
        <p className="text-xs text-yellow-300/70 mt-2">
          📱 Check your phone for the M-Pesa PIN prompt
        </p>
      )}
    </div>
  );
}

function DonationHistoryCard({ data }) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-4">
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-white/60">Your Donations</span>
        <span className="text-xs text-emerald-400 font-mono">
          Total: ${data.total_donated_usd?.toFixed(2)}
        </span>
      </div>
      <div className="space-y-2 max-h-40 overflow-y-auto scrollbar-thin">
        {(data.donations || []).map((d, i) => (
          <div key={i} className="flex items-center justify-between text-xs py-1.5 border-b border-white/5 last:border-0">
            <div className="flex-1 min-w-0">
              <p className="text-white/70 truncate">{d.campaign}</p>
              <p className="text-white/30 text-[10px]">{d.date} • {d.payment_method}</p>
            </div>
            <div className="text-right ml-3">
              <p className="text-white/80 font-mono">${d.amount_usd?.toFixed(2)}</p>
              <p className={`text-[10px] ${d.status === 'completed' ? 'text-emerald-400' : 'text-yellow-400'}`}>
                {d.status}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function CampaignCard({ data }) {
  const pct = data.progress_pct || 0;
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-4">
      {data.just_created && (
        <div className="text-xs text-emerald-400 font-semibold mb-2">✨ Campaign Created</div>
      )}
      <h4 className="text-sm font-semibold text-white/90 mb-1">{data.title}</h4>
      <div className="flex items-center gap-2 text-[10px] text-white/40 mb-3">
        {data.category && <span className="px-1.5 py-0.5 rounded bg-white/5">{data.category}</span>}
        {data.location && data.location !== 'N/A' && <span>{data.location}</span>}
      </div>
      {/* Progress bar */}
      <div className="w-full h-1.5 rounded-full bg-white/5 mb-1.5">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-green-400 transition-all"
          style={{ width: `${Math.min(pct, 100)}%` }}
        />
      </div>
      <div className="flex justify-between text-[10px]">
        <span className="text-white/50">${data.raised_usd?.toLocaleString()} raised</span>
        <span className="text-emerald-400">{pct}% of ${data.goal_usd?.toLocaleString()}</span>
      </div>
    </div>
  );
}

function CampaignListCard({ data }) {
  return (
    <div className="space-y-2">
      <span className="text-xs font-semibold text-white/50">
        {data.campaigns?.length || 0} campaigns found
      </span>
      {(data.campaigns || []).map((c, i) => (
        <CampaignCard key={i} data={c} />
      ))}
    </div>
  );
}

function PayoutStatusCard({ data }) {
  const isApproved = data.action === 'approved';
  return (
    <div className={`rounded-xl p-4 border ${isApproved
      ? 'bg-emerald-500/10 border-emerald-500/20'
      : 'bg-red-500/10 border-red-500/20'}`}
    >
      <div className="flex items-center gap-2">
        <div className={`w-2 h-2 rounded-full ${isApproved ? 'bg-emerald-400' : 'bg-red-400'}`} />
        <span className={`text-xs font-semibold ${isApproved ? 'text-emerald-400' : 'text-red-400'}`}>
          Payout #{data.payout_id} {data.action}
        </span>
      </div>
      <p className="text-sm text-white/70 mt-1">
        {data.amount} {data.currency}
      </p>
      {data.reason && (
        <p className="text-xs text-red-300/60 mt-1">Reason: {data.reason}</p>
      )}
    </div>
  );
}

function MilestoneUpdateCard({ data }) {
  return (
    <div className="rounded-xl bg-white/5 border border-white/10 p-4">
      <div className="flex items-center gap-2 mb-1">
        <span className="text-xs font-semibold text-white/60">Milestone Update</span>
      </div>
      <p className="text-sm text-white/80">{data.message || `Milestone #${data.milestone_id} updated`}</p>
      {data.status && (
        <span className="inline-block mt-2 px-2 py-0.5 rounded text-[10px] bg-white/5 text-white/50">
          {data.status}
        </span>
      )}
    </div>
  );
}

function ErrorCard({ data }) {
  return (
    <div className="rounded-xl bg-red-500/10 border border-red-500/20 p-3">
      <p className="text-xs text-red-300/80">{data.message || 'An error occurred'}</p>
    </div>
  );
}

// ── Card dispatcher ────────────────────────────────────────────

function ActionCard({ data }) {
  switch (data?.type) {
    case 'payment_link':    return <PaymentLinkCard data={data} />;
    case 'donation_receipt': return <DonationReceiptCard data={data} />;
    case 'donation_history': return <DonationHistoryCard data={data} />;
    case 'campaign_card':    return <CampaignCard data={data} />;
    case 'campaign_list':    return <CampaignListCard data={data} />;
    case 'payout_status':    return <PayoutStatusCard data={data} />;
    case 'milestone_update': return <MilestoneUpdateCard data={data} />;
    case 'error':            return <ErrorCard data={data} />;
    default:                 return null;
  }
}

// ── Main export — renders all action cards from text stream ────

export default function ActionCards({ textStreams }) {
  if (!textStreams || textStreams.length === 0) return null;

  // Parse JSON from each stream entry, skip invalid
  const cards = textStreams
    .map((stream) => {
      try {
        return JSON.parse(stream.text || stream);
      } catch {
        return null;
      }
    })
    .filter(Boolean);

  if (cards.length === 0) return null;

  return (
    <div className="w-full space-y-3">
      {cards.map((card, i) => (
        <ActionCard key={i} data={card} />
      ))}
    </div>
  );
}
