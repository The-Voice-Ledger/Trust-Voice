import { useEffect, useRef, useState } from 'react';

/**
 * ProjectExperience - compact animated "day arc" for Live-Work-Learn.
 *
 * Three days rendered as an auto-rotating horizontal strip with a
 * semicircular progress arc, staggered fade-in, and subtle scene
 * colour accents. Much less vertical space than the old timeline.
 */

/* Mini scene vignettes (inline SVG, no external dependency) */
function SceneConnection() {
  return (
    <svg viewBox="0 0 120 60" className="w-full h-auto opacity-40">
      {/* Tea cup */}
      <rect x="45" y="28" width="30" height="18" rx="4" fill="#059669" opacity="0.3" />
      <path d="M75 34 Q82 34 82 40 Q82 46 75 46" fill="none" stroke="#059669" strokeWidth="1.5" opacity="0.25" />
      {/* Steam wisps */}
      <path d="M55 26 Q53 20 56 16" fill="none" stroke="#059669" strokeWidth="1" opacity="0.2" className="exp-steam" />
      <path d="M62 24 Q60 18 63 14" fill="none" stroke="#059669" strokeWidth="1" opacity="0.15" className="exp-steam" style={{ animationDelay: '0.4s' }} />
      {/* Leaf */}
      <ellipse cx="35" cy="36" rx="8" ry="4" fill="#059669" opacity="0.2" transform="rotate(-30 35 36)" />
      <line x1="35" y1="36" x2="28" y2="42" stroke="#059669" strokeWidth="0.8" opacity="0.2" />
    </svg>
  );
}

function SceneContribution() {
  return (
    <svg viewBox="0 0 120 60" className="w-full h-auto opacity-40">
      {/* Sun */}
      <circle cx="90" cy="15" r="8" fill="#D97706" opacity="0.15" />
      {/* Person harvesting */}
      <circle cx="40" cy="20" r="3" fill="#059669" opacity="0.3" />
      <line x1="40" y1="23" x2="40" y2="34" stroke="#059669" strokeWidth="1.5" opacity="0.3" />
      <line x1="40" y1="27" x2="34" y2="32" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      <line x1="40" y1="27" x2="47" y2="30" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      <line x1="40" y1="34" x2="36" y2="44" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      <line x1="40" y1="34" x2="44" y2="44" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      {/* Moringa branch being picked */}
      <path d="M47 30 Q55 28 60 22" fill="none" stroke="#059669" strokeWidth="1" opacity="0.2" />
      <ellipse cx="60" cy="18" rx="6" ry="3" fill="#059669" opacity="0.15" />
      {/* Oil press silhouette */}
      <rect x="72" y="30" width="16" height="14" rx="2" fill="#D97706" opacity="0.12" />
      <circle cx="80" cy="37" r="3" fill="#D97706" opacity="0.1" />
    </svg>
  );
}

function SceneCreation() {
  return (
    <svg viewBox="0 0 120 60" className="w-full h-auto opacity-40">
      {/* Product bottles */}
      <rect x="25" y="26" width="10" height="20" rx="2" fill="#059669" opacity="0.25" />
      <rect x="28" y="22" width="4" height="4" rx="1" fill="#059669" opacity="0.2" />
      <rect x="42" y="30" width="8" height="16" rx="2" fill="#D97706" opacity="0.2" />
      <circle cx="46" cy="38" r="2" fill="#D97706" opacity="0.15" />
      {/* Person */}
      <circle cx="72" cy="22" r="3" fill="#059669" opacity="0.3" />
      <line x1="72" y1="25" x2="72" y2="36" stroke="#059669" strokeWidth="1.5" opacity="0.3" />
      <line x1="72" y1="29" x2="65" y2="33" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      <line x1="72" y1="29" x2="79" y2="33" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      <line x1="72" y1="36" x2="68" y2="46" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      <line x1="72" y1="36" x2="76" y2="46" stroke="#059669" strokeWidth="1.2" opacity="0.25" />
      {/* Sparkle */}
      <g opacity="0.2" className="exp-sparkle">
        <line x1="95" y1="18" x2="95" y2="28" stroke="#D97706" strokeWidth="1" />
        <line x1="90" y1="23" x2="100" y2="23" stroke="#D97706" strokeWidth="1" />
        <line x1="91.5" y1="19.5" x2="98.5" y2="26.5" stroke="#D97706" strokeWidth="0.8" />
        <line x1="98.5" y1="19.5" x2="91.5" y2="26.5" stroke="#D97706" strokeWidth="0.8" />
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
      { threshold: 0.2 },
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

  /* Arc progress SVG */
  const arcR = 38;
  const arcCirc = Math.PI * arcR; // semicircle
  const arcSegment = arcCirc / experience.days.length;

  return (
    <section
      ref={ref}
      id="experience"
      className="relative py-20 sm:py-24 px-6 overflow-hidden"
      style={{ background: 'linear-gradient(to bottom, #fafaf9, #f5f5f0, #fafaf9)' }}
    >
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="text-center mb-10">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-2 text-gray-400">
            {experience.sectionLabel}
          </p>
          <h2 className="font-display text-2xl sm:text-3xl font-semibold text-gray-900 tracking-tight">
            {experience.heading}
          </h2>
          <p className="text-gray-400 mt-2 max-w-md mx-auto text-sm leading-relaxed">
            {experience.subtitle}
          </p>
        </div>

        {/* Day selector arc + content */}
        <div className="flex flex-col items-center">

          {/* Arc indicator with day dots */}
          <div className="relative mb-10" style={{ width: 320, height: 120 }}>
            <svg width="320" height="120" viewBox="0 0 320 120">
              {/* Background arc */}
              <path
                d="M 30 105 A 130 130 0 0 1 290 105"
                fill="none"
                stroke="rgba(0,0,0,0.06)"
                strokeWidth="3"
                strokeLinecap="round"
              />
              {/* Active progress arc */}
              {visible && (
                <path
                  d="M 30 105 A 130 130 0 0 1 290 105"
                  fill="none"
                  stroke={colors[active]}
                  strokeWidth="3"
                  strokeLinecap="round"
                  strokeDasharray={`${(active + 1) * 72} 500`}
                  style={{ transition: 'stroke-dasharray 0.6s ease, stroke 0.4s ease' }}
                />
              )}
            </svg>

            {/* Day dots positioned along the arc */}
            {experience.days.map((day, i) => {
              const angle = Math.PI - (Math.PI * (i + 0.5)) / experience.days.length;
              const cx = 160 + 130 * Math.cos(angle);
              const cy = 105 - 130 * Math.sin(angle);
              const isActive = i === active;

              return (
                <button
                  key={i}
                  onClick={() => handleSelect(i)}
                  className="absolute flex flex-col items-center gap-1.5 -translate-x-1/2 -translate-y-1/2 group cursor-pointer"
                  style={{
                    left: cx,
                    top: cy,
                    opacity: visible ? 1 : 0,
                    transition: `opacity 0.4s ease ${0.3 + i * 0.15}s`,
                  }}
                >
                  <span
                    className="w-6 h-6 rounded-full border-2 transition-all duration-300"
                    style={{
                      borderColor: colors[i],
                      backgroundColor: isActive ? colors[i] : 'white',
                      transform: isActive ? 'scale(1.3)' : 'scale(1)',
                    }}
                  />
                  <span
                    className="text-[11px] font-display font-semibold whitespace-nowrap transition-colors duration-300"
                    style={{ color: isActive ? colors[i] : '#9ca3af' }}
                  >
                    {day.day}
                  </span>
                </button>
              );
            })}
          </div>

          {/* Content card (swaps on active change) */}
          <div className="relative w-full max-w-lg">
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
                    transform: isActive ? 'translateY(0) scale(1)' : 'translateY(8px) scale(0.97)',
                    pointerEvents: isActive ? 'auto' : 'none',
                  }}
                >
                  <div className="bg-white rounded-2xl p-6 sm:p-8 shadow-sm border border-gray-100">
                    <div className="flex items-start gap-5">
                      {/* Inline scene */}
                      <div className="w-24 sm:w-28 flex-shrink-0">
                        {Scene && <Scene />}
                      </div>

                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-2 mb-1.5">
                          <span
                            className="text-[10px] font-bold tracking-wider uppercase px-2 py-0.5 rounded-full"
                            style={{ backgroundColor: `${colors[i]}15`, color: colors[i] }}
                          >
                            {day.day}
                          </span>
                          <h3 className="font-display text-base sm:text-lg font-semibold text-gray-900">
                            {day.title}
                          </h3>
                        </div>
                        <p className="text-gray-500 text-sm leading-relaxed">
                          {day.description}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>

          {/* Dot indicators */}
          <div className="flex gap-2 mt-5">
            {experience.days.map((_, i) => (
              <button
                key={i}
                onClick={() => handleSelect(i)}
                className="w-1.5 h-1.5 rounded-full transition-all duration-300 cursor-pointer"
                style={{
                  backgroundColor: i === active ? colors[i] : '#d1d5db',
                  transform: i === active ? 'scale(1.5)' : 'scale(1)',
                }}
              />
            ))}
          </div>
        </div>
      </div>

      {/* Scoped animations */}
      <style>{`
        @keyframes expSteam {
          0%, 100% { opacity: 0.15; transform: translateY(0); }
          50% { opacity: 0.25; transform: translateY(-3px); }
        }
        .exp-steam { animation: expSteam 2.5s ease-in-out infinite; }
        @keyframes expSparkle {
          0%, 100% { opacity: 0.15; }
          50% { opacity: 0.35; }
        }
        .exp-sparkle { animation: expSparkle 2s ease-in-out infinite; }
      `}</style>
    </section>
  );
}
