import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listCampaigns } from '../api/campaigns';
import CampaignCard from '../components/CampaignCard';
import SkeletonCard from '../components/SkeletonCard';
import {
  HiOutlineMagnifyingGlass, HiOutlineSparkles, HiOutlineGlobeAlt,
  HiOutlineShieldCheck, HiOutlineCheckBadge, HiOutlineEye,
  HiOutlineFingerPrint, HiOutlineBuildingOffice2,
  HiOutlineArrowRight, HiOutlineMicrophone,
} from '../components/icons';
import { PageBg, PageHeader, SectionAccent, TopographyBg, NodeNetwork } from '../components/SvgDecorations';

const CATEGORIES = ['all', 'water', 'education', 'health', 'infrastructure', 'food', 'environment', 'shelter'];
const SORT_OPTIONS = ['newest', 'oldest', 'most_funded', 'goal_high', 'goal_low'];

export default function Home() {
  const { t } = useTranslation();
  const [campaigns, setCampaigns] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [category, setCategory] = useState('all');
  const [sort, setSort] = useState('newest');
  const [loading, setLoading] = useState(true);

  const load = useCallback(async (p = 1, append = false) => {
    setLoading(true);
    try {
      const data = await listCampaigns({
        page: p,
        pageSize: 6,
        status: 'active',
        category: category === 'all' ? undefined : category,
        search: search || undefined,
        sort,
      });
      if (data.items) {
        setCampaigns(append ? (prev) => [...prev, ...data.items] : data.items);
        setTotal(data.total);
      } else {
        // Legacy flat-list response
        setCampaigns(Array.isArray(data) ? data : []);
        setTotal(Array.isArray(data) ? data.length : 0);
      }
    } catch {
      setCampaigns([]);
    } finally {
      setLoading(false);
    }
  }, [category, search, sort]);

  useEffect(() => {
    setPage(1);
    load(1);
  }, [load]);

  const loadMore = () => {
    const next = page + 1;
    setPage(next);
    load(next, true);
  };

  return (
    <PageBg pattern="topography">
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Hero */}
      <PageHeader icon={HiOutlineGlobeAlt} title={t('home.hero_title')} subtitle={t('home.hero_subtitle')} accentColor="blue" bespoke="globe" />

      {/* Search */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('home.search_placeholder')}
            className="w-full pl-10 pr-4 py-3 rounded-2xl border border-gray-200/80 bg-white/80 backdrop-blur-sm text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent transition-all"
          />
          <HiOutlineMagnifyingGlass className="absolute left-3.5 top-3.5 h-4 w-4 text-gray-400" />
        </div>
        <Link
          to="/assistant"
          className="group flex items-center justify-center gap-2 px-5 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 text-white text-sm font-medium hover:shadow-lg hover:shadow-indigo-500/25 transition-all"
        >
          <HiOutlineSparkles className="w-4 h-4" />
          {t('home.ask_assistant', 'Ask the Assistant')}
          <HiOutlineArrowRight className="w-3.5 h-3.5 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all" />
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-8">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-4 py-2 rounded-full text-xs font-medium border transition-all capitalize
              ${cat === category
                ? 'bg-indigo-600 text-white border-indigo-600 shadow-md shadow-indigo-500/20'
                : 'bg-white/80 backdrop-blur-sm text-gray-600 border-gray-200/80 hover:border-indigo-300 hover:bg-indigo-50/60'}`}
          >
            {cat === 'all' ? t('home.filter_all') : cat}
          </button>
        ))}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="ml-auto text-sm border border-gray-200/80 bg-white/80 backdrop-blur-sm rounded-xl px-3 py-2"
        >
          {SORT_OPTIONS.map((s) => (
            <option key={s} value={s}>{t(`home.sort_${s}`)}</option>
          ))}
        </select>
      </div>

      {/* Campaign grid */}
      {loading && campaigns.length === 0 ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
          {[...Array(6)].map((_, i) => <SkeletonCard key={i} />)}
        </div>
      ) : campaigns.length === 0 ? (
        <div className="text-center py-20 text-gray-400">{t('home.no_campaigns')}</div>
      ) : (
        <>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
            {campaigns.map((c) => (
              <CampaignCard key={c.id} campaign={c} />
            ))}
          </div>
          {campaigns.length < total && (
            <div className="text-center mt-8">
              <button
                onClick={loadMore}
                disabled={loading}
                className="group inline-flex items-center gap-2 px-6 py-2.5 rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-200/80 text-sm font-medium text-gray-700 hover:bg-indigo-50/60 hover:border-indigo-200 transition-all"
              >
                {loading ? t('common.loading') : t('home.load_more')}
                <HiOutlineArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
              </button>
            </div>
          )}
        </>
      )}

      {/* ════════ AGENT VERIFICATION PROCESS ════════ */}
      <section className="relative mt-16 mb-8 overflow-hidden">
        <div className="absolute inset-0 -z-10 pointer-events-none" aria-hidden="true">
          <TopographyBg className="absolute inset-0 text-indigo-400 opacity-40" />
          <div className="absolute top-0 right-0 w-64 h-64 rounded-full opacity-[0.04]" style={{ background: 'radial-gradient(circle, #6366F1, transparent 70%)' }} />
          <div className="absolute bottom-0 left-0 w-48 h-48 rounded-full opacity-[0.03]" style={{ background: 'radial-gradient(circle, #A855F7, transparent 70%)' }} />
        </div>

        <div className="text-center mb-12">
          <span className="inline-block text-[10px] font-bold tracking-[0.2em] uppercase text-indigo-600 bg-indigo-50/80 px-4 py-1.5 rounded-full border border-indigo-100/60 mb-4">
            Trust & Verification
          </span>
          <h2 className="font-display text-2xl sm:text-3xl font-bold text-gray-900">How We Verify Every Campaign</h2>
          <p className="text-gray-500 text-sm mt-2 max-w-lg mx-auto">
            Our AI-powered agent verification ensures every campaign is legitimate, transparent, and blockchain-tracked
          </p>
          <SectionAccent className="mt-4 max-w-xs mx-auto" />
        </div>

        {/* Verification Steps — hexagonal node design (like Landing StepCards) */}
        <div className="relative">
          {/* Connector line — desktop only */}
          <div className="hidden lg:block absolute top-10 left-[10%] right-[10%] h-0.5 bg-gradient-to-r from-indigo-200 via-violet-200 to-indigo-200 rounded-full" />

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-6">
            <VerificationStep
              step="1"
              Icon={HiOutlineBuildingOffice2}
              title="NGO Registration"
              desc="Organizations submit verified credentials and mission details"
              accent="#6366F1"
              svgType="building"
            />
            <VerificationStep
              step="2"
              Icon={HiOutlineFingerPrint}
              title="Identity Verification"
              desc="AI agent validates identity documents and cross-references records"
              accent="#7C3AED"
              svgType="fingerprint"
            />
            <VerificationStep
              step="3"
              Icon={HiOutlineEye}
              title="Campaign Review"
              desc="Each campaign is audited for legitimacy, goals, and feasibility"
              accent="#A855F7"
              svgType="eye"
            />
            <VerificationStep
              step="4"
              Icon={HiOutlineShieldCheck}
              title="Blockchain Seal"
              desc="Approved campaigns receive an immutable on-chain verification stamp"
              accent="#E11D48"
              svgType="shield"
            />
            <VerificationStep
              step="5"
              Icon={HiOutlineCheckBadge}
              title="Continuous Monitoring"
              desc="AI agents monitor fund usage and flag anomalies in real-time"
              accent="#D97706"
              svgType="badge"
            />
          </div>
        </div>

        {/* CTA row */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mt-12">
          <Link
            to="/register-ngo"
            className="group inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-200/80 text-sm font-semibold text-gray-700 hover:bg-indigo-50/60 hover:border-indigo-200 transition-all"
          >
            <HiOutlineBuildingOffice2 className="w-4 h-4 text-indigo-600" />
            Register Your NGO
            <HiOutlineArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            to="/assistant"
            className="group inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-gradient-to-r from-indigo-600 to-violet-600 text-sm font-semibold text-white shadow-lg shadow-indigo-500/20 hover:shadow-xl hover:shadow-indigo-500/30 transition-all"
          >
            <HiOutlineMicrophone className="w-4 h-4" />
            Ask the AI Agent
            <HiOutlineArrowRight className="w-3.5 h-3.5 opacity-70 group-hover:translate-x-0.5 transition-transform" />
          </Link>
        </div>
      </section>
    </div>
    </PageBg>
  );
}

/* ─── Verification Step Card — hexagonal node + bespoke SVG ─── */
const STEP_SVGS = {
  building: (c) => (
    <>
      <rect x="26" y="20" width="12" height="30" stroke={c} strokeWidth="0.8" fill="none" opacity="0.15" />
      <rect x="42" y="14" width="14" height="36" stroke={c} strokeWidth="0.8" fill="none" opacity="0.15" />
      {[24, 30, 36, 42].map(y => <g key={y}><rect x="29" y={y} width="2.5" height="2.5" fill={c} opacity="0.10" /><rect x="45" y={y} width="2.5" height="2.5" fill={c} opacity="0.10" /><rect x="50" y={y} width="2.5" height="2.5" fill={c} opacity="0.10" /></g>)}
    </>
  ),
  fingerprint: (c) => (
    <>
      <circle cx="40" cy="40" r="16" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M32 32c0-6 4-10 8-10s8 4 8 10c0 8-2 16-6 22" stroke={c} strokeWidth="0.8" fill="none" opacity="0.15" />
      <path d="M36 34c0-3.5 2-6 4-6s4 2.5 4 6c0 5-1 10-3 14" stroke={c} strokeWidth="0.6" fill="none" opacity="0.12" />
      <path d="M39 36c0-1 .5-2 1-2s1 1 1 2c0 3-.5 6-1 8" stroke={c} strokeWidth="0.5" fill="none" opacity="0.10" />
    </>
  ),
  eye: (c) => (
    <>
      <ellipse cx="40" cy="40" rx="20" ry="12" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" />
      <circle cx="40" cy="40" r="7" stroke={c} strokeWidth="0.8" fill="none" opacity="0.15" />
      <circle cx="40" cy="40" r="3" fill={c} opacity="0.10" />
      <path d="M20 40c6-10 14-14 20-14s14 4 20 14" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M20 40c6 10 14 14 20 14s14-4 20-14" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
    </>
  ),
  shield: (c) => (
    <>
      <path d="M40 16c-8 4-16 6-20 6v18c0 10 8 18 20 24 12-6 20-14 20-24V22c-4 0-12-2-20-6z" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" />
      <path d="M40 22c-6 3-12 4.5-15 4.5v13.5c0 7.5 6 13.5 15 18 9-4.5 15-10.5 15-18V26.5c-3 0-9-1.5-15-4.5z" fill={c} opacity="0.04" />
      <path d="M34 40l4 4 8-8" stroke={c} strokeWidth="1.2" fill="none" opacity="0.20" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  badge: (c) => (
    <>
      <circle cx="40" cy="36" r="14" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" />
      <circle cx="40" cy="36" r="8" stroke={c} strokeWidth="0.5" strokeDasharray="2 3" fill="none" opacity="0.08" />
      <path d="M36 36l3 3 6-6" stroke={c} strokeWidth="1" fill="none" opacity="0.18" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M30 50l-4 10 14-4 14 4-4-10" stroke={c} strokeWidth="0.6" fill="none" opacity="0.10" />
    </>
  ),
};

function VerificationStep({ step, Icon, title, desc, accent, svgType }) {
  return (
    <div className="relative text-center group">
      {/* Hexagonal node container */}
      <div className="relative w-20 h-20 mx-auto mb-4">
        <svg className="absolute inset-0 w-full h-full" viewBox="0 0 80 80" fill="none">
          {/* Outer hex */}
          <polygon points="40,4 72,22 72,58 40,76 8,58 8,22" stroke={accent} strokeWidth="1.5" opacity="0.15" />
          {/* Inner hex fill */}
          <polygon points="40,12 64,26 64,54 40,68 16,54 16,26" fill={accent} opacity="0.06" />
          {/* Corner nodes */}
          <circle cx="40" cy="4" r="2" fill={accent} opacity="0.25" />
          <circle cx="72" cy="22" r="1.5" fill={accent} opacity="0.15" />
          <circle cx="8" cy="22" r="1.5" fill={accent} opacity="0.15" />
          {/* Bespoke inner SVG */}
          {STEP_SVGS[svgType]?.(accent)}
          {/* Spinning dashed orbit */}
          <circle cx="40" cy="40" r="35" stroke={accent} strokeWidth="0.4" strokeDasharray="3 6" opacity="0.08" className="origin-center" style={{ animation: 'spin 20s linear infinite' }} />
        </svg>
        <div className="absolute inset-[12px] rounded-2xl flex items-center justify-center bg-white shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all duration-300" style={{ boxShadow: `0 8px 30px ${accent}20` }}>
          <Icon className="w-7 h-7" style={{ color: accent }} />
        </div>
      </div>
      <div className="inline-flex items-center justify-center w-7 h-7 rounded-lg mb-2 text-xs font-bold font-display text-white" style={{ background: `linear-gradient(135deg, ${accent}, ${accent}CC)` }}>{step}</div>
      <h3 className="font-semibold text-gray-900 mb-1 font-display text-sm">{title}</h3>
      <p className="text-xs text-gray-500 leading-relaxed">{desc}</p>
    </div>
  );
}
