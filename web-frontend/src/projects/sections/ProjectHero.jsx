import { Link } from 'react-router-dom';
import { GlowOrb } from '../../components/SvgDecorations';
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
      {/* Background -- just two soft glows, nothing more */}
      <div className="absolute inset-0 pointer-events-none">
        <GlowOrb className="absolute -top-40 right-[10%] w-[600px] h-[600px] opacity-[0.06]" color={p} />
        <GlowOrb className="absolute bottom-[10%] -left-32 w-[400px] h-[400px] opacity-[0.04]" color={s} />
      </div>

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

        {/* CTAs -- side by side, understated */}
        <div className="flex flex-wrap items-center gap-3 mb-14">
          <Link
            to={hero.ctaLink}
            className="group inline-flex items-center gap-2.5 px-7 py-3 rounded-lg text-sm font-semibold text-white transition-all duration-200 hover:opacity-90"
            style={{ backgroundColor: p }}
          >
            {hero.ctaLabel}
            <HiOutlineArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            to={hero.secondaryLink}
            className="inline-flex items-center gap-2 px-6 py-3 rounded-lg text-sm font-medium text-white/50 border border-white/[0.08] hover:text-white/70 hover:border-white/15 transition-all duration-200"
          >
            <HiOutlineChatBubbleLeftRight className="w-4 h-4 opacity-50" />
            {hero.secondaryLabel}
          </Link>
        </div>

        {/* Stat ribbon -- subtle, horizontal */}
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
