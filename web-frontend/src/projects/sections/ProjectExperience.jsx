import { EXPERIENCE_SCENES } from '../illustrations/ProjectScenes';

/**
 * ProjectExperience -- the "Live-Work-Learn" timeline.
 * Clean vertical flow with scene illustrations and warm cards.
 */
export default function ProjectExperience({ config }) {
  const { experience, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  return (
    <section id="experience" className="relative py-24 sm:py-32 px-6 bg-stone-50">
      <div className="max-w-3xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-900 tracking-tight">
            {experience.heading}
          </h2>
          <p className="text-gray-400 mt-3 max-w-lg mx-auto text-[15px] leading-relaxed">
            {experience.subtitle}
          </p>
        </div>

        {/* Timeline */}
        <div className="relative">
          {/* Vertical connector */}
          <div
            className="absolute left-[11px] top-2 bottom-2 w-px hidden sm:block"
            style={{ background: `linear-gradient(to bottom, ${p}30, ${s}30, transparent)` }}
          />

          <div className="space-y-10">
            {experience.days.map((day, i) => (
              <div key={i} className="flex items-start gap-6">
                {/* Dot node */}
                <div className="flex-shrink-0 mt-2 relative z-10">
                  <div
                    className="w-[22px] h-[22px] rounded-full border-[3px] border-white"
                    style={{ backgroundColor: colors[i] }}
                  />
                </div>

                {/* Content card */}
                <div className="flex-1 bg-white rounded-xl p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
                  <div className="flex items-center gap-2.5 mb-2">
                    <span className="text-xs font-semibold tracking-wide uppercase" style={{ color: colors[i] }}>
                      {day.day}
                    </span>
                    <span className="text-gray-200">·</span>
                    <h3 className="font-display text-base sm:text-lg font-semibold text-gray-900">{day.title}</h3>
                  </div>
                  <p className="text-gray-500 leading-relaxed text-[15px]">{day.description}</p>

                  {/* Scene illustration */}
                  {EXPERIENCE_SCENES[i] && (() => {
                    const Scene = EXPERIENCE_SCENES[i];
                    return <Scene className="w-full mt-4 rounded-lg scene-fade-in" />;
                  })()}
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </section>
  );
}
