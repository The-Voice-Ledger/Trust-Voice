/**
 * ProjectFinancials - animated fundraising visualization.
 *
 * Replaces the formal table layout with:
 *  1. Animated progress rings for each CAPEX allocation
 *  2. A rising staircase growth path
 *  3. IntersectionObserver-triggered staggered entrances
 */
import { useEffect, useRef, useState } from 'react';

function parseAmountToNumber(amount = '') {
  const cleaned = String(amount).replace(/[$,\s]/g, '').toUpperCase();
  if (!cleaned) return 0;
  if (cleaned.endsWith('K')) return Number(cleaned.slice(0, -1)) * 1000;
  if (cleaned.endsWith('M')) return Number(cleaned.slice(0, -1)) * 1000000;
  return Number(cleaned);
}

function deriveCapexShares(capex = [], primary = '#059669', secondary = '#D97706') {
  const total = capex.reduce((sum, row) => sum + parseAmountToNumber(row.amount), 0);
  if (!total) return capex.map((_, i) => ({ pct: 0, color: i % 2 === 0 ? primary : secondary }));
  return capex.map((row, i) => {
    const value = parseAmountToNumber(row.amount);
    const pct = Math.round((value / total) * 1000) / 10;
    return { pct, color: i % 2 === 0 ? primary : secondary };
  });
}

/* Progress ring component (animated SVG circle) */
function Ring({ pct, color, size = 64, delay = 0, visible }) {
  const r = (size - 8) / 2;
  const circ = 2 * Math.PI * r;
  const offset = circ - (pct / 100) * circ;

  return (
    <svg width={size} height={size} className="flex-shrink-0">
      {/* Track */}
      <circle cx={size / 2} cy={size / 2} r={r} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="4" />
      {/* Fill */}
      <circle
        cx={size / 2}
        cy={size / 2}
        r={r}
        fill="none"
        stroke={color}
        strokeWidth="4"
        strokeLinecap="round"
        strokeDasharray={circ}
        strokeDashoffset={visible ? offset : circ}
        transform={`rotate(-90 ${size / 2} ${size / 2})`}
        style={{
          transition: `stroke-dashoffset 1.2s cubic-bezier(0.4, 0, 0.2, 1) ${delay}s`,
        }}
      />
      {/* Center label */}
      <text
        x={size / 2}
        y={size / 2 + 1}
        textAnchor="middle"
        dominantBaseline="central"
        className="fill-white font-display font-semibold"
        style={{ fontSize: size < 60 ? 11 : 13 }}
      >
        {pct}%
      </text>
    </svg>
  );
}

/* Growth staircase step */
function StairStep({ year, label, revenue, color, index, total, visible }) {
  const heights = [35, 65, 100]; // visual heights (%)
  const h = heights[index] || 50;

  return (
    <div
      className="flex flex-col items-center flex-1"
      style={{
        opacity: visible ? 1 : 0,
        transform: visible ? 'translateY(0)' : 'translateY(20px)',
        transition: `all 0.7s cubic-bezier(0.4, 0, 0.2, 1) ${0.6 + index * 0.2}s`,
      }}
    >
      {/* Revenue label */}
      <span className="font-display font-semibold text-sm sm:text-base mb-2" style={{ color }}>
        {revenue}
      </span>

      {/* Bar */}
      <div className="w-full max-w-[100px] mx-auto">
        <div
          className="rounded-t-lg mx-auto"
          style={{
            width: '70%',
            height: visible ? `${h}px` : '0px',
            background: `linear-gradient(to top, ${color}15, ${color}40)`,
            border: `1px solid ${color}30`,
            borderBottom: 'none',
            transition: `height 1s cubic-bezier(0.4, 0, 0.2, 1) ${0.8 + index * 0.2}s`,
          }}
        />
      </div>

      {/* Labels below bar */}
      <div className="text-center mt-2">
        <p className="font-display font-semibold text-white text-[13px]">{year}</p>
        <p className="text-white/30 text-[10px] mt-0.5">{label}</p>
      </div>
    </div>
  );
}

export default function ProjectFinancials({ config }) {
  const { financials, theme } = config;
  const p = theme.primary;
  const s = theme.secondary;
  const capexShares = deriveCapexShares(financials.capex, p, s || '#D97706');
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.15 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  return (
    <section
      ref={ref}
      id="financials"
      className="relative py-24 sm:py-32 px-6 overflow-hidden"
      style={{ background: 'linear-gradient(to bottom, #030712, #0a1210, #030712)' }}
    >
      {/* Subtle grid */}
      <div className="absolute inset-0 opacity-[0.02]" style={{
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1px)',
        backgroundSize: '32px 32px',
      }} />

      <div className="max-w-5xl mx-auto relative">
        {/* Header */}
        <div className="text-center mb-16">
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-white/30">
            {financials.sectionLabel}
          </p>
          <h2
            className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold tracking-tight mb-4"
            style={{
              background: `linear-gradient(90deg, ${p}, ${s || '#D97706'}, ${p})`,
              backgroundSize: '200% 100%',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              animation: 'shimmer 6s ease-in-out infinite',
            }}
          >
            {financials.heading}
          </h2>
          {/* Total raise with animated appearance (optional) */}
          {financials.totalRaise && (
          <div
            className="inline-flex items-baseline gap-2"
            style={{
              opacity: visible ? 1 : 0,
              transform: visible ? 'scale(1)' : 'scale(0.9)',
              transition: 'all 0.6s cubic-bezier(0.4, 0, 0.2, 1) 0.2s',
            }}
          >
            <span className="text-3xl sm:text-4xl font-display font-semibold" style={{ color: p }}>
              {financials.totalRaise}
            </span>
            <span className="text-sm text-white/35 font-medium">
              {financials.totalRaiseLabel}
            </span>
          </div>
          )}
        </div>

        {/* Two-column layout: Allocation rings + Growth staircase */}
        <div className="grid md:grid-cols-2 gap-12 md:gap-16">

          {/* LEFT: Where the Funds Go (ring-based) */}
          <div>
            <h3 className="font-display font-semibold text-white text-base mb-8 text-center md:text-left">
              Where the Funds Go
            </h3>
            <div className="space-y-5">
              {financials.capex.map((row, i) => {
                const share = capexShares[i] || { pct: 0, color: p };
                return (
                  <div
                    key={i}
                    className="flex items-center gap-4"
                    style={{
                      opacity: visible ? 1 : 0,
                      transform: visible ? 'translateX(0)' : 'translateX(-20px)',
                      transition: `all 0.6s cubic-bezier(0.4, 0, 0.2, 1) ${0.3 + i * 0.15}s`,
                    }}
                  >
                    <Ring
                      pct={share.pct}
                      color={share.color}
                      size={56}
                      delay={0.4 + i * 0.15}
                      visible={visible}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="flex items-baseline justify-between gap-2">
                        <p className="font-medium text-white/80 text-[14px] truncate">{row.item}</p>
                        <span
                          className="font-display font-semibold text-[14px] flex-shrink-0"
                          style={{ color: share.color }}
                        >
                          {row.amount}
                        </span>
                      </div>
                      <p className="text-white/25 text-xs mt-0.5 line-clamp-2">{row.detail}</p>
                      {/* Progress bar */}
                      <div className="mt-2 h-1 rounded-full bg-white/[0.04] overflow-hidden">
                        <div
                          className="h-full rounded-full"
                          style={{
                            width: visible ? `${share.pct}%` : '0%',
                            backgroundColor: share.color,
                            opacity: 0.5,
                            transition: `width 1s cubic-bezier(0.4, 0, 0.2, 1) ${0.5 + i * 0.15}s`,
                          }}
                        />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* RIGHT: Growth Path (staircase) */}
          <div>
            <h3 className="font-display font-semibold text-white text-base mb-8 text-center md:text-left">
              Growth Path
            </h3>
            <div className="flex items-end justify-center md:justify-start gap-3 sm:gap-4 pt-8">
              {financials.projections.map((row, i) => (
                <StairStep
                  key={i}
                  year={row.year}
                  label={row.label}
                  revenue={row.revenue}
                  color={i % 2 === 0 ? p : s}
                  index={i}
                  total={financials.projections.length}
                  visible={visible}
                />
              ))}
            </div>

            {/* Annotation */}
            <p
              className="text-white/20 text-xs text-center md:text-left mt-6 max-w-sm"
              style={{
                opacity: visible ? 1 : 0,
                transition: 'opacity 0.6s ease 1.4s',
              }}
            >
              By year 3, farm revenue sustains all operations, expansion, and community programs. No further fundraising needed.
            </p>
          </div>
        </div>
      </div>
    </section>
  );
}
