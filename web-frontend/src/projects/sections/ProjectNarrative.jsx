/**
 * ProjectNarrative -- clean storytelling section.
 * Alternating blocks with warm accents, generous spacing.
 * No giant numbers or competing decorations.
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

            return (
              <div key={i} className="flex items-start gap-6">
                {/* Accent marker */}
                <div className="flex-shrink-0 mt-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color, opacity: 0.6 }} />
                </div>

                {/* Text */}
                <div className="flex-1">
                  <h3 className="font-display text-xl sm:text-2xl font-semibold text-gray-900 mb-3 leading-snug">
                    {block.title}
                  </h3>
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
