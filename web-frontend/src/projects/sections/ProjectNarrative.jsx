import { NARRATIVE_SCENES } from '../illustrations/ProjectScenes';

/**
 * ProjectNarrative -- clean storytelling section.
 * Alternating blocks with warm accents, generous spacing.
 * Scene illustrations accompany each story.
 */
export default function ProjectNarrative({ config }) {
  const { narrative, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section id="narrative" className="relative py-24 sm:py-32 px-6">
      <div className="max-w-4xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-20">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-gray-400">
            {narrative.sectionLabel}
          </p>
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-900 tracking-tight leading-snug whitespace-pre-line">
            {narrative.heading}
          </h2>
        </div>

        {/* Story blocks */}
        <div className="space-y-16 sm:space-y-20">
          {narrative.blocks.map((block, i) => {
            const color = i % 2 === 0 ? p : s;

            const Scene = NARRATIVE_SCENES[i];

            return (
              <div key={i} className="flex flex-col md:flex-row items-start gap-6">
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
