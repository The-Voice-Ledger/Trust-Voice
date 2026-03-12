import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCampaign, getCampaignVideo } from '../api/campaigns';
import ProgressBar from '../components/ProgressBar';
import VideoPlayer from '../components/VideoPlayer';
import DonationForm from '../components/DonationForm';
import useAuthStore from '../stores/authStore';
import { HiOutlineArrowLeft, HiOutlineMapPin, HiOutlineCheckCircle, HiOutlineFilm, HiOutlineSparkles } from '../components/icons';
import { PageBg } from '../components/SvgDecorations';

export default function CampaignDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const [campaign, setCampaign] = useState(null);
  const [video, setVideo] = useState(null);
  const [showDonate, setShowDonate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const c = await getCampaign(id);
        setCampaign(c);
        try { setVideo(await getCampaignVideo(id)); } catch { /* no video */ }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <div className="text-center py-20 text-gray-400">{t('common.loading')}</div>;
  if (error) return <div className="text-center py-20 text-red-400">{error}</div>;
  if (!campaign) return null;

  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;

  return (
    <PageBg pattern="topography" colorA="#6366F1" colorB="#A855F7">
    <div className="max-w-3xl mx-auto px-4 py-6">
      <Link to="/campaigns" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mb-4 py-2">
        <HiOutlineArrowLeft className="w-4 h-4" /> {t('common.back')}
      </Link>

      {/* Header */}
      <div className="mb-6">
        {campaign.category && (
          <span className="inline-block bg-indigo-50 text-indigo-600 text-xs font-semibold px-2.5 py-0.5 rounded-full capitalize mb-2">
            {campaign.category}
          </span>
        )}
        <h1 className="page-header-accent text-2xl sm:text-3xl text-gray-900">{campaign.title}</h1>
        {campaign.ngo_name && (
          <p className="text-gray-500 mt-1">by {campaign.ngo_name}</p>
        )}
      </div>

      {/* Video */}
      {video ? (
        <VideoPlayer videoData={video} className="mb-6" />
      ) : (
        <div className="bg-gray-50 border border-dashed border-gray-200 rounded-xl p-8 text-center text-gray-400 text-sm mb-6 flex flex-col items-center gap-2">
          <HiOutlineFilm className="w-8 h-8 text-gray-300" />
          {t('campaign.no_video')}
        </div>
      )}

      {/* Progress */}
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-violet-500 to-transparent" />
        <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
          <path d="M45 35 L57 10 L69 35" stroke="#6366F1" strokeWidth="0.5" opacity="0.05" />
          <path d="M45 35 L69 35" stroke="#6366F1" strokeWidth="0.4" opacity="0.04" />
          <circle cx="57" cy="10" r="2" fill="#6366F1" opacity="0.06" />
        </svg>
        <ProgressBar percentage={pct} className="mb-3" />
        <div className="flex flex-col sm:flex-row sm:justify-between sm:items-baseline gap-1">
          <div>
            <span className="text-xl sm:text-2xl font-bold text-indigo-600">
              ${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}
            </span>
            <span className="text-gray-400 text-sm ml-2">
              {t('campaign.raised_of')} ${fmt(campaign.goal_amount_usd)}
            </span>
          </div>
          <span className="text-sm text-gray-400">
            {campaign.donation_count || 0} {t('campaign.donors')}
          </span>
        </div>
        {campaign.location_gps && (
          <p className="text-xs text-gray-400 mt-2 flex items-center gap-1">
            <HiOutlineMapPin className="w-3.5 h-3.5" /> GPS: {campaign.location_gps}
            {video?.location_verified && (
              <span className="text-green-600 font-medium ml-1 flex items-center gap-0.5">
                <HiOutlineCheckCircle className="w-3.5 h-3.5" /> {t('campaign.location_verified')}
              </span>
            )}
          </p>
        )}
      </div>

      {/* Description */}
      <div className="prose prose-sm max-w-none text-gray-700 mb-8 whitespace-pre-line">
        {campaign.description}
      </div>

      {/* Donate section */}
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-rose-500 via-pink-500 to-transparent" />
        <svg className="absolute top-2 right-2 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
          <path d="M40 22 C40 16, 48 12, 48 20 C48 28, 40 32, 40 32 C40 32, 32 28, 32 20 C32 12, 40 16, 40 22" stroke="#F43F5E" strokeWidth="0.5" opacity="0.06" />
          <circle cx="40" cy="38" r="1" fill="#F43F5E" opacity="0.05" />
        </svg>
        {!showDonate ? (
          <button
            onClick={() => setShowDonate(true)}
            className="w-full py-3 rounded-xl bg-indigo-600 text-white font-semibold hover:bg-indigo-700 transition text-center"
          >
            {t('campaign.donate_now')}
          </button>
        ) : (
          <>
            <h2 className="text-lg font-semibold mb-4">{t('donate.title')}</h2>
            <DonationForm campaignId={campaign.id} donorId={user?.donor_id} />
          </>
        )}

        {/* Assistant CTA */}
        <Link
          to={`/assistant?campaign=${campaign.id}`}
          className="mt-4 flex items-center justify-center gap-2 w-full py-3 rounded-xl bg-indigo-50 text-indigo-700 text-sm font-medium hover:bg-indigo-100 transition-all border border-indigo-100"
        >
          <HiOutlineSparkles className="w-4 h-4" />
          Ask the Assistant about this campaign
        </Link>
      </div>
    </div>
    </PageBg>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}
