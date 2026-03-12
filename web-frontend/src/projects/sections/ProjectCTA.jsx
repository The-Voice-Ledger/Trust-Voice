import { GlowOrb, PulseRing, TopographyBg } from '../../components/SvgDecorations';
import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles, HiOutlineChatBubbleLeftRight, HiOutlineArrowRight } from '../../components/icons';
import { Link } from 'react-router-dom';

/**
 * ProjectCTA -- grand final call-to-action with layered dark background.
 */
export default function ProjectCTA({ config }) {
  const { cta, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section id="cta" className={`relative py-28 sm:py-36 px-6 overflow-hidden bg-gradient-to-b ${theme.heroBg}`}>
      {/* Background layers */}
      <TopographyBg className="absolute inset-0 w-full h-full text-white/[0.015] pointer-events-none" />
      <GlowOrb className="absolute -top-40 left-[20%] w-[600px] h-[600px] opacity-[0.06]" color={p} />
      <GlowOrb className="absolute -bottom-32 right-[10%] w-[400px] h-[400px] opacity-[0.05]" color={s} />
      <PulseRing className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[700px] h-[700px] opacity-[0.03]" color={p} />

      <div className="relative max-w-3xl mx-auto text-center z-10">
        {/* Decorative hex cluster */}
        <div className="flex items-center justify-center gap-3 mb-10">
          <HexIcon Icon={HiOutlineSparkles} accent={s} size="sm" bespoke="leaf" />
          <HexIcon Icon={HiOutlineSparkles} accent={p} size="lg" bespoke="globe" glow />
          <HexIcon Icon={HiOutlineSparkles} accent={s} size="sm" bespoke="sun" />
        </div>

        <h2 className={`font-display text-3xl sm:text-4xl md:text-5xl font-bold tracking-tight mb-5 bg-gradient-to-r ${theme.heroText} bg-clip-text text-transparent`}>
          {cta.heading}
        </h2>
        <p className="text-white/40 text-base sm:text-lg leading-relaxed max-w-xl mx-auto mb-12">
          {cta.subheading}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link
            to={cta.primaryLink}
            className="group inline-flex items-center gap-3 px-10 py-4 rounded-2xl text-sm font-bold text-white shadow-xl shadow-black/20 hover:shadow-2xl hover:-translate-y-0.5 transition-all duration-300"
            style={{ background: `linear-gradient(135deg, ${p}, ${s})` }}
          >
            {cta.primaryLabel}
            <HiOutlineArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
          </Link>
          <Link
            to={cta.secondaryLink}
            className="inline-flex items-center gap-2.5 px-8 py-3.5 rounded-2xl text-sm font-semibold text-white/70 border border-white/10 bg-white/[0.03] backdrop-blur-sm hover:bg-white/[0.06] hover:text-white transition-all duration-300"
          >
            <HiOutlineChatBubbleLeftRight className="w-5 h-5" />
            {cta.secondaryLabel}
          </Link>
        </div>
      </div>
    </section>
  );
}
