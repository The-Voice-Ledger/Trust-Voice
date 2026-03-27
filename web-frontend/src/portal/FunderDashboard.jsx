/**
 * FunderDashboard — portal landing for DONOR / VIEWER roles.
 *
 * Shows donation stats, funded campaign progress, recent activity,
 * and quick links to receipts.  Adapted from the existing Dashboard page
 * but designed for the sidebar-based portal layout (no PageBg wrapper).
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDonorDonations, getReceipt, verifyReceipt, getTaxSummary, getDonorByTelegram } from '../api/donations';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineCheckCircle, HiOutlineXCircle, HiOutlineXMark,
  HiOutlineBanknotes, HiOutlineDocumentText, HiOutlineWallet,
  HiOutlineSparkles,
} from '../components/icons';

export default function FunderDashboard() {
  const user = useAuthStore((s) => s.user);
  const [donations, setDonations] = useState([]);
  const [taxSummary, setTaxSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [donorId, setDonorId] = useState(null);
  const [activeReceipt, setActiveReceipt] = useState(null);
  const [receiptLoading, setReceiptLoading] = useState(false);
  const currentYear = new Date().getFullYear();

  // Detect donor ID from user's telegram ID
  useEffect(() => {
    const detectDonorId = async () => {
      if (!user?.telegram_user_id) {
        setLoading(false);
        return;
      }
      
      try {
        const donor = await getDonorByTelegram(user.telegram_user_id);
        setDonorId(donor.id);
      } catch (err) {
        console.error('Could not detect donor from logged-in user:', err);
        setLoading(false);
      }
    };
    
    detectDonorId();
  }, [user]);

  useEffect(() => {
    if (!donorId) { setLoading(false); return; }
    Promise.all([
      getDonorDonations(donorId).catch(() => []),
      getTaxSummary(currentYear, donorId).catch(() => null),
    ]).then(([d, tax]) => {
      setDonations(Array.isArray(d) ? d : d?.items || d?.donations || []);
      setTaxSummary(tax);
    }).finally(() => setLoading(false));
  }, [donorId, currentYear]);

  const totalsByFx = donations
    .filter((d) => d.status === 'completed')
    .reduce((acc, d) => { acc[d.currency] = (acc[d.currency] || 0) + d.amount; return acc; }, {});

  const viewReceipt = async (donationId) => {
    setReceiptLoading(true);
    try {
      const receipt = await getReceipt(donationId);
      const verification = await verifyReceipt(donationId).catch(() => null);
      setActiveReceipt({ ...receipt, verification });
    } catch {
      setActiveReceipt({ error: true });
    } finally {
      setReceiptLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900 mb-1">Welcome back, {user?.full_name || 'Funder'}</h1>
        <p className="text-sm text-gray-500">Your funding impact at a glance</p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <StatCard accent="#10B981" icon={HiOutlineWallet} label="Total Donated">
          {Object.entries(totalsByFx).map(([cur, amt]) => (
            <span key={cur} className="block text-xl font-bold" style={{ color: '#10B981' }}>
              {Number(amt).toLocaleString('en-US', { maximumFractionDigits: 2 })} {cur}
            </span>
          ))}
          {Object.keys(totalsByFx).length === 0 && <span className="text-xl font-bold text-emerald-600">$0</span>}
        </StatCard>
        <StatCard accent="#059669" icon={HiOutlineBanknotes} label="Donations">
          <span className="text-xl font-bold text-gray-900">{donations.length}</span>
        </StatCard>
        {taxSummary && (
          <>
            <StatCard accent="#14B8A6" icon={HiOutlineSparkles} label={`Tax Year ${currentYear}`}>
              <span className="text-xl font-bold text-emerald-600">
                ${Number(taxSummary.total_deductible || taxSummary.total_amount || 0).toLocaleString()}
              </span>
            </StatCard>
            <StatCard accent="#0D9488" icon={HiOutlineDocumentText} label="Receipts">
              <span className="text-xl font-bold text-gray-900">{taxSummary.receipt_count || taxSummary.donation_count || 0}</span>
            </StatCard>
          </>
        )}
      </div>

      {/* Receipt modal */}
      {activeReceipt && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 shadow-md p-6 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-emerald-500 to-transparent" />
          <svg className="absolute top-2 right-12 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
            <rect x="46" y="10" width="22" height="28" rx="3" stroke="#14B8A6" strokeWidth="0.5" opacity="0.05" />
            <path d="M52 20 L62 20" stroke="#14B8A6" strokeWidth="0.4" opacity="0.04" />
            <path d="M52 26 L58 26" stroke="#14B8A6" strokeWidth="0.4" opacity="0.03" />
          </svg>
          <div className="flex justify-between items-start mb-4">
            <h2 className="font-semibold text-gray-900">Receipt Details</h2>
            <button onClick={() => setActiveReceipt(null)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition">
              <HiOutlineXMark className="w-5 h-5" />
            </button>
          </div>
          {activeReceipt.error ? (
            <p className="text-red-500 text-sm">Receipt unavailable</p>
          ) : (
            <div className="space-y-3 text-sm">
              {activeReceipt.donation_id && <Row label="Donation ID" value={`#${activeReceipt.donation_id}`} />}
              {activeReceipt.amount && <Row label="Amount" value={`${activeReceipt.amount} ${activeReceipt.currency || 'USD'}`} />}
              {activeReceipt.campaign_title && <Row label="Campaign" value={activeReceipt.campaign_title} />}
              {activeReceipt.ngo_name && <Row label="Organization" value={activeReceipt.ngo_name} />}
              {activeReceipt.receipt_date && <Row label="Date" value={new Date(activeReceipt.receipt_date).toLocaleDateString()} />}
              {activeReceipt.nft_token_id && <Row label="NFT Token" value={`#${activeReceipt.nft_token_id}`} />}
              {activeReceipt.blockchain_tx && (
                <Row label="Blockchain TX" value={
                  <a href={activeReceipt.blockchain_tx} target="_blank" rel="noreferrer" className="text-emerald-600 hover:underline font-mono text-xs">
                    {activeReceipt.blockchain_tx.slice(0, 20)}…
                  </a>
                } />
              )}
              {activeReceipt.verification && (
                <div className={`mt-3 p-3 rounded-lg flex items-center gap-2 ${activeReceipt.verification.is_valid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                  {activeReceipt.verification.is_valid
                    ? <HiOutlineCheckCircle className="w-5 h-5 flex-shrink-0" />
                    : <HiOutlineXCircle className="w-5 h-5 flex-shrink-0" />}
                  <p className="font-medium text-sm">
                    {activeReceipt.verification.is_valid ? 'Receipt Verified' : 'Verification Failed'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Recent donations */}
      <div className="mb-4 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Recent Funding</h2>
        <Link to="/portal/donations" className="text-sm text-emerald-600 hover:underline">View all →</Link>
      </div>

      {loading ? (
        <p className="text-center py-10 text-gray-400">Loading…</p>
      ) : donations.length === 0 ? (
        <div className="text-center py-16">
          <HiOutlineBanknotes className="w-12 h-12 text-gray-300 mx-auto mb-3" />
          <p className="text-gray-400 mb-4">You haven't made any donations yet.</p>
          <Link to="/campaigns" className="text-emerald-600 font-semibold hover:underline text-sm">Explore campaigns →</Link>
        </div>
      ) : (
        <div className="space-y-3">
          {donations.slice(0, 5).map((d) => (
            <div key={d.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-transparent" />
              <svg className="absolute bottom-0 right-0 w-12 h-12 pointer-events-none" viewBox="0 0 50 50" fill="none">
                <path d="M50 0v50H0" stroke="#10B981" strokeWidth="0.5" opacity="0.06" />
                <circle cx="50" cy="50" r="1.5" fill="#10B981" opacity="0.08" />
              </svg>
              <div>
                <p className="font-medium text-gray-900">
                  {d.amount} {d.currency}
                  <span className="ml-2 text-xs text-gray-400">via {d.payment_method}</span>
                </p>
                <p className="text-xs text-gray-400">
                  Campaign #{d.campaign_id} · {new Date(d.created_at).toLocaleDateString()}
                </p>
              </div>
              <div className="flex items-center gap-2">
                <StatusBadge status={d.status} />
                <button onClick={() => viewReceipt(d.id)} disabled={receiptLoading}
                  className="text-xs text-emerald-600 hover:underline py-1 px-2">
                  Receipt
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

/* ── Shared sub-components ──────────────── */

function StatCard({ accent, icon: Icon, label, children }) {
  return (
    <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden group transition-all hover:shadow-md hover:border-transparent">
      <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(to right, ${accent}, ${accent}80)` }} />
      <svg className="absolute -top-2 -right-2 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
        <circle cx="55" cy="25" r="20" stroke={accent} strokeWidth="0.5" opacity="0.08" />
        <circle cx="55" cy="25" r="10" stroke={accent} strokeWidth="0.3" strokeDasharray="2 3" opacity="0.05" />
        <circle cx="55" cy="5" r="1.5" fill={accent} opacity="0.10" />
      </svg>
      <svg className="absolute bottom-0 left-0 w-12 h-12 pointer-events-none" viewBox="0 0 50 50" fill="none">
        <path d="M0 50V20" stroke={accent} strokeWidth="0.5" opacity="0.06" />
        <path d="M0 50H30" stroke={accent} strokeWidth="0.5" opacity="0.06" />
        <circle cx="0" cy="50" r="1.5" fill={accent} opacity="0.08" />
      </svg>
      {Icon && <Icon className="w-5 h-5 mx-auto mb-1.5" style={{ color: accent }} />}
      <p className="relative text-sm text-gray-400 mb-1">{label}</p>
      <div className="relative">{children}</div>
    </div>
  );
}

function Row({ label, value }) {
  return (
    <div className="flex flex-col sm:flex-row sm:justify-between py-1.5 border-b border-gray-50 last:border-0 gap-0.5">
      <span className="text-gray-500">{label}</span>
      <span className="font-medium text-gray-900 sm:text-right">{value}</span>
    </div>
  );
}

function StatusBadge({ status }) {
  const colors = {
    completed: 'bg-green-50 text-green-600',
    pending: 'bg-yellow-50 text-yellow-600',
    processing: 'bg-emerald-50 text-emerald-600',
    failed: 'bg-red-50 text-red-600',
    refunded: 'bg-gray-50 text-gray-600',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
}
