import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { getAnalyticsSummary, getConversationMetrics, getFunnel, getConversationEvents } from '../api/analytics';

import {
  HiOutlineChatBubbleLeftRight, HiOutlineCheckBadge,
  HiOutlineArrowRightOnRectangle, HiOutlineChartBarSquare,
  HiOutlineArrowTrendingUp, HiOutlineArrowTrendingDown,
  HiOutlineMicrophone, HiOutlineEye, HiOutlineCreditCard,
  MdOutlineBookmarkAdded, MdOutlineAttachMoney, MdOutlinePushPin,
} from '../components/icons';
import { PageBg, PageHeader } from '../components/SvgDecorations';
import HexIcon from '../components/HexIcon';

const PERIODS = [
  { label: '7d', days: 7 },
  { label: '30d', days: 30 },
  { label: '90d', days: 90 },
];

export default function Analytics() {
  const { t } = useTranslation();
  const [days, setDays] = useState(7);
  const [summary, setSummary] = useState(null);
  const [metrics, setMetrics] = useState(null);
  const [funnel, setFunnel] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [s, m, f, e] = await Promise.all([
        getAnalyticsSummary({ days }).catch(() => null),
        getConversationMetrics({ days }).catch(() => null),
        getFunnel({ days }).catch(() => null),
        getConversationEvents({ limit: 15 }).catch(() => []),
      ]);
      setSummary(s);
      setMetrics(m);
      setFunnel(f);
      setEvents(Array.isArray(e) ? e : e?.events || []);
    } finally {
      setLoading(false);
    }
  }, [days]);

  useEffect(() => { load(); }, [load]);

  return (
    <PageBg pattern="nodes" colorA="#10B981" colorB="#0D9488">
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <PageHeader icon={HiOutlineChartBarSquare} title={t('analytics.title')} subtitle={t('analytics.subtitle')} accentColor="green" bespoke="chart" />

        <div className="flex items-center gap-3">
          {/* Period selector */}
          <div className="flex bg-white/60 backdrop-blur-sm rounded-lg p-1 border border-gray-200/50 shadow-sm">
            {PERIODS.map((p) => (
              <button
                key={p.days}
                onClick={() => setDays(p.days)}
                className={`px-3 py-2 rounded-md text-xs font-medium transition font-display ${
                  days === p.days ? 'bg-white shadow text-emerald-600' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-20 text-gray-400">{t('common.loading')}</div>
      ) : (
        <>
          {/* Summary cards */}
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
            <SummaryCard
              title={t('analytics.conversations')}
              value={summary?.started ?? '-'}
              Icon={HiOutlineChatBubbleLeftRight}
              color="blue"
              change={summary?.previous_period ? calcChange(summary.started, summary.previous_period.started) : null}
            />
            <SummaryCard
              title={t('analytics.completed')}
              value={summary?.completed ?? '-'}
              Icon={HiOutlineCheckBadge}
              color="emerald"
              change={summary?.previous_period ? calcChange(summary.completed, summary.previous_period.completed) : null}
            />
            <SummaryCard
              title={t('analytics.abandoned')}
              value={summary?.abandoned ?? '-'}
              Icon={HiOutlineArrowRightOnRectangle}
              color="amber"
            />
            <SummaryCard
              title={t('analytics.success_rate')}
              value={summary?.completion_rate != null ? `${Math.round(summary.completion_rate)}%` : '-'}
              Icon={HiOutlineChartBarSquare}
              color="green"
            />
          </div>

          {/* Two-column: Funnel + Recent events */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Funnel */}
            <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-emerald-500 via-green-500 to-transparent" />
              <svg className="absolute top-2 right-2 w-28 h-28 pointer-events-none" viewBox="0 0 112 112" fill="none">
                <path d="M30 20 L82 20 L72 50 L40 50 Z" stroke="#10B981" strokeWidth="0.5" opacity="0.05" />
                <path d="M40 55 L72 55 L65 80 L47 80 Z" stroke="#14B8A6" strokeWidth="0.5" opacity="0.05" />
                <path d="M47 85 L65 85 L60 100 L52 100 Z" stroke="#059669" strokeWidth="0.5" opacity="0.05" />
                <circle cx="56" cy="18" r="1.5" fill="#10B981" opacity="0.08" />
              </svg>
              <h2 className="relative font-semibold text-gray-900 mb-4 font-display">{t('analytics.donation_funnel')}</h2>
              {funnel ? (
                <div className="space-y-3">
                  {funnel.funnel && Object.entries(funnel.funnel).map(([stepName, data], i, arr) => (
                    <FunnelRow key={stepName} step={{ stage: stepName, count: data.count, drop_off: data.drop_off }} maxValue={arr[0]?.[1]?.count || 1} />
                  ))}
                  {funnel.overall_conversion != null && (
                    <div className="pt-3 border-t border-gray-100 text-center">
                      <span className="text-2xl font-bold text-emerald-600">{Math.round(funnel.overall_conversion)}%</span>
                      <p className="text-xs text-gray-400 mt-1">{t('analytics.conversion_rate')}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">{t('analytics.no_funnel')}</p>
              )}
            </div>

            {/* Recent events */}
            <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-green-500 to-transparent" />
              <svg className="absolute top-2 right-2 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
                <circle cx="65" cy="30" r="8" stroke="#0D9488" strokeWidth="0.5" opacity="0.06" />
                <circle cx="65" cy="30" r="3" fill="#0D9488" opacity="0.04" />
                <path d="M55 30 L40 30 L40 22" stroke="#0D9488" strokeWidth="0.5" opacity="0.05" />
                <path d="M65 40 L65 55 L75 55" stroke="#0D9488" strokeWidth="0.5" opacity="0.05" />
                <circle cx="40" cy="22" r="1.5" fill="#0D9488" opacity="0.07" />
                <circle cx="75" cy="55" r="1.5" fill="#0D9488" opacity="0.07" />
              </svg>
              <h2 className="relative font-semibold text-gray-900 mb-4 font-display">{t('analytics.recent_events')}</h2>
              {events.length > 0 ? (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {events.map((ev, i) => (
                    <div key={i} className="flex items-start gap-3 text-sm py-2.5 border-b border-gray-50 last:border-0">
                      <HexIcon Icon={EVENT_ICON_MAP[ev.event_type] || MdOutlinePushPin} accent="#10B981" size="sm" spin={false} />
                      <div className="flex-1 min-w-0">
                        <p className="text-gray-700 font-medium truncate">{ev.event_type}</p>
                        {ev.details && (
                          <p className="text-gray-400 text-xs truncate">{JSON.stringify(ev.details)}</p>
                        )}
                      </div>
                      <span className="text-xs text-gray-400 whitespace-nowrap">
                        {ev.created_at ? new Date(ev.created_at).toLocaleTimeString() : ''}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">{t('analytics.no_events')}</p>
              )}
            </div>
          </div>

          {/* Daily metrics (simple text grid if metrics available) */}
          {metrics?.daily_metrics && (
            <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-6 overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[2px] bg-gradient-to-r from-green-500 via-emerald-500 to-transparent" />
              <svg className="absolute top-2 right-2 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
                <rect x="54" y="28" width="6" height="16" rx="1" stroke="#14B8A6" strokeWidth="0.4" opacity="0.06" />
                <rect x="64" y="18" width="6" height="26" rx="1" stroke="#14B8A6" strokeWidth="0.4" opacity="0.06" />
                <rect x="74" y="22" width="6" height="22" rx="1" stroke="#14B8A6" strokeWidth="0.4" opacity="0.06" />
                <path d="M52 46 L82 46" stroke="#14B8A6" strokeWidth="0.5" opacity="0.06" />
              </svg>
              <h2 className="relative font-semibold text-gray-900 mb-4 font-display">{t('analytics.daily_breakdown')}</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 border-b border-gray-100">
                      <th className="pb-2 font-medium">{t('analytics.date')}</th>
                      <th className="pb-2 font-medium text-right">{t('analytics.conversations')}</th>
                      <th className="pb-2 font-medium text-right">{t('analytics.completed')}</th>
                      <th className="pb-2 font-medium text-right">{t('analytics.abandoned')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.daily_metrics.map((row, i) => (
                      <tr key={i} className="border-b border-gray-50 last:border-0">
                        <td className="py-2 text-gray-700">{row.date}</td>
                        <td className="py-2 text-right text-gray-600">{row.started || 0}</td>
                        <td className="py-2 text-right text-gray-600">{row.completed || 0}</td>
                        <td className="py-2 text-right font-medium text-amber-600">{row.abandoned || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>    </PageBg>  );
}

/* ── Sub-components ──────────────────────── */

const SUMMARY_SVGS = {
  blue: (
    <svg className="absolute -top-1 -right-1 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
      <circle cx="70" cy="26" r="22" stroke="#10B981" strokeWidth="0.5" opacity="0.07" />
      <circle cx="70" cy="26" r="12" stroke="#10B981" strokeWidth="0.4" strokeDasharray="2 3" opacity="0.05" />
      <path d="M58 38 L70 26 L82 38" stroke="#10B981" strokeWidth="0.5" opacity="0.06" />
      <circle cx="70" cy="26" r="2" fill="#10B981" opacity="0.08" />
    </svg>
  ),
  emerald: (
    <svg className="absolute -top-1 -right-1 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
      <path d="M60 40 L70 15 L80 40" stroke="#059669" strokeWidth="0.5" opacity="0.07" />
      <path d="M62 36 L70 18 L78 36" stroke="#059669" strokeWidth="0.4" strokeDasharray="3 2" opacity="0.05" />
      <circle cx="70" cy="15" r="2" fill="#059669" opacity="0.08" />
      <path d="M65 40 L75 40" stroke="#059669" strokeWidth="0.5" opacity="0.06" />
    </svg>
  ),
  amber: (
    <svg className="absolute -top-1 -right-1 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
      <rect x="56" y="12" width="28" height="28" rx="4" stroke="#D97706" strokeWidth="0.5" opacity="0.06" />
      <path d="M70 18 L70 34" stroke="#D97706" strokeWidth="0.5" strokeDasharray="2 2" opacity="0.05" />
      <path d="M62 26 L78 26" stroke="#D97706" strokeWidth="0.5" strokeDasharray="2 2" opacity="0.05" />
      <circle cx="70" cy="26" r="2" fill="#D97706" opacity="0.08" />
    </svg>
  ),
  green: (
    <svg className="absolute -top-1 -right-1 w-24 h-24 pointer-events-none" viewBox="0 0 96 96" fill="none">
      <circle cx="70" cy="26" r="20" stroke="#16A34A" strokeWidth="0.5" opacity="0.07" />
      <path d="M70 26 L70 10" stroke="#16A34A" strokeWidth="0.6" opacity="0.08" />
      <path d="M70 26 L84 32" stroke="#16A34A" strokeWidth="0.6" opacity="0.08" />
      <circle cx="70" cy="10" r="1.5" fill="#16A34A" opacity="0.10" />
      <circle cx="84" cy="32" r="1.5" fill="#16A34A" opacity="0.10" />
    </svg>
  ),
};

const SUMMARY_ACCENTS = { blue: '#10B981', emerald: '#059669', amber: '#D97706', green: '#16A34A' };

function SummaryCard({ title, value, Icon, color = 'blue', change }) {
  const colors = { blue: 'bg-emerald-50 text-emerald-600', emerald: 'bg-emerald-50 text-emerald-600', amber: 'bg-amber-50 text-amber-600', green: 'bg-green-50 text-green-600' };
  const accent = SUMMARY_ACCENTS[color] || '#10B981';
  return (
    <div className="relative rounded-2xl bg-white/80 backdrop-blur-sm border border-gray-100 p-4 sm:p-5 overflow-hidden group transition-all hover:shadow-md hover:border-transparent">
      {/* Top accent line */}
      <div className="absolute top-0 left-0 right-0 h-[2px]" style={{ background: `linear-gradient(to right, ${accent}, ${accent}60)` }} />
      {/* Bespoke SVG */}
      {SUMMARY_SVGS[color]}
      {/* Corner node */}
      <svg className="absolute bottom-0 left-0 w-10 h-10 pointer-events-none" viewBox="0 0 40 40" fill="none">
        <path d="M0 40V20" stroke={accent} strokeWidth="0.5" opacity="0.05" />
        <path d="M0 40H20" stroke={accent} strokeWidth="0.5" opacity="0.05" />
        <circle cx="0" cy="40" r="1.5" fill={accent} opacity="0.06" />
      </svg>
      <div className="relative flex items-center gap-2 sm:gap-2.5 mb-3">
        <HexIcon Icon={Icon} accent={accent} size="sm" spin={false} />
        <span className="text-sm text-gray-500 font-medium">{title}</span>
      </div>
      <div className="relative flex items-baseline gap-2">
        <span className="text-xl sm:text-2xl font-bold text-gray-900">{value}</span>
        {change != null && (
          <span className={`flex items-center gap-0.5 text-xs font-medium ${change >= 0 ? 'text-green-600' : 'text-red-500'}`}>
            {change >= 0 ? <HiOutlineArrowTrendingUp className="w-3.5 h-3.5" /> : <HiOutlineArrowTrendingDown className="w-3.5 h-3.5" />}
            {Math.abs(change)}%
          </span>
        )}
      </div>
    </div>
  );
}

function FunnelRow({ step, maxValue }) {
  const pct = maxValue > 0 ? (step.count / maxValue) * 100 : 0;
  return (
    <div>
      <div className="flex justify-between text-sm mb-1">
        <span className="text-gray-700 font-medium capitalize">{step.stage || step.step}</span>
        <div className="flex items-center gap-2">
          <span className="text-gray-500">{step.count}</span>
          {step.drop_off != null && step.drop_off > 0 && (
            <span className="text-xs text-red-400">-{step.drop_off}</span>
          )}
        </div>
      </div>
      <div className="w-full bg-gray-100 rounded-full h-2">
        <div
          className="h-full rounded-full bg-gradient-to-r from-emerald-500 to-green-500 transition-all duration-500"
          style={{ width: `${pct}%` }}
        />
      </div>
    </div>
  );
}

function calcChange(current, previous) {
  if (!previous || previous === 0) return null;
  return Math.round(((current - previous) / previous) * 100);
}

const EVENT_ICON_MAP = {
  conversation_started: HiOutlineChatBubbleLeftRight,
  donation_completed: MdOutlineAttachMoney,
  donation_initiated: HiOutlineCreditCard,
  voice_search: HiOutlineMicrophone,
  campaign_viewed: HiOutlineEye,
  registration: MdOutlineBookmarkAdded,
};

function EventIcon({ type }) {
  const Comp = EVENT_ICON_MAP[type] || MdOutlinePushPin;
  return <Comp className="w-5 h-5 text-emerald-500" />;
}
