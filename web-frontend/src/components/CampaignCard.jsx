import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ProgressBar from './ProgressBar';
import HexIcon from './HexIcon';
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

const CATEGORY_BESPOKE = {
  water: 'globe', education: 'badge', health: 'heart',
  infrastructure: 'gear', food: 'trending', environment: 'globe',
  shelter: 'building', children: 'users',
};

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

/* ── Category-specific bespoke SVG illustrations for the hero area ── */
const HERO_ILLUSTRATIONS = {
  water: (c) => (
    <>
      {/* Flowing wave lines */}
      <path d="M20 60 Q80 40, 140 55 T260 50 T380 58" stroke={c} strokeWidth="0.8" opacity="0.12" fill="none" />
      <path d="M20 75 Q90 55, 160 70 T280 62 T380 72" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <path d="M20 90 Q100 70, 180 85 T300 78 T380 88" stroke={c} strokeWidth="0.3" strokeDasharray="4 6" opacity="0.06" fill="none" />
      {/* Droplets */}
      <circle cx="320" cy="35" r="8" stroke={c} strokeWidth="0.6" opacity="0.10" fill="none" />
      <path d="M320 24 Q320 30, 314 35 Q320 44, 326 35 Q320 30, 320 24" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <circle cx="60" cy="40" r="3" stroke={c} strokeWidth="0.4" strokeDasharray="2 3" opacity="0.08" fill="none" />
    </>
  ),
  education: (c) => (
    <>
      {/* Open book */}
      <path d="M170 45 Q200 35, 230 45" stroke={c} strokeWidth="0.7" opacity="0.12" fill="none" />
      <path d="M170 45 L170 85 Q200 75, 230 85 L230 45" stroke={c} strokeWidth="0.6" opacity="0.10" fill="none" />
      <line x1="200" y1="40" x2="200" y2="82" stroke={c} strokeWidth="0.4" opacity="0.08" />
      {/* Page lines */}
      <line x1="178" y1="55" x2="195" y2="52" stroke={c} strokeWidth="0.3" opacity="0.06" />
      <line x1="178" y1="62" x2="195" y2="59" stroke={c} strokeWidth="0.3" opacity="0.06" />
      <line x1="205" y1="52" x2="222" y2="55" stroke={c} strokeWidth="0.3" opacity="0.06" />
      <line x1="205" y1="59" x2="222" y2="62" stroke={c} strokeWidth="0.3" opacity="0.06" />
      {/* Graduation cap hint */}
      <polygon points="335,30 355,20 375,30 355,40" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <line x1="355" y1="40" x2="355" y2="55" stroke={c} strokeWidth="0.3" opacity="0.06" />
    </>
  ),
  health: (c) => (
    <>
      {/* Heartbeat line */}
      <path d="M30 70 L120 70 L140 40 L160 95 L180 55 L200 80 L220 70 L380 70" stroke={c} strokeWidth="0.8" opacity="0.12" fill="none" />
      {/* Cross */}
      <rect x="320" y="25" width="6" height="22" rx="1" stroke={c} strokeWidth="0.6" opacity="0.10" fill="none" />
      <rect x="312" y="33" width="22" height="6" rx="1" stroke={c} strokeWidth="0.6" opacity="0.10" fill="none" />
      {/* Pulse rings */}
      <circle cx="170" cy="70" r="20" stroke={c} strokeWidth="0.3" strokeDasharray="3 5" opacity="0.06" fill="none" />
      <circle cx="170" cy="70" r="35" stroke={c} strokeWidth="0.2" strokeDasharray="2 6" opacity="0.04" fill="none" />
    </>
  ),
  infrastructure: (c) => (
    <>
      {/* Blueprint grid */}
      <rect x="60" y="30" width="100" height="70" rx="2" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <line x1="60" y1="55" x2="160" y2="55" stroke={c} strokeWidth="0.3" opacity="0.06" />
      <line x1="60" y1="75" x2="160" y2="75" stroke={c} strokeWidth="0.3" opacity="0.06" />
      <line x1="95" y1="30" x2="95" y2="100" stroke={c} strokeWidth="0.3" opacity="0.06" />
      <line x1="130" y1="30" x2="130" y2="100" stroke={c} strokeWidth="0.3" opacity="0.06" />
      {/* Crane */}
      <line x1="310" y1="20" x2="310" y2="95" stroke={c} strokeWidth="0.6" opacity="0.10" />
      <line x1="300" y1="95" x2="320" y2="95" stroke={c} strokeWidth="0.6" opacity="0.10" />
      <line x1="310" y1="25" x2="350" y2="25" stroke={c} strokeWidth="0.5" opacity="0.08" />
      <line x1="350" y1="25" x2="350" y2="50" stroke={c} strokeWidth="0.3" strokeDasharray="2 3" opacity="0.06" />
    </>
  ),
  food: (c) => (
    <>
      {/* Plant / wheat stalks */}
      <path d="M190 95 Q190 60, 200 40" stroke={c} strokeWidth="0.6" opacity="0.10" fill="none" />
      <path d="M190 75 Q178 65, 175 50" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <path d="M190 75 Q202 65, 205 50" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <path d="M192 55 Q182 45, 180 35" stroke={c} strokeWidth="0.4" opacity="0.07" fill="none" />
      <path d="M192 55 Q202 45, 204 35" stroke={c} strokeWidth="0.4" opacity="0.07" fill="none" />
      {/* Plate circle */}
      <circle cx="320" cy="65" r="25" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <circle cx="320" cy="65" r="18" stroke={c} strokeWidth="0.3" strokeDasharray="3 4" opacity="0.06" fill="none" />
      {/* Small grains */}
      <circle cx="80" cy="50" r="2" fill={c} opacity="0.06" />
      <circle cx="95" cy="42" r="1.5" fill={c} opacity="0.05" />
      <circle cx="75" cy="38" r="1" fill={c} opacity="0.04" />
    </>
  ),
  environment: (c) => (
    <>
      {/* Tree */}
      <line x1="200" y1="55" x2="200" y2="100" stroke={c} strokeWidth="0.6" opacity="0.10" />
      <circle cx="200" cy="42" r="20" stroke={c} strokeWidth="0.5" opacity="0.10" fill="none" />
      <circle cx="188" cy="36" r="12" stroke={c} strokeWidth="0.3" opacity="0.07" fill="none" />
      <circle cx="212" cy="36" r="12" stroke={c} strokeWidth="0.3" opacity="0.07" fill="none" />
      {/* Sun rays */}
      <circle cx="340" cy="30" r="12" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      {[0,45,90,135,180,225,270,315].map((a,i) => {
        const r1 = 16, r2 = 22, cx = 340, cy = 30;
        const rad = a * Math.PI / 180;
        return <line key={i} x1={cx+Math.cos(rad)*r1} y1={cy+Math.sin(rad)*r1} x2={cx+Math.cos(rad)*r2} y2={cy+Math.sin(rad)*r2} stroke={c} strokeWidth="0.3" opacity="0.06" />;
      })}
      {/* Ground line */}
      <path d="M50 100 Q130 92, 200 100 T350 96" stroke={c} strokeWidth="0.4" opacity="0.06" fill="none" />
    </>
  ),
  shelter: (c) => (
    <>
      {/* House outline */}
      <path d="M170 55 L200 30 L230 55" stroke={c} strokeWidth="0.7" opacity="0.12" fill="none" />
      <rect x="175" y="55" width="50" height="40" stroke={c} strokeWidth="0.5" opacity="0.10" fill="none" />
      <rect x="190" y="70" width="20" height="25" stroke={c} strokeWidth="0.4" opacity="0.08" fill="none" />
      {/* Window */}
      <rect x="180" y="60" width="10" height="10" rx="1" stroke={c} strokeWidth="0.3" opacity="0.07" fill="none" />
      <rect x="210" y="60" width="10" height="10" rx="1" stroke={c} strokeWidth="0.3" opacity="0.07" fill="none" />
      {/* Neighborhood hint */}
      <path d="M310 60 L330 42 L350 60" stroke={c} strokeWidth="0.4" opacity="0.07" fill="none" />
      <rect x="315" y="60" width="30" height="25" stroke={c} strokeWidth="0.3" opacity="0.06" fill="none" />
    </>
  ),
  children: (c) => (
    <>
      {/* Stars */}
      {[[80,35,8],[320,40,10],[260,25,6],[140,30,5]].map(([cx,cy,r],i) => (
        <polygon key={i} points={starPoints(cx,cy,r)} stroke={c} strokeWidth="0.5" opacity={0.06+i*0.02} fill="none" />
      ))}
      {/* Circles — bubbles */}
      <circle cx="200" cy="65" r="30" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
      <circle cx="180" cy="75" r="15" stroke={c} strokeWidth="0.3" strokeDasharray="3 4" opacity="0.06" fill="none" />
      <circle cx="225" cy="55" r="18" stroke={c} strokeWidth="0.3" opacity="0.06" fill="none" />
      {/* Small floating dots */}
      <circle cx="150" cy="45" r="2" fill={c} opacity="0.06"><animate attributeName="cy" values="45;40;45" dur="3s" repeatCount="indefinite" /></circle>
      <circle cx="250" cy="50" r="1.5" fill={c} opacity="0.05"><animate attributeName="cy" values="50;44;50" dur="2.5s" repeatCount="indefinite" /></circle>
    </>
  ),
};

/* Default illustration for unknown categories */
const DEFAULT_ILLUSTRATION = (c) => (
  <>
    {/* Circuit-style node network */}
    <circle cx="200" cy="60" r="25" stroke={c} strokeWidth="0.5" opacity="0.08" fill="none" />
    <circle cx="200" cy="60" r="12" stroke={c} strokeWidth="0.3" strokeDasharray="2 4" opacity="0.06" fill="none" />
    <line x1="225" y1="60" x2="300" y2="40" stroke={c} strokeWidth="0.4" opacity="0.06" />
    <circle cx="300" cy="40" r="8" stroke={c} strokeWidth="0.4" opacity="0.07" fill="none" />
    <line x1="175" y1="60" x2="100" y2="45" stroke={c} strokeWidth="0.4" opacity="0.06" />
    <circle cx="100" cy="45" r="8" stroke={c} strokeWidth="0.4" opacity="0.07" fill="none" />
    <line x1="200" y1="85" x2="200" y2="110" stroke={c} strokeWidth="0.3" opacity="0.05" />
    <circle cx="200" cy="115" r="5" stroke={c} strokeWidth="0.3" opacity="0.05" fill="none" />
    {/* Node dots */}
    <circle cx="200" cy="60" r="2.5" fill={c} opacity="0.10" />
    <circle cx="300" cy="40" r="2" fill={c} opacity="0.08" />
    <circle cx="100" cy="45" r="2" fill={c} opacity="0.08" />
  </>
);

function starPoints(cx, cy, r) {
  const pts = [];
  for (let i = 0; i < 10; i++) {
    const a = (Math.PI / 5) * i - Math.PI / 2;
    const rad = i % 2 === 0 ? r : r * 0.4;
    pts.push(`${cx + Math.cos(a) * rad},${cy + Math.sin(a) * rad}`);
  }
  return pts.join(' ');
}

/**
 * CampaignCard — elegant bespoke design with hex-node icons and category-specific SVG illustrations.
 */
export default function CampaignCard({ campaign }) {
  const { t } = useTranslation();
  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;
  const catKey = (campaign.category || '').toLowerCase();
  const accent = CATEGORY_ACCENT_COLORS[catKey] || CATEGORY_ACCENT_COLORS._default;
  const CatIcon = CATEGORY_ICONS[catKey] || MdHandshake;
  const bespoke = CATEGORY_BESPOKE[catKey] || 'globe';
  const illustration = HERO_ILLUSTRATIONS[catKey] || DEFAULT_ILLUSTRATION;

  return (
    <Link
      to={`/campaign/${campaign.id}`}
      className="group relative block rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden transition-all duration-500 hover:shadow-xl hover:shadow-black/[0.06] hover:-translate-y-1 hover:border-transparent"
    >
      {/* Gradient accent line */}
      <div className="h-[2px] w-full" style={{ background: `linear-gradient(to right, ${accent.from}, ${accent.to})` }} />

      {/* ── Elegant SVG hero ── */}
      <div className="relative h-36 flex items-center justify-center overflow-hidden" style={{ background: `linear-gradient(135deg, ${accent.from}06, ${accent.to}04)` }}>
        {/* Bespoke category illustration */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 150" fill="none" preserveAspectRatio="xMidYMid slice">
          {illustration(accent.from)}
        </svg>

        {/* Shared hex grid texture */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 150" fill="none" preserveAspectRatio="none">
          {/* Corner hexagons */}
          <polygon points="370,8 388,18 388,38 370,48 352,38 352,18" stroke={accent.from} strokeWidth="0.4" opacity="0.06" />
          <polygon points="30,102 48,112 48,132 30,142 12,132 12,112" stroke={accent.from} strokeWidth="0.4" opacity="0.06" />
          {/* Connection lines */}
          <path d="M370 48 L300 75" stroke={accent.from} strokeWidth="0.2" strokeDasharray="3 5" opacity="0.04" />
          <path d="M30 102 L100 80" stroke={accent.from} strokeWidth="0.2" strokeDasharray="3 5" opacity="0.04" />
          {/* Small node dots */}
          <circle cx="370" cy="8" r="1.5" fill={accent.from} opacity="0.10" />
          <circle cx="30" cy="142" r="1.5" fill={accent.from} opacity="0.10" />
          <circle cx="300" cy="75" r="1" fill={accent.from} opacity="0.06" />
          <circle cx="100" cy="80" r="1" fill={accent.from} opacity="0.06" />
        </svg>

        {/* Central hex-node icon */}
        <HexIcon Icon={CatIcon} accent={accent.from} bespoke={bespoke} size="lg" />

        {/* Category badge */}
        {campaign.category && (
          <span className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-xs font-bold px-2.5 py-1 rounded-lg capitalize font-display shadow-sm" style={{ color: accent.from }}>
            {campaign.category}
          </span>
        )}
        {/* NGO name */}
        {campaign.ngo_name && (
          <span className="absolute bottom-3 left-3 bg-white/80 backdrop-blur-sm text-xs px-2.5 py-1 rounded-lg font-medium shadow-sm" style={{ color: accent.from }}>
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

