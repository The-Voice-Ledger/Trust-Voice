import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectAdvantages -- strategic advantages with bold metrics.
 * Each card shows a large metric number alongside narrative text.
 */
export default function ProjectAdvantages({ config }) {
  const { advantages, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const colors = [p, s, theme.accent, p];

  return (
    <section id="advantages" className="relative py-24 sm:py-32 px-6 bg-gray-50 overflow-hidden">
      <div className="max-w-6xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: s }}>
            {advantages.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 tracking-tight">
            {advantages.heading}
          </h2>
        </div>

        {/* Cards grid */}
        <div className="grid sm:grid-cols-2 gap-6">
          {advantages.items.map((item, i) => {
            const c = colors[i % colors.length];
            return (
              <div
                key={i}
                className="group relative bg-white rounded-2xl border border-gray-100 p-8 shadow-sm hover:shadow-xl transition-all duration-300 overflow-hidden"
              >
                {/* Left accent border */}
                <div
                  className="absolute top-0 left-0 w-[3px] h-full rounded-r-md"
                  style={{ background: `linear-gradient(to bottom, ${c}, transparent)` }}
                />

                <div className="flex items-start gap-6">
                  {/* Metric + icon */}
                  <div className="flex-shrink-0 flex flex-col items-center gap-2">
                    <HexIcon
                      Icon={HiOutlineSparkles}
                      accent={c}
                      size="md"
                      bespoke={item.bespoke}
                    />
                    <div className="text-center">
                      <p className="text-2xl sm:text-3xl font-display font-extrabold" style={{ color: c }}>
                        {item.metric}
                      </p>
                      <p className="text-[10px] text-gray-400 font-semibold uppercase tracking-wider">
                        {item.metricLabel}
                      </p>
                    </div>
                  </div>

                  {/* Text */}
                  <div className="flex-1 pt-1">
                    <h3 className="font-display text-lg font-bold text-gray-900 mb-2">{item.title}</h3>
                    <p className="text-gray-500 leading-relaxed text-[15px]">{item.text}</p>
                  </div>
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
