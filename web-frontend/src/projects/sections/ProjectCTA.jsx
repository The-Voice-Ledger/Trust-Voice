import { Link } from 'react-router-dom';
import {
  HiOutlineChatBubbleLeftRight,
  HiOutlineArrowRight,
} from '../../components/icons';
import { CtaHorizon } from '../illustrations/ProjectScenes';

/**
 * ProjectCTA -- warm final call-to-action. Simple and inviting.
 */
export default function ProjectCTA({ config }) {
  const { cta, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section id="cta" className={`relative py-28 sm:py-36 px-6 overflow-hidden bg-gradient-to-b ${theme.heroBg}`}>
      {/* Ambient scattered light motes */}
      <div className="absolute inset-0 pointer-events-none overflow-hidden" aria-hidden="true">
        <div className="absolute top-16 left-[15%] w-1.5 h-1.5 rounded-full opacity-[0.06] scene-glow-slow" style={{ backgroundColor: s }} />
        <div className="absolute top-28 right-[22%] w-1 h-1 rounded-full opacity-[0.04] scene-glow-slow" style={{ backgroundColor: p, animationDelay: '1.2s' }} />
        <div className="absolute top-10 right-[40%] w-2 h-2 rounded-full opacity-[0.03] scene-glow-slow" style={{ backgroundColor: s, animationDelay: '2.4s' }} />
        <div className="absolute bottom-32 left-[60%] w-1 h-1 rounded-full opacity-[0.05] scene-glow-slow" style={{ backgroundColor: p, animationDelay: '0.8s' }} />
      </div>

      <div className="relative max-w-2xl mx-auto text-center z-10">
        <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-white tracking-tight mb-5">
          {cta.heading}
        </h2>
        <p className="text-white/35 text-base sm:text-lg leading-relaxed max-w-lg mx-auto mb-10">
          {cta.subheading}
        </p>

        <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
          <Link
            to={cta.primaryLink}
            className="group inline-flex items-center gap-2.5 px-8 py-3.5 rounded-lg text-sm font-semibold text-white transition-all duration-200 hover:opacity-90"
            style={{ backgroundColor: p }}
          >
            {cta.primaryLabel}
            <HiOutlineArrowRight className="w-3.5 h-3.5 opacity-60 group-hover:translate-x-0.5 transition-transform" />
          </Link>
          <Link
            to={cta.secondaryLink}
            className="inline-flex items-center gap-2 px-6 py-3.5 rounded-lg text-sm font-medium text-white/50 border border-white/[0.08] hover:text-white/70 hover:border-white/15 transition-all duration-200"
          >
            <HiOutlineChatBubbleLeftRight className="w-4 h-4 opacity-50" />
            {cta.secondaryLabel}
          </Link>
        </div>
      </div>
      {/* Horizon landscape illustration */}
      <div className="absolute bottom-0 left-0 right-0 pointer-events-none z-[1]">
        <CtaHorizon className="opacity-60" />
      </div>
    </section>
  );
}
