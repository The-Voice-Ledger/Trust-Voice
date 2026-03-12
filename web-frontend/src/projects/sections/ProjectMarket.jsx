/**
 * ProjectMarket -- market sizing section on warm dark background.
 * Clean metric cards without techy decorations.
 */
export default function ProjectMarket({ config }) {
  const { market, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const cards = [market.tam, market.sam, market.revenue];
  const colors = [p, s, theme.accent];

  return (
    <section id="market" className="relative py-24 sm:py-32 px-6 bg-gray-950">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-white/30">
            {market.sectionLabel}
          </p>
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-white tracking-tight">
            {market.heading}
          </h2>
        </div>

        {/* Metric cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {cards.map((card, i) => (
            <div
              key={i}
              className="rounded-xl border border-white/[0.06] bg-white/[0.03] p-7 hover:bg-white/[0.05] transition-colors duration-300"
            >
              {/* Number */}
              <p className="text-3xl sm:text-4xl font-display font-semibold mb-1" style={{ color: colors[i] }}>
                {card.value}
              </p>

              {/* Label */}
              <p className="text-sm font-medium text-white/60 mb-3">{card.label}</p>

              {/* Detail */}
              <p className="text-sm text-white/35 leading-relaxed">{card.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
