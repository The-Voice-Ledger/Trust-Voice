/**
 * ProjectFinancials -- investment breakdown.
 * Clean dark section with toned-down callout and warm tables.
 */
export default function ProjectFinancials({ config }) {
  const { financials, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;

  return (
    <section id="financials" className="relative py-24 sm:py-32 px-6 bg-gray-950">
      <div className="max-w-5xl mx-auto">
        {/* Header with total raise inline */}
        <div className="text-center mb-14">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-white/30">
            {financials.sectionLabel}
          </p>
          <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-white tracking-tight mb-4">
            {financials.heading}
          </h2>
          <div className="inline-flex items-baseline gap-2">
            <span className="text-3xl sm:text-4xl font-display font-semibold" style={{ color: p }}>
              {financials.totalRaise}
            </span>
            <span className="text-sm text-white/35 font-medium">
              {financials.totalRaiseLabel}
            </span>
          </div>
        </div>

        {/* CAPEX + Projections side by side */}
        <div className="grid md:grid-cols-2 gap-6">
          {/* CAPEX */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
            <div className="px-6 py-4 font-display font-semibold text-white text-base border-b border-white/[0.06]">
              Capital Deployment
            </div>
            <div className="divide-y divide-white/[0.04]">
              {financials.capex.map((row, i) => (
                <div key={i} className="px-6 py-4 flex items-start justify-between gap-4">
                  <div>
                    <p className="font-medium text-white/80 text-[15px]">{row.item}</p>
                    <p className="text-white/25 text-xs mt-0.5">{row.detail}</p>
                  </div>
                  <span className="font-display font-semibold text-[15px] whitespace-nowrap" style={{ color: p }}>
                    {row.amount}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Projections */}
          <div className="rounded-xl border border-white/[0.06] bg-white/[0.02] overflow-hidden">
            <div className="px-6 py-4 font-display font-semibold text-white text-base border-b border-white/[0.06]">
              Revenue Projections
            </div>
            <table className="w-full text-left">
              <thead>
                <tr className="text-[11px] uppercase tracking-wider text-white/25 border-b border-white/[0.04]">
                  <th className="px-6 py-3 font-medium">Period</th>
                  <th className="px-4 py-3 font-medium">Revenue</th>
                  <th className="px-4 py-3 font-medium">EBITDA</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-white/[0.04]">
                {financials.projections.map((row, i) => (
                  <tr key={i}>
                    <td className="px-6 py-4">
                      <span className="font-medium text-white/80 text-[15px]">{row.year}</span>
                      <span className="text-white/25 text-xs ml-2">{row.label}</span>
                    </td>
                    <td className="px-4 py-4 font-display font-semibold text-sm" style={{ color: p }}>
                      {row.revenue}
                    </td>
                    <td className="px-4 py-4 font-display font-semibold text-sm" style={{ color: row.ebitda ? s : 'transparent' }}>
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
