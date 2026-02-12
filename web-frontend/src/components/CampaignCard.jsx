import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import ProgressBar from './ProgressBar';
import {
  MdOutlineWaterDrop, MdOutlineSchool, MdOutlineLocalHospital,
  MdOutlineConstruction, MdOutlineRestaurant, MdOutlineForest,
  MdOutlineHouse, MdOutlineChildCare, MdHandshake,
} from 'react-icons/md';

const CATEGORY_ICONS = {
  water: MdOutlineWaterDrop, education: MdOutlineSchool, health: MdOutlineLocalHospital,
  infrastructure: MdOutlineConstruction, food: MdOutlineRestaurant, environment: MdOutlineForest,
  shelter: MdOutlineHouse, children: MdOutlineChildCare,
};

/**
 * CampaignCard — displays a single campaign in the grid.
 */
export default function CampaignCard({ campaign }) {
  const { t } = useTranslation();
  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;

  return (
    <Link
      to={`/campaign/${campaign.id}`}
      className="group block bg-white rounded-2xl shadow-sm hover:shadow-md transition-shadow overflow-hidden border border-gray-100"
    >
      {/* Category badge */}
      <div className="relative h-36 bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center">
        {(() => { const Icon = CATEGORY_ICONS[(campaign.category || '').toLowerCase()] || MdHandshake; return <Icon className="w-14 h-14 text-white/50" />; })()}
        {campaign.category && (
          <span className="absolute top-3 left-3 bg-white/90 text-xs font-semibold text-indigo-700 px-2 py-0.5 rounded-full capitalize">
            {campaign.category}
          </span>
        )}
        {campaign.ngo_name && (
          <span className="absolute bottom-3 left-3 bg-black/40 text-white text-xs px-2 py-0.5 rounded-full">
            {campaign.ngo_name}
          </span>
        )}
      </div>

      <div className="p-4">
        <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors line-clamp-2">
          {campaign.title}
        </h3>

        <ProgressBar percentage={pct} className="mt-3" />

        <div className="flex justify-between items-baseline mt-2 text-sm">
          <span className="font-bold text-indigo-600">
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

