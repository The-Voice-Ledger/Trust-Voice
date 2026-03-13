import { useState, useEffect } from 'react';
import { useParams, Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { getNgo, getNgoCampaigns } from '../api/campaigns';
import ProgressBar from '../components/ProgressBar';
import {
  HiOutlineArrowLeft, HiOutlineGlobeAlt, HiOutlineCheckBadge,
  HiOutlineBuildingOffice2, HiOutlineMapPin, HiOutlineArrowTopRightOnSquare,
} from '../components/icons';
import { PageBg, PageHeader } from '../components/SvgDecorations';

export default function NgoProfile() {
  const { id } = useParams();
  const { t } = useTranslation();
  const [ngo, setNgo] = useState(null);
  const [campaigns, setCampaigns] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const [ngoData, campsData] = await Promise.all([
          getNgo(id),
          getNgoCampaigns(id).catch(() => []),
        ]);
        setNgo(ngoData);
        setCampaigns(Array.isArray(campsData) ? campsData : []);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    })();
  }, [id]);

  if (loading) return <div className="text-center py-20 text-gray-400">{t('common.loading')}</div>;
  if (error) return <div className="text-center py-20 text-red-400">{error}</div>;
  if (!ngo) return null;

  const isVerified = ngo.verification_status === 'VERIFIED';
  const focusAreas = ngo.focus_areas ? ngo.focus_areas.split(',').map((a) => a.trim()).filter(Boolean) : [];

  return (
    <PageBg pattern="topography" colorA="#059669" colorB="#6366F1">
    <div className="max-w-3xl mx-auto px-4 py-6">
      <Link to="/campaigns" className="inline-flex items-center gap-1 text-sm text-indigo-600 hover:underline mb-4 py-2">
        <HiOutlineArrowLeft className="w-4 h-4" /> {t('common.back')}
      </Link>

      {/* Header card */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-5 sm:p-6 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-teal-500 to-transparent" />
        <svg className="absolute -top-1 -right-1 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
          <rect x="50" y="10" width="30" height="36" rx="3" stroke="#059669" strokeWidth="0.5" opacity="0.06" />
          <path d="M56 22 L74 22" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
          <path d="M56 28 L70 28" stroke="#059669" strokeWidth="0.4" opacity="0.04" />
          <circle cx="65" cy="50" r="1.5" fill="#059669" opacity="0.05" />
        </svg>

        <div className="flex items-start gap-4">
          {/* Logo / initial */}
          <div className="shrink-0 w-14 h-14 rounded-xl bg-emerald-50 border border-emerald-200/50 flex items-center justify-center">
            {ngo.logo_url ? (
              <img src={ngo.logo_url} alt="" className="w-10 h-10 rounded-lg object-cover" />
            ) : (
              <HiOutlineBuildingOffice2 className="w-7 h-7 text-emerald-600" />
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 flex-wrap">
              <h1 className="text-xl sm:text-2xl font-bold text-gray-900">{ngo.name}</h1>
              {isVerified && (
                <span className="inline-flex items-center gap-0.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-full px-2 py-0.5">
                  <HiOutlineCheckBadge className="w-3.5 h-3.5" /> Verified
                </span>
              )}
            </div>

            {ngo.organization_type && (
              <p className="text-sm text-gray-500 capitalize mt-0.5">{ngo.organization_type.replace(/_/g, ' ')}</p>
            )}

            <div className="flex flex-wrap items-center gap-3 mt-2 text-xs text-gray-500">
              {ngo.country && (
                <span className="flex items-center gap-1">
                  <HiOutlineMapPin className="w-3.5 h-3.5" /> {ngo.country}{ngo.region ? `, ${ngo.region}` : ''}
                </span>
              )}
              {ngo.year_established && (
                <span>Est. {ngo.year_established}</span>
              )}
            </div>
          </div>
        </div>

        {/* Website link */}
        {ngo.website_url && (
          <a
            href={ngo.website_url.startsWith('http') ? ngo.website_url : `https://${ngo.website_url}`}
            target="_blank"
            rel="noopener noreferrer"
            className="mt-4 inline-flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-50 border border-emerald-200/50 text-sm font-medium text-emerald-700 hover:bg-emerald-100 transition"
          >
            <HiOutlineGlobeAlt className="w-4 h-4" />
            {ngo.website_url.replace(/^https?:\/\//, '')}
            <HiOutlineArrowTopRightOnSquare className="w-3.5 h-3.5 opacity-60" />
          </a>
        )}
      </div>

      {/* Mission */}
      {ngo.mission_statement && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-violet-500 via-purple-500 to-transparent" />
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Mission</h3>
          <p className="text-sm text-gray-600 leading-relaxed whitespace-pre-line">{ngo.mission_statement}</p>
          {focusAreas.length > 0 && (
            <div className="flex flex-wrap gap-1.5 mt-3">
              {focusAreas.map((area) => (
                <span key={area} className="px-2.5 py-0.5 bg-violet-50 border border-violet-200/50 text-violet-700 text-[11px] font-medium rounded-full capitalize">
                  {area}
                </span>
              ))}
            </div>
          )}
        </div>
      )}

      {/* Intro video */}
      {(ngo.intro_video_url || ngo.intro_video_ipfs_hash) && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-violet-500 to-transparent" />
          <h3 className="text-sm font-semibold text-gray-800 mb-3">About Us</h3>
          <div className="rounded-xl overflow-hidden bg-black aspect-video">
            <video
              controls
              className="w-full h-full"
              src={ngo.intro_video_url || `https://gateway.pinata.cloud/ipfs/${ngo.intro_video_ipfs_hash}`}
            />
          </div>
        </div>
      )}

      {/* Campaigns by this NGO */}
      <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 mb-6 overflow-hidden">
        <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-indigo-500 via-violet-500 to-transparent" />
        <h3 className="text-sm font-semibold text-gray-800 mb-3">
          Campaigns ({campaigns.length})
        </h3>
        {campaigns.length === 0 ? (
          <p className="text-sm text-gray-400">No active campaigns yet.</p>
        ) : (
          <div className="space-y-3">
            {campaigns.map((c) => {
              const pct = c.goal_amount_usd > 0
                ? Math.min(100, ((c.current_usd_total || c.raised_amount_usd) / c.goal_amount_usd) * 100)
                : 0;
              return (
                <Link
                  key={c.id}
                  to={`/campaign/${c.id}`}
                  className="group block rounded-xl border border-gray-100 hover:border-indigo-200 p-3 transition hover:shadow-sm"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <div>
                      <h4 className="text-sm font-semibold text-gray-800 group-hover:text-indigo-600 transition">{c.title}</h4>
                      {c.category && (
                        <span className="text-[10px] text-indigo-600 bg-indigo-50 rounded-full px-2 py-0.5 capitalize">{c.category}</span>
                      )}
                    </div>
                    <span className={`shrink-0 text-[10px] font-medium px-2 py-0.5 rounded-full ${
                      c.status === 'active'
                        ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                        : 'bg-gray-50 text-gray-500 border border-gray-200'
                    }`}>
                      {c.status}
                    </span>
                  </div>
                  <ProgressBar percentage={pct} className="mb-1.5" />
                  <div className="flex justify-between text-[11px] text-gray-500">
                    <span>${fmt(c.current_usd_total || c.raised_amount_usd)} of ${fmt(c.goal_amount_usd)}</span>
                    {c.donation_count > 0 && <span>{c.donation_count} donors</span>}
                  </div>
                </Link>
              );
            })}
          </div>
        )}
      </div>

      {/* Contact */}
      {(ngo.contact_email || ngo.admin_phone) && (
        <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden">
          <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-gray-300 via-gray-200 to-transparent" />
          <h3 className="text-sm font-semibold text-gray-800 mb-2">Contact</h3>
          <div className="space-y-1 text-sm text-gray-600">
            {ngo.contact_email && <p>{ngo.contact_email}</p>}
            {ngo.admin_phone && <p>{ngo.admin_phone}</p>}
          </div>
        </div>
      )}
    </div>
    </PageBg>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}
