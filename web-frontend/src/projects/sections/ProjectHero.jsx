import { Link } from 'react-router-dom';
import {
  HiOutlineArrowRight,
  HiOutlineChatBubbleLeftRight,
} from '../../components/icons';
import { HeroPanorama } from '../illustrations/ProjectScenes';

/**
 * ProjectHero -- warm, spacious, cinematic hero.
 * Fewer elements, more breathing room. Let the words do the work.
 */
export default function ProjectHero({ config }) {
  const { hero, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section
      id="hero"
      className={`relative min-h-screen flex flex-col justify-end overflow-hidden bg-gradient-to-b ${theme.heroBg}`}
    >


      {/* Content -- pushed toward center-bottom for cinematic feel */}
      <div className="relative z-10 px-6 max-w-4xl mx-auto w-full pb-32 sm:pb-36 pt-48 sm:pt-56">
        {/* Small badge */}
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full border border-white/[0.08] bg-white/[0.03] mb-10">
          <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: p }} />
          <span className="text-[11px] font-medium text-white/50 tracking-[0.15em] uppercase">
            {hero.badge}
          </span>
        </div>

        {/* Title -- warm, not screaming */}
        <h1 className="font-display text-3xl sm:text-4xl md:text-5xl font-semibold tracking-tight leading-[1.1] text-white mb-6">
          {hero.title.split('\n').map((line, i) => (
            <span key={i}>
              {i > 0 && <br />}
              {i === 0 ? line : <span style={{ color: s }} className="opacity-80">{line}</span>}
            </span>
          ))}
        </h1>

        {/* Subtitle */}
        <p className="text-white/40 text-base sm:text-lg leading-relaxed max-w-xl mb-10">
          {hero.subtitle}
        </p>

        {/* CTAs -- prominent, warm cards */}
        <div className="flex flex-wrap items-center gap-4 mb-14">
          <Link
            to={hero.ctaLink}
            className="group relative inline-flex items-center gap-3 px-8 py-4 rounded-xl text-[15px] font-semibold text-white shadow-lg shadow-emerald-900/20 transition-all duration-300 hover:shadow-xl hover:shadow-emerald-800/25 hover:scale-[1.02]"
            style={{ backgroundColor: p }}
          >
            <span className="absolute inset-0 rounded-xl ring-1 ring-inset ring-white/10" />
            {hero.ctaLabel}
            <HiOutlineArrowRight className="w-4 h-4 opacity-70 group-hover:translate-x-1 transition-transform duration-300" />
          </Link>
          <Link
            to={hero.secondaryLink}
            className="group inline-flex items-center gap-2.5 px-7 py-4 rounded-xl text-[15px] font-medium text-white/55 border border-white/[0.1] bg-white/[0.03] backdrop-blur-sm hover:text-white/75 hover:border-white/20 hover:bg-white/[0.05] transition-all duration-300"
          >
            <HiOutlineChatBubbleLeftRight className="w-4 h-4 opacity-50 group-hover:opacity-70 transition-opacity" />
            {hero.secondaryLabel}
          </Link>
        </div>

        {/* Stat ribbon -- subtle, horizontal */}
        {hero.stats?.length > 0 && (
          <div className="flex items-center gap-10 sm:gap-14">
            {hero.stats.map((stat, i) => (
              <div key={i}>
                <p className="text-xl sm:text-2xl font-display font-semibold" style={{ color: i === 0 ? p : i === 1 ? s : 'rgba(255,255,255,0.5)' }}>
                  {stat.value}
                </p>
                <p className="text-[10px] text-white/30 font-medium tracking-wider uppercase mt-0.5">
                  {stat.label}
                </p>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Panoramic sunrise landscape illustration */}
      <div className="absolute bottom-20 left-0 right-0 pointer-events-none z-[1]" style={{ height: '55%' }}>
        <HeroPanorama className="opacity-80 h-full" />
      </div>

      {/* Bottom transition -- soft gradient into the next section */}
      <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-stone-50 to-transparent z-[2]" />
    </section>
  );
}
