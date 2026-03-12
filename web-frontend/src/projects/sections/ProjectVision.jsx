import { useEffect, useRef, useState } from 'react';
import { VISION_SCENES } from '../illustrations/ProjectScenes';

/**
 * ProjectVision - warm three-column "Core Vision" section.
 * Scroll-triggered staggered card entrance with hover lift.
 */
export default function ProjectVision({ config }) {
  const { vision, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.15 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  return (
    <section ref={ref} id="vision" className="relative py-24 sm:py-32 px-6 bg-stone-50">
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
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-gray-900 tracking-tight leading-snug">
            {vision.heading}
          </h2>
        </div>

        {/* Vision cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {vision.items.map((item, i) => (
            <div
              key={i}
              className="group bg-white rounded-xl p-7 shadow-sm hover:shadow-lg hover:-translate-y-1 transition-all duration-300"
              style={{
                opacity: visible ? 1 : 0,
                transform: visible ? 'translateY(0)' : 'translateY(24px)',
                transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${0.15 + i * 0.12}s`,
              }}
            >
              {/* Scene illustration */}
              {VISION_SCENES[i] && (() => {
                const Scene = VISION_SCENES[i];
                return <Scene className="w-full h-20 mb-4 scene-fade-in" />;
              })()}

              {/* Color dot + label */}
              <div className="flex items-center gap-2.5 mb-4">
                <div
                  className="w-2.5 h-2.5 rounded-full transition-transform duration-300 group-hover:scale-150"
                  style={{ backgroundColor: colors[i] }}
                />
                <span className="text-xs font-semibold tracking-wide uppercase text-gray-400">
                  {item.label}
                </span>
              </div>

              {/* Text */}
              <p className="text-gray-600 leading-relaxed text-[15px]">{item.text}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
