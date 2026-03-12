import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ProgressBar from './ProgressBar';
import {
  MdOutlineWaterDrop, MdOutlineSchool, MdOutlineLocalHospital,
  MdOutlineConstruction, MdOutlineRestaurant, MdOutlineForest,
  MdOutlineHouse, MdOutlineChildCare, MdHandshake,
} from './icons';

const CATEGORY_ICONS = {
  water: MdOutlineWaterDrop, education: MdOutlineSchool, health: MdOutlineLocalHospital,
  infrastructure: MdOutlineConstruction, food: MdOutlineRestaurant, environment: MdOutlineForest,
  shelter: MdOutlineHouse, children: MdOutlineChildCare,
};

const CATEGORY_GRADIENTS = {
  water: 'from-cyan-500 to-blue-600',
  education: 'from-amber-500 to-orange-600',
  health: 'from-rose-500 to-red-600',
  infrastructure: 'from-slate-500 to-gray-700',
  food: 'from-lime-500 to-green-600',
  environment: 'from-emerald-500 to-teal-600',
  shelter: 'from-orange-500 to-amber-700',
  children: 'from-rose-500 to-rose-600',
};
const DEFAULT_GRADIENT = 'from-blue-500 to-teal-600';

const CATEGORY_ACCENT_COLORS = {
  water: { from: '#0891B2', to: '#2563EB' },
  education: { from: '#D97706', to: '#EA580C' },
  health: { from: '#E11D48', to: '#DC2626' },
  infrastructure: { from: '#475569', to: '#374151' },
  food: { from: '#65A30D', to: '#16A34A' },
  environment: { from: '#059669', to: '#0D9488' },
  shelter: { from: '#EA580C', to: '#B45309' },
  children: { from: '#E11D48', to: '#F43F5E' },
  _default: { from: '#2563EB', to: '#0D9488' },
};

/**
 * CampaignCard — bespoke design with unique SVG decorations per category.
 */
export default function CampaignCard({ campaign }) {
  const { t } = useTranslation();
  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;
  const catKey = (campaign.category || '').toLowerCase();
  const gradient = CATEGORY_GRADIENTS[catKey] || DEFAULT_GRADIENT;
  const accent = CATEGORY_ACCENT_COLORS[catKey] || CATEGORY_ACCENT_COLORS._default;

  return (
    <Link
      to={`/campaign/${campaign.id}`}
      className="group relative block rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden transition-all duration-500 hover:shadow-xl hover:shadow-black/[0.06] hover:-translate-y-1 hover:border-transparent"
    >
      {/* Gradient accent line */}
      <div className="h-[2px] w-full" style={{ background: `linear-gradient(to right, ${accent.from}, ${accent.to})` }} />

      {/* Category hero */}
      <div className={`relative h-36 bg-gradient-to-br ${gradient} flex items-center justify-center overflow-hidden`}>
        {/* Bespoke SVG pattern overlay */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 150" fill="none" preserveAspectRatio="none">
          <circle cx="360" cy="20" r="50" stroke="white" strokeWidth="0.5" opacity="0.12" />
          <circle cx="360" cy="20" r="28" stroke="white" strokeWidth="0.3" opacity="0.08" />
          <polygon points="40,120 55,110 55,90 40,80 25,90 25,110" stroke="white" strokeWidth="0.5" opacity="0.10" />
          <path d="M0 130 Q100 105 200 115 T400 100" stroke="white" strokeWidth="0.6" opacity="0.08" />
          <circle cx="40" cy="100" r="2" fill="white" opacity="0.15" />
          <circle cx="200" cy="115" r="1.5" fill="white" opacity="0.10" />
        </svg>

        {(() => { const Icon = CATEGORY_ICONS[catKey] || MdHandshake; return <Icon className="w-14 h-14 text-white/40" />; })()}
        {campaign.category && (
          <span className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-xs font-bold px-2 py-0.5 rounded-lg capitalize font-display" style={{ color: accent.from }}>
            {campaign.category}
          </span>
        )}
        {campaign.ngo_name && (
          <span className="absolute bottom-3 left-3 bg-black/40 backdrop-blur-sm text-white text-xs px-2 py-0.5 rounded-lg">
            {campaign.ngo_name}
          </span>
        )}
      </div>

      <div className="relative p-4">
        {/* Corner accent SVG */}
        <svg className="absolute bottom-0 right-0 w-16 h-16 pointer-events-none" viewBox="0 0 60 60" fill="none">
          <path d="M60 0v60H0" stroke={accent.from} strokeWidth="0.5" opacity="0.08" />
          <circle cx="60" cy="60" r="2" fill={accent.from} opacity="0.12" />
        </svg>

        <h3 className="font-semibold text-gray-900 group-hover:text-gray-700 transition-colors line-clamp-2 font-display">
          {campaign.title}
        </h3>

        <ProgressBar percentage={pct} className="mt-3" />

        <div className="flex justify-between items-baseline mt-2 text-sm">
          <span className="font-bold" style={{ color: accent.from }}>
            ${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}
          </span>
          <span className="text-gray-400">
            {t('campaign.raised_of')} ${fmt(campaign.goal_amount_usd)} {t('campaign.goal')}
          </span>
        </div>

        {campaign.donation_count > 0 && (
          <p className="text-xs text-gray-400 mt-1">
            {campaign.donation_count} {t('campaign.donors')}
          </p>
        )}
      </div>
    </Link>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

