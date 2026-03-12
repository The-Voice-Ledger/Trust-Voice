/**
 * ProjectAdvantages -- strategic advantages.
 * Clean horizontal cards with inline metric, no heavy decorations.
 */
export default function ProjectAdvantages({ config }) {
  const { advantages, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent, p];

  return (
    <section id="advantages" className="relative py-24 sm:py-32 px-6">
      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-gray-900 tracking-tight">
            {advantages.heading}
          </h2>
        </div>

        {/* Cards */}
        <div className="grid sm:grid-cols-2 gap-5">
          {advantages.items.map((item, i) => {
            const c = colors[i % colors.length];
            return (
              <div
                key={i}
                className="bg-white rounded-xl border border-gray-100 p-6 shadow-sm hover:shadow-md transition-shadow duration-300"
              >
                {/* Metric row */}
                <div className="flex items-baseline gap-2 mb-2">
                  <span className="text-2xl font-display font-semibold" style={{ color: c }}>
                    {item.metric}
                  </span>
                  <span className="text-[11px] text-gray-400 font-medium uppercase tracking-wide">
                    {item.metricLabel}
                  </span>
                </div>

                {/* Title + text */}
                <h3 className="font-display text-base font-semibold text-gray-900 mb-1.5">{item.title}</h3>
                <p className="text-gray-500 leading-relaxed text-[14px]">{item.text}</p>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
