import HexIcon from '../../components/HexIcon';
import { HiOutlineSparkles } from '../../components/icons';

/**
 * ProjectFinancials -- investment breakdown with CAPEX table,
 * projections, and prominent total raise callout.
 */
export default function ProjectFinancials({ config }) {
  const { financials, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section id="financials" className="relative py-24 sm:py-32 px-6 bg-gray-950 overflow-hidden">
      {/* Background grid */}
      <div className="absolute inset-0 pointer-events-none opacity-[0.02]">
        <svg className="w-full h-full" xmlns="http://www.w3.org/2000/svg">
          <defs>
            <pattern id="finGrid" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
              <circle cx="20" cy="20" r="0.5" fill="white" />
            </pattern>
          </defs>
          <rect width="100%" height="100%" fill="url(#finGrid)" />
        </svg>
      </div>

      <div className="relative max-w-6xl mx-auto z-10">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-xs font-bold tracking-[0.25em] uppercase mb-3" style={{ color: s }}>
            {financials.sectionLabel}
          </p>
          <h2 className="font-display text-3xl sm:text-4xl md:text-5xl font-bold text-white tracking-tight">
            {financials.heading}
          </h2>
        </div>

        {/* Total raise callout */}
        <div className="flex items-center justify-center mb-14">
          <div className="text-center">
            <HexIcon Icon={HiOutlineSparkles} accent={p} size="lg" bespoke="money" glow className="mx-auto mb-4" />
            <p className="text-5xl sm:text-6xl font-display font-extrabold" style={{ color: p }}>
              {financials.totalRaise}
            </p>
            <p className="text-sm text-white/40 font-semibold uppercase tracking-wider mt-2">
              {financials.totalRaiseLabel}
            </p>
          </div>
        </div>

        {/* CAPEX + Projections side by side */}
        <div className="grid md:grid-cols-2 gap-8">
          {/* CAPEX */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.03] overflow-hidden">
            <div
              className="px-6 py-4 font-display font-bold text-white text-lg border-b border-white/5"
              style={{ background: `linear-gradient(135deg, ${p}22, transparent)` }}
            >
              Capital Deployment
            </div>
            <div className="divide-y divide-white/5">
              {financials.capex.map((row, i) => (
                <div key={i} className="px-6 py-5 flex items-start justify-between gap-4">
                  <div>
                    <p className="font-semibold text-white/90 text-[15px]">{row.item}</p>
                    <p className="text-white/30 text-xs mt-1">{row.detail}</p>
                  </div>
                  <span className="font-display font-bold text-[15px] whitespace-nowrap" style={{ color: p }}>
                    {row.amount}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Projections */}
          <div className="rounded-2xl border border-white/5 bg-white/[0.03] overflow-hidden">
            <div
              className="px-6 py-4 font-display font-bold text-white text-lg border-b border-white/5"
              style={{ background: `linear-gradient(135deg, ${s}22, transparent)` }}
            >
              Revenue Projections
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="text-[11px] uppercase tracking-wider text-white/30 border-b border-white/5">
                  <th className="px-6 py-3 font-semibold">Period</th>
                  <th className="px-4 py-3 font-semibold">Revenue</th>
                  <th className="px-4 py-3 font-semibold">EBITDA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/5">
                {financials.projections.map((row, i) => (
                  <tr key={i}>
                    <td className="px-6 py-5">
                      <span className="font-semibold text-white/90 text-[15px]">{row.year}</span>
                      <span className="text-white/30 text-xs ml-2">{row.label}</span>
                    </td>
                    <td className="px-4 py-5 font-display font-bold" style={{ color: p }}>
                      {row.revenue}
                    </td>
                    <td className="px-4 py-5 font-display font-bold" style={{ color: row.ebitda ? s : 'transparent' }}>
                      {row.ebitda || '--'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </section>
  );
}
