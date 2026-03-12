import { useState, useEffect, useRef } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { Swiper, SwiperSlide } from 'swiper/react';
import { Navigation, Pagination, Autoplay } from 'swiper/modules';
import { listCampaigns } from '../api/campaigns';
import { getAnalyticsSummary } from '../api/analytics';
import ProgressBar from '../components/ProgressBar';
import TrustPipeline from '../components/TrustPipeline';
import {
  CircuitTrace, HexGrid, GlowOrb,
  PulseRing, WaveDivider, DataParticles, SectionAccent, TopographyBg, NodeNetwork,
} from '../components/SvgDecorations';
import {
  HiOutlineChatBubbleLeftRight, HiOutlineCheckBadge,
  HiOutlineChartBarSquare, HiOutlineRocketLaunch,
  HiOutlineGlobeAlt, HiOutlineChartBar, HiOutlineCog6Tooth,
  HiOutlineHeart, HiOutlineBuildingOffice2, HiOutlinePlusCircle,
  HiOutlineCamera, HiOutlinePlayCircle, HiOutlineMapPin,
  HiOutlineUserGroup, HiOutlineArrowRight,
  HiOutlineSpeakerWave, HiOutlineSpeakerXMark, HiOutlineSparkles,
  HiOutlineMicrophone, HiOutlineEye, HiOutlineCreditCard,
  MdOutlineWaterDrop, MdOutlineSchool, MdOutlineLocalHospital,
  MdOutlineConstruction, MdOutlineRestaurant, MdOutlineForest,
  MdOutlineHouse, MdOutlineChildCare, MdHandshake,
} from '../components/icons';

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
      <section className="relative overflow-hidden bg-gradient-to-br from-slate-900 via-blue-950 to-teal-950 text-white">
        {/* SVG decorative layers — really subtle, a hint of tech texture */}
        <HexGrid className="absolute inset-0 text-white opacity-20" />
        <CircuitTrace className="absolute inset-0 w-full h-full text-blue-300 opacity-25" />
        <DataParticles className="absolute inset-0 w-full h-full text-blue-400 opacity-30" />
        <GlowOrb className="absolute -top-32 -right-32 w-[500px] h-[500px]" color="#2563EB" />
        <GlowOrb className="absolute -bottom-32 -left-32 w-[400px] h-[400px]" color="#0D9488" />
        <PulseRing className="absolute top-20 right-20 w-40 h-40 text-blue-400 hidden lg:block" />
        <PulseRing className="absolute bottom-10 left-16 w-32 h-32 text-teal-400 hidden lg:block" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-24 sm:py-32 text-center">
          <div className="inline-flex items-center gap-2 bg-white/[0.07] backdrop-blur-xl rounded-full px-5 py-2 text-sm font-medium mb-8 border border-white/[0.08] shadow-lg shadow-blue-500/10">
            <HiOutlineMicrophone className="w-4 h-4 text-blue-300" />
            <span className="text-blue-200">{t('landing.badge')}</span>
          </div>
          <h1 className="hero-heading text-3xl sm:text-5xl lg:text-7xl mb-6">
            <span className="bg-gradient-to-r from-white via-blue-200 to-teal-200 bg-clip-text text-transparent">
              {t('landing.hero_title')}
            </span>
          </h1>
          <p className="text-lg sm:text-xl text-blue-200/70 max-w-2xl mx-auto mb-12">
            {t('landing.hero_subtitle')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center w-full sm:w-auto">
            <Link
              to="/campaigns"
              className="group w-full sm:w-auto text-center px-8 py-4 rounded-2xl bg-white text-blue-700 font-bold text-lg shadow-xl shadow-blue-500/25 hover:shadow-2xl hover:shadow-blue-500/40 hover:-translate-y-0.5 transition-all flex items-center justify-center gap-2"
            >
              {t('landing.explore_btn')}
              <HiOutlineArrowRight className="w-5 h-5 group-hover:translate-x-1 transition-transform" />
            </Link>
            <Link
              to="/assistant"
              className="w-full sm:w-auto text-center px-8 py-4 rounded-2xl bg-white/10 backdrop-blur-md text-white font-bold text-lg border border-white/20 hover:bg-white/20 transition-all flex items-center justify-center gap-2"
            >
              <HiOutlineSparkles className="w-5 h-5" />
              {t('landing.ask_assistant', 'Ask Assistant')}
            </Link>
          </div>
        </div>
      </section>

      {/* ════════ LIVE STATS BAR ════════ */}
      <section className="relative -mt-8 z-10 max-w-5xl mx-auto px-4 sm:px-6">
        <div className="tech-card relative px-4 sm:px-6 py-4 sm:py-6 grid grid-cols-2 sm:grid-cols-4 gap-4 sm:gap-6 shadow-xl shadow-gray-200/50">
          <StatCard value={stats?.started ?? '-'} label={t('landing.stat_conversations')} Icon={HiOutlineChatBubbleLeftRight} color="blue" />
          <StatCard value={stats?.completed ?? '-'} label={t('landing.stat_completed')} Icon={HiOutlineCheckBadge} color="emerald" />
          <StatCard
            value={stats?.completion_rate != null ? `${Math.round(stats.completion_rate)}%` : '-'}
            label={t('landing.stat_success_rate')}
            Icon={HiOutlineChartBarSquare}
            color="amber"
          />
          <StatCard value={featured.length > 0 ? `${featured.length}+` : '-'} label={t('landing.stat_active_campaigns')} Icon={HiOutlineRocketLaunch} color="teal" />
        </div>
      </section>

      {/* ════════ VIDEO SHOWCASE ════════ */}
      <HeroVideo />

      {/* ════════ MEDIA SHOWCASE — Swiper Carousel ════════ */}
      <section className="relative max-w-7xl mx-auto px-4 sm:px-6 py-20">
        {/* Subtle background treatment */}
        <div className="absolute inset-0 -z-10 pointer-events-none" aria-hidden="true">
          <div className="absolute top-0 right-0 w-80 h-80 rounded-full opacity-[0.04]" style={{ background: 'radial-gradient(circle, #2563EB, transparent 70%)' }} />
          <div className="absolute bottom-0 left-0 w-60 h-60 rounded-full opacity-[0.03]" style={{ background: 'radial-gradient(circle, #0D9488, transparent 70%)' }} />
        </div>
        <div className="text-center mb-12">
          <span className="section-label mb-4">Featured</span>
          <h2 className="section-heading text-3xl sm:text-4xl text-gray-900 mb-3 mt-4">{t('landing.showcase_title')}</h2>
          <p className="text-gray-500 max-w-lg mx-auto">{t('landing.showcase_subtitle')}</p>
          <SectionAccent className="mt-6 max-w-xs mx-auto" />
        </div>

        {loadingFeatured ? (
          <div className="flex justify-center py-16">
            <div className="w-10 h-10 border-4 border-blue-200 border-t-blue-600 rounded-full animate-spin" />
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
            className="group inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-blue-50 text-blue-700 font-semibold hover:bg-blue-100 transition-all"
          >
            {t('landing.view_all_campaigns')}
            <HiOutlineArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
        </div>
      </section>

      {/* ════════ HOW IT WORKS ════════ */}
      <section className="relative bg-gradient-to-b from-gray-50/90 to-white border-y border-gray-100 overflow-hidden">
        <TopographyBg className="absolute inset-0 text-blue-400 opacity-70" />
        <div className="relative max-w-7xl mx-auto px-4 sm:px-6 py-20">
          <div className="text-center mb-14">
            <span className="section-label mb-4">Process</span>
            <h2 className="section-heading text-3xl sm:text-4xl text-gray-900 mt-4">{t('landing.how_title')}</h2>
            <SectionAccent className="mt-4 max-w-xs mx-auto" />
          </div>
          <div className="relative">
            {/* Connector line — desktop only */}
            <div className="hidden lg:block absolute top-8 left-[16%] right-[16%] h-0.5 bg-gradient-to-r from-blue-200 via-teal-200 to-blue-200 rounded-full" />
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
      <WaveDivider className="w-full text-gray-900 -mb-1" />
      <section className="relative overflow-hidden py-20">
        {/* Subtle network pattern background */}
        <NodeNetwork className="absolute inset-0 text-slate-300 opacity-40" />
        <div className="absolute inset-0 bg-gradient-to-b from-white/40 via-transparent to-white/60 pointer-events-none" />

        <div className="relative max-w-7xl mx-auto px-4 sm:px-6">
          <div className="text-center mb-14">
            <span className="section-label mb-4">Platform</span>
            <h2 className="section-heading text-3xl sm:text-4xl text-gray-900 mt-4 mb-4">{t('landing.features_title')}</h2>
            <p className="text-gray-500 max-w-lg mx-auto">{t('landing.features_subtitle')}</p>
            <SectionAccent className="mt-6 max-w-xs mx-auto" />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            <BespokeFeatureCard
              to="/campaigns" title={t('landing.feat_campaigns')} desc={t('landing.feat_campaigns_desc')}
              accentFrom="#2563EB" accentTo="#3B82F6" svgType="globe"
            />
            <BespokeFeatureCard
              to="/analytics" title={t('landing.feat_analytics')} desc={t('landing.feat_analytics_desc')}
              accentFrom="#059669" accentTo="#10B981" svgType="chart"
            />
            <BespokeFeatureCard
              to="/admin" title={t('landing.feat_admin')} desc={t('landing.feat_admin_desc')}
              accentFrom="#D97706" accentTo="#F59E0B" svgType="gear"
            />
            <BespokeFeatureCard
              to="/donate" title={t('landing.feat_donate')} desc={t('landing.feat_donate_desc')}
              accentFrom="#E11D48" accentTo="#F43F5E" svgType="heart"
            />
            <BespokeFeatureCard
              to="/register-ngo" title={t('landing.feat_ngo')} desc={t('landing.feat_ngo_desc')}
              accentFrom="#7C3AED" accentTo="#8B5CF6" svgType="building" hasMic
            />
            <BespokeFeatureCard
              to="/create-campaign" title={t('landing.feat_create')} desc={t('landing.feat_create_desc')}
              accentFrom="#0D9488" accentTo="#14B8A6" svgType="rocket" hasMic
            />
            <BespokeFeatureCard
              to="/field-agent" title={t('landing.feat_field')} desc={t('landing.feat_field_desc')}
              accentFrom="#0284C7" accentTo="#0EA5E9" svgType="camera"
              className="sm:col-start-1 lg:col-start-2"
            />
          </div>
        </div>
      </section>

      {/* ════════ TRUST PIPELINE ANIMATION ════════ */}
      <TrustPipeline />

      {/* ════════ FOR TESTERS — CTA ════════ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-blue-700 via-blue-600 to-teal-500 text-white">
        <HexGrid className="absolute inset-0 text-white" />
        <CircuitTrace className="absolute inset-0 w-full h-full text-white" />
        <GlowOrb className="absolute top-0 right-1/4 w-[300px] h-[300px]" color="#ffffff" />
        <div className="relative max-w-4xl mx-auto px-4 sm:px-6 py-20 text-center">
          <h2 className="section-heading text-2xl sm:text-4xl mb-4">{t('landing.tester_title')}</h2>
          <p className="text-white/70 max-w-xl mx-auto mb-10 text-lg">{t('landing.tester_desc')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center w-full sm:w-auto px-4 sm:px-0">
            <Link
              to="/register-ngo"
              className="w-full sm:w-auto text-center px-8 py-4 rounded-2xl bg-white text-blue-700 font-bold hover:bg-blue-50 transition shadow-lg shadow-blue-900/20"
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

const STAT_ACCENTS = {
  blue: { from: '#2563EB', to: '#3B82F6' },
  emerald: { from: '#059669', to: '#10B981' },
  amber: { from: '#D97706', to: '#F59E0B' },
  teal: { from: '#0D9488', to: '#14B8A6' },
};

function StatCard({ value, label, Icon, color = 'blue' }) {
  const accent = STAT_ACCENTS[color] || STAT_ACCENTS.blue;
  return (
    <div className="relative flex flex-col items-center text-center group">
      {/* Bespoke icon container with SVG ring */}
      <div className="relative w-14 h-14 mb-3">
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 56 56" fill="none">
          <circle cx="28" cy="28" r="26" stroke={accent.from} strokeWidth="1" opacity="0.15" />
          <circle cx="28" cy="28" r="22" stroke={accent.from} strokeWidth="0.5" strokeDasharray="3 4" opacity="0.10" className="group-hover:animate-spin" style={{ animationDuration: '8s' }} />
          <circle cx="28" cy="2" r="2" fill={accent.from} opacity="0.20" />
        </svg>
        <div className="absolute inset-[6px] rounded-xl flex items-center justify-center" style={{ background: `linear-gradient(135deg, ${accent.from}15, ${accent.to}10)` }}>
          <Icon className="w-5 h-5" style={{ color: accent.from }} />
        </div>
      </div>
      <div className="text-xl sm:text-2xl font-bold text-gray-900 font-display">{value}</div>
      <p className="text-xs text-gray-500 mt-0.5">{label}</p>
    </div>
  );
}

const STEP_COLORS = ['#2563EB', '#0D9488', '#7C3AED', '#E11D48'];

function StepCard({ step, Icon, title, desc }) {
  const accent = STEP_COLORS[(parseInt(step) - 1) % 4];
  return (
    <div className="relative text-center group">
      {/* Bespoke hexagonal node */}
      <div className="relative w-20 h-20 mx-auto mb-5">
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 80 80" fill="none">
          <polygon points="40,4 72,22 72,58 40,76 8,58 8,22" stroke={accent} strokeWidth="1.5" opacity="0.15" />
          <polygon points="40,12 64,26 64,54 40,68 16,54 16,26" fill={accent} opacity="0.06" />
          <circle cx="40" cy="4" r="2" fill={accent} opacity="0.25" />
          <circle cx="72" cy="22" r="1.5" fill={accent} opacity="0.15" />
          <circle cx="8" cy="22" r="1.5" fill={accent} opacity="0.15" />
        </svg>
        <div className="absolute inset-[12px] rounded-2xl flex items-center justify-center bg-white shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all" style={{ boxShadow: `0 8px 30px ${accent}20` }}>
          <Icon className="w-7 h-7" style={{ color: accent }} />
        </div>
      </div>
      <div className="inline-flex items-center justify-center w-7 h-7 rounded-lg mb-2 text-xs font-bold font-display text-white" style={{ background: `linear-gradient(135deg, ${accent}, ${accent}CC)` }}>{step}</div>
      <h3 className="font-semibold text-gray-900 mb-1 font-display">{title}</h3>
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
    <section className="relative max-w-5xl mx-auto px-4 sm:px-6 pt-16 pb-8">
      <div className="text-center mb-8">
        <span className="section-label mb-4">
          {t('landing.video_label', 'See It In Action')}
        </span>
        <h2 className="section-heading text-2xl sm:text-3xl text-gray-900 mt-4">
          {t('landing.video_title', 'Transparency You Can Watch')}
        </h2>
        <SectionAccent className="mt-4 max-w-xs mx-auto" />
      </div>

      <div className="relative rounded-2xl overflow-hidden shadow-2xl shadow-blue-200/40 border border-gray-100 bg-black group">
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
            <div className="w-10 h-10 border-4 border-blue-300 border-t-blue-600 rounded-full animate-spin" />
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
              <svg className="w-7 h-7 text-blue-700" fill="currentColor" viewBox="0 0 24 24">
                <rect x="6" y="4" width="4" height="16" rx="1" />
                <rect x="14" y="4" width="4" height="16" rx="1" />
              </svg>
            ) : (
              <HiOutlinePlayCircle className="w-9 h-9 text-blue-700" />
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
              <HiOutlineSpeakerWave className="w-5 h-5 text-blue-600" />
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

/* ─── Bespoke Feature Card — each type has a unique SVG decoration ─── */
const FEATURE_SVG = {
  globe: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <circle cx="40" cy="40" r="28" stroke={c} strokeWidth="1" opacity="0.15" />
      <circle cx="40" cy="40" r="18" stroke={c} strokeWidth="0.8" opacity="0.10" />
      <ellipse cx="40" cy="40" rx="10" ry="28" stroke={c} strokeWidth="0.7" opacity="0.12" />
      <path d="M12 40h56" stroke={c} strokeWidth="0.5" opacity="0.10" />
      <path d="M12 30h56M12 50h56" stroke={c} strokeWidth="0.3" opacity="0.08" />
      <circle cx="40" cy="12" r="2" fill={c} opacity="0.15" />
      <circle cx="40" cy="68" r="2" fill={c} opacity="0.15" />
    </svg>
  ),
  chart: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <rect x="10" y="45" width="8" height="25" rx="1" fill={c} opacity="0.08" />
      <rect x="22" y="30" width="8" height="40" rx="1" fill={c} opacity="0.10" />
      <rect x="34" y="20" width="8" height="50" rx="1" fill={c} opacity="0.12" />
      <rect x="46" y="35" width="8" height="35" rx="1" fill={c} opacity="0.09" />
      <rect x="58" y="15" width="8" height="55" rx="1" fill={c} opacity="0.11" />
      <path d="M10 42 L22 28 L34 18 L46 32 L58 12" stroke={c} strokeWidth="1.2" opacity="0.15" strokeLinejoin="round" />
      <circle cx="10" cy="42" r="2" fill={c} opacity="0.20" />
      <circle cx="34" cy="18" r="2" fill={c} opacity="0.20" />
      <circle cx="58" cy="12" r="2" fill={c} opacity="0.20" />
    </svg>
  ),
  gear: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <circle cx="40" cy="40" r="12" stroke={c} strokeWidth="1" opacity="0.15" />
      <circle cx="40" cy="40" r="5" fill={c} opacity="0.08" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((a, i) => {
        const rad = (a * Math.PI) / 180;
        const x1 = 40 + 15 * Math.cos(rad), y1 = 40 + 15 * Math.sin(rad);
        const x2 = 40 + 22 * Math.cos(rad), y2 = 40 + 22 * Math.sin(rad);
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={c} strokeWidth="3" strokeLinecap="round" opacity="0.12" />;
      })}
      <circle cx="40" cy="40" r="28" stroke={c} strokeWidth="0.5" strokeDasharray="3 5" opacity="0.08" />
    </svg>
  ),
  heart: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <path d="M40 65 C25 50 10 42 10 30 10 20 18 14 25 14 30 14 35 17 40 24 45 17 50 14 55 14 62 14 70 20 70 30 70 42 55 50 40 65Z"
        stroke={c} strokeWidth="1" opacity="0.12" />
      <path d="M40 58 C28 46 18 40 18 32 18 24 24 20 29 20 33 20 37 23 40 28 43 23 47 20 51 20 56 20 62 24 62 32 62 40 52 46 40 58Z"
        fill={c} opacity="0.06" />
      <circle cx="30" cy="28" r="3" fill={c} opacity="0.10" />
      <circle cx="50" cy="28" r="3" fill={c} opacity="0.10" />
      <path d="M20 55l-5 5M60 55l5 5" stroke={c} strokeWidth="0.5" opacity="0.08" />
    </svg>
  ),
  building: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <rect x="15" y="25" width="22" height="45" stroke={c} strokeWidth="0.8" opacity="0.12" />
      <rect x="37" y="15" width="28" height="55" stroke={c} strokeWidth="0.8" opacity="0.12" />
      {[30, 38, 46, 54].map(y => <g key={y}>
        <rect x="20" y={y} width="4" height="4" fill={c} opacity="0.08" />
        <rect x="28" y={y} width="4" height="4" fill={c} opacity="0.08" />
        <rect x="42" y={y} width="4" height="4" fill={c} opacity="0.08" />
        <rect x="50" y={y} width="4" height="4" fill={c} opacity="0.08" />
        <rect x="58" y={y} width="4" height="4" fill={c} opacity="0.08" />
      </g>)}
      <path d="M48 70v-8h6v8" stroke={c} strokeWidth="0.6" opacity="0.15" />
      <circle cx="51" cy="10" r="3" stroke={c} strokeWidth="0.5" opacity="0.10" />
    </svg>
  ),
  rocket: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <path d="M40 10 C40 10 30 25 30 45 L35 55 H45 L50 45 C50 25 40 10 40 10Z"
        stroke={c} strokeWidth="1" opacity="0.12" />
      <circle cx="40" cy="32" r="4" fill={c} opacity="0.10" />
      <path d="M30 45 L22 55 L30 50" stroke={c} strokeWidth="0.8" opacity="0.10" />
      <path d="M50 45 L58 55 L50 50" stroke={c} strokeWidth="0.8" opacity="0.10" />
      <path d="M35 58 L37 68 L40 62 L43 68 L45 58" stroke={c} strokeWidth="0.7" opacity="0.15" fill={c} fillOpacity="0.05" />
      {[0, 1, 2].map(i => <circle key={i} cx={40} cy={70 + i * 4} r={1.5 - i * 0.3} fill={c} opacity={0.12 - i * 0.03} />)}
    </svg>
  ),
  camera: (c) => (
    <svg viewBox="0 0 80 80" fill="none" className="w-full h-full">
      <rect x="12" y="28" width="56" height="38" rx="4" stroke={c} strokeWidth="0.8" opacity="0.12" />
      <path d="M28 28l4-10h16l4 10" stroke={c} strokeWidth="0.8" opacity="0.10" />
      <circle cx="40" cy="47" r="12" stroke={c} strokeWidth="1" opacity="0.12" />
      <circle cx="40" cy="47" r="7" stroke={c} strokeWidth="0.6" opacity="0.08" />
      <circle cx="40" cy="47" r="3" fill={c} opacity="0.10" />
      <circle cx="58" cy="34" r="2.5" fill={c} opacity="0.08" />
      <rect x="16" y="32" width="8" height="2" rx="1" fill={c} opacity="0.08" />
    </svg>
  ),
};

function BespokeFeatureCard({ to, title, desc, accentFrom, accentTo, svgType, hasMic, className = '' }) {
  const renderSvg = FEATURE_SVG[svgType];
  return (
    <Link
      to={to}
      className={`group relative block rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-6 overflow-hidden transition-all duration-500 hover:shadow-xl hover:shadow-black/[0.06] hover:-translate-y-1 hover:border-transparent ${className}`}
    >
      {/* Bespoke background SVG */}
      <div className="absolute -top-2 -right-2 w-32 h-32 pointer-events-none opacity-80 group-hover:opacity-100 transition-opacity duration-500">
        {renderSvg && renderSvg(accentFrom)}
      </div>

      {/* Gradient accent line at top */}
      <div className="absolute top-0 left-0 right-0 h-[2px] opacity-0 group-hover:opacity-100 transition-opacity duration-500"
        style={{ background: `linear-gradient(to right, ${accentFrom}, ${accentTo})` }} />

      {/* Corner accent */}
      <div className="absolute bottom-0 right-0 w-16 h-16 pointer-events-none">
        <svg viewBox="0 0 60 60" fill="none" className="w-full h-full">
          <path d="M60 0v60H0" stroke={accentFrom} strokeWidth="0.5" opacity="0.08" />
          <circle cx="60" cy="60" r="2" fill={accentFrom} opacity="0.12" />
        </svg>
      </div>

      {/* Icon */}
      <div className="relative w-14 h-14 rounded-2xl flex items-center justify-center mb-4 transition-all duration-500 group-hover:scale-105"
        style={{
          background: `linear-gradient(135deg, ${accentFrom}12, ${accentTo}08)`,
          boxShadow: `0 0 0 1px ${accentFrom}15`,
        }}
      >
        <div className="w-8 h-8" style={{ color: accentFrom }}>
          {renderSvg && (
            <svg viewBox="0 0 80 80" className="w-full h-full">
              <g transform="translate(15,15) scale(0.625)">
                {renderSvg(accentFrom).props.children}
              </g>
            </svg>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="relative">
        <div className="flex items-center gap-2 mb-2">
          <h3 className="font-display font-semibold text-gray-900 group-hover:text-gray-700 transition-colors">{title}</h3>
          {hasMic && (
            <span className="flex items-center gap-0.5 text-[10px] font-bold px-2 py-0.5 rounded-full uppercase font-display border"
              style={{ color: accentFrom, backgroundColor: `${accentFrom}08`, borderColor: `${accentFrom}20` }}>
              <HiOutlineMicrophone className="w-3 h-3" /> Voice
            </span>
          )}
        </div>
        <p className="text-sm text-gray-500 leading-relaxed">{desc}</p>
      </div>

      {/* Hover gradient overlay */}
      <div className="absolute inset-0 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-500 pointer-events-none"
        style={{ background: `linear-gradient(135deg, ${accentFrom}04, ${accentTo}06)` }} />
    </Link>
  );
}

function MediaCard({ campaign, t }) {
  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;

  const catKey = (campaign.category || '').toLowerCase();
  const CategoryIcon = CATEGORY_ICONS[catKey] || MdHandshake;
  const accent = MEDIA_CARD_ACCENTS[catKey] || MEDIA_CARD_ACCENTS._default;

  return (
    <Link
      to={`/campaign/${campaign.id}`}
      className="group relative block rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 overflow-hidden transition-all duration-500 hover:shadow-xl hover:shadow-black/[0.06] hover:-translate-y-1 hover:border-transparent"
    >
      {/* Gradient accent line */}
      <div className="h-[2px] w-full" style={{ background: `linear-gradient(to right, ${accent.from}, ${accent.to})` }} />

      {/* Video/Image preview */}
      <div className="relative aspect-video overflow-hidden" style={{ background: `linear-gradient(135deg, ${accent.from}, ${accent.to})` }}>
        {/* Bespoke SVG overlay */}
        <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 400 225" fill="none" preserveAspectRatio="none">
          <circle cx="350" cy="30" r="60" stroke="white" strokeWidth="0.5" opacity="0.15" />
          <circle cx="350" cy="30" r="35" stroke="white" strokeWidth="0.3" opacity="0.10" />
          <path d="M0 200 Q100 170 200 185 T400 160" stroke="white" strokeWidth="0.8" opacity="0.10" />
          <path d="M0 215 Q150 190 300 200 T400 180" stroke="white" strokeWidth="0.5" opacity="0.08" />
          <circle cx="50" cy="180" r="3" fill="white" opacity="0.15" />
          <circle cx="200" cy="190" r="2" fill="white" opacity="0.12" />
          <circle cx="350" cy="170" r="2.5" fill="white" opacity="0.12" />
        </svg>

        {campaign.has_video || campaign.video_cid ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <div className="w-16 h-16 rounded-2xl bg-white/90 backdrop-blur flex items-center justify-center shadow-xl group-hover:scale-110 transition-transform">
              <HiOutlinePlayCircle className="w-9 h-9" style={{ color: accent.from }} />
            </div>
            <span className="absolute bottom-3 left-3 bg-black/50 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-lg flex items-center gap-1.5">
              <HiOutlinePlayCircle className="w-3.5 h-3.5" />
              {t('campaign.watch_video')}
            </span>
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <CategoryIcon className="w-20 h-20 text-white/30" />
          </div>
        )}
        {campaign.category && (
          <span className="absolute top-3 left-3 bg-white/90 backdrop-blur-sm text-xs font-bold px-2.5 py-1 rounded-lg capitalize font-display" style={{ color: accent.from }}>
            {campaign.category}
          </span>
        )}
        {campaign.ngo_name && (
          <span className="absolute top-3 right-3 bg-black/40 backdrop-blur-sm text-white text-xs px-2.5 py-1 rounded-lg">
            {campaign.ngo_name}
          </span>
        )}
      </div>

      <div className="relative p-5">
        {/* Corner SVG accent */}
        <svg className="absolute bottom-0 right-0 w-20 h-20 pointer-events-none" viewBox="0 0 80 80" fill="none">
          <path d="M80 0v80H0" stroke={accent.from} strokeWidth="0.5" opacity="0.08" />
          <circle cx="80" cy="80" r="2" fill={accent.from} opacity="0.12" />
        </svg>

        <h3 className="font-bold text-gray-900 text-lg group-hover:text-gray-700 transition-colors line-clamp-2 mb-2 font-display">
          {campaign.title}
        </h3>
        {campaign.description && (
          <p className="text-sm text-gray-500 line-clamp-2 mb-4">{campaign.description}</p>
        )}

        <ProgressBar percentage={pct} className="mb-3" />

        <div className="flex justify-between items-baseline text-sm">
          <span className="font-bold" style={{ color: accent.from }}>${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}</span>
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

const MEDIA_CARD_ACCENTS = {
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

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}
