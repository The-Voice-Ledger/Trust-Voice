/**
 * HexIcon — the single bespoke icon container used across ALL pages.
 *
 * Hexagonal node with:
 *  • Outer hex stroke + inner hex fill
 *  • Corner node dots on vertices
 *  • Optional bespoke SVG illustration inside the hex
 *  • Spinning dashed orbit circle
 *  • White (or gradient) rounded card in center with the icon
 *
 * Sizes:  xs (28), sm (40), md (56), lg (80)
 */

/* ─── Bespoke inner SVG library (keyed by name) ─── */
const BESPOKE_SVGS = {
  globe: (c) => (
    <>
      <circle cx="40" cy="40" r="16" stroke={c} strokeWidth="0.7" fill="none" opacity="0.12" />
      <ellipse cx="40" cy="40" rx="8" ry="16" stroke={c} strokeWidth="0.5" fill="none" opacity="0.10" />
      <path d="M24 40h32" stroke={c} strokeWidth="0.4" fill="none" opacity="0.08" />
      <path d="M24 34h32M24 46h32" stroke={c} strokeWidth="0.3" fill="none" opacity="0.06" />
      <circle cx="40" cy="24" r="1.5" fill={c} opacity="0.12" />
      <circle cx="40" cy="56" r="1.5" fill={c} opacity="0.12" />
    </>
  ),
  chart: (c) => (
    <>
      <rect x="24" y="42" width="5" height="14" rx="1" fill={c} opacity="0.08" />
      <rect x="31" y="34" width="5" height="22" rx="1" fill={c} opacity="0.10" />
      <rect x="38" y="26" width="5" height="30" rx="1" fill={c} opacity="0.12" />
      <rect x="45" y="38" width="5" height="18" rx="1" fill={c} opacity="0.09" />
      <rect x="52" y="22" width="5" height="34" rx="1" fill={c} opacity="0.11" />
      <path d="M24 40 L31 30 L38 24 L45 34 L52 20" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" strokeLinejoin="round" />
      <circle cx="38" cy="24" r="1.5" fill={c} opacity="0.15" />
      <circle cx="52" cy="20" r="1.5" fill={c} opacity="0.15" />
    </>
  ),
  gear: (c) => (
    <>
      <circle cx="40" cy="40" r="8" stroke={c} strokeWidth="0.7" fill="none" opacity="0.12" />
      <circle cx="40" cy="40" r="3.5" fill={c} opacity="0.06" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((a, i) => {
        const rad = (a * Math.PI) / 180;
        const x1 = 40 + 10 * Math.cos(rad), y1 = 40 + 10 * Math.sin(rad);
        const x2 = 40 + 15 * Math.cos(rad), y2 = 40 + 15 * Math.sin(rad);
        return <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={c} strokeWidth="2" strokeLinecap="round" opacity="0.10" />;
      })}
      <circle cx="40" cy="40" r="18" stroke={c} strokeWidth="0.3" strokeDasharray="2 4" fill="none" opacity="0.06" />
    </>
  ),
  heart: (c) => (
    <>
      <path d="M40 55 C30 46 22 40 22 33 22 27 26 23 31 23 34 23 37 25 40 29 43 25 46 23 49 23 54 23 58 27 58 33 58 40 50 46 40 55Z"
        stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" />
      <path d="M40 50 C33 44 27 39 27 34 27 29 30 26 33 26 35 26 38 28 40 31 42 28 45 26 47 26 50 26 53 29 53 34 53 39 47 44 40 50Z"
        fill={c} opacity="0.05" />
      <circle cx="33" cy="31" r="2" fill={c} opacity="0.08" />
      <circle cx="47" cy="31" r="2" fill={c} opacity="0.08" />
    </>
  ),
  building: (c) => (
    <>
      <rect x="26" y="24" width="12" height="26" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" />
      <rect x="42" y="18" width="14" height="32" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" />
      {[28, 33, 38, 43].map(y => <g key={y}><rect x="29" y={y} width="2.5" height="2.5" fill={c} opacity="0.08" /><rect x="45" y={y} width="2.5" height="2.5" fill={c} opacity="0.08" /><rect x="50" y={y} width="2.5" height="2.5" fill={c} opacity="0.08" /></g>)}
      <path d="M47 50v-6h4v6" stroke={c} strokeWidth="0.5" fill="none" opacity="0.12" />
    </>
  ),
  rocket: (c) => (
    <>
      <path d="M40 18 C40 18 33 28 33 42 L36 48 H44 L47 42 C47 28 40 18 40 18Z"
        stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="32" r="3" fill={c} opacity="0.08" />
      <path d="M33 42 L27 49 L33 46" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M47 42 L53 49 L47 46" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M37 50 L38 56 L40 52 L42 56 L43 50" stroke={c} strokeWidth="0.5" fill={c} fillOpacity="0.04" opacity="0.12" />
    </>
  ),
  camera: (c) => (
    <>
      <rect x="20" y="30" width="40" height="26" rx="3" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M32 30l3-7h10l3 7" stroke={c} strokeWidth="0.6" fill="none" opacity="0.08" />
      <circle cx="40" cy="43" r="8" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="43" r="4.5" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <circle cx="40" cy="43" r="2" fill={c} opacity="0.08" />
      <circle cx="53" cy="34" r="1.5" fill={c} opacity="0.06" />
    </>
  ),
  fingerprint: (c) => (
    <>
      <circle cx="40" cy="40" r="14" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <path d="M33 34c0-5 3.5-9 7-9s7 4 7 9c0 7-1.5 14-5 19" stroke={c} strokeWidth="0.7" fill="none" opacity="0.12" />
      <path d="M36 36c0-3 1.5-5 4-5s4 2 4 5c0 4.5-1 9-2.5 12" stroke={c} strokeWidth="0.5" fill="none" opacity="0.10" />
      <path d="M39 38c0-1 .5-1.5 1-1.5s1 .5 1 1.5c0 2.5-.5 5-1 7" stroke={c} strokeWidth="0.4" fill="none" opacity="0.08" />
    </>
  ),
  eye: (c) => (
    <>
      <ellipse cx="40" cy="40" rx="17" ry="10" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="40" r="6" stroke={c} strokeWidth="0.6" fill="none" opacity="0.12" />
      <circle cx="40" cy="40" r="2.5" fill={c} opacity="0.08" />
      <path d="M23 40c5-9 11-12 17-12s12 3 17 12" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <path d="M23 40c5 9 11 12 17 12s12-3 17-12" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
    </>
  ),
  shield: (c) => (
    <>
      <path d="M40 18c-7 3.5-14 5.5-18 5.5v16c0 9 7 16 18 21 11-5 18-12 18-21V23.5c-4 0-11-2-18-5.5z" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M40 23c-5.5 2.5-11 4-14 4v12.5c0 7 5.5 12.5 14 16.5 8.5-4 14-9.5 14-16.5V27c-3 0-8.5-1.5-14-4z" fill={c} opacity="0.03" />
      <path d="M35 40l3.5 3.5 7-7" stroke={c} strokeWidth="1" fill="none" opacity="0.15" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  badge: (c) => (
    <>
      <circle cx="40" cy="36" r="12" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="36" r="7" stroke={c} strokeWidth="0.4" strokeDasharray="2 2.5" fill="none" opacity="0.06" />
      <path d="M36 36l3 3 5-5" stroke={c} strokeWidth="0.8" fill="none" opacity="0.15" strokeLinecap="round" strokeLinejoin="round" />
      <path d="M31 48l-3 8 12-3 12 3-3-8" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
    </>
  ),
  lock: (c) => (
    <>
      <rect x="30" y="36" width="20" height="16" rx="2.5" stroke={c} strokeWidth="0.7" fill="none" opacity="0.12" />
      <path d="M34 36V30a6 6 0 0112 0v6" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="44" r="2" fill={c} opacity="0.10" />
      <path d="M40 46v3" stroke={c} strokeWidth="0.6" fill="none" opacity="0.08" />
    </>
  ),
  chat: (c) => (
    <>
      <path d="M22 26h36v20c0 2-1 3-3 3H30l-6 5v-5h-2c-2 0-3-1-3-3V29c0-2 1-3 3-3z" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="33" cy="38" r="1.5" fill={c} opacity="0.08" />
      <circle cx="40" cy="38" r="1.5" fill={c} opacity="0.08" />
      <circle cx="47" cy="38" r="1.5" fill={c} opacity="0.08" />
    </>
  ),
  sparkles: (c) => (
    <>
      <path d="M40 22v36M22 40h36" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <path d="M40 26l2 8 8 2-8 2-2 8-2-8-8-2 8-2z" stroke={c} strokeWidth="0.6" fill="none" opacity="0.12" />
      <path d="M40 30l1.2 5 5 1.2-5 1.2-1.2 5-1.2-5-5-1.2 5-1.2z" fill={c} opacity="0.04" />
      <circle cx="52" cy="28" r="1.5" fill={c} opacity="0.08" />
      <circle cx="28" cy="52" r="1" fill={c} opacity="0.06" />
    </>
  ),
  microphone: (c) => (
    <>
      <rect x="35" y="24" width="10" height="18" rx="5" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M28 40c0 7 5.5 12 12 12s12-5 12-12" stroke={c} strokeWidth="0.6" fill="none" opacity="0.08" />
      <path d="M40 52v6M34 58h12" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
    </>
  ),
  check: (c) => (
    <>
      <circle cx="40" cy="40" r="16" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="40" r="10" fill={c} opacity="0.04" />
      <path d="M32 40l5.5 5.5 11-11" stroke={c} strokeWidth="1.2" fill="none" opacity="0.18" strokeLinecap="round" strokeLinejoin="round" />
    </>
  ),
  money: (c) => (
    <>
      <circle cx="40" cy="40" r="15" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M40 28v24" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M35 33h7a3.5 3.5 0 010 7H35h8a3.5 3.5 0 010 7H35" stroke={c} strokeWidth="0.6" fill="none" opacity="0.10" />
    </>
  ),
  trending: (c) => (
    <>
      <path d="M24 52L34 40l6 6L56 28" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" strokeLinejoin="round" />
      <path d="M48 28h8v8" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="34" cy="40" r="1.5" fill={c} opacity="0.10" />
      <circle cx="56" cy="28" r="1.5" fill={c} opacity="0.10" />
    </>
  ),
  users: (c) => (
    <>
      <circle cx="34" cy="32" r="5" stroke={c} strokeWidth="0.6" fill="none" opacity="0.10" />
      <circle cx="48" cy="32" r="5" stroke={c} strokeWidth="0.6" fill="none" opacity="0.10" />
      <path d="M24 54c0-5.5 4.5-10 10-10s10 4.5 10 10" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M38 54c0-5.5 4.5-10 10-10s10 4.5 10 10" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
    </>
  ),
  creditcard: (c) => (
    <>
      <rect x="22" y="28" width="36" height="24" rx="3" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M22 36h36" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <rect x="27" y="41" width="8" height="2.5" rx="1" fill={c} opacity="0.06" />
      <rect x="38" y="41" width="5" height="2.5" rx="1" fill={c} opacity="0.06" />
    </>
  ),
  play: (c) => (
    <>
      <circle cx="40" cy="40" r="16" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M35 30v20l16-10z" fill={c} opacity="0.08" stroke={c} strokeWidth="0.5" />
    </>
  ),
  search: (c) => (
    <>
      <circle cx="37" cy="37" r="10" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M44 44l10 10" stroke={c} strokeWidth="0.8" fill="none" opacity="0.12" strokeLinecap="round" />
      <circle cx="37" cy="37" r="5" stroke={c} strokeWidth="0.3" strokeDasharray="2 3" fill="none" opacity="0.06" />
    </>
  ),
  question: (c) => (
    <>
      <circle cx="40" cy="38" r="14" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M35 33a5 5 0 019 2c0 3-4 3-4 6" stroke={c} strokeWidth="0.7" fill="none" opacity="0.12" strokeLinecap="round" />
      <circle cx="40" cy="47" r="1" fill={c} opacity="0.12" />
    </>
  ),
  wallet: (c) => (
    <>
      <rect x="24" y="28" width="32" height="24" rx="3" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M24 34h32" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <rect x="44" y="38" width="10" height="6" rx="2" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <circle cx="48" cy="41" r="1" fill={c} opacity="0.08" />
    </>
  ),
  /* ── Project-specific bespoke icons ── */
  leaf: (c) => (
    <>
      <path d="M28 52C28 36 40 24 56 24c0 16-12 28-28 28z" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M28 52C36 44 44 36 56 24" stroke={c} strokeWidth="0.5" fill="none" opacity="0.08" />
      <path d="M36 44c-2 4-6 6-8 8" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <path d="M44 36c-2 4-4 6-6 8" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
    </>
  ),
  sun: (c) => (
    <>
      <circle cx="40" cy="40" r="8" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <circle cx="40" cy="40" r="4" fill={c} opacity="0.06" />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((a) => {
        const r = (a * Math.PI) / 180;
        return <line key={a} x1={40 + 11 * Math.cos(r)} y1={40 + 11 * Math.sin(r)} x2={40 + 16 * Math.cos(r)} y2={40 + 16 * Math.sin(r)} stroke={c} strokeWidth="0.5" opacity="0.08" strokeLinecap="round" />;
      })}
    </>
  ),
  mountain: (c) => (
    <>
      <path d="M20 56L34 28l8 12 6-8L60 56z" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M28 56l6-9 4 5 3-4 8 8" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <circle cx="52" cy="26" r="4" stroke={c} strokeWidth="0.5" fill="none" opacity="0.06" />
    </>
  ),
  cottage: (c) => (
    <>
      <path d="M22 42L40 26l18 16" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <rect x="26" y="42" width="28" height="14" stroke={c} strokeWidth="0.6" fill="none" opacity="0.08" />
      <rect x="35" y="46" width="10" height="10" stroke={c} strokeWidth="0.5" fill="none" opacity="0.06" />
      <path d="M40 42v-2" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <rect x="48" y="44" width="4" height="4" rx="0.5" stroke={c} strokeWidth="0.3" fill="none" opacity="0.05" />
    </>
  ),
  'oil-drop': (c) => (
    <>
      <path d="M40 20C40 20 26 36 26 46a14 14 0 0028 0c0-10-14-26-14-26z" stroke={c} strokeWidth="0.7" fill="none" opacity="0.10" />
      <path d="M40 26c0 0-8 10-8 16a8 8 0 0016 0c0-6-8-16-8-16z" stroke={c} strokeWidth="0.4" fill="none" opacity="0.06" />
      <ellipse cx="36" cy="44" rx="2" ry="3" fill={c} opacity="0.05" />
    </>
  ),
};

/* ─── Size presets ─── */
const SIZES = {
  xs: { box: 28, view: 28, inset: 4, iconCls: 'w-3.5 h-3.5', hex: { p1: '14,2 26,9 26,19 14,26 2,19 2,9', p2: '14,5 23,10 23,18 14,23 5,18 5,10' }, orbit: 12, nodes: [[14,2,1],[26,9,0.8],[2,9,0.8]] },
  sm: { box: 40, view: 40, inset: 6, iconCls: 'w-4.5 h-4.5', hex: { p1: '20,2 37,11 37,29 20,38 3,29 3,11', p2: '20,6 33,13 33,27 20,34 7,27 7,13' }, orbit: 17, nodes: [[20,2,1.2],[37,11,0.8],[3,11,0.8]] },
  md: { box: 56, view: 56, inset: 8, iconCls: 'w-6 h-6', hex: { p1: '28,3 51,16 51,40 28,53 5,40 5,16', p2: '28,8 46,19 46,37 28,48 10,37 10,19' }, orbit: 24, nodes: [[28,3,1.5],[51,16,1],[5,16,1]] },
  lg: { box: 80, view: 80, inset: 12, iconCls: 'w-7 h-7', hex: { p1: '40,4 72,22 72,58 40,76 8,58 8,22', p2: '40,12 64,26 64,54 40,68 16,54 16,26' }, orbit: 35, nodes: [[40,4,2],[72,22,1.5],[8,22,1.5]] },
};

/**
 * @param {Object}   props
 * @param {Function} props.Icon       - icon component (from icons.jsx)
 * @param {string}   props.accent     - hex color, e.g. '#6366F1'
 * @param {string}   [props.bespoke]  - key into BESPOKE_SVGS (optional)
 * @param {'xs'|'sm'|'md'|'lg'} [props.size='lg'] - size preset
 * @param {boolean}  [props.spin]     - show spinning orbit (default: true)
 * @param {boolean}  [props.gradient] - use gradient bg for center card (default: false, uses white)
 * @param {string}   [props.gradientTo] - second color for gradient (default: same as accent with lower opacity)
 * @param {string}   [props.className]
 */
export default function HexIcon({
  Icon,
  accent,
  bespoke,
  size = 'lg',
  spin = true,
  gradient = false,
  gradientTo,
  className = '',
}) {
  const s = SIZES[size] || SIZES.lg;
  const cx = s.view / 2;
  const cy = s.view / 2;
  const renderBespoke = bespoke && BESPOKE_SVGS[bespoke];

  return (
    <div className={`relative group ${className}`} style={{ width: s.box, height: s.box }}>
      <svg className="absolute inset-0 w-full h-full" viewBox={`0 0 ${s.view} ${s.view}`} fill="none">
        {/* Outer hex */}
        <polygon points={s.hex.p1} stroke={accent} strokeWidth="1.5" opacity="0.15" />
        {/* Inner hex fill */}
        <polygon points={s.hex.p2} fill={accent} opacity="0.06" />
        {/* Corner nodes */}
        {s.nodes.map(([nx, ny, nr], i) => (
          <circle key={i} cx={nx} cy={ny} r={nr} fill={accent} opacity={i === 0 ? 0.25 : 0.15} />
        ))}
        {/* Bespoke inner SVG — scaled to fit */}
        {renderBespoke && size === 'lg' && renderBespoke(accent)}
        {renderBespoke && size === 'md' && (
          <g transform={`translate(${-12}, ${-12}) scale(0.7)`}>
            {renderBespoke(accent)}
          </g>
        )}
        {/* Spinning dashed orbit */}
        {spin && (
          <circle
            cx={cx} cy={cy} r={s.orbit}
            stroke={accent} strokeWidth="0.4" strokeDasharray="3 6" opacity="0.08"
            className="origin-center"
            style={{ animation: 'spin 20s linear infinite', transformOrigin: `${cx}px ${cy}px` }}
          />
        )}
      </svg>
      <div
        className={`absolute rounded-2xl flex items-center justify-center ${
          gradient
            ? 'shadow-lg'
            : 'bg-white shadow-lg group-hover:shadow-xl group-hover:scale-105 transition-all duration-300'
        }`}
        style={{
          inset: s.inset,
          ...(gradient
            ? { background: `linear-gradient(135deg, ${accent}, ${gradientTo || accent}CC)` }
            : { boxShadow: `0 8px 30px ${accent}20` }),
        }}
      >
        <Icon className={`${s.iconCls} ${gradient ? 'text-white' : ''}`} style={gradient ? undefined : { color: accent }} />
      </div>
    </div>
  );
}

/* Re-export the BESPOKE_SVGS keys for reference */
export const BESPOKE_KEYS = Object.keys(BESPOKE_SVGS);
