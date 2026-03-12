import { Link } from 'react-router-dom';
import { getAllProjectSlugs, getProject } from '../projects/projectRegistry';
import {
  HiOutlineArrowRight, HiOutlinePlayCircle,
  HiOutlineGlobeAlt, HiOutlineMapPin,
} from '../components/icons';
import {
  CircuitTrace, HexGrid, GlowOrb, SectionAccent,
} from '../components/SvgDecorations';

/**
 * ProjectsIndex -- /projects gallery page.
 *
 * Lists all projects from the registry. Featured project gets a hero
 * slot with video preview; future projects appear in a card grid below.
 */
export default function ProjectsIndex() {
  const slugs = getAllProjectSlugs();
  const projects = slugs.map(getProject).filter(Boolean);
  const featured = projects[0]; // first project is featured
  const rest = projects.slice(1);

  return (
    <div className="relative">
      {/* ═══ HERO ═══ */}
      <section className="relative overflow-hidden bg-gradient-to-br from-indigo-950 via-violet-950 to-purple-950 text-white">
        <HexGrid className="absolute inset-0 text-white opacity-20" />
        <CircuitTrace className="absolute inset-0 w-full h-full text-violet-300 opacity-25" />
        <GlowOrb className="absolute -top-32 -right-32 w-[500px] h-[500px]" color="#6D28D9" />
        <GlowOrb className="absolute -bottom-32 -left-32 w-[400px] h-[400px]" color="#7C3AED" />

        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 py-20 sm:py-28 text-center">
          <span className="inline-flex items-center gap-2 bg-white/[0.07] backdrop-blur-xl rounded-full px-5 py-2 text-sm font-medium mb-8 border border-white/[0.08] shadow-lg shadow-violet-500/10">
            <HiOutlineGlobeAlt className="w-4 h-4 text-violet-300" />
            <span className="text-violet-200">Community Projects</span>
          </span>
          <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight mb-5">
            <span className="bg-gradient-to-r from-white via-violet-200 to-pink-200 bg-clip-text text-transparent">
              Projects Powered by TrustVoice
            </span>
          </h1>
          <p className="text-violet-200/60 text-base sm:text-lg max-w-2xl mx-auto">
            Transparent, voice-verified, community-funded. Explore the projects building real impact on the ground.
          </p>
        </div>
      </section>

      {/* ═══ FEATURED PROJECT ═══ */}
      {featured && (
        <section className="relative -mt-10 z-10 max-w-6xl mx-auto px-4 sm:px-6 pb-16">
          <Link
            to={`/project/${featured.slug}`}
            className="group block relative rounded-2xl overflow-hidden shadow-2xl shadow-gray-300/40 ring-1 ring-gray-200/60 hover:shadow-3xl hover:ring-gray-300/80 transition-all duration-500"
          >
            {/* video / gradient background */}
            <div className="relative h-[340px] sm:h-[420px] overflow-hidden">
              {featured.videoShowcase?.url ? (
                <video
                  className="absolute inset-0 w-full h-full object-cover"
                  src={featured.videoShowcase.url}
                  muted
                  autoPlay
                  loop
                  playsInline
                  preload="metadata"
                />
              ) : (
                <div className={`absolute inset-0 bg-gradient-to-br ${featured.theme.heroBg}`} />
              )}
              {/* dark overlay for text readability */}
              <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-black/30 to-transparent" />

              {/* content overlay */}
              <div className="absolute inset-0 flex flex-col justify-end p-6 sm:p-10">
                <div className="flex items-center gap-2 mb-3">
                  <span
                    className="inline-block w-2.5 h-2.5 rounded-full"
                    style={{ backgroundColor: featured.theme.primary }}
                  />
                  <span className="text-xs font-semibold text-white/60 tracking-[0.15em] uppercase">
                    Featured Project
                  </span>
                </div>
                <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-bold text-white mb-2 tracking-tight group-hover:text-white/90 transition">
                  {featured.name}: {featured.tagline}
                </h2>
                <p className="text-white/50 text-sm sm:text-base max-w-2xl mb-5 leading-relaxed line-clamp-2">
                  {featured.hero.subtitle}
                </p>
                <div className="flex flex-wrap items-center gap-3">
                  <span className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-white text-sm font-semibold transition-all group-hover:-translate-y-0.5 group-hover:shadow-lg"
                    style={{ backgroundColor: featured.theme.primary }}
                  >
                    Explore the Project
                    <HiOutlineArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
                  </span>
                  {featured.videoShowcase?.url && (
                    <span className="inline-flex items-center gap-1.5 text-white/50 text-sm">
                      <HiOutlinePlayCircle className="w-4.5 h-4.5" />
                      Includes video tour
                    </span>
                  )}
                </div>
              </div>
            </div>
          </Link>

          {/* quick stats from the featured project */}
          {featured.market && (
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mt-6">
              {[
                { label: 'Global Market', value: featured.market.tam?.value },
                { label: 'Annual Growth', value: featured.market.tam?.detail?.match(/[\d.]+%/)?.[0] },
                { label: 'Location', value: 'Zimbabwe', icon: HiOutlineMapPin },
                { label: 'Type', value: 'Community Farm' },
              ].filter(s => s.value).map((s, i) => (
                <div key={i} className="bg-white rounded-xl px-4 py-3 shadow-sm ring-1 ring-gray-100 text-center">
                  <div className="text-lg font-bold text-gray-900 font-display">{s.value}</div>
                  <div className="text-xs text-gray-500 mt-0.5">{s.label}</div>
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ═══ MORE PROJECTS (future) ═══ */}
      {rest.length > 0 && (
        <section className="max-w-6xl mx-auto px-4 sm:px-6 pb-20">
          <h3 className="font-display text-xl font-semibold text-gray-900 mb-6">More Projects</h3>
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
            {rest.map((p) => (
              <Link
                key={p.slug}
                to={`/project/${p.slug}`}
                className="group bg-white rounded-xl overflow-hidden shadow-sm ring-1 ring-gray-100 hover:shadow-lg hover:ring-gray-200 transition-all"
              >
                <div className={`h-36 bg-gradient-to-br ${p.theme.heroBg}`} />
                <div className="p-5">
                  <h4 className="font-display font-semibold text-gray-900 mb-1 group-hover:text-indigo-600 transition">
                    {p.name}
                  </h4>
                  <p className="text-sm text-gray-500">{p.tagline}</p>
                </div>
              </Link>
            ))}
          </div>
        </section>
      )}

      {/* ═══ EMPTY STATE ═══ */}
      {rest.length === 0 && (
        <section className="max-w-3xl mx-auto px-4 sm:px-6 pb-20 text-center">
          <div className="bg-gradient-to-b from-indigo-50/60 to-white rounded-2xl py-12 px-6 ring-1 ring-indigo-100/50">
            <p className="text-gray-500 text-sm mb-1">More projects coming soon.</p>
            <p className="text-gray-400 text-xs">
              TrustVoice enables transparent, voice-verified fundraising for community projects worldwide.
            </p>
          </div>
          <SectionAccent className="mt-8 max-w-xs mx-auto" />
        </section>
      )}
    </div>
  );
}
