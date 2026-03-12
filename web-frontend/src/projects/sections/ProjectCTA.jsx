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
      {/* Sunset to the west */}
      <div className="absolute bottom-12 sm:bottom-16 left-[8%] sm:left-[12%] pointer-events-none z-[2]">
        <svg width="200" height="140" viewBox="0 0 200 140" fill="none" aria-hidden="true" className="opacity-70">
          <defs>
            <radialGradient id="cta-sun-glow" cx="50%" cy="70%" r="55%">
              <stop offset="0%" stopColor="#F59E0B" stopOpacity="0.25" />
              <stop offset="40%" stopColor="#D97706" stopOpacity="0.12" />
              <stop offset="70%" stopColor="#EA580C" stopOpacity="0.06" />
              <stop offset="100%" stopColor="#DC2626" stopOpacity="0" />
            </radialGradient>
            <clipPath id="cta-sun-clip">
              <rect x="0" y="0" width="200" height="100" />
            </clipPath>
          </defs>

          {/* Ambient glow wash */}
          <ellipse cx="100" cy="100" rx="95" ry="65" fill="url(#cta-sun-glow)" />

          {/* Sun rays radiating outward */}
          {[0, 20, 40, 60, 80, 100, 120, 140, 160, 180].map((angle, i) => {
            const rad = (angle * Math.PI) / 180;
            const x1 = 100 + 28 * Math.cos(rad);
            const y1 = 100 - 28 * Math.sin(rad);
            const x2 = 100 + (55 + (i % 3) * 12) * Math.cos(rad);
            const y2 = 100 - (55 + (i % 3) * 12) * Math.sin(rad);
            return (
              <line key={i}
                x1={x1} y1={y1} x2={x2} y2={y2}
                stroke="#F59E0B"
                strokeWidth={1 + (i % 2) * 0.5}
                opacity={0.08 + (i % 3) * 0.03}
                strokeLinecap="round"
              />
            );
          })}

          {/* Sun disc — half below horizon */}
          <g clipPath="url(#cta-sun-clip)">
            <circle cx="100" cy="100" r="24" fill="#F59E0B" opacity="0.18" />
            <circle cx="100" cy="100" r="18" fill="#FBBF24" opacity="0.14" />
            <circle cx="100" cy="100" r="11" fill="#FDE68A" opacity="0.12" />
          </g>

          {/* Horizon line */}
          <line x1="10" y1="100" x2="190" y2="100" stroke="#D97706" strokeWidth="1" opacity="0.1" />

          {/* Reflection below horizon */}
          <ellipse cx="100" cy="108" rx="40" ry="6" fill="#F59E0B" opacity="0.06" />
          <ellipse cx="100" cy="115" rx="25" ry="3" fill="#D97706" opacity="0.04" />

          {/* Warm sky bands */}
          <rect x="20" y="75" width="160" height="3" rx="1.5" fill="#F59E0B" opacity="0.04" />
          <rect x="30" y="83" width="140" height="2" rx="1" fill="#EA580C" opacity="0.03" />
          <rect x="40" y="90" width="120" height="2" rx="1" fill="#D97706" opacity="0.04" />
        </svg>
      </div>

      {/* Horizon landscape illustration */}
      <div className="absolute bottom-0 left-0 right-0 pointer-events-none z-[1]">
        <CtaHorizon className="opacity-60" />
      </div>
    </section>
  );
}
