import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCampaign, listCampaigns } from '../api/campaigns';
import DonationForm from '../components/DonationForm';
import VoiceButton from '../components/VoiceButton';
import { voiceDonate } from '../api/voice';
import useAuthStore from '../stores/authStore';
import ProgressBar from '../components/ProgressBar';
import {
  HiOutlineHeart, HiOutlineCheckCircle, HiOutlineArrowLeft,
} from 'react-icons/hi2';
import {
  MdOutlineWaterDrop, MdOutlineSchool, MdOutlineLocalHospital,
  MdOutlineConstruction, MdOutlineRestaurant, MdOutlineForest,
  MdOutlineHouse, MdOutlineChildCare, MdHandshake,
} from 'react-icons/md';

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
    <div className="max-w-lg mx-auto px-4 py-8">
      <Link to="/campaigns" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mb-4 py-2">
        <HiOutlineArrowLeft className="w-4 h-4" /> {t('common.back')}
      </Link>

      <div className="text-center mb-8">
        <div className="w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br from-pink-500 to-rose-600 flex items-center justify-center shadow-lg shadow-pink-200/50 mb-4">
          <HiOutlineHeart className="w-8 h-8 text-white" />
        </div>
        <h1 className="text-2xl font-bold text-gray-900">{t('donate.title')}</h1>
        <p className="text-sm text-gray-500 mt-1">{t('donate.checkout_subtitle')}</p>
      </div>

      {/* Campaign selector (if no ID in URL) */}
      {!campaignId && (
        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-1">{t('donate.select_campaign')}</label>
          <select
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
            className="w-full rounded-xl border border-gray-200 px-3 py-3 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          >
            <option value="">{t('donate.choose_campaign')}</option>
            {campaigns.map((c) => (
              <option key={c.id} value={c.id}>{c.title} — ${fmt(c.goal_amount_usd)} goal</option>
            ))}
          </select>
        </div>
      )}

      {/* Campaign info card */}
      {campaign && (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-5 mb-6">
          <div className="flex items-start gap-3">
            <div className="w-10 h-10 rounded-xl bg-indigo-50 flex items-center justify-center flex-shrink-0">
              <CategoryIcon cat={campaign.category} />
            </div>
            <div className="flex-1">
              <h2 className="font-semibold text-gray-900">{campaign.title}</h2>
              {campaign.ngo_name && <p className="text-xs text-gray-400">{campaign.ngo_name}</p>}
            </div>
          </div>
          <ProgressBar
            percentage={campaign.goal_amount_usd > 0 ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100) : 0}
            className="mt-3"
          />
          <div className="flex justify-between text-sm mt-2">
            <span className="font-bold text-indigo-600">${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}</span>
            <span className="text-gray-400">{t('campaign.raised_of')} ${fmt(campaign.goal_amount_usd)}</span>
          </div>
        </div>
      )}

      {/* Donation form */}
      {campaign ? (
        <div className="bg-white rounded-2xl border border-gray-100 shadow-sm p-4 sm:p-6">
          {donated ? (
            <div className="text-center py-8">
              <div className="w-16 h-16 mx-auto rounded-full bg-green-100 flex items-center justify-center mb-3">
                <HiOutlineCheckCircle className="w-8 h-8 text-green-600" />
              </div>
              <p className="text-lg font-semibold text-green-600">{t('donate.success')}</p>
              <Link to="/dashboard" className="text-sm text-indigo-600 hover:underline mt-3 inline-block">
                {t('donate.view_history')} →
              </Link>
            </div>
          ) : (
            <>
              <DonationForm
                campaignId={campaign.id}
                donorId={user?.donor_id}
                onSuccess={() => setDonated(true)}
              />
              <div className="mt-4 text-center border-t border-gray-100 pt-4">
                <p className="text-xs text-gray-400 mb-2">{t('donate.or_use_voice')}</p>
                <VoiceButton
                  apiCall={voiceDonate}
                  apiArgs={[user?.id || 'web_anonymous', campaign.id]}
                />
              </div>
            </>
          )}
        </div>
      ) : (
        <div className="text-center py-10 text-gray-400">
          {t('donate.select_campaign_first')}
        </div>
      )}
    </div>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}

const DONATE_CATEGORY_ICONS = {
  water: MdOutlineWaterDrop, education: MdOutlineSchool, health: MdOutlineLocalHospital,
  infrastructure: MdOutlineConstruction, food: MdOutlineRestaurant, environment: MdOutlineForest,
  shelter: MdOutlineHouse, children: MdOutlineChildCare,
};

function CategoryIcon({ cat }) {
  const Comp = DONATE_CATEGORY_ICONS[(cat || '').toLowerCase()] || MdHandshake;
  return <Comp className="w-5 h-5 text-indigo-600" />;
}
