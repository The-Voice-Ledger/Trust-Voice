import { useEffect, useRef, useState } from 'react';

/**
 * ProjectAdvantages - strategic advantages.
 * Scroll-triggered staggered entrance with bolder metrics.
 */
export default function ProjectAdvantages({ config }) {
  const { advantages, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent, p];

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
    <section ref={ref} id="advantages" className="relative py-24 sm:py-32 px-6">
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
            {advantages.heading}
          </h2>
        </div>

        {/* Cards */}
        <div className="grid sm:grid-cols-2 gap-5">
          {advantages.items.map((item, i) => {
            const c = colors[i % colors.length];
            return (
              <div
                key={i}
                className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm hover:shadow-lg hover:-translate-y-0.5 transition-all duration-300"
                style={{
                  opacity: visible ? 1 : 0,
                  transform: visible ? 'translateY(0)' : 'translateY(20px)',
                  transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${0.15 + i * 0.1}s`,
                }}
              >
                {/* Metric row */}
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-3xl font-display font-bold" style={{ color: c }}>
                    {item.metric}
                  </span>
                  <span className="text-[11px] text-gray-400 font-semibold uppercase tracking-wide">
                    {item.metricLabel}
                  </span>
                </div>

                {/* Title + text */}
                <h3 className="font-display text-base font-semibold text-gray-900 mb-1.5">{item.title}</h3>
                <p className="text-gray-500 leading-relaxed text-[14px]">{item.text}</p>

                {/* Accent line */}
                <div
                  className="mt-4 h-px rounded-full"
                  style={{
                    width: visible ? '30%' : '0%',
                    backgroundColor: c,
                    opacity: 0.2,
                    transition: `width 0.8s cubic-bezier(0.4, 0, 0.2, 1) ${0.5 + i * 0.1}s`,
                  }}
                />
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
