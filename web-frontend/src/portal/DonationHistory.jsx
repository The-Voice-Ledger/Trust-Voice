/**
 * DonationHistory — Portal page for viewing complete donation history.
 *
 * Shows all donations with filtering, sorting, receipt access,
 * and detailed transaction information for donors.
 */
import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { getDonorDonations, getReceipt, verifyReceipt, getTaxSummary, getDonorByTelegram } from '../api/donations';
import useAuthStore from '../stores/authStore';
import {
  HiOutlineCheckCircle, HiOutlineXCircle, HiOutlineXMark,
  HiOutlineBanknotes, HiOutlineDocumentText, HiOutlineWallet,
  HiOutlineSparkles, HiOutlineClock, HiOutlineMagnifyingGlass,
  IconChevronDown, IconArrowTrendingUp, IconArrowTrendingDown,
  IconArrowLeft, IconArrowRight,
} from '../components/icons';

export default function DonationHistory() {
  const user = useAuthStore((s) => s.user);
  const [donations, setDonations] = useState([]);
  const [filteredDonations, setFilteredDonations] = useState([]);
  const [taxSummary, setTaxSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [donorId, setDonorId] = useState(null);
  const [activeReceipt, setActiveReceipt] = useState(null);
  const [receiptLoading, setReceiptLoading] = useState(false);
  const [searchTerm, setSearchTerm] = useState('');
  const [statusFilter, setStatusFilter] = useState('all');
  const [sortField, setSortField] = useState('created_at');
  const [sortDirection, setSortDirection] = useState('desc');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(5);
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
    if (!donorId) { 
      setLoading(false); 
      return; 
    }
    
    Promise.all([
      getDonorDonations(donorId).catch(() => []),
      getTaxSummary(currentYear, donorId).catch(() => null),
    ]).then(([d, tax]) => {
      setDonations(Array.isArray(d) ? d : d?.items || d?.donations || []);
      setTaxSummary(tax);
    }).finally(() => setLoading(false));
  }, [donorId, currentYear]);

  // Filter and sort donations
  useEffect(() => {
    setCurrentPage(1); // Reset to first page when filters change
    let filtered = donations;

    // Apply status filter
    if (statusFilter !== 'all') {
      filtered = filtered.filter(d => d.status === statusFilter);
    }

    // Apply search filter
    if (searchTerm) {
      filtered = filtered.filter(d => 
        d.campaign_title?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.ngo_name?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.payment_method?.toLowerCase().includes(searchTerm.toLowerCase()) ||
        d.id.toString().includes(searchTerm)
      );
    }

    // Apply sorting
    filtered.sort((a, b) => {
      let aValue = a[sortField];
      let bValue = b[sortField];

      if (sortField === 'amount') {
        aValue = parseFloat(aValue) || 0;
        bValue = parseFloat(bValue) || 0;
      } else if (sortField === 'created_at') {
        aValue = new Date(aValue);
        bValue = new Date(bValue);
      }

      if (sortDirection === 'asc') {
        return aValue > bValue ? 1 : -1;
      } else {
        return aValue < bValue ? 1 : -1;
      }
    });

    setFilteredDonations(filtered);
  }, [donations, searchTerm, statusFilter, sortField, sortDirection]);

  // Reset page when itemsPerPage changes
  useEffect(() => {
    setCurrentPage(1);
  }, [itemsPerPage]);

  const totalsByFx = donations
    .filter((d) => d.status === 'completed')
    .reduce((acc, d) => { 
      acc[d.currency] = (acc[d.currency] || 0) + d.amount; 
      return acc; 
    }, {});

  // Pagination logic
  const totalPages = Math.ceil(filteredDonations.length / itemsPerPage);
  const startIndex = (currentPage - 1) * itemsPerPage;
  const endIndex = startIndex + itemsPerPage;
  const paginatedDonations = filteredDonations.slice(startIndex, endIndex);

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

  const toggleSort = (field) => {
    if (sortField === field) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('desc');
    }
  };

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-8">
        <div className="text-center py-20">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-emerald-600 mx-auto mb-4"></div>
          <p className="text-gray-400">Loading donation history...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-4xl mx-auto px-4 sm:px-6 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-xl sm:text-2xl font-bold text-gray-900 mb-1">Donation History</h1>
        <p className="text-sm text-gray-500">Complete record of all your contributions</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden group transition-all hover:shadow-md hover:border-transparent">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500 to-transparent" />
          <HiOutlineWallet className="w-5 h-5 mx-auto mb-1.5 text-emerald-600" />
          <p className="text-sm text-gray-400 mb-1">Total Donated</p>
          <div className="relative">
            {Object.entries(totalsByFx).map(([cur, amt]) => (
              <span key={cur} className="block text-lg sm:text-xl font-bold text-emerald-600">
                {Number(amt).toLocaleString('en-US', { maximumFractionDigits: 2 })} {cur}
              </span>
            ))}
            {Object.keys(totalsByFx).length === 0 && <span className="text-lg sm:text-xl font-bold text-emerald-600">$0</span>}
          </div>
        </div>

        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden group transition-all hover:shadow-md hover:border-transparent">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-blue-500 to-transparent" />
          <HiOutlineBanknotes className="w-5 h-5 mx-auto mb-1.5 text-blue-600" />
          <p className="text-sm text-gray-400 mb-1">Total Donations</p>
          <span className="text-lg sm:text-xl font-bold text-gray-900">{donations.length}</span>
        </div>

        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden group transition-all hover:shadow-md hover:border-transparent">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-green-500 to-transparent" />
          <HiOutlineCheckCircle className="w-5 h-5 mx-auto mb-1.5 text-green-600" />
          <p className="text-sm text-gray-400 mb-1">Completed</p>
          <span className="text-lg sm:text-xl font-bold text-green-600">
            {donations.filter(d => d.status === 'completed').length}
          </span>
        </div>

        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 text-center overflow-hidden group transition-all hover:shadow-md hover:border-transparent">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-purple-500 to-transparent" />
          <HiOutlineDocumentText className="w-5 h-5 mx-auto mb-1.5 text-purple-600" />
          <p className="text-sm text-gray-400 mb-1">Tax Year {currentYear}</p>
          <span className="text-lg sm:text-xl font-bold text-purple-600">
            ${Number(taxSummary?.total_deductible || taxSummary?.total_amount || 0).toLocaleString()}
          </span>
        </div>
      </div>

      {/* Filters */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6">
        <div className="flex flex-col sm:flex-row gap-4">
          {/* Search */}
          <div className="flex-1">
            <div className="relative">
              <HiOutlineMagnifyingGlass className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-400 w-4 h-4" />
              <input
                type="text"
                placeholder="Search donations..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div className="flex items-center gap-2">
            <IconChevronDown className="text-gray-400 w-4 h-4" />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
            >
              <option value="all">All Status</option>
              <option value="completed">Completed</option>
              <option value="pending">Pending</option>
              <option value="failed">Failed</option>
              <option value="processing">Processing</option>
            </select>
          </div>
        </div>
      </div>

      {/* Receipt Modal */}
      {activeReceipt && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 shadow-md p-6 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-green-500 via-emerald-500 to-transparent" />
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
                    ? <HiOutlineCheckCircle className="w-5 h-5 shrink-0" />
                    : <HiOutlineXCircle className="w-5 h-5 shrink-0" />}
                  <p className="font-medium text-sm">
                    {activeReceipt.verification.is_valid ? 'Receipt Verified' : 'Verification Failed'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Donations List */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-transparent" />
        
        {paginatedDonations.length === 0 ? (
          <div className="text-center py-16">
            <HiOutlineBanknotes className="w-12 h-12 text-gray-300 mx-auto mb-3" />
            <p className="text-gray-400 mb-4">
              {filteredDonations.length === 0 ? 'You haven\'t made any donations yet.' : 'No donations match your filters.'}
            </p>
            {filteredDonations.length === 0 && (
              <Link to="/campaigns" className="text-emerald-600 font-semibold hover:underline text-sm">Explore campaigns →</Link>
            )}
          </div>
        ) : (
          <div className="p-4 sm:p-0">
            {/* Mobile Card View */}
            <div className="sm:hidden space-y-3">
              {paginatedDonations.map((donation) => (
                <div key={donation.id} className="group relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2 overflow-hidden transition-all hover:shadow-md hover:border-transparent">
                  <div className="absolute top-0 left-0 right-0 h-0.5 bg-gradient-to-r from-emerald-500/20 via-green-500/20 to-transparent" />
                  
                  <div>
                    <p className="font-medium text-gray-900">
                      {Number(donation.amount).toLocaleString('en-US', { maximumFractionDigits: 2 })} {donation.currency}
                      <span className="ml-2 text-xs text-gray-400">via {donation.payment_method}</span>
                    </p>
                    <p className="text-xs text-gray-400">
                      {donation.campaign_title || 'Campaign #' + donation.campaign_id} · {new Date(donation.created_at).toLocaleDateString()}
                    </p>
                    {donation.ngo_name && (
                      <p className="text-xs text-gray-400">{donation.ngo_name}</p>
                    )}
                  </div>
                  
                  <div className="flex items-center gap-2">
                    <StatusBadge status={donation.status} />
                    {donation.status === 'completed' && (
                      <button 
                        onClick={() => viewReceipt(donation.id)} 
                        disabled={receiptLoading}
                        className="text-xs text-emerald-600 hover:underline py-1 px-2"
                      >
                        Receipt
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>

            {/* Desktop Table View */}
            <div className="hidden sm:block overflow-x-auto">
              <table className="w-full min-w-[600px]">
                <thead className="bg-gray-50/50 border-b border-gray-100">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button 
                        onClick={() => toggleSort('created_at')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Date
                        {sortField === 'created_at' && (
                          sortDirection === 'asc' ? <IconArrowTrendingUp className="w-3 h-3" /> : <IconArrowTrendingDown className="w-3 h-3" />
                        )}
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      <button 
                        onClick={() => toggleSort('amount')}
                        className="flex items-center gap-1 hover:text-gray-700"
                      >
                        Amount
                        {sortField === 'amount' && (
                          sortDirection === 'asc' ? <IconArrowTrendingUp className="w-3 h-3" /> : <IconArrowTrendingDown className="w-3 h-3" />
                        )}
                      </button>
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Campaign</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Method</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-gray-100">
                  {paginatedDonations.map((donation) => (
                    <tr key={donation.id} className="hover:bg-gray-50/50 transition-colors">
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        <div className="flex items-center gap-2">
                          <HiOutlineClock className="w-4 h-4 text-gray-400" />
                          {new Date(donation.created_at).toLocaleDateString()}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="font-medium text-gray-900">
                          {Number(donation.amount).toLocaleString('en-US', { maximumFractionDigits: 2 })} {donation.currency}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-sm text-gray-900">
                        <div>
                          <div className="font-medium">{donation.campaign_title || 'Campaign #' + donation.campaign_id}</div>
                          <div className="text-xs text-gray-400">{donation.ngo_name || 'Individual Campaign'}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <span className="capitalize">{donation.payment_method}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <StatusBadge status={donation.status} />
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="flex items-center gap-2">
                          {donation.status === 'completed' && (
                            <button 
                              onClick={() => viewReceipt(donation.id)} 
                              disabled={receiptLoading}
                              className="text-xs text-emerald-600 hover:underline py-1 px-2">
                              Receipt
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </div>

      {/* Pagination */}
      {filteredDonations.length > 0 && (
        <div className="mt-6 flex flex-col lg:flex-row items-center justify-between gap-4">
          <div className="flex flex-col sm:flex-row items-center gap-4">
            <div className="flex items-center gap-2">
              <label className="text-sm text-gray-600">Show:</label>
              <select
                value={itemsPerPage}
                onChange={(e) => {
                  const newSize = parseInt(e.target.value);
                  const newCurrentPage = Math.min(currentPage, Math.ceil(filteredDonations.length / newSize));
                  setItemsPerPage(newSize);
                  setCurrentPage(newCurrentPage);
                }}
                className="px-3 py-2 border border-gray-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-emerald-500"
              >
                <option value={5}>5</option>
                <option value={10}>10</option>
                <option value={25}>25</option>
                <option value={50}>50</option>
              </select>
              <span className="text-sm text-gray-600">per page</span>
            </div>
          </div>
          
          <div className="flex items-center gap-2">
            <button
              onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
              disabled={currentPage === 1}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <IconArrowLeft className="w-4 h-4" />
              <span className="hidden sm:inline">Previous</span>
            </button>
            
            <div className="flex items-center gap-1">
              {/* Responsive page numbers */}
              {(() => {
                const pages = [];
                const maxVisible = 5; // Maximum visible page numbers
                
                if (totalPages <= maxVisible) {
                  // Show all pages if total is less than or equal to maxVisible
                  for (let i = 1; i <= totalPages; i++) {
                    pages.push(i);
                  }
                } else {
                  // Show first page, current page, and last page with ellipsis
                  pages.push(1);
                  
                  if (currentPage > 3) {
                    pages.push('...');
                  }
                  
                  // Show pages around current page
                  const start = Math.max(2, currentPage - 1);
                  const end = Math.min(totalPages - 1, currentPage + 1);
                  
                  for (let i = start; i <= end; i++) {
                    if (i !== 1 && i !== totalPages) {
                      pages.push(i);
                    }
                  }
                  
                  if (currentPage < totalPages - 2) {
                    pages.push('...');
                  }
                  
                  if (totalPages > 1) {
                    pages.push(totalPages);
                  }
                }
                
                return pages.map((page, index) => 
                  page === '...' ? (
                    <span key={`ellipsis-${index}`} className="px-2 py-2 text-sm text-gray-400">...</span>
                  ) : (
                    <button
                      key={page}
                      onClick={() => setCurrentPage(page)}
                      className={`px-3 py-2 text-sm rounded-lg transition-colors ${
                        currentPage === page
                          ? 'bg-emerald-600 text-white hover:bg-emerald-700'
                          : 'border border-gray-300 hover:bg-gray-50'
                      }`}
                    >
                      {page}
                    </button>
                  )
                );
              })()}
            </div>
            
            <button
              onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
              disabled={currentPage === totalPages}
              className="flex items-center gap-1 px-3 py-2 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              <span className="hidden sm:inline">Next</span>
              <IconArrowRight className="w-4 h-4" />
            </button>
          </div>
        </div>
      )}

      {/* Summary */}
      <div className="mt-6 text-center text-sm text-gray-400">
        {filteredDonations.length} donation{filteredDonations.length !== 1 ? 's' : ''}
      </div>
    </div>
  );
}

/* ── Shared sub-components ──────────────── */

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
    <span className={`text-xs px-2 py-1 rounded-full font-medium ${colors[status] || colors.pending}`}>
      {status}
    </span>
  );
}
