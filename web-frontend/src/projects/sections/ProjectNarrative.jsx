import { useEffect, useRef, useState } from 'react';
import { NARRATIVE_SCENES } from '../illustrations/ProjectScenes';

/**
 * ProjectNarrative - clean storytelling section.
 * Alternating blocks with scroll-triggered slide-in entrances.
 */
export default function ProjectNarrative({ config }) {
  const { narrative, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.1 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  return (
    <section ref={ref} id="narrative" className="relative py-24 sm:py-32 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Section header */}
        <div
          className="text-center mb-20"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(16px)',
            transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-gray-400">
            {narrative.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-gray-900 tracking-tight leading-snug whitespace-pre-line">
            {narrative.heading}
          </h2>
        </div>

        {/* Story blocks */}
        <div className="space-y-16 sm:space-y-20">
          {narrative.blocks.map((block, i) => {
            const color = i % 2 === 0 ? p : s;
            const Scene = NARRATIVE_SCENES[i];
            const slideDir = i % 2 === 0 ? '-24px' : '24px';

            return (
              <div
                key={i}
                className="flex flex-col md:flex-row items-start gap-6"
                style={{
                  opacity: visible ? 1 : 0,
                  transform: visible ? 'translateX(0)' : `translateX(${slideDir})`,
                  transition: `all 0.7s cubic-bezier(0.4, 0, 0.2, 1) ${0.2 + i * 0.15}s`,
                }}
              >
                {/* Scene illustration (alternating side) */}
                {Scene && (
                  <div className={`flex-shrink-0 w-full md:w-56 ${i % 2 !== 0 ? 'md:order-2' : ''}`}>
                    <Scene className="w-full rounded-lg scene-fade-in" />
                  </div>
                )}

                {/* Text */}
                <div className="flex-1">
                  <div className="flex items-center gap-2.5 mb-2">
                    <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color, opacity: 0.6 }} />
                    <h3 className="font-display text-xl sm:text-2xl font-semibold text-gray-900 leading-snug">
                      {block.title}
                    </h3>
                  </div>
                  <p className="text-gray-500 leading-[1.8] text-[15px] sm:text-base">
                    {block.text}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
