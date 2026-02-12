import { useState, useEffect, useCallback } from 'react';
import { useTranslation } from 'react-i18next';
import { listCampaigns } from '../api/campaigns';
import { voiceSearchCampaigns } from '../api/voice';
import CampaignCard from '../components/CampaignCard';
import VoiceButton from '../components/VoiceButton';
import { HiOutlineMagnifyingGlass } from 'react-icons/hi2';
import { HiOutlineMicrophone } from 'react-icons/hi';

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
  const [voiceResults, setVoiceResults] = useState(null);

  const load = useCallback(async (p = 1, append = false) => {
    setLoading(true);
    try {
      const data = await listCampaigns({
        page: p,
        pageSize: 12,
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

  const handleVoiceResult = (result) => {
    setVoiceResults(result);
    if (result.campaigns?.length) {
      setCampaigns(result.campaigns);
      setTotal(result.campaigns.length);
    }
  };

  const clearVoice = () => {
    setVoiceResults(null);
    load(1);
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Hero */}
      <section className="text-center mb-8">
        <h1 className="text-3xl sm:text-4xl font-extrabold text-gray-900 mb-2 flex items-center justify-center gap-3">
          {t('home.hero_title')}
          <HiOutlineMicrophone className="w-8 h-8 text-indigo-500" />
        </h1>
        <p className="text-gray-500 max-w-lg mx-auto">{t('home.hero_subtitle')}</p>
      </section>

      {/* Search + Voice */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('home.search_placeholder')}
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <HiOutlineMagnifyingGlass className="absolute left-3 top-3 h-4 w-4 text-gray-400" />
        </div>
        <VoiceButton
          apiCall={voiceSearchCampaigns}
          onResult={handleVoiceResult}
          className="self-center"
        />
      </div>

      {/* Voice result banner */}
      {voiceResults && (
        <div className="bg-indigo-50 border border-indigo-200 rounded-xl p-3 mb-4 flex justify-between items-center">
          <p className="text-sm text-indigo-700 flex items-center gap-1.5">
            <HiOutlineMicrophone className="w-4 h-4 flex-shrink-0" />
            <em>"{voiceResults.transcription}"</em> — {voiceResults.response_text}
          </p>
          <button onClick={clearVoice} className="text-indigo-500 text-xs hover:underline">{t('common.close')}</button>
        </div>
      )}

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition capitalize
              ${cat === category
                ? 'bg-indigo-600 text-white border-indigo-600'
                : 'bg-white text-gray-600 border-gray-200 hover:border-indigo-300'}`}
          >
            {cat === 'all' ? t('home.filter_all') : cat}
          </button>
        ))}
        <select
          value={sort}
          onChange={(e) => setSort(e.target.value)}
          className="ml-auto text-xs border border-gray-200 rounded-lg px-2 py-1"
        >
          {SORT_OPTIONS.map((s) => (
            <option key={s} value={s}>{t(`home.sort_${s}`)}</option>
          ))}
        </select>
      </div>

      {/* Campaign grid */}
      {loading && campaigns.length === 0 ? (
        <div className="text-center py-20 text-gray-400">{t('common.loading')}</div>
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
                className="px-6 py-2 rounded-xl bg-gray-100 text-sm font-medium text-gray-700 hover:bg-gray-200 transition"
              >
                {loading ? t('common.loading') : t('home.load_more')}
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
}
