import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { getAnalyticsSummary, getConversationMetrics, getFunnel, getConversationEvents } from '../api/analytics';
import VoiceButton from '../components/VoiceButton';
import { voiceSearchCampaigns } from '../api/voice';

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
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-8">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{t('analytics.title')}</h1>
          <p className="text-gray-500 text-sm mt-1">{t('analytics.subtitle')}</p>
        </div>

        <div className="flex items-center gap-3">
          {/* Period selector */}
          <div className="flex bg-gray-100 rounded-lg p-1">
            {PERIODS.map((p) => (
              <button
                key={p.days}
                onClick={() => setDays(p.days)}
                className={`px-3 py-1.5 rounded-md text-xs font-medium transition ${
                  days === p.days ? 'bg-white shadow text-indigo-600' : 'text-gray-500 hover:text-gray-700'
                }`}
              >
                {p.label}
              </button>
            ))}
          </div>
          <VoiceButton
            apiCall={voiceSearchCampaigns}
            onResult={() => {}}
            className="!py-2 !px-3 !text-xs"
          />
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
              value={summary?.started ?? '—'}
              icon="💬"
              change={summary?.previous_period ? calcChange(summary.started, summary.previous_period.started) : null}
            />
            <SummaryCard
              title={t('analytics.completed')}
              value={summary?.completed ?? '—'}
              icon="✅"
              change={summary?.previous_period ? calcChange(summary.completed, summary.previous_period.completed) : null}
            />
            <SummaryCard
              title={t('analytics.abandoned')}
              value={summary?.abandoned ?? '—'}
              icon="🚪"
            />
            <SummaryCard
              title={t('analytics.success_rate')}
              value={summary?.completion_rate != null ? `${Math.round(summary.completion_rate)}%` : '—'}
              icon="📊"
            />
          </div>

          {/* Two-column: Funnel + Recent events */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
            {/* Funnel */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <h2 className="font-semibold text-gray-900 mb-4">{t('analytics.donation_funnel')}</h2>
              {funnel ? (
                <div className="space-y-3">
                  {funnel.funnel?.map((step, i) => (
                    <FunnelRow key={i} step={step} maxValue={funnel.funnel?.[0]?.count || 1} />
                  ))}
                  {funnel.conversion_rate != null && (
                    <div className="pt-3 border-t border-gray-100 text-center">
                      <span className="text-2xl font-bold text-indigo-600">{Math.round(funnel.conversion_rate)}%</span>
                      <p className="text-xs text-gray-400 mt-1">{t('analytics.conversion_rate')}</p>
                    </div>
                  )}
                </div>
              ) : (
                <p className="text-gray-400 text-sm">{t('analytics.no_funnel')}</p>
              )}
            </div>

            {/* Recent events */}
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <h2 className="font-semibold text-gray-900 mb-4">{t('analytics.recent_events')}</h2>
              {events.length > 0 ? (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {events.map((ev, i) => (
                    <div key={i} className="flex items-start gap-3 text-sm py-2 border-b border-gray-50 last:border-0">
                      <span className="text-lg">{eventIcon(ev.event_type)}</span>
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
            <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-6">
              <h2 className="font-semibold text-gray-900 mb-4">{t('analytics.daily_breakdown')}</h2>
              <div className="overflow-x-auto">
                <table className="w-full text-sm">
                  <thead>
                    <tr className="text-left text-gray-400 border-b border-gray-100">
                      <th className="pb-2 font-medium">{t('analytics.date')}</th>
                      <th className="pb-2 font-medium text-right">{t('analytics.conversations')}</th>
                      <th className="pb-2 font-medium text-right">{t('analytics.completed')}</th>
                      <th className="pb-2 font-medium text-right">{t('analytics.donations')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {metrics.daily_metrics.map((row, i) => (
                      <tr key={i} className="border-b border-gray-50 last:border-0">
                        <td className="py-2 text-gray-700">{row.date}</td>
                        <td className="py-2 text-right text-gray-600">{row.conversations || 0}</td>
                        <td className="py-2 text-right text-gray-600">{row.completed || 0}</td>
                        <td className="py-2 text-right font-medium text-indigo-600">{row.donations || 0}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
}

/* ── Sub-components ──────────────────────── */

function SummaryCard({ title, value, icon, change }) {
  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 p-5">
      <div className="flex items-center gap-2 mb-2">
        <span className="text-lg">{icon}</span>
        <span className="text-sm text-gray-400">{title}</span>
      </div>
      <div className="flex items-baseline gap-2">
        <span className="text-2xl font-bold text-gray-900">{value}</span>
        {change != null && (
          <span className={`text-xs font-medium ${change >= 0 ? 'text-green-600' : 'text-red-500'}`}>
            {change >= 0 ? '↑' : '↓'} {Math.abs(change)}%
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
          className="h-full rounded-full bg-gradient-to-r from-indigo-500 to-purple-500 transition-all duration-500"
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

function eventIcon(type) {
  const icons = {
    conversation_started: '💬',
    donation_completed: '💰',
    donation_initiated: '💳',
    voice_search: '🎙️',
    campaign_viewed: '👁️',
    registration: '📝',
  };
  return icons[type] || '📌';
}
