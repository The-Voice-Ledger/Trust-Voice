import HexIcon from '../../components/HexIcon';
import { GlowOrb } from '../../components/SvgDecorations';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectNarrative -- deep storytelling section.
 * Full-width alternating blocks with large typography,
 * numbered sequence, and atmospheric decorations.
 */
export default function ProjectNarrative({ config }) {
  const { narrative, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section id="narrative" className="relative py-24 sm:py-32 px-6 overflow-hidden">
      {/* Subtle background glow */}
      <GlowOrb className="absolute -top-64 -right-64 w-[600px] h-[600px] opacity-[0.03]" color={p} />
      <GlowOrb className="absolute -bottom-48 -left-48 w-[500px] h-[500px] opacity-[0.03]" color={s} />

      <div className="max-w-5xl mx-auto">
        {/* Section header */}
        <div className="text-center mb-20">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: s }}>
            {narrative.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-gray-900 tracking-tight leading-tight whitespace-pre-line">
            {narrative.heading}
          </h2>
          <div className="flex items-center justify-center gap-3 mt-6">
            <div className="w-16 h-px" style={{ background: p }} />
            <HexIcon Icon={HiOutlineSparkles} accent={p} size="xs" bespoke="leaf" />
            <div className="w-16 h-px" style={{ background: s }} />
          </div>
        </div>

        {/* Story blocks */}
        <div className="space-y-20 sm:space-y-28">
          {narrative.blocks.map((block, i) => {
            const isEven = i % 2 === 0;
            const color = isEven ? p : s;

            return (
              <div
                key={i}
                className={`flex flex-col ${isEven ? 'md:flex-row' : 'md:flex-row-reverse'} items-start gap-8 md:gap-14`}
              >
                {/* Illustration column */}
                <div className="flex-shrink-0 w-full md:w-auto flex flex-col items-center md:items-start">
                  {/* Sequence number */}
                  <span
                    className="text-[80px] sm:text-[100px] leading-none font-display font-black opacity-[0.06] select-none"
                    style={{ color }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                  <div className="-mt-8">
                    <HexIcon
                      Icon={HiOutlineSparkles}
                      accent={color}
                      size="lg"
                      bespoke={block.bespoke || block.icon}
                      glow
                    />
                  </div>
                </div>

                {/* Text column */}
                <div className="flex-1 pt-2">
                  <h3 className="font-display text-2xl sm:text-3xl font-bold text-gray-900 mb-4 leading-snug">
                    {block.title}
                  </h3>
                  <p className="text-gray-600 leading-[1.8] text-base sm:text-[17px]">
                    {block.text}
                  </p>
                  {/* Gradient underline */}
                  <div className="mt-6 h-[2px] w-20 rounded-full" style={{ background: `linear-gradient(90deg, ${color}, transparent)` }} />
                </div>
              </div>
            );
          })}
        </div>
      </div>
    </section>
  );
}
