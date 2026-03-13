/**
 * CampaignFinancials — treasury breakdown, donations, and payouts.
 *
 * /portal/projects/:id/financials
 */
import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import {
  getCampaign, getCampaignTreasury, getCampaignDonations, getCampaignPayouts, createPayout,
} from '../api/campaigns';
import {
  HiOutlineArrowLeft, HiOutlineBanknotes, HiOutlineShieldCheck,
  HiOutlineDocumentText, HiOutlineCheckCircle,
} from '../components/icons';

const fmt = (n) => n == null ? '0' : Number(n).toLocaleString('en-US', { maximumFractionDigits: 2 });

export default function CampaignFinancials() {
  const { id } = useParams();
  const [campaign, setCampaign] = useState(null);
  const [treasury, setTreasury] = useState(null);
  const [donations, setDonations] = useState([]);
  const [payouts, setPayouts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Payout request
  const [showPayout, setShowPayout] = useState(false);
  const [payoutForm, setPayoutForm] = useState({ amount: '', currency: 'USD', payment_method: 'bank', notes: '' });
  const [requesting, setRequesting] = useState(false);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [c, tr, don, pay] = await Promise.all([
          getCampaign(id),
          getCampaignTreasury(id).catch(() => null),
          getCampaignDonations(id).catch(() => []),
          getCampaignPayouts(id).catch(() => []),
        ]);
        setCampaign(c);
        setTreasury(tr);
        setDonations(Array.isArray(don) ? don : don?.items || don?.donations || []);
        setPayouts(Array.isArray(pay) ? pay : pay?.payouts || []);
      } catch (err) { setError(err.message); }
      finally { setLoading(false); }
    })();
  }, [id]);

  const handlePayout = async () => {
    setRequesting(true); setError(null);
    try {
      await createPayout({
        campaign_id: parseInt(id),
        amount: parseFloat(payoutForm.amount),
        currency: payoutForm.currency,
        payment_method: payoutForm.payment_method,
        notes: payoutForm.notes,
      });
      setShowPayout(false);
      setPayoutForm({ amount: '', currency: 'USD', payment_method: 'bank', notes: '' });
      // Refresh payouts
      const pay = await getCampaignPayouts(id).catch(() => []);
      setPayouts(Array.isArray(pay) ? pay : pay?.payouts || []);
    } catch (err) { setError(err.message); }
    finally { setRequesting(false); }
  };

  if (loading) return <div className="text-center py-20 text-gray-400">Loading…</div>;

  return (
    <div className="max-w-3xl mx-auto px-4 sm:px-6 py-8">
      <div className="flex items-center justify-between mb-6">
        <Link to="/portal/projects" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline">
          <HiOutlineArrowLeft className="w-4 h-4" /> My Projects
        </Link>
      </div>

      <div className="mb-6">
        <h1 className="text-xl font-bold text-gray-900">Campaign Financials</h1>
        <p className="text-sm text-gray-500 mt-0.5">{campaign?.title}</p>
      </div>

      {error && <div className="bg-red-50 border border-red-200 rounded-lg p-3 mb-4 text-sm text-red-600">{error}</div>}

      {/* Treasury summary */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <Stat accent="#6366F1" label="Total Raised" value={`$${fmt(campaign?.current_usd_total || campaign?.raised_amount_usd)}`} />
        <Stat accent="#059669" label="Goal" value={`$${fmt(campaign?.goal_amount_usd)}`} />
        <Stat accent="#A855F7" label="Released" value={`$${fmt(treasury?.total_released_usd)}`} />
        <Stat accent="#D97706" label="In Escrow" value={`$${fmt(treasury?.escrow_balance_usd || ((campaign?.current_usd_total || 0) - (treasury?.total_released_usd || 0)))}`} />
      </div>

      {/* Donations */}
      <div className="mb-8">
        <h2 className="text-lg font-semibold text-gray-900 mb-4 flex items-center gap-2">
          <HiOutlineDocumentText className="w-5 h-5 text-indigo-500" /> Donations ({donations.length})
        </h2>
        {donations.length === 0 ? (
          <p className="text-center py-8 text-gray-400 text-sm">No donations yet</p>
        ) : (
          <div className="space-y-2">
            {donations.map((d) => (
              <div key={d.id} className="relative rounded-xl bg-white/80 backdrop-blur-sm border border-gray-100 p-3 flex items-center justify-between overflow-hidden hover:shadow-sm transition">
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-indigo-500/20 via-violet-500/20 to-transparent" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{d.amount} {d.currency}</p>
                  <p className="text-xs text-gray-400">{d.donor_name || `Donor #${d.donor_id || '?'}`} · {d.payment_method} · {d.created_at ? new Date(d.created_at).toLocaleDateString() : ''}</p>
                </div>
                <StatusBadge status={d.status} />
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Payouts */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <h2 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
            <HiOutlineBanknotes className="w-5 h-5 text-emerald-500" /> Payouts ({payouts.length})
          </h2>
          <button onClick={() => setShowPayout(!showPayout)}
            className="text-sm text-indigo-600 hover:underline font-medium">
            {showPayout ? 'Cancel' : '+ Request Payout'}
          </button>
        </div>

        {showPayout && (
          <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-5 mb-4 overflow-hidden">
            <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-indigo-500 to-transparent" />
            <div className="grid grid-cols-2 gap-4 mb-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Amount</label>
                <input type="number" min={1} value={payoutForm.amount}
                  onChange={(e) => setPayoutForm((p) => ({ ...p, amount: e.target.value }))}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none" />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Currency</label>
                <select value={payoutForm.currency}
                  onChange={(e) => setPayoutForm((p) => ({ ...p, currency: e.target.value }))}
                  className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none">
                  <option value="USD">USD</option>
                  <option value="KES">KES</option>
                  <option value="ZAR">ZAR</option>
                  <option value="ETH">ETH</option>
                </select>
              </div>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Payment Method</label>
              <select value={payoutForm.payment_method}
                onChange={(e) => setPayoutForm((p) => ({ ...p, payment_method: e.target.value }))}
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none">
                <option value="bank">Bank Transfer</option>
                <option value="mpesa">M-Pesa</option>
                <option value="crypto">Crypto</option>
              </select>
            </div>
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">Notes</label>
              <textarea rows={2} value={payoutForm.notes}
                onChange={(e) => setPayoutForm((p) => ({ ...p, notes: e.target.value }))}
                placeholder="Purpose of this payout…"
                className="w-full px-3 py-2.5 rounded-xl border border-gray-200 text-sm resize-none focus:ring-2 focus:ring-indigo-200 focus:border-indigo-400 outline-none" />
            </div>
            <button onClick={handlePayout} disabled={requesting || !payoutForm.amount}
              className="w-full py-3 rounded-xl bg-gradient-to-r from-emerald-600 to-green-600 text-white font-semibold text-sm hover:from-emerald-700 hover:to-green-700 transition disabled:opacity-50">
              {requesting ? 'Submitting…' : 'Request Payout'}
            </button>
          </div>
        )}

        {payouts.length === 0 ? (
          <p className="text-center py-8 text-gray-400 text-sm">No payouts yet</p>
        ) : (
          <div className="space-y-2">
            {payouts.map((p) => (
              <div key={p.id} className="relative rounded-xl bg-white/80 backdrop-blur-sm border border-gray-100 p-3 flex items-center justify-between overflow-hidden hover:shadow-sm transition">
                <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/20 via-violet-500/20 to-transparent" />
                <div>
                  <p className="text-sm font-medium text-gray-900">{p.amount} {p.currency}</p>
                  <p className="text-xs text-gray-400">{p.payment_method} · {p.created_at ? new Date(p.created_at).toLocaleDateString() : ''}</p>
                  {p.notes && <p className="text-xs text-gray-500 mt-0.5">{p.notes}</p>}
                </div>
                <StatusBadge status={p.status} />
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

function Stat({ accent, label, value }) {
  return (
    <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 text-center overflow-hidden transition-all hover:shadow-md hover:border-transparent">
      <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(to right, ${accent}, ${accent}80)` }} />
      <svg className="absolute -top-2 -right-2 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
        <circle cx="45" cy="20" r="14" stroke={accent} strokeWidth="0.5" opacity="0.06" />
      </svg>
      <p className="text-xs text-gray-400">{label}</p>
      <p className="text-lg font-bold text-gray-900 mt-0.5">{value}</p>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-green-50 text-green-600',
    approved: 'bg-green-50 text-green-600',
    pending: 'bg-yellow-50 text-yellow-600',
    processing: 'bg-indigo-50 text-indigo-600',
    failed: 'bg-red-50 text-red-600',
    rejected: 'bg-red-50 text-red-600',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || 'bg-gray-50 text-gray-600'}`}>
      {status}
    </span>
  );
}
