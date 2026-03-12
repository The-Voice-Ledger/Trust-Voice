import HexIcon from '../../components/HexIcon';
import { GlowOrb } from '../../components/SvgDecorations';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectExperience -- the "Live-Work-Learn" immersive timeline.
 * Three rich day-cards with connecting vertical line and decorations.
 */
export default function ProjectExperience({ config }) {
  const { experience, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  return (
    <section id="experience" className="relative py-24 sm:py-32 px-6 overflow-hidden">
      {/* Background glow */}
      <GlowOrb className="absolute -top-48 right-0 w-[500px] h-[500px] opacity-[0.03]" color={s} />

      <div className="max-w-4xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-20">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: p }}>
            {experience.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
            {experience.heading}
          </h2>
          <p className="text-gray-500 mt-4 max-w-xl mx-auto leading-relaxed">
            {experience.subtitle}
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical connector */}
          <div
            className="absolute left-10 md:left-[39px] top-0 bottom-0 w-px hidden sm:block"
            style={{ background: `linear-gradient(to bottom, ${p}, ${s}, ${theme.accent}, transparent)` }}
          />

          <div className="space-y-16">
            {experience.days.map((day, i) => (
              <div key={i} className="flex items-start gap-8 md:gap-12">
                {/* Icon node */}
                <div className="relative flex-shrink-0 z-10">
                  {/* Glow ring behind icon */}
                  <div
                    className="absolute inset-0 rounded-full blur-xl opacity-20"
                    style={{ backgroundColor: colors[i] }}
                  />
                  <HexIcon
                    Icon={HiOutlineSparkles}
                    accent={colors[i]}
                    size="lg"
                    bespoke={day.bespoke}
                    glow
                  />
                </div>

                {/* Content card */}
                <div className="flex-1 bg-white rounded-2xl border border-gray-100 p-6 sm:p-8 shadow-sm hover:shadow-lg transition-shadow duration-300">
                  <div className="flex items-center gap-3 mb-3">
                    <span
                      className="text-xs font-bold tracking-[0.15em] uppercase px-3 py-1 rounded-md"
                      style={{
                        color: colors[i],
                        backgroundColor: `${colors[i]}0D`,
                      }}
                    >
                      {day.day}
                    </span>
                    <span className="text-xs text-gray-300">|</span>
                    <h3 className="font-display text-lg sm:text-xl font-bold text-gray-900">{day.title}</h3>
                  </div>
                  <p className="text-gray-600 leading-relaxed text-[15px] sm:text-base">{day.description}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
