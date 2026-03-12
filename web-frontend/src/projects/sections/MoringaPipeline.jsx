/**
 * MoringaPipeline — animated SVG value-chain visualisation.
 *
 * Shows the full Moringa journey:
 *   Farm → Harvest → Processing → Products (branch) → Community Market
 *
 * Features:
 *  - Human figure silhouettes at each stage
 *  - Branching network from Processing → 4 derivative products
 *  - Travelling particle along the main spine
 *  - Staggered node entrance on scroll
 *  - Warm emerald/amber palette matching the Ukulima theme
 */
import { useEffect, useRef, useState } from 'react';

/* ── Stage data ── */
const STAGES = [
  { id: 'farm',       label: 'The Farm',       sub: 'Moringa groves',          x: 90,  y: 110 },
  { id: 'harvest',    label: 'Harvest',         sub: 'Hand-picked leaves',      x: 270, y: 110 },
  { id: 'process',    label: 'Processing',      sub: 'On-site facility',        x: 450, y: 110 },
  { id: 'products',   label: 'Products',        sub: 'Value-added goods',       x: 630, y: 110 },
  { id: 'community',  label: 'Community',       sub: 'Local & global reach',    x: 810, y: 110 },
];

/* ── Product branches (fan out from "Products" node) ── */
const PRODUCTS = [
  { label: 'Powder',   y: 30 },
  { label: 'Oil',      y: 70 },
  { label: 'Tea',      y: 150 },
  { label: 'Capsules', y: 190 },
];

/* ── Human figure silhouette (minimalist, ~24 viewBox) ── */
function Person({ x, y, scale = 1, color = '#059669', opacity = 0.5, action = 'stand' }) {
  const t = `translate(${x}, ${y}) scale(${scale})`;
  if (action === 'harvest') {
    return (
      <g transform={t} opacity={opacity}>
        <circle cx="0" cy="-18" r="3.5" fill={color} />
        <line x1="0" y1="-14" x2="0" y2="-2" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="-5" y2="-4" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="6" y2="-6" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="-4" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="4" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      </g>
    );
  }
  if (action === 'carry') {
    return (
      <g transform={t} opacity={opacity}>
        <circle cx="0" cy="-18" r="3.5" fill={color} />
        <line x1="0" y1="-14" x2="0" y2="-2" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="-6" y2="-14" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="6" y2="-14" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <rect x="-4" y="-18" width="8" height="4" rx="1" fill={color} opacity="0.6" />
        <line x1="0" y1="-2" x2="-3" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="3" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      </g>
    );
  }
  if (action === 'operate') {
    return (
      <g transform={t} opacity={opacity}>
        <circle cx="0" cy="-18" r="3.5" fill={color} />
        <line x1="0" y1="-14" x2="0" y2="-2" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="7" y2="-8" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="-5" y2="-6" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="-3" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="3" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      </g>
    );
  }
  if (action === 'shop') {
    return (
      <g transform={t} opacity={opacity}>
        <circle cx="0" cy="-18" r="3.5" fill={color} />
        <line x1="0" y1="-14" x2="0" y2="-2" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="-5" y2="-5" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-10" x2="5" y2="-5" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="-4" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        <line x1="0" y1="-2" x2="4" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
        {/* bag */}
        <rect x="4" y="-8" width="5" height="6" rx="1" fill={color} opacity="0.5" />
      </g>
    );
  }
  /* default: standing */
  return (
    <g transform={t} opacity={opacity}>
      <circle cx="0" cy="-18" r="3.5" fill={color} />
      <line x1="0" y1="-14" x2="0" y2="-2" stroke={color} strokeWidth="1.8" strokeLinecap="round" />
      <line x1="0" y1="-10" x2="-5" y2="-5" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
      <line x1="0" y1="-10" x2="5" y2="-5" stroke={color} strokeWidth="1.4" strokeLinecap="round" />
      <line x1="0" y1="-2" x2="-3" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="0" y1="-2" x2="3" y2="8" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
    </g>
  );
}

/* ── Moringa tree mini-icon ── */
function MoringaTree({ x, y, h = 28, opacity = 0.35 }) {
  return (
    <g>
      <rect x={x - 1.2} y={y - h} width="2.4" height={h} rx="1.2" fill="#059669" opacity={opacity} />
      <ellipse cx={x} cy={y - h - 5} rx="10" ry="7" fill="#059669" opacity={opacity * 0.8} />
      <ellipse cx={x - 5} cy={y - h + 2} rx="6" ry="4" fill="#059669" opacity={opacity * 0.6} />
      <ellipse cx={x + 5} cy={y - h + 2} rx="6" ry="4" fill="#059669" opacity={opacity * 0.6} />
    </g>
  );
}

/* ── Node icons per stage ── */
const STAGE_ICONS = {
  farm: (x, y) => (
    <g>
      <MoringaTree x={x - 12} y={y + 6} h={22} opacity={0.4} />
      <MoringaTree x={x + 12} y={y + 6} h={18} opacity={0.3} />
      <MoringaTree x={x} y={y + 6} h={26} opacity={0.5} />
    </g>
  ),
  harvest: (x, y) => (
    <g>
      <Person x={x - 8} y={y + 16} scale={0.7} action="harvest" color="#059669" opacity={0.5} />
      <Person x={x + 10} y={y + 16} scale={0.65} action="harvest" color="#059669" opacity={0.4} />
    </g>
  ),
  process: (x, y) => (
    <g>
      {/* machine silhouette */}
      <rect x={x - 10} y={y - 4} width="20" height="12" rx="2" fill="#D97706" opacity="0.2" />
      <rect x={x - 7} y={y - 7} width="5" height="3" rx="1" fill="#D97706" opacity="0.15" />
      <circle cx={x + 5} cy={y + 2} r="3" fill="#D97706" opacity="0.15" />
      <Person x={x - 16} y={y + 16} scale={0.65} action="operate" color="#D97706" opacity={0.45} />
    </g>
  ),
  products: (x, y) => (
    <g>
      {/* small product icons */}
      <rect x={x - 10} y={y - 6} width="7" height="10" rx="1.5" fill="#059669" opacity="0.25" />
      <circle cx={x + 2} cy={y - 1} r="4" fill="#D97706" opacity="0.2" />
      <rect x={x + 6} y={y - 4} width="5" height="8" rx="1" fill="#059669" opacity="0.2" />
    </g>
  ),
  community: (x, y) => (
    <g>
      <Person x={x - 14} y={y + 16} scale={0.6} action="shop" color="#059669" opacity={0.4} />
      <Person x={x} y={y + 16} scale={0.65} action="stand" color="#D97706" opacity={0.45} />
      <Person x={x + 14} y={y + 16} scale={0.6} action="carry" color="#059669" opacity={0.4} />
    </g>
  ),
};

/* ── Theme colours ── */
const E = '#059669';
const A = '#D97706';

export default function MoringaPipeline({ config }) {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.2 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  /* Main spine path (Farm → Harvest → Processing → Products → Community) */
  const spinePts = STAGES.map(s => ({ x: s.x, y: s.y }));
  let spineD = `M${spinePts[0].x},${spinePts[0].y}`;
  for (let i = 0; i < spinePts.length - 1; i++) {
    const gap = spinePts[i + 1].x - spinePts[i].x;
    const cpOff = gap * 0.4;
    spineD += ` C${spinePts[i].x + cpOff},${spinePts[i].y} ${spinePts[i + 1].x - cpOff},${spinePts[i + 1].y} ${spinePts[i + 1].x},${spinePts[i + 1].y}`;
  }

  /* Branch paths from "Products" node to each product derivative */
  const prodNode = STAGES[3]; // Products
  const branchPaths = PRODUCTS.map(p => {
    const midX = prodNode.x + 35;
    return `M${prodNode.x + 18},${prodNode.y} C${midX},${prodNode.y} ${midX},${p.y} ${prodNode.x + 55},${p.y}`;
  });

  const p = config?.theme?.primary || E;
  const s = config?.theme?.secondary || A;

  return (
    <section
      ref={ref}
      id="pipeline"
      className="relative py-20 sm:py-28 overflow-hidden"
      style={{ background: 'linear-gradient(to bottom, #030712, #0a1a12, #030712)' }}
    >
      {/* Subtle dot grid */}
      <div className="absolute inset-0 opacity-[0.03]" style={{
        backgroundImage: 'radial-gradient(circle, rgba(255,255,255,0.4) 1px, transparent 1px)',
        backgroundSize: '32px 32px',
      }} />

      <div className="max-w-5xl mx-auto px-4">
        {/* Header */}
        <p className="text-center text-xs font-medium tracking-[0.2em] uppercase text-white/30 mb-3 font-display">
          From Seed to Shelf
        </p>
        <h2 className="font-display text-2xl sm:text-3xl md:text-4xl font-semibold text-white tracking-tight text-center mb-4">
          The Moringa Journey
        </h2>
        <p className="text-white/30 text-sm sm:text-base text-center max-w-xl mx-auto mb-14 leading-relaxed">
          Every leaf tells a story — from the soil to the shelf, powered by the community that built it.
        </p>

        {/* Pipeline SVG */}
        <div className="overflow-x-auto scrollbar-hide -mx-4 px-4">
          <svg
            viewBox="0 0 900 240"
            className="mx-auto w-full min-w-[680px]"
            style={{ maxWidth: 900 }}
            aria-label="Moringa value chain from farm to community"
          >
            <defs>
              {/* Glow filter */}
              <filter id="mp-glow">
                <feGaussianBlur stdDeviation="3" result="b" />
                <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
              {/* Main gradient */}
              <linearGradient id="mp-grad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={E} />
                <stop offset="50%" stopColor={A} />
                <stop offset="100%" stopColor={E} />
              </linearGradient>
              {/* Branch gradient */}
              <linearGradient id="mp-branch" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor={A} stopOpacity="0.6" />
                <stop offset="100%" stopColor={E} stopOpacity="0.3" />
              </linearGradient>
            </defs>

            {/* ── Background spine track ── */}
            <path d={spineD} fill="none" stroke="rgba(255,255,255,0.06)" strokeWidth="2" strokeLinecap="round" />

            {/* ── Animated spine ── */}
            <path
              d={spineD}
              fill="none"
              stroke="url(#mp-grad)"
              strokeWidth="2"
              strokeDasharray="8 6"
              strokeLinecap="round"
              filter="url(#mp-glow)"
              className={visible ? 'mp-dash-animate' : ''}
              style={{ opacity: visible ? 1 : 0, transition: 'opacity 0.6s' }}
            />

            {/* ── Branch paths (Products → derivatives) ── */}
            {branchPaths.map((d, i) => (
              <g key={`br-${i}`}>
                <path d={d} fill="none" stroke="rgba(255,255,255,0.04)" strokeWidth="1.5" strokeLinecap="round" />
                <path
                  d={d}
                  fill="none"
                  stroke="url(#mp-branch)"
                  strokeWidth="1.5"
                  strokeDasharray="5 4"
                  strokeLinecap="round"
                  className={visible ? 'mp-dash-animate' : ''}
                  style={{ opacity: visible ? 0.7 : 0, transition: `opacity 0.6s ${0.5 + i * 0.15}s` }}
                />
              </g>
            ))}

            {/* ── Product derivative labels ── */}
            {PRODUCTS.map((pr, i) => {
              const bx = STAGES[3].x + 55;
              return (
                <g
                  key={`prod-${i}`}
                  className={visible ? 'mp-node-in' : 'opacity-0'}
                  style={{ animationDelay: `${0.8 + i * 0.12}s` }}
                >
                  <circle cx={bx} cy={pr.y} r="12" fill="rgba(255,255,255,0.03)" stroke={E} strokeWidth="1" opacity="0.5" />
                  <circle cx={bx} cy={pr.y} r="7" fill={E} opacity="0.12" />
                  <text
                    x={bx + 18}
                    y={pr.y + 4}
                    className="fill-white/50 text-[10px] font-display"
                  >
                    {pr.label}
                  </text>
                </g>
              );
            })}

            {/* ── Travelling particle ── */}
            {visible && (
              <circle r="4" fill={A} filter="url(#mp-glow)" opacity="0.9">
                <animateMotion dur="5s" repeatCount="indefinite" path={spineD} />
              </circle>
            )}

            {/* ── Stage nodes ── */}
            {STAGES.map((st, i) => {
              const delay = `${i * 0.18}s`;
              const color = i <= 1 ? E : i === 2 ? A : E;
              return (
                <g
                  key={st.id}
                  className={visible ? 'mp-node-in' : 'opacity-0'}
                  style={{ animationDelay: delay }}
                >
                  {/* Outer ring */}
                  <circle cx={st.x} cy={st.y} r="24" fill="rgba(255,255,255,0.02)" stroke={color} strokeWidth="1.2" opacity="0.5" />
                  {/* Inner disc */}
                  <circle cx={st.x} cy={st.y} r="16" fill={color} opacity="0.1" />

                  {/* Stage icon illustration */}
                  {STAGE_ICONS[st.id]?.(st.x, st.y)}

                  {/* Label */}
                  <text
                    x={st.x}
                    y={st.y + 42}
                    textAnchor="middle"
                    className="fill-white text-[12px] font-display font-semibold"
                  >
                    {st.label}
                  </text>
                  <text
                    x={st.x}
                    y={st.y + 55}
                    textAnchor="middle"
                    className="fill-white/30 text-[9px]"
                  >
                    {st.sub}
                  </text>
                </g>
              );
            })}

            {/* ── Network connection dots (ambient, between nodes) ── */}
            {visible && [
              { cx: 175, cy: 95, r: 1.5, d: 0 },
              { cx: 185, cy: 125, r: 1, d: 0.5 },
              { cx: 355, cy: 98, r: 1.2, d: 1 },
              { cx: 365, cy: 122, r: 1, d: 1.5 },
              { cx: 540, cy: 92, r: 1.3, d: 0.8 },
              { cx: 545, cy: 128, r: 1, d: 1.2 },
              { cx: 720, cy: 96, r: 1.2, d: 0.3 },
              { cx: 725, cy: 124, r: 1, d: 0.9 },
            ].map((dot, i) => (
              <circle
                key={`nd-${i}`}
                cx={dot.cx}
                cy={dot.cy}
                r={dot.r}
                fill="white"
                opacity="0.08"
                className="mp-pulse"
                style={{ animationDelay: `${dot.d}s` }}
              />
            ))}
          </svg>
        </div>
      </div>

      {/* Scoped animations */}
      <style>{`
        @keyframes mp-dashMove {
          to { stroke-dashoffset: -56; }
        }
        .mp-dash-animate {
          animation: mp-dashMove 2.5s linear infinite;
        }
        @keyframes mp-nodeIn {
          from { opacity: 0; transform: translateY(14px) scale(0.8); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        .mp-node-in {
          animation: mp-nodeIn 0.6s ease-out both;
        }
        @keyframes mp-pulse {
          0%, 100% { opacity: 0.06; }
          50% { opacity: 0.18; }
        }
        .mp-pulse {
          animation: mp-pulse 3s ease-in-out infinite;
        }
      `}</style>
    </section>
  );
}
