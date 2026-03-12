import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectMarket -- "Green Gold Economy" market sizing section.
 * Three bold metric cards: TAM, SAM, Obtainable Revenue.
 */
export default function ProjectMarket({ config }) {
  const { market, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const cards = [market.tam, market.sam, market.revenue];
  const colors = [p, s, theme.accent];

  return (
    <section id="market" className="relative py-24 sm:py-32 px-6 bg-gray-950 overflow-hidden">
      {/* Subtle background grid */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.03]">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="mktGrid" x="0" y="0" width="60" height="60" patternUnits="userSpaceOnUse">
              <path d="M60 0H0v60" fill="none" stroke="white" strokeWidth="0.4" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#mktGrid)" />
        </svg>
      </div>

      <div className="relative max-w-6xl mx-auto z-10">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: s }}>
            {market.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-white tracking-tight">
            {market.heading}
          </h2>
        </div>

        {/* Metric cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {cards.map((card, i) => (
            <div
              key={i}
              className="group relative rounded-2xl border border-white/5 bg-white/[0.03] backdrop-blur-sm p-8 hover:bg-white/[0.06] transition-all duration-300 overflow-hidden"
            >
              {/* Top accent */}
              <div
                className="absolute top-0 left-0 right-0 h-[2px]"
                style={{ background: `linear-gradient(90deg, ${colors[i]}, transparent)` }}
              />

              {/* Icon */}
              <div className="mb-5">
                <HexIcon
                  Icon={HiOutlineSparkles}
                  accent={colors[i]}
                  size="md"
                  bespoke={card.bespoke}
                />
              </div>

              {/* Big number */}
              <p className="text-4xl sm:text-5xl font-display font-extrabold mb-2" style={{ color: colors[i] }}>
                {card.value}
              </p>

              {/* Label */}
              <p className="text-sm font-semibold text-white/70 mb-2">{card.label}</p>

              {/* Detail */}
              <p className="text-sm text-white/40 leading-relaxed">{card.detail}</p>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
