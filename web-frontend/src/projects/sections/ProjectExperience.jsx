import { useEffect, useRef, useState } from 'react';

/**
 * ProjectExperience - bold animated "day arc" for Live-Work-Learn.
 *
 * Large semicircular arc with day titles on the arc itself,
 * wide content card with prominent scene illustration.
 */

/* Mini scene vignettes (inline SVG) */
function SceneConnection() {
  return (
    <svg viewBox="0 0 160 90" className="w-full h-auto">
      {/* Ground line */}
      <line x1="10" y1="78" x2="150" y2="78" stroke="#059669" strokeWidth="0.5" opacity="0.1" />
      {/* Tea cup */}
      <rect x="55" y="45" width="40" height="24" rx="5" fill="#059669" opacity="0.2" />
      <path d="M95 52 Q106 52 106 62 Q106 72 95 72" fill="none" stroke="#059669" strokeWidth="2" opacity="0.15" />
      {/* Steam wisps */}
      <path d="M68 42 Q65 32 69 24" fill="none" stroke="#059669" strokeWidth="1.5" opacity="0.15" className="exp-steam" />
      <path d="M78 39 Q75 28 79 20" fill="none" stroke="#059669" strokeWidth="1.5" opacity="0.12" className="exp-steam" style={{ animationDelay: '0.5s' }} />
      <path d="M88 41 Q86 33 89 26" fill="none" stroke="#059669" strokeWidth="1" opacity="0.1" className="exp-steam" style={{ animationDelay: '1s' }} />
      {/* Leaves decoration */}
      <ellipse cx="28" cy="58" rx="12" ry="5" fill="#059669" opacity="0.12" transform="rotate(-25 28 58)" />
      <ellipse cx="22" cy="66" rx="9" ry="4" fill="#059669" opacity="0.1" transform="rotate(15 22 66)" />
      <line x1="28" y1="58" x2="18" y2="74" stroke="#059669" strokeWidth="0.8" opacity="0.1" />
      {/* Person sitting */}
      <circle cx="125" cy="50" r="4.5" fill="#059669" opacity="0.2" />
      <line x1="125" y1="55" x2="125" y2="68" stroke="#059669" strokeWidth="2" opacity="0.2" />
      <line x1="125" y1="60" x2="118" y2="56" stroke="#059669" strokeWidth="1.5" opacity="0.15" />
      <line x1="125" y1="68" x2="120" y2="78" stroke="#059669" strokeWidth="1.5" opacity="0.15" />
      <line x1="125" y1="68" x2="130" y2="78" stroke="#059669" strokeWidth="1.5" opacity="0.15" />
    </svg>
  );
}

function SceneContribution() {
  return (
    <svg viewBox="0 0 160 90" className="w-full h-auto">
      {/* Sun */}
      <circle cx="130" cy="18" r="12" fill="#D97706" opacity="0.1" />
      <circle cx="130" cy="18" r="7" fill="#D97706" opacity="0.08" className="exp-sparkle" />
      {/* Ground */}
      <line x1="10" y1="78" x2="150" y2="78" stroke="#059669" strokeWidth="0.5" opacity="0.1" />
      {/* Person harvesting */}
      <circle cx="45" cy="30" r="4.5" fill="#059669" opacity="0.25" />
      <line x1="45" y1="35" x2="45" y2="52" stroke="#059669" strokeWidth="2" opacity="0.25" />
      <line x1="45" y1="42" x2="36" y2="48" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      <line x1="45" y1="42" x2="56" y2="44" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      <line x1="45" y1="52" x2="40" y2="66" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      <line x1="45" y1="52" x2="50" y2="66" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      {/* Moringa branch */}
      <path d="M56 44 Q68 40 78 30" fill="none" stroke="#059669" strokeWidth="1.2" opacity="0.15" />
      <ellipse cx="78" cy="24" rx="10" ry="5" fill="#059669" opacity="0.1" />
      <ellipse cx="70" cy="32" rx="7" ry="3.5" fill="#059669" opacity="0.08" />
      {/* Oil press */}
      <rect x="95" y="45" width="26" height="20" rx="3" fill="#D97706" opacity="0.12" />
      <rect x="100" y="38" width="8" height="7" rx="1.5" fill="#D97706" opacity="0.08" />
      <circle cx="108" cy="55" r="5" fill="#D97706" opacity="0.08" />
      {/* Second person */}
      <circle cx="90" cy="30" r="4" fill="#D97706" opacity="0.18" />
      <line x1="90" y1="34" x2="90" y2="48" stroke="#D97706" strokeWidth="1.8" opacity="0.18" />
      <line x1="90" y1="40" x2="96" y2="46" stroke="#D97706" strokeWidth="1.3" opacity="0.14" />
    </svg>
  );
}

function SceneCreation() {
  return (
    <svg viewBox="0 0 160 90" className="w-full h-auto">
      {/* Ground */}
      <line x1="10" y1="78" x2="150" y2="78" stroke="#059669" strokeWidth="0.5" opacity="0.1" />
      {/* Product bottles - larger */}
      <rect x="22" y="40" width="14" height="28" rx="3" fill="#059669" opacity="0.18" />
      <rect x="26" y="34" width="6" height="6" rx="1.5" fill="#059669" opacity="0.14" />
      <rect x="42" y="46" width="12" height="22" rx="2.5" fill="#D97706" opacity="0.15" />
      <circle cx="48" cy="56" r="3" fill="#D97706" opacity="0.1" />
      <rect x="60" y="50" width="10" height="18" rx="2" fill="#059669" opacity="0.12" />
      {/* Person creating */}
      <circle cx="100" cy="32" r="4.5" fill="#059669" opacity="0.25" />
      <line x1="100" y1="37" x2="100" y2="54" stroke="#059669" strokeWidth="2" opacity="0.25" />
      <line x1="100" y1="44" x2="90" y2="50" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      <line x1="100" y1="44" x2="110" y2="50" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      <line x1="100" y1="54" x2="95" y2="68" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      <line x1="100" y1="54" x2="105" y2="68" stroke="#059669" strokeWidth="1.5" opacity="0.2" />
      {/* Sparkles */}
      <g opacity="0.15" className="exp-sparkle">
        <line x1="132" y1="24" x2="132" y2="38" stroke="#D97706" strokeWidth="1.2" />
        <line x1="125" y1="31" x2="139" y2="31" stroke="#D97706" strokeWidth="1.2" />
        <line x1="127" y1="26" x2="137" y2="36" stroke="#D97706" strokeWidth="0.8" />
        <line x1="137" y1="26" x2="127" y2="36" stroke="#D97706" strokeWidth="0.8" />
      </g>
      <g opacity="0.1" className="exp-sparkle" style={{ animationDelay: '0.7s' }}>
        <line x1="78" y1="22" x2="78" y2="32" stroke="#D97706" strokeWidth="1" />
        <line x1="73" y1="27" x2="83" y2="27" stroke="#D97706" strokeWidth="1" />
      </g>
    </svg>
  );
}

const SCENES = [SceneConnection, SceneContribution, SceneCreation];

export default function ProjectExperience({ config }) {
  const { experience, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const accent = theme.accent;
  const colors = [p, s, accent];

  const ref = useRef(null);
  const [visible, setVisible] = useState(false);
  const [active, setActive] = useState(0);
  const timerRef = useRef(null);

  /* Scroll trigger */
  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.15 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  /* Auto-rotate every 4s */
  useEffect(() => {
    if (!visible) return;
    timerRef.current = setInterval(() => {
      setActive(prev => (prev + 1) % experience.days.length);
    }, 4000);
    return () => clearInterval(timerRef.current);
  }, [visible, experience.days.length]);

  const handleSelect = (i) => {
    setActive(i);
    clearInterval(timerRef.current);
    timerRef.current = setInterval(() => {
      setActive(prev => (prev + 1) % experience.days.length);
    }, 4000);
  };

  return (
    <section
      ref={ref}
      id="experience"
      className="relative py-20 sm:py-28 px-6 overflow-hidden"
      style={{ background: 'linear-gradient(to bottom, #fafaf9, #f5f5f0, #fafaf9)' }}
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-gray-400">
            {experience.sectionLabel}
          </p>
          <h2 className="font-display text-4xl sm:text-5xl font-semibold text-gray-900 tracking-tight">
            {experience.heading}
          </h2>
          <p className="text-gray-400 mt-3 max-w-lg mx-auto text-base leading-relaxed">
            {experience.subtitle}
          </p>
        </div>

        {/* Day selector rings + content */}
        <div className="flex flex-col items-center">

          {/* Concentric rings with day labels */}
          <div className="relative mb-12" style={{ width: 380, height: 380 }}>
            <svg width="380" height="380" viewBox="0 0 380 380" className="absolute inset-0">
              <defs>
                {colors.map((c, i) => (
                  <radialGradient key={i} id={`ring-glow-${i}`} cx="50%" cy="50%" r="50%">
                    <stop offset="0%" stopColor={c} stopOpacity="0.15" />
                    <stop offset="100%" stopColor={c} stopOpacity="0" />
                  </radialGradient>
                ))}
              </defs>

              {/* Radial pulse on active change */}
              {visible && (
                <circle
                  cx="190" cy="190"
                  r={65 + active * 30}
                  fill="none"
                  stroke={colors[active]}
                  strokeWidth="1"
                  opacity="0"
                  className="exp-ripple"
                  key={`ripple-${active}`}
                />
              )}

              {/* Three concentric ring tracks */}
              {[65, 95, 125].map((r, i) => {
                const isActive = i === active;
                return (
                  <g key={i}>
                    <circle
                      cx="190" cy="190" r={r}
                      fill="none"
                      stroke="rgba(0,0,0,0.04)"
                      strokeWidth={isActive ? 2.5 : 1.5}
                      style={{ transition: 'stroke-width 0.4s ease' }}
                    />
                    <circle
                      cx="190" cy="190" r={r}
                      fill="none"
                      stroke={colors[i]}
                      strokeWidth={isActive ? 2.5 : 0}
                      opacity={isActive ? 0.5 : 0}
                      strokeDasharray={`${2 * Math.PI * r}`}
                      strokeDashoffset={isActive ? 0 : 2 * Math.PI * r}
                      strokeLinecap="round"
                      style={{ transition: 'stroke-dashoffset 0.8s ease, opacity 0.4s ease, stroke-width 0.4s ease' }}
                    />
                    {isActive && (
                      <circle cx="190" cy="190" r={r} fill={`url(#ring-glow-${i})`} opacity="0.6" />
                    )}
                  </g>
                );
              })}

              {/* Dot markers on each ring + connector lines outward */}
              {[
                { angle: 210, r: 65 },
                { angle: 90, r: 95 },
                { angle: 330, r: 125 },
              ].map(({ angle, r }, i) => {
                const rad = (angle * Math.PI) / 180;
                const dx = 190 + r * Math.cos(rad);
                const dy = 190 - r * Math.sin(rad);
                const lx = 190 + (r + 40) * Math.cos(rad);
                const ly = 190 - (r + 40) * Math.sin(rad);
                const isActive = i === active;
                return (
                  <g key={i} className="cursor-pointer" onClick={() => handleSelect(i)}>
                    {isActive && (
                      <circle cx={dx} cy={dy} r="18" fill={colors[i]} opacity="0.08" />
                    )}
                    <circle cx={dx} cy={dy}
                      r={isActive ? 14 : 10}
                      fill={isActive ? `${colors[i]}15` : 'white'}
                      stroke={isActive ? colors[i] : 'rgba(0,0,0,0.08)'}
                      strokeWidth="2"
                      style={{ transition: 'all 0.3s ease' }}
                    />
                    <circle cx={dx} cy={dy}
                      r={isActive ? 5 : 3.5}
                      fill={colors[i]}
                      opacity={isActive ? 1 : 0.3}
                      style={{ transition: 'all 0.3s ease' }}
                    />
                    <line
                      x1={dx} y1={dy} x2={lx} y2={ly}
                      stroke={isActive ? colors[i] : 'rgba(0,0,0,0.06)'}
                      strokeWidth="1"
                      strokeDasharray="3 2"
                      opacity={isActive ? 0.4 : 0.15}
                      style={{ transition: 'all 0.3s ease' }}
                    />
                  </g>
                );
              })}

              {/* 3Cs center text */}
              <text
                x="190" y="184"
                textAnchor="middle"
                className="font-display"
                style={{
                  fontSize: 28,
                  fontWeight: 700,
                  fill: visible ? (colors[active] || '#059669') : 'transparent',
                  transition: 'fill 0.5s ease',
                  letterSpacing: '0.04em',
                }}
              >
                3Cs
              </text>
              <text
                x="190" y="202"
                textAnchor="middle"
                style={{
                  fontSize: 8.5,
                  fontWeight: 600,
                  fill: 'rgba(0,0,0,0.22)',
                  letterSpacing: '0.15em',
                  textTransform: 'uppercase',
                  opacity: visible ? 1 : 0,
                  transition: 'opacity 0.6s ease 0.3s',
                }}
              >
                Connect · Contribute · Create
              </text>
            </svg>

            {/* Day labels — positioned OUTSIDE the rings */}
            {experience.days.map((day, i) => {
              const nodeAngles = [210, 90, 330];
              const nodeRadii = [65, 95, 125];
              const labelRadius = nodeRadii[i] + 52;
              const rad = (nodeAngles[i] * Math.PI) / 180;
              const lx = 190 + labelRadius * Math.cos(rad);
              const ly = 190 - labelRadius * Math.sin(rad);
              const isActive = i === active;
              const textAlign = i === 0 ? 'right' : i === 2 ? 'left' : 'center';

              return (
                <button
                  key={i}
                  onClick={() => handleSelect(i)}
                  className="absolute cursor-pointer whitespace-nowrap"
                  style={{
                    left: lx,
                    top: ly,
                    transform: 'translate(-50%, -50%)',
                    textAlign,
                    opacity: visible ? 1 : 0,
                    transition: `opacity 0.5s ease ${0.3 + i * 0.15}s`,
                  }}
                >
                  <span
                    className="block text-xs font-display font-bold tracking-wide uppercase transition-colors duration-300"
                    style={{ color: isActive ? colors[i] : '#9ca3af' }}
                  >
                    {day.day}
                  </span>
                  <span
                    className="block text-[11px] font-medium mt-0.5 transition-colors duration-300"
                    style={{ color: isActive ? '#374151' : '#d1d5db' }}
                  >
                    {day.title}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Content card (swaps on active change) */}
          <div className="relative w-full max-w-2xl">
            {experience.days.map((day, i) => {
              const isActive = i === active;
              const Scene = SCENES[i];

              return (
                <div
                  key={i}
                  className="w-full transition-all duration-500 ease-out"
                  style={{
                    position: i === 0 ? 'relative' : 'absolute',
                    top: 0,
                    left: 0,
                    opacity: isActive ? 1 : 0,
                    transform: isActive ? 'translateY(0) scale(1)' : 'translateY(12px) scale(0.96)',
                    pointerEvents: isActive ? 'auto' : 'none',
                  }}
                >
                  <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden">
                    <div className="flex flex-col sm:flex-row">
                      {/* Scene illustration - prominent */}
                      <div
                        className="sm:w-48 md:w-56 flex-shrink-0 p-5 sm:p-6 flex items-center justify-center"
                        style={{ backgroundColor: `${colors[i]}06` }}
                      >
                        {Scene && <Scene />}
                      </div>

                      {/* Text content */}
                      <div className="flex-1 p-6 sm:p-8">
                        <div className="flex items-center gap-2.5 mb-3">
                          <span
                            className="text-[10px] font-bold tracking-wider uppercase px-2.5 py-1 rounded-full"
                            style={{ backgroundColor: `${colors[i]}12`, color: colors[i] }}
                          >
                            {day.day}
                          </span>
                          <h3 className="font-display text-lg sm:text-xl font-semibold text-gray-900">
                            {day.title}
                          </h3>
                        </div>
                        <p className="text-gray-500 text-[15px] leading-relaxed">
                          {day.description}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Progress dots */}
          <div className="flex gap-2.5 mt-6">
            {experience.days.map((_, i) => (
              <button
                key={i}
                onClick={() => handleSelect(i)}
                className="h-1.5 rounded-full transition-all duration-400 cursor-pointer"
                style={{
                  width: i === active ? 24 : 6,
                  backgroundColor: i === active ? colors[i] : '#d1d5db',
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Scoped animations */}
      <style>{`
        @keyframes expSteam {
          0%, 100% { opacity: 0.12; transform: translateY(0); }
          50% { opacity: 0.22; transform: translateY(-4px); }
        }
        .exp-steam { animation: expSteam 2.5s ease-in-out infinite; }
        @keyframes expSparkle {
          0%, 100% { opacity: 0.1; }
          50% { opacity: 0.3; }
        }
        .exp-sparkle { animation: expSparkle 2s ease-in-out infinite; }
        @keyframes expRipple {
          0% { opacity: 0.35; transform-origin: center; r: inherit; }
          100% { opacity: 0; r: 160; }
        }
        .exp-ripple { animation: expRipple 0.8s ease-out forwards; }
      `}</style>
    </section>
  );
}
