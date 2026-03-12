import { useEffect, useRef, useState } from 'react';
import { PILLAR_SCENES } from '../illustrations/ProjectScenes';

/**
 * ProjectPillars - revenue model section.
 * Scroll-triggered staggered card entrance with hover lift.
 */
export default function ProjectPillars({ config }) {
  const { pillars, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.12 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  return (
    <section ref={ref} id="pillars" className="relative py-24 sm:py-32 px-6 bg-stone-50">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div
          className="text-center mb-16"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(16px)',
            transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-gray-900 tracking-tight">
            {pillars.heading}
          </h2>
          <p className="text-gray-400 mt-3 max-w-lg mx-auto text-[15px]">{pillars.subtitle}</p>
        </div>

        {/* Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {pillars.items.map((pillar, i) => (
            <div
              key={i}
              className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              style={{
                opacity: visible ? 1 : 0,
                transform: visible ? 'translateY(0)' : 'translateY(24px)',
                transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${0.15 + i * 0.12}s`,
              }}
            >
              {/* Top color bar - thicker on hover */}
              <div
                className="h-1 transition-all duration-300"
                style={{ backgroundColor: colors[i] }}
              />

              {/* Scene illustration */}
              {PILLAR_SCENES[i] && (() => {
                const Scene = PILLAR_SCENES[i];
                return <Scene className="w-full scene-fade-in" />;
              })()}

              <div className="p-7">
                {/* Highlight */}
                <p className="text-xs font-bold tracking-wide uppercase mb-3" style={{ color: colors[i] }}>
                  {pillar.highlight}
                </p>

                {/* Title + description */}
                <h3 className="font-display text-lg font-semibold text-gray-900 mb-2.5">{pillar.title}</h3>
                <p className="text-gray-500 leading-relaxed text-[15px]">{pillar.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
