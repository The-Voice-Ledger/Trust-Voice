/**
 * ProjectVision -- warm three-column "Core Vision" section.
 * Clean cards with subtle color accent, generous white space.
 */
export default function ProjectVision({ config }) {
  const { vision, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent];

  return (
    <section id="vision" className="relative py-24 sm:py-32 px-6 bg-stone-50">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-900 tracking-tight leading-snug">
            {vision.heading}
          </h2>
        </div>

        {/* Vision cards */}
        <div className="grid md:grid-cols-3 gap-6">
          {vision.items.map((item, i) => (
            <div
              key={i}
              className="group bg-white rounded-xl p-7 shadow-sm hover:shadow-md transition-shadow duration-300"
            >
              {/* Color dot + label */}
              <div className="flex items-center gap-2.5 mb-4">
                <div className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: colors[i] }} />
                <span className="text-xs font-semibold tracking-wide uppercase text-gray-400">
                  {item.label}
                </span>
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
