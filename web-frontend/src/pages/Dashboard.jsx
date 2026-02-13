import { useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next';
import { Navigate, Link } from 'react-router-dom';
import useAuthStore from '../stores/authStore';
import { getDonorDonations, getReceipt, verifyReceipt, getTaxSummary } from '../api/donations';
import { HiOutlineXMark, HiOutlineCheckCircle, HiOutlineXCircle } from 'react-icons/hi2';

export default function Dashboard() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const [donations, setDonations] = useState([]);
  const [taxSummary, setTaxSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeReceipt, setActiveReceipt] = useState(null);
  const [receiptLoading, setReceiptLoading] = useState(false);
  const currentYear = new Date().getFullYear();

  useEffect(() => {
    if (!user?.donor_id) { setLoading(false); return; }
    Promise.all([
      getDonorDonations(user.donor_id).catch(() => []),
      getTaxSummary(currentYear, user.donor_id).catch(() => null),
    ]).then(([d, tax]) => {
      setDonations(Array.isArray(d) ? d : d?.items || d?.donations || []);
      setTaxSummary(tax);
    }).finally(() => setLoading(false));
  }, [user, currentYear]);

  if (!user) return <Navigate to="/login" replace />;

  const totalsByFx = donations
    .filter((d) => d.status === 'completed')
    .reduce((acc, d) => {
      acc[d.currency] = (acc[d.currency] || 0) + d.amount;
      return acc;
    }, {});

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
    <div className="max-w-3xl mx-auto px-4 py-6">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">{t('dashboard.title')}</h1>

      {/* Stats cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-5 text-center">
          <p className="text-sm text-gray-400 mb-1">{t('dashboard.total_donated')}</p>
          <p className="text-xl sm:text-2xl font-bold text-indigo-600">
            {Object.entries(totalsByFx).map(([cur, amt]) => (
              <span key={cur} className="block">
                {Number(amt).toLocaleString('en-US', { maximumFractionDigits: 2 })} {cur}
              </span>
            ))}
            {Object.keys(totalsByFx).length === 0 && <span>$0</span>}
          </p>
        </div>
        <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-5 text-center">
          <p className="text-sm text-gray-400 mb-1">{t('dashboard.donations_count')}</p>
          <p className="text-xl sm:text-2xl font-bold text-gray-900">{donations.length}</p>
        </div>
        {taxSummary && (
          <>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-5 text-center">
              <p className="text-sm text-gray-400 mb-1">{t('dashboard.tax_year')} {currentYear}</p>
              <p className="text-xl sm:text-2xl font-bold text-emerald-600">
                ${Number(taxSummary.total_deductible || taxSummary.total_amount || 0).toLocaleString()}
              </p>
            </div>
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-4 sm:p-5 text-center">
              <p className="text-sm text-gray-400 mb-1">{t('dashboard.receipts_count')}</p>
              <p className="text-xl sm:text-2xl font-bold text-gray-900">{taxSummary.receipt_count || taxSummary.donation_count || 0}</p>
            </div>
          </>
        )}
      </div>

      {/* Receipt modal */}
      {activeReceipt && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-md p-6 mb-6">
          <div className="flex justify-between items-start mb-4">
            <h2 className="font-semibold text-gray-900">{t('dashboard.receipt_details')}</h2>
            <button onClick={() => setActiveReceipt(null)} className="text-gray-400 hover:text-gray-600 p-1 rounded-lg hover:bg-gray-100 transition">
              <HiOutlineXMark className="w-5 h-5" />
            </button>
          </div>
          {activeReceipt.error ? (
            <p className="text-red-500 text-sm">{t('dashboard.receipt_unavailable')}</p>
          ) : (
            <div className="space-y-3 text-sm">
              {activeReceipt.donation_id && <ReceiptRow label="Donation ID" value={`#${activeReceipt.donation_id}`} />}
              {activeReceipt.amount && <ReceiptRow label="Amount" value={`${activeReceipt.amount} ${activeReceipt.currency || 'USD'}`} />}
              {activeReceipt.campaign_title && <ReceiptRow label="Campaign" value={activeReceipt.campaign_title} />}
              {activeReceipt.ngo_name && <ReceiptRow label="Organization" value={activeReceipt.ngo_name} />}
              {activeReceipt.receipt_date && <ReceiptRow label="Date" value={new Date(activeReceipt.receipt_date).toLocaleDateString()} />}
              {activeReceipt.nft_token_id && (
                <ReceiptRow label="NFT Token" value={`#${activeReceipt.nft_token_id}`} />
              )}
              {activeReceipt.blockchain_tx && (
                <ReceiptRow label="Blockchain TX" value={
                  <a href={activeReceipt.blockchain_tx} target="_blank" rel="noreferrer" className="text-indigo-600 hover:underline font-mono text-xs">
                    {activeReceipt.blockchain_tx.slice(0, 20)}…
                  </a>
                } />
              )}
              {activeReceipt.verification && (
                <div className={`mt-3 p-3 rounded-lg flex items-center gap-2 ${activeReceipt.verification.is_valid ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
                  {activeReceipt.verification.is_valid
                    ? <HiOutlineCheckCircle className="w-5 h-5 flex-shrink-0" />
                    : <HiOutlineXCircle className="w-5 h-5 flex-shrink-0" />
                  }
                  <p className="font-medium text-sm">
                    {activeReceipt.verification.is_valid ? 'Receipt Verified' : 'Verification Failed'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Donations list */}
      {loading ? (
        <p className="text-center text-gray-400">{t('common.loading')}</p>
      ) : donations.length === 0 ? (
        <div className="text-center py-10">
          <p className="text-gray-400 mb-4">{t('dashboard.no_donations')}</p>
          <Link to="/campaigns" className="text-indigo-600 hover:underline text-sm font-medium">
            {t('landing.explore_btn')} →
          </Link>
        </div>
      ) : (
        <div className="space-y-3">
          {donations.map((d) => (
            <div key={d.id} className="bg-white rounded-xl border border-gray-100 p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
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
                <button
                  onClick={() => viewReceipt(d.id)}
                  disabled={receiptLoading}
                  className="text-xs text-indigo-600 hover:underline py-1 px-2"
                >
                  {t('dashboard.receipt')}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function ReceiptRow({ label, value }) {
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
    processing: 'bg-blue-50 text-blue-600',
    failed: 'bg-red-50 text-red-600',
    refunded: 'bg-gray-50 text-gray-600',
  };
  return (
    <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
}
