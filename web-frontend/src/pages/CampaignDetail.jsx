import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getCampaign, getCampaignVideo, getProjectUpdates, getCampaignTreasury } from '../api/campaigns';
import ProgressBar from '../components/ProgressBar';
import MilestoneTracker from '../components/MilestoneTracker';
import VideoPlayer from '../components/VideoPlayer';
import DonationForm from '../components/DonationForm';
import useAuthStore from '../stores/authStore';
import { getProjectByCampaignId } from '../projects/projectRegistry';
import {
  HiOutlineArrowLeft, HiOutlineMapPin, HiOutlineCheckCircle, HiOutlineFilm,
  HiOutlineSparkles, HiOutlineDocumentText, HiOutlineShieldCheck,
  HiOutlineBanknotes, HiOutlineArrowTopRightOnSquare, HiOutlineGlobeAlt,
  HiOutlineCheckBadge, HiOutlineBuildingOffice2,
} from '../components/icons';
import { PageBg } from '../components/SvgDecorations';

export default function CampaignDetail() {
  const { id } = useParams();
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const [campaign, setCampaign] = useState(null);
  const [video, setVideo] = useState(null);
  const [updates, setUpdates] = useState([]);
  const [treasury, setTreasury] = useState(null);
  const [showDonate, setShowDonate] = useState(false);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const c = await getCampaign(id);
        setCampaign(c);
        // Fetch supplementary data in parallel — all public endpoints
        const [videoRes, updatesRes, treasuryRes] = await Promise.all([
          getCampaignVideo(id).catch(() => null),
          getProjectUpdates(id).catch(() => []),
          getCampaignTreasury(id).catch(() => null),
        ]);
        if (videoRes) setVideo(videoRes.video || videoRes);
        setUpdates(Array.isArray(updatesRes) ? updatesRes : []);
        setTreasury(treasuryRes);
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

  const linkedProject = getProjectByCampaignId(campaign.id);

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
          <div className="flex items-center gap-2 mt-2 flex-wrap">
            <Link to={`/ngo/${campaign.ngo_id}`} className="inline-flex items-center gap-1.5 text-sm text-gray-600 hover:text-indigo-600 transition font-medium">
              <HiOutlineBuildingOffice2 className="w-4 h-4" />
              {campaign.ngo_name}
            </Link>
            {campaign.ngo_verification_status === 'VERIFIED' && (
              <span className="inline-flex items-center gap-0.5 text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-1.5 py-0.5">
                <HiOutlineCheckBadge className="w-3 h-3" /> Verified
              </span>
            )}
            {campaign.ngo_website_url && (
              <a
                href={campaign.ngo_website_url.startsWith('http') ? campaign.ngo_website_url : `https://${campaign.ngo_website_url}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-1 text-[11px] text-gray-400 hover:text-indigo-500 transition"
              >
                <HiOutlineGlobeAlt className="w-3 h-3" />
                {campaign.ngo_website_url.replace(/^https?:\/\//, '')}
              </a>
            )}
          </div>
        )}
      </div>

      {/* Project Landing Page link */}
      {linkedProject && (
        <Link
          to={`/project/${linkedProject.slug}`}
          className="group flex items-center gap-3 mb-6 px-4 py-3 rounded-2xl bg-gradient-to-r from-emerald-50 to-teal-50 border border-emerald-200/60 hover:border-emerald-300 transition-all hover:shadow-md"
        >
          <span className="flex items-center justify-center w-9 h-9 rounded-xl bg-emerald-600/10 text-emerald-600 shrink-0">
            <HiOutlineArrowTopRightOnSquare className="w-5 h-5" />
          </span>
          <div className="flex-1 min-w-0">
            <p className="text-sm font-semibold text-emerald-800 leading-tight">
              {linkedProject.name} - {linkedProject.tagline}
            </p>
            <p className="text-[11px] text-emerald-600/70 mt-0.5">Visit the full project page</p>
          </div>
          <span className="text-emerald-400 group-hover:translate-x-0.5 transition-transform">›</span>
        </Link>
      )}

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

      {/* Milestone Tracker (if campaign uses milestones) */}
      <MilestoneTracker campaignId={campaign.id} />

      {/* Treasury Transparency */}
      {treasury && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-teal-500 to-transparent" />
          <svg className="absolute -top-1 -right-1 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
            <rect x="50" y="8" width="18" height="24" rx="2" stroke="#10B981" strokeWidth="0.5" opacity="0.06" />
            <line x1="54" y1="14" x2="64" y2="14" stroke="#10B981" strokeWidth="0.4" opacity="0.05" />
            <line x1="54" y1="20" x2="64" y2="20" stroke="#10B981" strokeWidth="0.4" opacity="0.05" />
            <line x1="54" y1="26" x2="60" y2="26" stroke="#10B981" strokeWidth="0.4" opacity="0.05" />
          </svg>
          <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-1.5 mb-3">
            <HiOutlineBanknotes className="w-4 h-4 text-emerald-600" /> Treasury Transparency
          </h3>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-center">
            <div>
              <p className="text-lg font-bold text-emerald-600">${fmt(treasury.total_raised_usd)}</p>
              <p className="text-[11px] text-gray-400 uppercase tracking-wide">Total Raised</p>
            </div>
            <div>
              <p className="text-lg font-bold text-indigo-600">${fmt(treasury.total_released_usd)}</p>
              <p className="text-[11px] text-gray-400 uppercase tracking-wide">Released</p>
            </div>
            <div>
              <p className="text-lg font-bold text-amber-600">${fmt(treasury.funds_held_usd)}</p>
              <p className="text-[11px] text-gray-400 uppercase tracking-wide">Held in Treasury</p>
            </div>
            <div>
              <p className="text-lg font-bold text-gray-500">${fmt(treasury.total_fees_collected_usd)}</p>
              <p className="text-[11px] text-gray-400 uppercase tracking-wide">Platform Fees</p>
            </div>
          </div>
          {treasury.total_milestone_target_usd > 0 && (
            <div className="mt-3">
              <div className="h-1.5 rounded-full bg-gray-100 overflow-hidden">
                <div
                  className="h-full rounded-full bg-gradient-to-r from-emerald-400 to-teal-500 transition-all"
                  style={{ width: `${Math.min(100, (treasury.total_released_usd / treasury.total_milestone_target_usd) * 100)}%` }}
                />
              </div>
              <p className="text-[10px] text-gray-400 mt-1 text-right">
                {Math.round((treasury.total_released_usd / treasury.total_milestone_target_usd) * 100)}% of milestone targets released
              </p>
            </div>
          )}
        </div>
      )}

      {/* Project Updates from NGO */}
      {updates.length > 0 && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-purple-500 to-transparent" />
          <h3 className="text-sm font-semibold text-gray-800 flex items-center gap-1.5 mb-3">
            <HiOutlineDocumentText className="w-4 h-4 text-violet-600" /> Project Updates
          </h3>
          <div className="space-y-4">
            {updates.map((u) => (
              <div key={u.id} className="border-l-2 border-violet-200 pl-3">
                <div className="flex items-start justify-between gap-2">
                  <h4 className="text-sm font-medium text-gray-800">{u.title}</h4>
                  {u.verified ? (
                    <span className="shrink-0 inline-flex items-center gap-0.5 text-[10px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-1.5 py-0.5">
                      <HiOutlineShieldCheck className="w-3 h-3" /> Verified
                    </span>
                  ) : (
                    <span className="shrink-0 text-[10px] font-medium text-amber-600 bg-amber-50 border border-amber-200 rounded-full px-1.5 py-0.5">
                      Unverified
                    </span>
                  )}
                </div>
                <p className="text-xs text-gray-600 mt-1 whitespace-pre-line leading-relaxed">{u.body}</p>
                {u.author_name && (
                  <p className="text-[10px] text-gray-400 mt-1">
                    Posted by {u.author_name} &middot; {u.created_at ? new Date(u.created_at).toLocaleDateString() : ''}
                  </p>
                )}
                {u.media_ipfs_hashes && u.media_ipfs_hashes.length > 0 && (
                  <div className="flex gap-1.5 mt-2 flex-wrap">
                    {u.media_ipfs_hashes.map((hash, i) => (
                      <a
                        key={i}
                        href={`https://gateway.pinata.cloud/ipfs/${hash}`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-[10px] text-indigo-600 underline"
                      >
                        Media {i + 1}
                      </a>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

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
            <h2 className="text-lg font-semibold mb-4">{t('fund.title')}</h2>
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
