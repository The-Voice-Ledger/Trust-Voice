import { useEffect, useRef, useState } from 'react';

/**
 * ProjectMarket - market metrics on dark background.
 * Scroll-triggered count-up feel with staggered card entrance.
 */
export default function ProjectMarket({ config }) {
  const { market, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const cards = [market.tam, market.sam, market.revenue];
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
    <section ref={ref} id="market" className="relative py-24 sm:py-32 px-6 bg-gray-950 overflow-hidden">
      {/* Subtle radial glow */}
      <div
        className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[400px] rounded-full pointer-events-none"
        style={{
          background: `radial-gradient(ellipse, ${p}08 0%, transparent 70%)`,
          opacity: visible ? 1 : 0,
          transition: 'opacity 1s ease 0.3s',
        }}
      />

      <div className="max-w-5xl mx-auto relative">
        {/* Section header */}
        <div
          className="text-center mb-16"
          style={{
            opacity: visible ? 1 : 0,
            transform: visible ? 'translateY(0)' : 'translateY(16px)',
            transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-white/30">
            {market.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl font-semibold text-white tracking-tight">
            {market.heading}
          </h2>
        </div>

        {/* Metric cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {cards.map((card, i) => (
            <div
              key={i}
              className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-7 hover:bg-white/[0.06] hover:border-white/[0.1] transition-all duration-300"
              style={{
                opacity: visible ? 1 : 0,
                transform: visible ? 'translateY(0) scale(1)' : 'translateY(20px) scale(0.97)',
                transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${0.2 + i * 0.12}s`,
              }}
            >
              {/* Number */}
              <p className="text-4xl sm:text-5xl font-display font-bold mb-2" style={{ color: colors[i] }}>
                {card.value}
              </p>

              {/* Label */}
              <p className="text-sm font-semibold text-white/60 mb-3">{card.label}</p>

              {/* Detail */}
              <p className="text-sm text-white/35 leading-relaxed">{card.detail}</p>

              {/* Accent line */}
              <div
                className="mt-5 h-px rounded-full"
                style={{
                  width: visible ? '40%' : '0%',
                  backgroundColor: colors[i],
                  opacity: 0.3,
                  transition: `width 0.8s cubic-bezier(0.4, 0, 0.2, 1) ${0.5 + i * 0.12}s`,
                }}
              />
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
