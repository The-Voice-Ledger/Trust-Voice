import { PILLAR_SCENES } from '../illustrations/ProjectScenes';

/**
 * ProjectPillars -- revenue model section.
 * Clean cards with warm top accent, scene illustration, generous spacing.
 */
export default function ProjectPillars({ config }) {
  const { pillars, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  return (
    <section id="pillars" className="relative py-24 sm:py-32 px-6 bg-stone-50">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-900 tracking-tight">
            {pillars.heading}
          </h2>
          <p className="text-gray-400 mt-3 max-w-lg mx-auto text-[15px]">{pillars.subtitle}</p>
        </div>

        {/* Cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {pillars.items.map((pillar, i) => (
            <div
              key={i}
              className="bg-white rounded-xl overflow-hidden shadow-sm hover:shadow-md transition-shadow duration-300"
            >
              {/* Top color bar */}
              <div className="h-1" style={{ backgroundColor: colors[i] }} />

              {/* Scene illustration */}
              {PILLAR_SCENES[i] && (() => {
                const Scene = PILLAR_SCENES[i];
                return <Scene className="w-full scene-fade-in" />;
              })()}

              <div className="p-7">
                {/* Highlight */}
                <p className="text-xs font-semibold tracking-wide uppercase mb-3" style={{ color: colors[i] }}>
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
