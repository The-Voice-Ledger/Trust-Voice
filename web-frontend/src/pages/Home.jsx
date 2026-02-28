import { useState, useEffect, useCallback } from 'react';
import { Link } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { listCampaigns } from '../api/campaigns';
import CampaignCard from '../components/CampaignCard';
import SkeletonCard from '../components/SkeletonCard';
import { HiOutlineMagnifyingGlass, HiOutlineSparkles } from 'react-icons/hi2';

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

  return (
    <div className="max-w-6xl mx-auto px-4 py-6">
      {/* Hero */}
      <section className="text-center mb-8">
        <h1 className="text-2xl sm:text-4xl font-extrabold text-gray-900 mb-2 flex items-center justify-center gap-2 sm:gap-3">
          {t('home.hero_title')}
          <HiOutlineSparkles className="w-6 h-6 sm:w-8 sm:h-8 text-indigo-500" />
        </h1>
        <p className="text-gray-500 max-w-lg mx-auto">{t('home.hero_subtitle')}</p>
      </section>

      {/* Search */}
      <div className="flex flex-col sm:flex-row gap-3 mb-6">
        <div className="flex-1 relative">
          <input
            type="text"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder={t('home.search_placeholder')}
            className="w-full pl-10 pr-4 py-3 rounded-xl border border-gray-200 text-sm focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
          />
          <HiOutlineMagnifyingGlass className="absolute left-3 top-3.5 h-4 w-4 text-gray-400" />
        </div>
        <Link
          to="/assistant"
          className="flex items-center justify-center gap-2 px-5 py-3 rounded-xl bg-indigo-50 text-indigo-700 text-sm font-medium hover:bg-indigo-100 transition-all border border-indigo-100"
        >
          <HiOutlineSparkles className="w-4 h-4" />
          {t('home.ask_assistant', 'Ask Assistant')}
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {CATEGORIES.map((cat) => (
          <button
            key={cat}
            onClick={() => setCategory(cat)}
            className={`px-4 py-2 rounded-full text-xs font-medium border transition capitalize
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
          className="ml-auto text-sm border border-gray-200 rounded-lg px-3 py-2"
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
                className="px-6 py-2.5 rounded-xl bg-gray-100 text-sm font-medium text-gray-700 hover:bg-gray-200 transition"
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
