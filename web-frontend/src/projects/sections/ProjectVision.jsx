import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectVision -- three-column "Core Vision" section.
 * Concept / Mission / Investment cards with bespoke hex icons.
 */
export default function ProjectVision({ config }) {
  const { vision, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  const colors = [p, s, theme.accent];

  return (
    <section id="vision" className="relative py-24 sm:py-32 px-6">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: p }}>
            {vision.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 tracking-tight leading-tight">
            {vision.heading}
          </h2>
        </div>

        {/* Vision cards */}
        <div className="grid md:grid-cols-3 gap-8">
          {vision.items.map((item, i) => (
            <div
              key={i}
              className="group relative bg-white rounded-2xl border border-gray-100 p-8 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 overflow-hidden"
            >
              {/* Top gradient line */}
              <div
                className="absolute top-0 left-0 right-0 h-[3px]"
                style={{ background: `linear-gradient(90deg, ${colors[i]}, transparent)` }}
              />

              {/* Corner tech decoration */}
              <svg className="absolute -top-2 -right-2 w-24 h-24 pointer-events-none opacity-[0.04]" viewBox="0 0 80 80" fill="none">
                <circle cx="60" cy="20" r="18" stroke={colors[i]} strokeWidth="0.5" />
                <circle cx="60" cy="20" r="8" stroke={colors[i]} strokeWidth="0.3" strokeDasharray="2 4" />
              </svg>

              {/* Label badge */}
              <div className="mb-5">
                <span
                  className="inline-block text-[11px] font-bold tracking-[0.15em] uppercase px-3 py-1 rounded-md"
                  style={{ color: colors[i], backgroundColor: `${colors[i]}0D` }}
                >
                  {item.label}
                </span>
              </div>

              {/* Icon */}
              <div className="mb-5">
                <HexIcon
                  Icon={HiOutlineSparkles}
                  accent={colors[i]}
                  size="lg"
                  bespoke={item.bespoke}
                />
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
