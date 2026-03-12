import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCampaign, listCampaigns } from '../api/campaigns';
import DonationForm from '../components/DonationForm';
import useAuthStore from '../stores/authStore';
import ProgressBar from '../components/ProgressBar';
import {
  HiOutlineBanknotes, HiOutlineCheckCircle, HiOutlineArrowLeft,
  HiOutlineShieldCheck, HiOutlineLockClosed, HiOutlineFingerPrint,
  MdOutlineWaterDrop, MdOutlineSchool, MdOutlineLocalHospital,
  MdOutlineConstruction, MdOutlineRestaurant, MdOutlineForest,
  MdOutlineHouse, MdOutlineChildCare, MdHandshake,
} from '../components/icons';
import { PageBg } from '../components/SvgDecorations';
import HexIcon from '../components/HexIcon';

export default function DonateCheckout() {
  const { t } = useTranslation();
  const { campaignId } = useParams();
  const user = useAuthStore((s) => s.user);
  const [campaign, setCampaign] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [selectedId, setSelectedId] = useState(campaignId || '');
  const [loading, setLoading] = useState(true);
  const [donated, setDonated] = useState(false);

  // Load campaign if ID provided, else load list for selection
  useEffect(() => {
    if (campaignId) {
      getCampaign(campaignId).then(setCampaign).catch(() => {}).finally(() => setLoading(false));
    } else {
      listCampaigns({ page: 1, pageSize: 50, status: 'active', sort: 'most_funded' })
        .then((d) => setCampaigns(d.items || (Array.isArray(d) ? d : [])))
        .catch(() => {})
        .finally(() => setLoading(false));
    }
  }, [campaignId]);

  // Load campaign when selected from dropdown
  useEffect(() => {
    if (selectedId && !campaignId) {
      getCampaign(selectedId).then(setCampaign).catch(() => {});
    }
  }, [selectedId, campaignId]);

  if (loading) return <div className="text-center py-20 text-gray-400">{t('common.loading')}</div>;

  return (
    <PageBg pattern="topography" colorA="#F43F5E" colorB="#A855F7">
    <div className="max-w-lg mx-auto px-4 py-8">
      <Link to="/campaigns" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mb-6 py-2">
        <HiOutlineArrowLeft className="w-4 h-4" /> {t('common.back')}
      </Link>

      {/* ── Hero Section ──────────────────────── */}
      <div className="relative text-center mb-10">
        {/* Decorative rings behind icon */}
        <HexIcon Icon={HiOutlineBanknotes} accent="#059669" size="lg" bespoke="globe" gradient gradientTo="#10B981" className="mx-auto mb-5" />
        <h1 className="text-2xl sm:text-3xl font-bold text-gray-900 font-display">{t('fund.title')}</h1>
        <p className="text-sm text-gray-500 mt-2 max-w-xs mx-auto">{t('fund.checkout_subtitle')}</p>
        {/* Decorative line */}
        <div className="mt-5 flex items-center gap-3 max-w-[200px] mx-auto">
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-rose-300 to-transparent" />
          <svg width="8" height="8" viewBox="0 0 8 8" fill="none"><path d="M4 0L8 4L4 8L0 4Z" fill="#F43F5E" opacity="0.3" /></svg>
          <div className="flex-1 h-px bg-gradient-to-r from-transparent via-rose-300 to-transparent" />
        </div>
      </div>

      {/* ── Campaign Selector ─────────────────── */}
      {!campaignId && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-5 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-rose-400 via-pink-400 to-transparent" />
          <svg className="absolute -top-2 -right-2 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
            <circle cx="68" cy="28" r="20" stroke="#F43F5E" strokeWidth="0.5" opacity="0.06" />
            <circle cx="68" cy="28" r="10" stroke="#F43F5E" strokeWidth="0.3" strokeDasharray="2 3" opacity="0.04" />
            <path d="M68 8 L68 48" stroke="#F43F5E" strokeWidth="0.2" opacity="0.03" />
            <path d="M48 28 L88 28" stroke="#F43F5E" strokeWidth="0.2" opacity="0.03" />
          </svg>
          <label className="relative block text-sm font-medium text-gray-700 mb-2">{t('fund.select_campaign')}</label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="relative w-full rounded-xl border border-gray-200 px-3 py-3 text-sm focus:ring-2 focus:ring-rose-500 focus:border-transparent bg-white/50"
          >
            <option value="">{t('fund.choose_campaign')}</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>{c.title} · ${fmt(c.goal_amount_usd)} goal</option>
            ))}
          </select>
        </div>
      )}

      {/* ── Campaign Info Card ────────────────── */}
      {campaign && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden mb-6 group">
          {/* Gradient banner with category SVG */}
          <div className="relative h-16 bg-gradient-to-r from-indigo-500/10 via-violet-500/10 to-transparent">
            <CampaignBannerSvg category={campaign.category} />
            <div className="absolute top-0 left-0 w-full h-px bg-gradient-to-r from-indigo-500 via-violet-500 to-transparent" />
          </div>
          <div className="px-5 pb-5 -mt-5">
            <div className="relative flex items-start gap-3">
              <HexIcon Icon={() => <CategoryIcon cat={campaign.category} />} accent="#6366F1" size="sm" bespoke="globe" />
              <div className="flex-1 pt-1">
                <h2 className="font-semibold text-gray-900">{campaign.title}</h2>
                {campaign.ngo_name && <p className="text-xs text-gray-400 mt-0.5">{campaign.ngo_name}</p>}
              </div>
            </div>
            <ProgressBar
              percentage={campaign.goal_amount_usd > 0 ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100) : 0}
              className="mt-4"
            />
            <div className="flex justify-between text-sm mt-2">
              <span className="font-bold text-indigo-600">${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}</span>
              <span className="text-gray-400">{t('campaign.raised_of')} ${fmt(campaign.goal_amount_usd)}</span>
            </div>
          </div>
          {/* Corner node */}
          <svg className="absolute bottom-1 left-1 w-8 h-8 pointer-events-none" viewBox="0 0 32 32" fill="none">
            <path d="M0 32V16" stroke="#6366F1" strokeWidth="0.5" opacity="0.05" />
            <path d="M0 32H16" stroke="#6366F1" strokeWidth="0.5" opacity="0.05" />
            <circle cx="0" cy="32" r="1.5" fill="#6366F1" opacity="0.07" />
          </svg>
        </div>
      )}

      {/* ── Funding Form Card ────────────────── */}
      {campaign ? (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden">
          {/* Top accent */}
          <div className="h-[2px] bg-gradient-to-r from-emerald-500 via-teal-500 to-transparent" />
          {/* Currency SVG decoration */}
          <svg className="absolute top-4 right-4 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
            <circle cx="68" cy="28" r="18" stroke="#059669" strokeWidth="0.5" opacity="0.06" />
            <circle cx="68" cy="28" r="9" stroke="#059669" strokeWidth="0.3" strokeDasharray="2 3" opacity="0.04" />
            <path d="M68 16V40" stroke="#059669" strokeWidth="0.4" opacity="0.05" />
            <path d="M64 20 C72 20, 72 28, 64 28 C72 28, 72 36, 64 36" stroke="#059669" strokeWidth="0.5" opacity="0.06" />
          </svg>
          {/* Connection lines */}
          <svg className="absolute bottom-0 left-0 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
            <path d="M0 64V32" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
            <path d="M0 64H32" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
            <circle cx="0" cy="64" r="1.5" fill="#059669" opacity="0.06" />
            <circle cx="0" cy="32" r="1" fill="#059669" opacity="0.04" />
            <circle cx="32" cy="64" r="1" fill="#059669" opacity="0.04" />
          </svg>

          <div className="relative p-5 sm:p-6">
            {donated ? (
              <DonationSuccess t={t} method={null} />
            ) : (
              <DonationForm
                campaignId={campaign.id}
                donorId={user?.donor_id}
                onSuccess={() => setDonated(true)}
              />
            )}
          </div>
        </div>
      ) : (
        <div className="relative rounded-2xl bg-white/60 backdrop-blur-sm border border-dashed border-gray-200 p-12 text-center overflow-hidden">
          <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 200" fill="none" preserveAspectRatio="none">
            <circle cx="200" cy="100" r="60" stroke="#F43F5E" strokeWidth="0.3" strokeDasharray="4 8" opacity="0.06" />
            <circle cx="200" cy="100" r="90" stroke="#A855F7" strokeWidth="0.2" strokeDasharray="2 10" opacity="0.04" />
          </svg>
          <HiOutlineBanknotes className="w-8 h-8 text-gray-300 mx-auto mb-2" />
          <p className="text-gray-400 text-sm">{t('fund.select_campaign_first')}</p>
        </div>
      )}

      {/* ── Trust Signals ─────────────────────── */}
      <div className="mt-8 grid grid-cols-3 gap-3">
        <TrustBadge Icon={HiOutlineShieldCheck} label={t('fund.trust_secure', 'Secure')} color="#059669" />
        <TrustBadge Icon={HiOutlineLockClosed} label={t('fund.trust_encrypted', 'Encrypted')} color="#6366F1" />
        <TrustBadge Icon={HiOutlineFingerPrint} label={t('fund.trust_verified', 'Verified')} color="#7C3AED" />
      </div>

      {/* ── Transparency pipeline ─────────────── */}
      <div className="mt-6 relative">
        <div className="flex items-center justify-between px-2">
          {['Fund', 'Verify', 'Track', 'Impact'].map((step, i) => {
            const stepIcons = [HiOutlineBanknotes, HiOutlineShieldCheck, HiOutlineFingerPrint, HiOutlineCheckCircle];
            const stepColors = ['#E11D48', '#059669', '#7C3AED', '#6366F1'];
            const stepBesps = ['heart', 'shield', 'fingerprint', 'check'];
            return (
            <div key={step} className="flex flex-col items-center gap-1.5 relative z-10">
              <HexIcon Icon={stepIcons[i]} accent={stepColors[i]} bespoke={stepBesps[i]} size="xs" />
              <span className="text-[10px] text-gray-400 font-medium">{step}</span>
            </div>
            );
          })}
        </div>
        {/* Connection line */}
        <div className="absolute top-4 left-6 right-6 h-px bg-gradient-to-r from-rose-300 via-gray-200 to-gray-200 -z-0" />
      </div>
    </div>
    </PageBg>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

const FUND_CATEGORY_ICONS = {
  water: MdOutlineWaterDrop, education: MdOutlineSchool, health: MdOutlineLocalHospital,
  infrastructure: MdOutlineConstruction, food: MdOutlineRestaurant, environment: MdOutlineForest,
  shelter: MdOutlineHouse, children: MdOutlineChildCare,
};

function CategoryIcon({ cat }) {
  const Comp = FUND_CATEGORY_ICONS[(cat || '').toLowerCase()] || MdHandshake;
  return <Comp className="w-5 h-5 text-indigo-600" />;
}

/* ── Category-specific banner SVGs ─────────── */
const CATEGORY_BANNERS = {
  water: () => (
    <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 64" fill="none" preserveAspectRatio="none">
      <path d="M0 40 Q50 20, 100 35 T200 30 T300 38 T400 25" stroke="#6366F1" strokeWidth="0.8" opacity="0.10" />
      <path d="M0 50 Q60 30, 120 45 T240 35 T360 48 T400 35" stroke="#A855F7" strokeWidth="0.5" opacity="0.08" />
    </svg>
  ),
  education: () => (
    <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 64" fill="none" preserveAspectRatio="none">
      <path d="M340 15 L370 10 L370 35 L340 40 Z" stroke="#6366F1" strokeWidth="0.6" opacity="0.08" />
      <path d="M345 20 L365 16" stroke="#6366F1" strokeWidth="0.4" opacity="0.06" />
      <path d="M345 26 L360 23" stroke="#6366F1" strokeWidth="0.4" opacity="0.06" />
    </svg>
  ),
  health: () => (
    <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 64" fill="none" preserveAspectRatio="none">
      <path d="M355 22 L355 42" stroke="#DC2626" strokeWidth="1" opacity="0.08" />
      <path d="M345 32 L365 32" stroke="#DC2626" strokeWidth="1" opacity="0.08" />
      <circle cx="355" cy="32" r="14" stroke="#DC2626" strokeWidth="0.4" opacity="0.06" />
    </svg>
  ),
};

function CampaignBannerSvg({ category }) {
  const Banner = CATEGORY_BANNERS[(category || '').toLowerCase()];
  if (!Banner) return (
    <svg className="absolute inset-0 w-full h-full" viewBox="0 0 400 64" fill="none" preserveAspectRatio="none">
      <circle cx="360" cy="32" r="18" stroke="#6366F1" strokeWidth="0.5" opacity="0.06" />
      <circle cx="360" cy="32" r="8" stroke="#A855F7" strokeWidth="0.3" strokeDasharray="2 3" opacity="0.05" />
    </svg>
  );
  return <Banner />;
}

/* ── Trust Badge ───────────────────────────── */
function TrustBadge({ Icon, label, color }) {
  return (
    <div className="relative rounded-xl bg-white/60 backdrop-blur-sm border border-gray-100 p-3 text-center overflow-hidden group hover:shadow-sm transition-all">
      <HexIcon Icon={Icon} accent={color} size="xs" className="mx-auto mb-1.5" />
      <span className="text-[10px] font-medium text-gray-500">{label}</span>
    </div>
  );
}

/* ── Funding Success ──────────────────────── */
function DonationSuccess({ t }) {
  return (
    <div className="text-center py-8 relative">
      {/* Celebration SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 300 200" fill="none">
        <circle cx="50" cy="40" r="3" fill="#10B981" opacity="0.15"><animate attributeName="cy" values="40;35;40" dur="2s" repeatCount="indefinite" /></circle>
        <circle cx="250" cy="50" r="2" fill="#6366F1" opacity="0.12"><animate attributeName="cy" values="50;44;50" dur="2.5s" repeatCount="indefinite" /></circle>
        <circle cx="80" cy="160" r="2.5" fill="#F43F5E" opacity="0.10"><animate attributeName="cy" values="160;155;160" dur="1.8s" repeatCount="indefinite" /></circle>
        <circle cx="220" cy="150" r="2" fill="#7C3AED" opacity="0.12"><animate attributeName="cy" values="150;144;150" dur="2.2s" repeatCount="indefinite" /></circle>
        <path d="M140 20 L145 10 L150 20" stroke="#10B981" strokeWidth="0.5" opacity="0.10"><animate attributeName="opacity" values="0.10;0.20;0.10" dur="2s" repeatCount="indefinite" /></path>
        <path d="M160 180 L155 190 L150 180" stroke="#6366F1" strokeWidth="0.5" opacity="0.10"><animate attributeName="opacity" values="0.10;0.18;0.10" dur="2.5s" repeatCount="indefinite" /></path>
      </svg>
      <div className="relative w-20 h-20 mx-auto mb-4">
        <HexIcon Icon={HiOutlineCheckCircle} accent="#059669" size="lg" bespoke="check" />
      </div>
      <p className="relative text-lg font-semibold text-green-600">{t('fund.success')}</p>
      <p className="relative text-sm text-gray-400 mt-1">Your contribution is being processed on the blockchain</p>
      <Link to="/dashboard" className="relative inline-flex items-center gap-1.5 text-sm text-indigo-600 hover:underline mt-4 font-medium">
        {t('fund.view_history')} <span>→</span>
      </Link>
    </div>
  );
}
