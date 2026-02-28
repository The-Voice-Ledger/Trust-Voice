import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination, Autoplay } from 'swiper/modules';
import { listCampaigns } from '../api/campaigns';
import { getAnalyticsSummary } from '../api/analytics';
import ProgressBar from '../components/ProgressBar';
import VoiceButton from '../components/VoiceButton';
import { voiceSearchCampaigns } from '../api/voice';
import {
  HiOutlineChatBubbleLeftRight, HiOutlineCheckBadge,
  HiOutlineChartBarSquare, HiOutlineRocketLaunch,
  HiOutlineGlobeAlt, HiOutlineChartBar, HiOutlineCog6Tooth,
  HiOutlineHeart, HiOutlineBuildingOffice2, HiOutlinePlusCircle,
  HiOutlineCamera, HiOutlinePlayCircle, HiOutlineMapPin,
  HiOutlineUserGroup, HiOutlineArrowRight, HiOutlineVideoCameraSlash,
  HiOutlineSpeakerWave, HiOutlineSpeakerXMark,
} from 'react-icons/hi2';
import { HiOutlineMicrophone, HiOutlineEye, HiOutlineCreditCard } from 'react-icons/hi';
import {
  MdOutlineWaterDrop, MdOutlineSchool, MdOutlineLocalHospital,
  MdOutlineConstruction, MdOutlineRestaurant, MdOutlineForest,
  MdOutlineHouse, MdOutlineChildCare, MdHandshake,
} from 'react-icons/md';

const CATEGORY_ICONS = {
  water: MdOutlineWaterDrop,
  education: MdOutlineSchool,
  health: MdOutlineLocalHospital,
  infrastructure: MdOutlineConstruction,
  food: MdOutlineRestaurant,
  environment: MdOutlineForest,
  shelter: MdOutlineHouse,
  children: MdOutlineChildCare,
};

/**
 * Landing — rich homepage with hero, Swiper video carousel,
 * feature cards, live stats and CTA.
 */
export default function Landing() {
  const { t } = useTranslation();
  const [featured, setFeatured] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadingFeatured, setLoadingFeatured] = useState(true);

  useEffect(() => {
    listCampaigns({ page: 1, pageSize: 8, status: 'active', sort: 'most_funded' })
      .then((d) => setFeatured(d.items || (Array.isArray(d) ? d : [])))
      .catch(() => {})
      .finally(() => setLoadingFeatured(false));

    getAnalyticsSummary({ days: 30 })
      .then(setStats)
      .catch(() => {});
  }, []);

  return (
    <div className="relative">
      {/* ════════ HERO ════════ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-indigo-950 to-purple-950 text-white">
        {/* Decorative elements */}
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-60" />
        <div className="absolute -top-32 -right-32 w-[500px] h-[500px] bg-indigo-500/20 rounded-full blur-[120px]" />
        <div className="absolute -bottom-32 -left-32 w-[400px] h-[400px] bg-purple-500/20 rounded-full blur-[120px]" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-24 sm:py-32 text-center">
          <div className="inline-flex items-center gap-2 bg-white/10 backdrop-blur-md rounded-full px-5 py-2 text-sm font-medium mb-8 border border-white/10">
            <HiOutlineMicrophone className="w-4 h-4 text-indigo-300" />
            <span className="text-indigo-200">{t('landing.badge')}</span>
          </div>
          <h1 className="text-3xl sm:text-5xl lg:text-7xl font-extrabold tracking-tight mb-6 leading-[1.1]">
            <span className="bg-gradient-to-r from-white via-indigo-200 to-purple-200 bg-clip-text text-transparent">
              {t('landing.hero_title')}
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-indigo-200/70 max-w-2xl mx-auto mb-12">
            {t('landing.hero_subtitle')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center w-full sm:w-auto">
            <Link
              to="/campaigns"
              className="group w-full sm:w-auto text-center px-8 py-4 rounded-2xl bg-white text-indigo-700 font-bold text-lg shadow-xl shadow-indigo-500/25 hover:shadow-2xl hover:shadow-indigo-500/40 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2"
            >
              {t('landing.explore_btn')}
              <HiOutlineArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <VoiceButton
              apiCall={voiceSearchCampaigns}
              onResult={() => {}}
              className="!bg-white/10 !backdrop-blur-md !border-white/20 !text-white hover:!bg-white/20 !rounded-2xl !px-8 !py-4"
            />
          </div>
        </div>
      </section>

      {/* ════════ LIVE STATS BAR ════════ */}
      <section className="relative -mt-8 z-10 max-w-5xl mx-auto px-4 sm:px-6">
        <div className="bg-white rounded-2xl shadow-xl shadow-gray-200/50 border border-gray-100 px-4 sm:px-6 py-4 sm:py-6 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6">
          <StatCard value={stats?.started ?? '—'} label={t('landing.stat_conversations')} Icon={HiOutlineChatBubbleLeftRight} color="indigo" />
          <StatCard value={stats?.completed ?? '—'} label={t('landing.stat_completed')} Icon={HiOutlineCheckBadge} color="emerald" />
          <StatCard
            value={stats?.completion_rate != null ? `${Math.round(stats.completion_rate)}%` : '—'}
            label={t('landing.stat_success_rate')}
            Icon={HiOutlineChartBarSquare}
            color="amber"
          />
          <StatCard value={featured.length > 0 ? `${featured.length}+` : '—'} label={t('landing.stat_active_campaigns')} Icon={HiOutlineRocketLaunch} color="pink" />
        </div>
      </section>

      {/* ════════ VIDEO SHOWCASE ════════ */}
      <HeroVideo />

      {/* ════════ MEDIA SHOWCASE — Swiper Carousel ════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <div className="text-center mb-12">
          <p className="text-sm font-semibold text-indigo-600 uppercase tracking-wider mb-2">Featured</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 mb-3">{t('landing.showcase_title')}</h2>
          <p className="text-gray-500 max-w-lg mx-auto">{t('landing.showcase_subtitle')}</p>
        </div>

        {loadingFeatured ? (
          <div className="flex justify-center py-16">
            <div className="w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        ) : featured.length === 0 ? (
          <div className="text-center py-16 text-gray-400">{t('home.no_campaigns')}</div>
        ) : (
          <Swiper
            modules={[Navigation, Pagination, Autoplay]}
            spaceBetween={24}
            slidesPerView={1}
            navigation
            pagination={{ clickable: true }}
            autoplay={{ delay: 5000, disableOnInteraction: true }}
            breakpoints={{
              640: { slidesPerView: 2 },
              1024: { slidesPerView: 3 },
            }}
            className="pb-14"
          >
            {featured.map((c) => (
              <SwiperSlide key={c.id}>
                <MediaCard campaign={c} t={t} />
              </SwiperSlide>
            ))}
          </Swiper>
        )}

        <div className="text-center mt-8">
          <Link
            to="/campaigns"
            className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-50 text-indigo-700 font-semibold hover:bg-indigo-100 transition-all"
          >
            {t('landing.view_all_campaigns')}
            <HiOutlineArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

      {/* ════════ HOW IT WORKS ════════ */}
      <section className="bg-gray-50/80 border-y border-gray-100">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-20">
          <p className="text-sm font-semibold text-indigo-600 uppercase tracking-wider text-center mb-2">Process</p>
          <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-14">{t('landing.how_title')}</h2>
          <div className="relative">
            {/* Connector line — desktop only */}
            <div className="hidden lg:block absolute top-8 left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-indigo-200 via-purple-200 to-indigo-200 rounded-full" />
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
              <StepCard step="1" Icon={HiOutlineMicrophone} title={t('landing.step1_title')} desc={t('landing.step1_desc')} />
              <StepCard step="2" Icon={HiOutlineEye} title={t('landing.step2_title')} desc={t('landing.step2_desc')} />
              <StepCard step="3" Icon={HiOutlineCreditCard} title={t('landing.step3_title')} desc={t('landing.step3_desc')} />
              <StepCard step="4" Icon={HiOutlineCamera} title={t('landing.step4_title')} desc={t('landing.step4_desc')} />
            </div>
          </div>
        </div>
      </section>

      {/* ════════ PLATFORM FEATURES ════════ */}
      <section className="max-w-7xl mx-auto px-4 sm:px-6 py-20">
        <p className="text-sm font-semibold text-indigo-600 uppercase tracking-wider text-center mb-2">Platform</p>
        <h2 className="text-3xl sm:text-4xl font-bold text-gray-900 text-center mb-4">{t('landing.features_title')}</h2>
        <p className="text-gray-500 text-center max-w-lg mx-auto mb-14">{t('landing.features_subtitle')}</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <FeatureCard to="/campaigns" Icon={HiOutlineGlobeAlt} title={t('landing.feat_campaigns')} desc={t('landing.feat_campaigns_desc')} color="indigo" />
          <FeatureCard to="/analytics" Icon={HiOutlineChartBar} title={t('landing.feat_analytics')} desc={t('landing.feat_analytics_desc')} color="emerald" />
          <FeatureCard to="/admin" Icon={HiOutlineCog6Tooth} title={t('landing.feat_admin')} desc={t('landing.feat_admin_desc')} color="amber" />
          <FeatureCard to="/donate" Icon={HiOutlineHeart} title={t('landing.feat_donate')} desc={t('landing.feat_donate_desc')} color="pink" />
          <FeatureCard to="/register-ngo" Icon={HiOutlineBuildingOffice2} title={t('landing.feat_ngo')} desc={t('landing.feat_ngo_desc')} color="blue" hasMic />
          <FeatureCard to="/create-campaign" Icon={HiOutlinePlusCircle} title={t('landing.feat_create')} desc={t('landing.feat_create_desc')} color="violet" hasMic />
          <FeatureCard to="/field-agent" Icon={HiOutlineCamera} title={t('landing.feat_field')} desc={t('landing.feat_field_desc')} color="teal" />
        </div>
      </section>

      {/* ════════ FOR TESTERS — CTA ════════ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-600 text-white">
        <div className="absolute inset-0 bg-[url('data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjAiIGhlaWdodD0iNjAiIHZpZXdCb3g9IjAgMCA2MCA2MCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48ZyBmaWxsPSJub25lIiBmaWxsLXJ1bGU9ImV2ZW5vZGQiPjxnIGZpbGw9IiNmZmYiIGZpbGwtb3BhY2l0eT0iMC4wMyI+PGNpcmNsZSBjeD0iMSIgY3k9IjEiIHI9IjEiLz48L2c+PC9nPjwvc3ZnPg==')] opacity-60" />
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 py-20 text-center">
          <h2 className="text-2xl sm:text-4xl font-bold mb-4">{t('landing.tester_title')}</h2>
          <p className="text-white/70 max-w-xl mx-auto mb-10 text-lg">{t('landing.tester_desc')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center w-full sm:w-auto px-4 sm:px-0">
            <Link
              to="/register-ngo"
              className="w-full sm:w-auto text-center px-8 py-4 rounded-2xl bg-white text-indigo-700 font-bold hover:bg-indigo-50 transition shadow-lg shadow-indigo-900/20"
            >
              {t('landing.tester_register')}
            </Link>
            <Link
              to="/login"
              className="w-full sm:w-auto text-center px-8 py-4 rounded-2xl bg-white/10 backdrop-blur text-white font-bold border border-white/20 hover:bg-white/20 transition"
            >
              {t('landing.tester_login')}
            </Link>
          </div>
        </div>
      </section>
    </div>
  );
}

/* ── Sub-components ──────────────────────── */

function StatCard({ value, label, Icon, color = 'indigo' }) {
  const colors = {
    indigo: 'bg-indigo-50 text-indigo-600',
    emerald: 'bg-emerald-50 text-emerald-600',
    amber: 'bg-amber-50 text-amber-600',
    pink: 'bg-pink-50 text-pink-600',
  };
  return (
    <div className="flex flex-col items-center text-center">
      <div className={`w-10 h-10 rounded-xl ${colors[color]} flex items-center justify-center mb-2`}>
        <Icon className="w-5 h-5" />
      </div>
      <div className="text-xl sm:text-2xl font-bold text-gray-900">{value}</div>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}

function StepCard({ step, Icon, title, desc }) {
  return (
    <div className="relative text-center group">
      <div className="relative z-10 w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 text-white flex items-center justify-center mx-auto mb-5 shadow-lg shadow-indigo-200/50 group-hover:shadow-xl group-hover:shadow-indigo-300/50 group-hover:scale-105 transition-all ring-4 ring-white">
        <Icon className="w-7 h-7" />
      </div>
      <div className="inline-flex items-center justify-center w-6 h-6 rounded-full bg-indigo-100 text-indigo-600 text-xs font-bold mb-2">{step}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500">{desc}</p>
    </div>
  );
}

/* ─── Hero Video Showcase ─── */
const HERO_VIDEO_URL = 'https://violet-rainy-toad-577.mypinata.cloud/ipfs/bafybeicgwgrqh62sqefihbeixhsqwfovi6slyl7e6payyp2agns6xiz2su';

function HeroVideo() {
  const { t } = useTranslation();
  const videoRef = useRef(null);
  const [muted, setMuted] = useState(true);
  const [playing, setPlaying] = useState(false);
  const [loaded, setLoaded] = useState(false);

  const toggleMute = () => {
    if (!videoRef.current) return;
    videoRef.current.muted = !muted;
    setMuted(!muted);
  };

  const togglePlay = () => {
    if (!videoRef.current) return;
    if (videoRef.current.paused) {
      videoRef.current.play();
      setPlaying(true);
    } else {
      videoRef.current.pause();
      setPlaying(false);
    }
  };

  return (
    <section className="max-w-5xl mx-auto px-4 sm:px-6 pt-16 pb-8">
      <div className="text-center mb-8">
        <p className="text-sm font-semibold text-indigo-600 uppercase tracking-wider mb-2">
          {t('landing.video_label', 'See It In Action')}
        </p>
        <h2 className="text-2xl sm:text-3xl font-bold text-gray-900">
          {t('landing.video_title', 'Transparency You Can Watch')}
        </h2>
      </div>

      <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-indigo-200/40 border border-gray-100 bg-black group">
        <video
          ref={videoRef}
          autoPlay
          loop
          muted
          playsInline
          onCanPlay={() => { setLoaded(true); setPlaying(true); }}
          className="w-full aspect-video object-cover"
          src={HERO_VIDEO_URL}
        />

        {/* Loading spinner */}
        {!loaded && (
          <div className="absolute inset-0 flex items-center justify-center bg-gray-900">
            <div className="w-10 h-10 border-4 border-indigo-300 border-t-indigo-600 rounded-full animate-spin" />
          </div>
        )}

        {/* Controls overlay — visible on hover / tap */}
        <div className="absolute inset-0 flex items-center justify-center bg-black/0 group-hover:bg-black/20 transition-colors">
          {/* Center play/pause */}
          <button
            onClick={togglePlay}
            className="opacity-0 group-hover:opacity-100 transition-opacity w-16 h-16 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-xl hover:scale-110 active:scale-95"
            aria-label={playing ? 'Pause' : 'Play'}
          >
            {playing ? (
              <svg className="w-7 h-7 text-indigo-700" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <HiOutlinePlayCircle className="w-9 h-9 text-indigo-700" />
            )}
          </button>
        </div>

        {/* Mute/Unmute button — always visible in corner */}
        <button
          onClick={toggleMute}
          className="absolute bottom-4 right-4 flex items-center gap-2 px-4 py-2 rounded-xl bg-white/90 backdrop-blur-md shadow-lg text-sm font-medium text-gray-700 hover:bg-white transition-all hover:scale-105 active:scale-95 border border-gray-200/50"
          aria-label={muted ? 'Unmute' : 'Mute'}
        >
          {muted ? (
            <>
              <HiOutlineSpeakerXMark className="w-5 h-5 text-gray-500" />
              <span className="hidden sm:inline">{t('landing.video_unmute', 'Tap to unmute')}</span>
            </>
          ) : (
            <>
              <HiOutlineSpeakerWave className="w-5 h-5 text-indigo-600" />
              <span className="hidden sm:inline">{t('landing.video_mute', 'Mute')}</span>
            </>
          )}
        </button>

        {/* IPFS badge */}
        <div className="absolute top-4 left-4 flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-black/50 backdrop-blur-sm text-white/80 text-xs font-medium">
          <HiOutlineCheckBadge className="w-4 h-4 text-green-400" />
          IPFS Verified
        </div>
      </div>
    </section>
  );
}

function FeatureCard({ to, Icon, title, desc, hasMic, color = 'indigo' }) {
  const colorMap = {
    indigo: 'from-indigo-500 to-indigo-600 shadow-indigo-200/50 hover:shadow-indigo-300/60',
    emerald: 'from-emerald-500 to-emerald-600 shadow-emerald-200/50 hover:shadow-emerald-300/60',
    amber: 'from-amber-500 to-amber-600 shadow-amber-200/50 hover:shadow-amber-300/60',
    pink: 'from-pink-500 to-pink-600 shadow-pink-200/50 hover:shadow-pink-300/60',
    blue: 'from-blue-500 to-blue-600 shadow-blue-200/50 hover:shadow-blue-300/60',
    violet: 'from-violet-500 to-violet-600 shadow-violet-200/50 hover:shadow-violet-300/60',
    teal: 'from-teal-500 to-teal-600 shadow-teal-200/50 hover:shadow-teal-300/60',
  };

  return (
    <Link
      to={to}
      className="group block bg-white rounded-2xl border border-gray-100 p-6 transition-all hover:-translate-y-1 hover:shadow-xl hover:border-gray-200"
    >
      <div className="flex items-start gap-4">
        <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorMap[color]} text-white flex items-center justify-center flex-shrink-0 shadow-lg group-hover:shadow-xl transition-shadow`}>
          <Icon className="w-6 h-6" />
        </div>
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <h3 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">{title}</h3>
            {hasMic && (
              <span className="flex items-center gap-0.5 text-[10px] font-bold text-indigo-500 bg-indigo-50 px-1.5 py-0.5 rounded-full uppercase">
                <HiOutlineMicrophone className="w-3 h-3" /> Voice
              </span>
            )}
          </div>
          <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
        </div>
      </div>
    </Link>
  );
}

function MediaCard({ campaign, t }) {
  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;

  const CategoryIcon = CATEGORY_ICONS[(campaign.category || '').toLowerCase()] || MdHandshake;

  return (
    <Link
      to={`/campaign/${campaign.id}`}
      className="group block bg-white rounded-2xl shadow-sm hover:shadow-xl transition-all hover:-translate-y-1 overflow-hidden border border-gray-100"
    >
      {/* Video/Image preview */}
      <div className="relative aspect-video bg-gradient-to-br from-indigo-500 to-purple-600 overflow-hidden">
        {campaign.has_video || campaign.video_cid ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/30">
            <div className="w-16 h-16 rounded-full bg-white/90 backdrop-blur flex items-center justify-center shadow-xl group-hover:scale-110 transition-transform">
              <HiOutlinePlayCircle className="w-9 h-9 text-indigo-600" />
            </div>
            <span className="absolute bottom-3 left-3 bg-black/60 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-lg flex items-center gap-1.5">
              <HiOutlinePlayCircle className="w-3.5 h-3.5" />
              {t('campaign.watch_video')}
            </span>
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <CategoryIcon className="w-20 h-20 text-white/40" />
          </div>
        )}
        {campaign.category && (
          <span className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-xs font-semibold text-indigo-700 px-2.5 py-1 rounded-lg capitalize">
            {campaign.category}
          </span>
        )}
        {campaign.ngo_name && (
          <span className="absolute top-3 right-3 bg-black/50 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-lg">
            {campaign.ngo_name}
          </span>
        )}
      </div>

      <div className="p-4 sm:p-5">
        <h3 className="font-bold text-gray-900 text-lg group-hover:text-indigo-600 transition-colors line-clamp-2 mb-2">
          {campaign.title}
        </h3>
        {campaign.description && (
          <p className="text-sm text-gray-500 line-clamp-2 mb-4">{campaign.description}</p>
        )}

        <ProgressBar percentage={pct} className="mb-3" />

        <div className="flex justify-between items-baseline text-sm">
          <span className="font-bold text-indigo-600">${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}</span>
          <span className="text-gray-400">{t('campaign.raised_of')} ${fmt(campaign.goal_amount_usd)}</span>
        </div>

        {(campaign.donation_count > 0 || campaign.location_gps) && (
          <div className="flex items-center gap-3 mt-3 text-xs text-gray-400">
            {campaign.donation_count > 0 && (
              <span className="flex items-center gap-1">
                <HiOutlineUserGroup className="w-3.5 h-3.5" />
                {campaign.donation_count} {t('campaign.donors')}
              </span>
            )}
            {campaign.location_gps && (
              <span className="flex items-center gap-1 text-green-500">
                <HiOutlineMapPin className="w-3.5 h-3.5" />
                GPS Verified
              </span>
            )}
          </div>
        )}
      </div>
    </Link>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}
