import { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listCampaigns } from '../api/campaigns';
import { getAnalyticsSummary } from '../api/analytics';
import ProgressBar from '../components/ProgressBar';
import VoiceButton from '../components/VoiceButton';
import { voiceSearchCampaigns } from '../api/voice';

/**
 * Landing — the rich homepage with hero, media showcase,
 * feature cards, live stats and featured campaigns.
 */
export default function Landing() {
  const { t } = useTranslation();
  const [featured, setFeatured] = useState([]);
  const [stats, setStats] = useState(null);
  const [loadingFeatured, setLoadingFeatured] = useState(true);

  useEffect(() => {
    listCampaigns({ page: 1, pageSize: 6, status: 'active', sort: 'most_funded' })
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
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-600 via-purple-600 to-pink-500 text-white">
        {/* Decorative blobs */}
        <div className="absolute -top-24 -right-24 w-96 h-96 bg-white/10 rounded-full blur-3xl" />
        <div className="absolute -bottom-20 -left-20 w-80 h-80 bg-pink-400/20 rounded-full blur-3xl" />

        <div className="relative max-w-6xl mx-auto px-4 py-20 sm:py-28 text-center">
          <div className="inline-flex items-center gap-2 bg-white/15 backdrop-blur rounded-full px-4 py-1.5 text-sm font-medium mb-6">
            <span className="text-lg">🎙️</span>
            {t('landing.badge')}
          </div>
          <h1 className="text-4xl sm:text-5xl lg:text-6xl font-extrabold tracking-tight mb-6 leading-tight">
            {t('landing.hero_title')}
          </h1>
          <p className="text-lg sm:text-xl text-white/80 max-w-2xl mx-auto mb-10">
            {t('landing.hero_subtitle')}
          </p>

          <div className="flex flex-col sm:flex-row gap-4 justify-center items-center">
            <Link
              to="/campaigns"
              className="px-8 py-3.5 rounded-xl bg-white text-indigo-700 font-bold text-lg shadow-lg hover:shadow-xl hover:-translate-y-0.5 transition-all"
            >
              {t('landing.explore_btn')}
            </Link>
            <VoiceButton
              apiCall={voiceSearchCampaigns}
              onResult={() => {}}
              className="!bg-white/20 !backdrop-blur !border-white/30 !text-white !hover:bg-white/30"
            />
          </div>
        </div>
      </section>

      {/* ════════ LIVE STATS BAR ════════ */}
      <section className="bg-white border-b border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-6 grid grid-cols-2 sm:grid-cols-4 gap-6 text-center">
          <StatCard value={stats?.started ?? '—'} label={t('landing.stat_conversations')} icon="💬" />
          <StatCard value={stats?.completed ?? '—'} label={t('landing.stat_completed')} icon="✅" />
          <StatCard
            value={stats?.completion_rate != null ? `${Math.round(stats.completion_rate)}%` : '—'}
            label={t('landing.stat_success_rate')}
            icon="📊"
          />
          <StatCard value={featured.length > 0 ? `${featured.length}+` : '—'} label={t('landing.stat_active_campaigns')} icon="🚀" />
        </div>
      </section>

      {/* ════════ MEDIA SHOWCASE — Featured Campaigns with Videos/Images ════════ */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold text-gray-900 mb-3">{t('landing.showcase_title')}</h2>
          <p className="text-gray-500 max-w-lg mx-auto">{t('landing.showcase_subtitle')}</p>
        </div>

        {loadingFeatured ? (
          <div className="text-center py-12 text-gray-400">{t('common.loading')}</div>
        ) : featured.length === 0 ? (
          <div className="text-center py-12 text-gray-400">{t('home.no_campaigns')}</div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {featured.map((c) => (
              <MediaCard key={c.id} campaign={c} t={t} />
            ))}
          </div>
        )}

        <div className="text-center mt-10">
          <Link
            to="/campaigns"
            className="inline-flex items-center gap-2 px-6 py-3 rounded-xl bg-indigo-50 text-indigo-700 font-semibold hover:bg-indigo-100 transition"
          >
            {t('landing.view_all_campaigns')} →
          </Link>
        </div>
      </section>

      {/* ════════ HOW IT WORKS ════════ */}
      <section className="bg-gray-50 border-y border-gray-100">
        <div className="max-w-6xl mx-auto px-4 py-16">
          <h2 className="text-3xl font-bold text-gray-900 text-center mb-12">{t('landing.how_title')}</h2>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-8">
            <StepCard step="1" icon="🎙️" title={t('landing.step1_title')} desc={t('landing.step1_desc')} />
            <StepCard step="2" icon="👁️" title={t('landing.step2_title')} desc={t('landing.step2_desc')} />
            <StepCard step="3" icon="💳" title={t('landing.step3_title')} desc={t('landing.step3_desc')} />
            <StepCard step="4" icon="📸" title={t('landing.step4_title')} desc={t('landing.step4_desc')} />
          </div>
        </div>
      </section>

      {/* ════════ PLATFORM FEATURES — App Cards Grid ════════ */}
      <section className="max-w-6xl mx-auto px-4 py-16">
        <h2 className="text-3xl font-bold text-gray-900 text-center mb-4">{t('landing.features_title')}</h2>
        <p className="text-gray-500 text-center max-w-lg mx-auto mb-12">{t('landing.features_subtitle')}</p>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          <FeatureCard
            to="/campaigns"
            icon="🔍"
            title={t('landing.feat_campaigns')}
            desc={t('landing.feat_campaigns_desc')}
            color="indigo"
          />
          <FeatureCard
            to="/analytics"
            icon="📊"
            title={t('landing.feat_analytics')}
            desc={t('landing.feat_analytics_desc')}
            color="emerald"
          />
          <FeatureCard
            to="/admin"
            icon="⚙️"
            title={t('landing.feat_admin')}
            desc={t('landing.feat_admin_desc')}
            color="amber"
          />
          <FeatureCard
            to="/donate"
            icon="💝"
            title={t('landing.feat_donate')}
            desc={t('landing.feat_donate_desc')}
            color="pink"
          />
          <FeatureCard
            to="/register-ngo"
            icon="🏛️"
            title={t('landing.feat_ngo')}
            desc={t('landing.feat_ngo_desc')}
            badge="🎤"
            color="blue"
          />
          <FeatureCard
            to="/create-campaign"
            icon="✨"
            title={t('landing.feat_create')}
            desc={t('landing.feat_create_desc')}
            badge="🎤"
            color="violet"
          />
          <FeatureCard
            to="/field-agent"
            icon="📸"
            title={t('landing.feat_field')}
            desc={t('landing.feat_field_desc')}
            color="teal"
          />
        </div>
      </section>

      {/* ════════ FOR TESTERS — Georgetown CTA ════════ */}
      <section className="bg-gradient-to-r from-indigo-600 to-purple-600 text-white">
        <div className="max-w-4xl mx-auto px-4 py-16 text-center">
          <h2 className="text-2xl sm:text-3xl font-bold mb-4">{t('landing.tester_title')}</h2>
          <p className="text-white/80 max-w-xl mx-auto mb-8">{t('landing.tester_desc')}</p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link
              to="/register-ngo"
              className="px-6 py-3 rounded-xl bg-white text-indigo-700 font-bold hover:bg-indigo-50 transition"
            >
              {t('landing.tester_register')}
            </Link>
            <Link
              to="/login"
              className="px-6 py-3 rounded-xl bg-white/20 text-white font-bold border border-white/30 hover:bg-white/30 transition"
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

function StatCard({ value, label, icon }) {
  return (
    <div>
      <div className="text-2xl font-bold text-gray-900">{icon} {value}</div>
      <p className="text-xs text-gray-500 mt-1">{label}</p>
    </div>
  );
}

function StepCard({ step, icon, title, desc }) {
  return (
    <div className="text-center">
      <div className="w-14 h-14 rounded-2xl bg-indigo-100 text-2xl flex items-center justify-center mx-auto mb-4">
        {icon}
      </div>
      <div className="text-xs font-bold text-indigo-500 uppercase mb-1">Step {step}</div>
      <h3 className="font-semibold text-gray-900 mb-1">{title}</h3>
      <p className="text-sm text-gray-500">{desc}</p>
    </div>
  );
}

function FeatureCard({ to, icon, title, desc, badge, color = 'indigo' }) {
  const bg = {
    indigo: 'bg-indigo-50 hover:bg-indigo-100 border-indigo-100',
    emerald: 'bg-emerald-50 hover:bg-emerald-100 border-emerald-100',
    amber: 'bg-amber-50 hover:bg-amber-100 border-amber-100',
    pink: 'bg-pink-50 hover:bg-pink-100 border-pink-100',
    blue: 'bg-blue-50 hover:bg-blue-100 border-blue-100',
    violet: 'bg-violet-50 hover:bg-violet-100 border-violet-100',
    teal: 'bg-teal-50 hover:bg-teal-100 border-teal-100',
  };

  return (
    <Link
      to={to}
      className={`block rounded-2xl border p-6 transition-all hover:-translate-y-0.5 hover:shadow-md ${bg[color] || bg.indigo}`}
    >
      <div className="flex items-center gap-3 mb-3">
        <span className="text-3xl">{icon}</span>
        <h3 className="font-semibold text-gray-900">{title}</h3>
        {badge && <span className="text-lg">{badge}</span>}
      </div>
      <p className="text-sm text-gray-600">{desc}</p>
    </Link>
  );
}

function MediaCard({ campaign, t }) {
  const pct = campaign.goal_amount_usd > 0
    ? Math.min(100, ((campaign.current_usd_total || campaign.raised_amount_usd) / campaign.goal_amount_usd) * 100)
    : 0;

  const categoryEmoji = {
    water: '💧', education: '📚', health: '🏥', infrastructure: '🏗️',
    food: '🍲', environment: '🌿', shelter: '🏠', children: '👶',
  };

  return (
    <Link
      to={`/campaign/${campaign.id}`}
      className="group block bg-white rounded-2xl shadow-sm hover:shadow-lg transition-all hover:-translate-y-1 overflow-hidden border border-gray-100"
    >
      {/* Video/Image preview area */}
      <div className="relative aspect-video bg-gradient-to-br from-indigo-500 to-purple-600 overflow-hidden">
        {campaign.has_video || campaign.video_cid ? (
          <div className="absolute inset-0 flex items-center justify-center bg-black/20">
            <div className="w-16 h-16 rounded-full bg-white/90 flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform">
              <svg className="w-7 h-7 text-indigo-600 ml-1" fill="currentColor" viewBox="0 0 24 24">
                <path d="M8 5v14l11-7z" />
              </svg>
            </div>
            <span className="absolute bottom-3 left-3 bg-black/60 text-white text-xs px-2 py-1 rounded-full flex items-center gap-1">
              🎥 {t('campaign.watch_video')}
            </span>
          </div>
        ) : (
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-7xl opacity-60">
              {categoryEmoji[(campaign.category || '').toLowerCase()] || '🤝'}
            </span>
          </div>
        )}
        {campaign.category && (
          <span className="absolute top-3 left-3 bg-white/90 text-xs font-semibold text-indigo-700 px-2 py-0.5 rounded-full capitalize">
            {campaign.category}
          </span>
        )}
        {campaign.ngo_name && (
          <span className="absolute top-3 right-3 bg-black/50 text-white text-xs px-2 py-0.5 rounded-full">
            {campaign.ngo_name}
          </span>
        )}
      </div>

      <div className="p-5">
        <h3 className="font-bold text-gray-900 text-lg group-hover:text-indigo-600 transition-colors line-clamp-2 mb-2">
          {campaign.title}
        </h3>
        {campaign.description && (
          <p className="text-sm text-gray-500 line-clamp-2 mb-3">{campaign.description}</p>
        )}

        <ProgressBar percentage={pct} className="mb-2" />

        <div className="flex justify-between items-baseline text-sm">
          <span className="font-bold text-indigo-600">
            ${fmt(campaign.current_usd_total || campaign.raised_amount_usd)}
          </span>
          <span className="text-gray-400">
            {t('campaign.raised_of')} ${fmt(campaign.goal_amount_usd)}
          </span>
        </div>

        {(campaign.donation_count > 0 || campaign.location_gps) && (
          <div className="flex items-center gap-3 mt-2 text-xs text-gray-400">
            {campaign.donation_count > 0 && (
              <span>👥 {campaign.donation_count} {t('campaign.donors')}</span>
            )}
            {campaign.location_gps && (
              <span>📍 GPS Verified</span>
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
