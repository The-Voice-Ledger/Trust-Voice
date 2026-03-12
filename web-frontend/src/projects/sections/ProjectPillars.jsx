import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectPillars -- three-pronged revenue model with rich cards.
 */
export default function ProjectPillars({ config }) {
  const { pillars, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  return (
    <section id="pillars" className="relative py-24 sm:py-32 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: p }}>
            {pillars.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
            {pillars.heading}
          </h2>
          <p className="text-gray-500 mt-3 max-w-xl mx-auto">{pillars.subtitle}</p>
        </div>

        {/* Cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {pillars.items.map((pillar, i) => (
            <div
              key={i}
              className="group relative rounded-2xl bg-white border border-gray-100 overflow-hidden shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300"
            >
              {/* Top gradient band */}
              <div
                className="h-1.5"
                style={{ background: `linear-gradient(90deg, ${colors[i]}, ${colors[(i + 1) % 3]})` }}
              />

              {/* Corner SVG accent */}
              <svg className="absolute top-4 right-4 w-24 h-24 pointer-events-none" viewBox="0 0 80 80" fill="none">
                <circle cx="55" cy="22" r="16" stroke={colors[i]} strokeWidth="0.4" opacity="0.06" />
                <circle cx="55" cy="22" r="7" stroke={colors[i]} strokeWidth="0.3" strokeDasharray="2 4" opacity="0.04" />
              </svg>

              <div className="p-8">
                {/* Highlight badge */}
                <span
                  className="inline-block text-[10px] font-bold tracking-[0.15em] uppercase px-2.5 py-1 rounded-md mb-5"
                  style={{ color: colors[i], backgroundColor: `${colors[i]}0D` }}
                >
                  {pillar.highlight}
                </span>

                {/* Icon */}
                <div className="mb-5">
                  <HexIcon
                    Icon={HiOutlineSparkles}
                    accent={colors[i]}
                    size="lg"
                    bespoke={pillar.bespoke}
                  />
                </div>

                {/* Title + description */}
                <h3 className="font-display text-xl font-bold text-gray-900 mb-3">{pillar.title}</h3>
                <p className="text-gray-500 leading-relaxed text-[15px]">{pillar.description}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
}
