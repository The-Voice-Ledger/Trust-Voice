import { Link } from 'react-router-dom';
import HexIcon from '../../components/HexIcon';
import { TopographyBg, GlowOrb, PulseRing } from '../../components/SvgDecorations';
import {
  HiOutlineArrowRight,
  HiOutlineSparkles,
  HiOutlineChatBubbleLeftRight,
} from '../../components/icons';

/**
 * ProjectHero -- immersive full-viewport cinematic hero.
 *
 * Multi-layered: background effects, floating hexagonal constellation,
 * large display type with overtitle badge, stat ribbon, dual CTAs.
 */
export default function ProjectHero({ config }) {
  const { hero, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section
      id="hero"
      className={`relative min-h-screen flex flex-col justify-center overflow-hidden bg-gradient-to-b ${theme.heroBg}`}
    >
      {/* ---- Background layers ---- */}
      <div className="absolute inset-0 pointer-events-none">
        <TopographyBg className="absolute inset-0 w-full h-full text-white/[0.02]" />

        {/* Large glows */}
        <GlowOrb className="absolute -top-48 right-0 w-[700px] h-[700px] opacity-[0.07]" color={p} />
        <GlowOrb className="absolute -bottom-32 -left-32 w-[500px] h-[500px] opacity-[0.06]" color={s} />
        <PulseRing className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[800px] h-[800px] opacity-[0.04]" color={p} />

        {/* Horizontal light streaks */}
        <div className="absolute top-[35%] left-0 w-full h-px opacity-[0.04]" style={{ background: `linear-gradient(90deg, transparent, ${p}, transparent)` }} />
        <div className="absolute top-[65%] left-0 w-full h-px opacity-[0.03]" style={{ background: `linear-gradient(90deg, transparent, ${s}, transparent)` }} />
      </div>

      {/* ---- Floating hex constellation ---- */}
      <div className="absolute inset-0 pointer-events-none">
        {[
          { top: '10%', left: '4%', size: 'sm', bespoke: 'leaf', opacity: 0.18, delay: '0s' },
          { top: '18%', right: '6%', size: 'xs', bespoke: 'sun', opacity: 0.12, delay: '1s' },
          { top: '55%', left: '7%', size: 'xs', bespoke: 'mountain', opacity: 0.10, delay: '2s' },
          { bottom: '22%', right: '4%', size: 'sm', bespoke: 'cottage', opacity: 0.14, delay: '0.5s' },
          { top: '70%', left: '85%', size: 'xs', bespoke: 'globe', opacity: 0.08, delay: '1.5s' },
          { top: '35%', left: '92%', size: 'xs', bespoke: 'oil-drop', opacity: 0.07, delay: '3s' },
        ].map((pos, i) => (
          <div
            key={i}
            className="absolute animate-pulse"
            style={{ ...pos, animationDelay: pos.delay, animationDuration: '4s' }}
          >
            <HexIcon
              Icon={HiOutlineSparkles}
              accent={i % 2 === 0 ? p : s}
              size={pos.size}
              spin
              bespoke={pos.bespoke}
            />
          </div>
        ))}
      </div>

      {/* ---- Content ---- */}
      <div className="relative z-10 text-center px-6 max-w-5xl mx-auto py-32 sm:py-40">
        {/* Badge */}
        <div className="inline-flex items-center gap-2.5 px-5 py-2 rounded-full border border-white/10 bg-white/[0.03] backdrop-blur-sm mb-8">
          <div className="w-2 h-2 rounded-full animate-pulse" style={{ backgroundColor: p }} />
          <span className="text-xs font-semibold text-white/60 tracking-[0.18em] uppercase">
            {hero.badge}
          </span>
        </div>

        {/* Overtitle */}
        <p className="text-sm sm:text-base font-bold tracking-[0.3em] uppercase mb-6" style={{ color: s }}>
          {hero.overtitle}
        </p>

        {/* Main title -- multi-line with gradient */}
        <h1 className={`font-display text-4xl sm:text-6xl md:text-7xl lg:text-8xl font-extrabold tracking-tight leading-[0.92] mb-8 bg-gradient-to-r ${theme.heroText} bg-clip-text text-transparent`}>
          {hero.title.split('\n').map((line, i) => (
            <span key={i}>
              {line}
              {i < hero.title.split('\n').length - 1 && <br />}
            </span>
          ))}
        </h1>

        {/* Decorative divider */}
        <div className="flex items-center justify-center gap-3 mb-8">
          <div className="w-12 h-px" style={{ background: p }} />
          <HexIcon Icon={HiOutlineSparkles} accent={p} size="xs" bespoke="leaf" />
          <div className="w-12 h-px" style={{ background: s }} />
        </div>

        {/* Subtitle */}
        <p className="text-base sm:text-lg md:text-xl text-white/50 max-w-2xl mx-auto leading-relaxed mb-12">
          {hero.subtitle}
        </p>

        {/* CTAs */}
        <div className="flex flex-col sm:flex-row items-center justify-center gap-4 mb-16">
          <Link
            to={hero.ctaLink}
            className="group inline-flex items-center gap-3 px-9 py-4 rounded-2xl text-sm font-bold text-white shadow-xl shadow-black/20 hover:shadow-2xl hover:-translate-y-0.5 transition-all duration-300"
            style={{ background: `linear-gradient(135deg, ${p}, ${s})` }}
          >
            {hero.ctaLabel}
            <HiOutlineArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            to={hero.secondaryLink}
            className="inline-flex items-center gap-2.5 px-7 py-3.5 rounded-2xl text-sm font-semibold text-white/70 border border-white/10 bg-white/[0.03] backdrop-blur-sm hover:bg-white/[0.06] hover:text-white transition-all duration-300"
          >
            <HiOutlineChatBubbleLeftRight className="w-4 h-4" />
            {hero.secondaryLabel}
          </Link>
        </div>

        {/* Stat ribbon */}
        <div className="flex flex-wrap items-center justify-center gap-8 sm:gap-12">
          {hero.stats.map((stat, i) => (
            <div key={i} className="text-center">
              <p className="text-2xl sm:text-3xl font-extrabold font-display" style={{ color: i % 2 === 0 ? p : s }}>
                {stat.value}
              </p>
              <p className="text-[11px] sm:text-xs text-white/40 font-medium tracking-wider uppercase mt-1">
                {stat.label}
              </p>
            </div>
          ))}
        </div>
      </div>

      {/* ---- Bottom fade to next section ---- */}
      <div className="absolute bottom-0 left-0 right-0 h-40 bg-gradient-to-t from-gray-50 to-transparent" />

      {/* Scroll indicator */}
      <div className="absolute bottom-24 left-1/2 -translate-x-1/2 flex flex-col items-center gap-2 opacity-40 animate-bounce">
        <div className="w-5 h-8 rounded-full border border-white/20 flex items-start justify-center p-1">
          <div className="w-1 h-2 rounded-full bg-white/40" />
        </div>
      </div>
    </section>
  );
}
