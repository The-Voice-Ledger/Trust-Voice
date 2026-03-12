import { useEffect, useRef, useState, useCallback } from 'react';

/* ───────────────────────────────────────────────────────────
 *  Inline SVG Scene Components - bespoke illustrations
 *  for each of the four narrative chapters
 * ─────────────────────────────────────────────────────────── */

const e = '#059669'; // emerald
const a = '#D97706'; // amber
const soil = '#8B7355';
const sky = '#E8F5F0';

function SceneAncientPulse({ visible }) {
  return (
    <svg viewBox="0 0 280 180" fill="none" aria-hidden="true" className="w-full h-full">
      <style>{`
        @keyframes nr-root-grow { from { stroke-dashoffset: 60 } to { stroke-dashoffset: 0 } }
        @keyframes nr-leaf-sway { 0%,100% { transform: rotate(0deg) } 50% { transform: rotate(3deg) } }
        @keyframes nr-ring-pulse { 0%,100% { opacity: 0.06 } 50% { opacity: 0.14 } }
        @keyframes nr-glow { 0%,100% { opacity: 0.08 } 50% { opacity: 0.18 } }
      `}</style>

      {/* Faint sacred geometry rings */}
      <circle cx="140" cy="85" r="70" stroke={e} strokeWidth="0.5" fill="none" opacity="0.08"
        style={{ animation: visible ? 'nr-ring-pulse 4s ease-in-out infinite' : 'none' }} />
      <circle cx="140" cy="85" r="50" stroke={e} strokeWidth="0.4" fill="none" opacity="0.06"
        style={{ animation: visible ? 'nr-ring-pulse 4s ease-in-out infinite 0.5s' : 'none' }} />
      <circle cx="140" cy="85" r="30" stroke={a} strokeWidth="0.3" fill="none" opacity="0.06"
        style={{ animation: visible ? 'nr-ring-pulse 4s ease-in-out infinite 1s' : 'none' }} />

      {/* Ancient tree - trunk */}
      <path d="M140 170 L140 82 Q138 65 135 55" stroke={soil} strokeWidth="3.5" fill="none" opacity="0.35"
        strokeLinecap="round" />
      <path d="M140 100 Q155 85 162 70" stroke={soil} strokeWidth="2" fill="none" opacity="0.25"
        strokeLinecap="round" />
      <path d="M140 90 Q125 75 115 62" stroke={soil} strokeWidth="2" fill="none" opacity="0.25"
        strokeLinecap="round" />

      {/* Root system */}
      {[
        'M140 170 Q120 178 100 175', 'M140 170 Q160 178 185 172',
        'M140 170 Q130 180 115 180', 'M140 170 Q155 182 170 178',
      ].map((d, i) => (
        <path key={i} d={d} stroke={soil} strokeWidth="1.5" fill="none" opacity="0.18"
          strokeLinecap="round" strokeDasharray="60" strokeDashoffset={visible ? 0 : 60}
          style={{ transition: `stroke-dashoffset 1.2s ease ${0.5 + i * 0.2}s` }} />
      ))}

      {/* Leaf canopy clusters */}
      {[
        { cx: 132, cy: 48, rx: 18, ry: 12 },
        { cx: 155, cy: 52, rx: 16, ry: 10 },
        { cx: 115, cy: 56, rx: 14, ry: 10 },
        { cx: 165, cy: 64, rx: 12, ry: 9 },
        { cx: 140, cy: 38, rx: 14, ry: 10 },
      ].map((l, i) => (
        <ellipse key={i} cx={l.cx} cy={l.cy} rx={l.rx} ry={l.ry} fill={e}
          opacity={visible ? 0.16 + i * 0.02 : 0}
          style={{
            transformOrigin: `${l.cx}px ${l.cy + l.ry}px`,
            animation: visible ? `nr-leaf-sway ${3 + i * 0.4}s ease-in-out infinite ${i * 0.3}s` : 'none',
            transition: `opacity 0.8s ease ${0.3 + i * 0.15}s`,
          }} />
      ))}

      {/* Golden glow behind tree */}
      <circle cx="140" cy="60" r="25" fill={a} opacity={visible ? 0.08 : 0}
        style={{
          animation: visible ? 'nr-glow 5s ease-in-out infinite' : 'none',
          transition: 'opacity 1s ease 0.4s',
        }} />

      {/* Tiny moringa leaf shapes scattered */}
      {[
        { x: 90, y: 90 }, { x: 195, y: 75 }, { x: 80, y: 130 }, { x: 200, y: 120 },
      ].map((p, i) => (
        <ellipse key={i} cx={p.x} cy={p.y} rx="3" ry="1.5" fill={e}
          opacity={visible ? 0.12 : 0}
          style={{ transition: `opacity 0.6s ease ${1 + i * 0.2}s` }}
          transform={`rotate(${30 + i * 40} ${p.x} ${p.y})`} />
      ))}
    </svg>
  );
}

function SceneGreenGold({ visible }) {
  return (
    <svg viewBox="0 0 280 180" fill="none" aria-hidden="true" className="w-full h-full">
      <style>{`
        @keyframes nr-sun-ray { 0%,100% { opacity: 0.06 } 50% { opacity: 0.15 } }
        @keyframes nr-dust { 0% { transform: translateX(0); opacity: 0.15 } 100% { transform: translateX(20px); opacity: 0 } }
        @keyframes nr-bird { 0%,100% { transform: translate(0,0) } 50% { transform: translate(8px,-4px) } }
      `}</style>

      {/* Mountain range - layered silhouettes */}
      <path d="M0 130 L40 65 L70 95 L110 45 L150 80 L190 35 L230 75 L260 55 L280 90 L280 180 L0 180Z"
        fill={e} opacity="0.06" />
      <path d="M0 145 L50 90 L90 120 L130 75 L170 105 L210 65 L250 100 L280 85 L280 180 L0 180Z"
        fill={e} opacity="0.1" />
      <path d="M0 160 L60 120 L100 140 L155 110 L200 135 L240 115 L280 130 L280 180 L0 180Z"
        fill={e} opacity="0.14" />

      {/* Sun with rays */}
      <circle cx="220" cy="35" r="18" fill={a} opacity="0.12" />
      <circle cx="220" cy="35" r="12" fill={a} opacity="0.08"
        style={{ animation: visible ? 'nr-sun-ray 3s ease-in-out infinite' : 'none' }} />
      {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => {
        const rad = (angle * Math.PI) / 180;
        const x1 = 220 + Math.cos(rad) * 22;
        const y1 = 35 + Math.sin(rad) * 22;
        const x2 = 220 + Math.cos(rad) * 30;
        const y2 = 35 + Math.sin(rad) * 30;
        return (
          <line key={i} x1={x1} y1={y1} x2={x2} y2={y2} stroke={a} strokeWidth="1" opacity="0.1"
            strokeLinecap="round"
            style={{ animation: visible ? `nr-sun-ray 3s ease-in-out infinite ${i * 0.2}s` : 'none' }} />
        );
      })}

      {/* Dusty trail winding through mountains */}
      <path d="M0 165 Q40 155 70 160 Q110 158 140 150 Q170 145 200 148 Q240 150 280 142"
        stroke={soil} strokeWidth="2.5" fill="none" opacity="0.15" strokeLinecap="round"
        strokeDasharray="200" strokeDashoffset={visible ? 0 : 200}
        style={{ transition: 'stroke-dashoffset 2s ease 0.3s' }} />

      {/* Dust particles along trail */}
      {visible && [160, 180, 200].map((x, i) => (
        <circle key={i} cx={x} cy={148 + i * 2} r="1" fill={soil} opacity="0.15"
          style={{ animation: `nr-dust 2s ease-out infinite ${i * 0.6}s` }} />
      ))}

      {/* Small 4x4 vehicle silhouette on trail */}
      <g opacity={visible ? 0.2 : 0} style={{ transition: 'opacity 0.8s ease 1.2s' }}>
        <rect x="95" y="150" width="20" height="10" rx="2" fill={soil} />
        <rect x="98" y="146" width="12" height="6" rx="1.5" fill={soil} opacity="0.8" />
        <circle cx="100" cy="161" r="2.5" fill={soil} />
        <circle cx="112" cy="161" r="2.5" fill={soil} />
      </g>

      {/* Birds */}
      {[[50, 30], [70, 25], [85, 35]].map(([bx, by], i) => (
        <path key={i} d={`M${bx-4} ${by+2} Q${bx} ${by-2} ${bx+4} ${by+2}`}
          stroke={e} strokeWidth="1" fill="none" opacity="0.15"
          style={{ animation: visible ? `nr-bird 3s ease-in-out infinite ${i * 0.5}s` : 'none' }} />
      ))}

      {/* Solar panel hint (off-grid) */}
      <g opacity={visible ? 0.12 : 0} style={{ transition: 'opacity 0.8s ease 1.5s' }}>
        <rect x="235" y="108" width="16" height="10" rx="1" fill="#3B82F6" transform="rotate(-15 243 113)" />
        <rect x="233" y="118" width="2" height="12" rx="1" fill={soil} />
      </g>
    </svg>
  );
}

function ScenePlaceYouCanTouch({ visible }) {
  return (
    <svg viewBox="0 0 280 180" fill="none" aria-hidden="true" className="w-full h-full">
      <style>{`
        @keyframes nr-water { 0%,100% { d: path("M60 155 Q90 150 120 155 Q150 160 180 155 Q210 150 240 155") }
          50% { d: path("M60 155 Q90 160 120 155 Q150 150 180 155 Q210 160 240 155") } }
        @keyframes nr-smoke { 0% { transform: translateY(0); opacity: 0.12 } 100% { transform: translateY(-12px); opacity: 0 } }
        @keyframes nr-flicker { 0%,100% { opacity: 0.3 } 50% { opacity: 0.15 } }
      `}</style>

      {/* Gentle hills background */}
      <path d="M0 130 Q70 110 140 125 Q210 115 280 130 L280 180 L0 180Z" fill={e} opacity="0.06" />
      <path d="M0 145 Q90 130 160 140 Q220 135 280 145 L280 180 L0 180Z" fill={e} opacity="0.1" />

      {/* Irrigated field rows */}
      {[0, 1, 2, 3, 4].map(i => (
        <g key={i} opacity={visible ? 0.12 + i * 0.02 : 0}
          style={{ transition: `opacity 0.6s ease ${0.8 + i * 0.1}s` }}>
          <line x1={20} y1={148 + i * 6} x2={110} y2={148 + i * 6}
            stroke={e} strokeWidth="1" strokeDasharray="3 5" />
          {[30, 45, 60, 75, 90].map((x, j) => (
            <circle key={j} cx={x} cy={147 + i * 6} r="1.5" fill={e} opacity="0.7" />
          ))}
        </g>
      ))}

      {/* Stone cottage - main */}
      <g opacity={visible ? 1 : 0} style={{ transition: 'opacity 0.8s ease 0.4s' }}>
        {/* Walls */}
        <rect x="145" y="82" width="56" height="42" rx="2" fill={soil} opacity="0.18" />
        {/* Stone texture hints */}
        {[
          [150, 88, 8, 5], [161, 87, 10, 6], [174, 88, 7, 5],
          [148, 96, 9, 5], [160, 97, 8, 5], [171, 96, 10, 5],
          [150, 104, 7, 5], [162, 105, 9, 5], [175, 104, 8, 5],
        ].map(([x, y, w, h], i) => (
          <rect key={i} x={x} y={y} width={w} height={h} rx="1"
            fill={soil} opacity="0.06" stroke={soil} strokeWidth="0.3" strokeOpacity="0.08" />
        ))}
        {/* Thatched roof */}
        <polygon points="138,82 173,58 208,82" fill={a} opacity="0.15" />
        <line x1="142" y1="80" x2="173" y2="60" stroke={a} strokeWidth="0.5" opacity="0.1" />
        <line x1="204" y1="80" x2="173" y2="60" stroke={a} strokeWidth="0.5" opacity="0.1" />
        {/* Window */}
        <rect x="155" y="92" width="10" height="8" rx="1" fill={a} opacity="0.2"
          style={{ animation: visible ? 'nr-flicker 3s ease-in-out infinite' : 'none' }} />
        {/* Door */}
        <rect x="175" y="100" width="12" height="24" rx="2" fill={soil} opacity="0.12" />
        <circle cx="185" cy="113" r="1" fill={a} opacity="0.3" />
        {/* Chimney + smoke */}
        <rect x="185" y="62" width="6" height="20" rx="1" fill={soil} opacity="0.15" />
        {visible && [0, 1, 2].map(i => (
          <circle key={i} cx={188 + i * 2} cy={58 - i * 5} r={2 + i} fill="white" opacity="0.12"
            style={{ animation: `nr-smoke 2.5s ease-out infinite ${i * 0.8}s` }} />
        ))}
      </g>

      {/* Second cottage hint (smaller, behind) */}
      <g opacity={visible ? 0.5 : 0} style={{ transition: 'opacity 0.8s ease 0.7s' }}>
        <rect x="220" y="95" width="35" height="28" rx="2" fill={soil} opacity="0.12" />
        <polygon points="215,95 237,78 260,95" fill={a} opacity="0.1" />
      </g>

      {/* Irrigation channel */}
      <path d="M60 155 Q90 150 120 155 Q150 160 180 155 Q210 150 240 155"
        stroke="#3B82F6" strokeWidth="1.5" fill="none" opacity="0.12"
        strokeDasharray="120" strokeDashoffset={visible ? 0 : 120}
        style={{ transition: 'stroke-dashoffset 1.8s ease 0.6s' }} />

      {/* Hands silhouette holding soil (bottom center) */}
      <g opacity={visible ? 0.15 : 0}
        style={{ transition: 'opacity 1s ease 1.2s' }}>
        <path d="M110 175 Q120 168 130 170 Q135 165 140 168 Q145 165 150 170 Q160 168 170 175"
          stroke={soil} strokeWidth="1.5" fill={soil} fillOpacity="0.05" strokeLinecap="round" />
        {/* Small plant in hands */}
        <line x1="140" y1="168" x2="140" y2="158" stroke={e} strokeWidth="1.5" strokeLinecap="round" />
        <ellipse cx="136" cy="156" rx="4" ry="2.5" fill={e} opacity="0.5" />
        <ellipse cx="144" cy="156" rx="4" ry="2.5" fill={e} opacity="0.5" />
      </g>
    </svg>
  );
}

function SceneCommunity({ visible }) {
  return (
    <svg viewBox="0 0 280 180" fill="none" aria-hidden="true" className="w-full h-full">
      <style>{`
        @keyframes nr-people-bob { 0%,100% { transform: translateY(0) } 50% { transform: translateY(-2px) } }
        @keyframes nr-harvest-reach { 0%,100% { transform: rotate(0deg) } 50% { transform: rotate(8deg) } }
        @keyframes nr-circle-draw { from { stroke-dashoffset: 340 } to { stroke-dashoffset: 0 } }
      `}</style>

      {/* Community circle (unity ring) */}
      <circle cx="140" cy="90" r="54" stroke={e} strokeWidth="1" fill="none"
        opacity={visible ? 0.12 : 0}
        strokeDasharray="340" strokeDashoffset={visible ? 0 : 340}
        style={{ transition: 'stroke-dashoffset 2s ease 0.3s, opacity 0.5s ease' }} />
      <circle cx="140" cy="90" r="54" stroke={a} strokeWidth="0.5" fill="none"
        opacity={visible ? 0.06 : 0} strokeDasharray="6 8"
        style={{ transition: 'opacity 1s ease 0.8s' }} />

      {/* People figures arranged in circle */}
      {[
        { angle: -90, color: e },
        { angle: -30, color: a },
        { angle: 30, color: e },
        { angle: 90, color: soil },
        { angle: 150, color: a },
        { angle: 210, color: e },
      ].map(({ angle, color }, i) => {
        const rad = (angle * Math.PI) / 180;
        const px = 140 + Math.cos(rad) * 54;
        const py = 90 + Math.sin(rad) * 54;
        return (
          <g key={i} opacity={visible ? 0.3 : 0}
            style={{
              transition: `opacity 0.5s ease ${0.5 + i * 0.15}s`,
              animation: visible ? `nr-people-bob 3s ease-in-out infinite ${i * 0.3}s` : 'none',
            }}>
            <circle cx={px} cy={py - 5} r="4" fill={color} />
            <rect x={px - 2.5} y={py - 1} width="5" height="10" rx="2.5" fill={color} opacity="0.8" />
          </g>
        );
      })}

      {/* Center moringa tea cup */}
      <g opacity={visible ? 0.2 : 0} style={{ transition: 'opacity 0.8s ease 1.2s' }}>
        <path d="M130 88 L132 98 L148 98 L150 88Z" fill={e} />
        <ellipse cx="140" cy="88" rx="10" ry="3" fill={e} opacity="0.6" />
        {/* Steam */}
        {visible && [0, 1].map(i => (
          <path key={i} d={`M${137 + i * 6} 85 Q${139 + i * 4} 80 ${137 + i * 6} 75`}
            stroke={e} strokeWidth="0.8" fill="none" opacity="0.15"
            style={{ animation: `nr-smoke 2s ease-out infinite ${i * 0.5}s` }} />
        ))}
      </g>

      {/* Harvest scene (bottom left) */}
      <g opacity={visible ? 0.2 : 0} style={{ transition: 'opacity 0.8s ease 0.8s' }}>
        {/* Moringa branch */}
        <path d="M30 140 Q50 130 70 135" stroke={e} strokeWidth="2" fill="none" strokeLinecap="round"
          style={{
            transformOrigin: '30px 140px',
            animation: visible ? 'nr-harvest-reach 4s ease-in-out infinite' : 'none',
          }} />
        {[40, 50, 60].map((lx, i) => (
          <ellipse key={i} cx={lx} cy={132 + i} rx="5" ry="2.5" fill={e} opacity="0.6"
            transform={`rotate(${-10 + i * 10} ${lx} ${132 + i})`} />
        ))}
        {/* Basket below */}
        <path d="M35 150 L45 150 Q50 155 50 160 L30 160 Q30 155 35 150Z" fill={a} opacity="0.5" />
      </g>

      {/* Learning / book symbol (bottom right) */}
      <g opacity={visible ? 0.15 : 0} style={{ transition: 'opacity 0.8s ease 1s' }}>
        <path d="M220 145 L220 160 L235 155 L250 160 L250 145 L235 140Z" fill={soil} />
        <line x1="235" y1="140" x2="235" y2="155" stroke="white" strokeWidth="0.5" opacity="0.3" />
      </g>

      {/* Dawn horizon glow */}
      <ellipse cx="140" cy="175" rx="120" ry="20" fill={a} opacity={visible ? 0.04 : 0}
        style={{ transition: 'opacity 1s ease 0.5s' }} />
    </svg>
  );
}

/* The four scenes mapped to narrative blocks */
const SCENES = [SceneAncientPulse, SceneGreenGold, ScenePlaceYouCanTouch, SceneCommunity];

/* Accent colors that cycle across blocks */
const BLOCK_COLORS = ['#059669', '#D97706', '#059669', '#D97706'];

/* ───────────────────────────────────────────────────────────
 *  useBlockVisibility — individual IO per story card
 * ─────────────────────────────────────────────────────────── */
function useBlockVisibility(count) {
  const refs = useRef([]);
  const [vis, setVis] = useState(() => Array(count).fill(false));

  const setRef = useCallback(
    (idx) => (el) => { refs.current[idx] = el; },
    [],
  );

  useEffect(() => {
    const observers = refs.current.map((el, i) => {
      if (!el) return null;
      const io = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            setVis((prev) => {
              const next = [...prev];
              next[i] = true;
              return next;
            });
            io.disconnect();
          }
        },
        { threshold: 0.15 },
      );
      io.observe(el);
      return io;
    });
    return () => observers.forEach((io) => io?.disconnect());
  }, [count]);

  return { setRef, vis };
}

/* ───────────────────────────────────────────────────────────
 *  ProjectNarrative — elegant vertical story-river
 * ─────────────────────────────────────────────────────────── */
export default function ProjectNarrative({ config }) {
  const { narrative, theme } = config;

  const headerRef = useRef(null);
  const [headerVisible, setHeaderVisible] = useState(false);

  useEffect(() => {
    if (!headerRef.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setHeaderVisible(true); io.disconnect(); } },
      { threshold: 0.2 },
    );
    io.observe(headerRef.current);
    return () => io.disconnect();
  }, []);

  const { setRef, vis } = useBlockVisibility(narrative.blocks.length);

  return (
    <section id="narrative" className="relative py-24 sm:py-32 px-6 overflow-hidden">
      {/* Faint vertical river line (decorative) */}
      <div
        className="absolute left-1/2 top-44 bottom-16 w-px hidden md:block"
        style={{
          background: `linear-gradient(to bottom, transparent, ${theme.primary}18, ${theme.primary}10, transparent)`,
        }}
      />

      <div className="max-w-5xl mx-auto">
        {/* ─── Section header ─── */}
        <div
          ref={headerRef}
          className="text-center mb-24"
          style={{
            opacity: headerVisible ? 1 : 0,
            transform: headerVisible ? 'translateY(0)' : 'translateY(20px)',
            transition: 'all 0.7s cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <p className="text-xs font-medium tracking-[0.2em] uppercase mb-3 text-gray-400">
            {narrative.sectionLabel}
          </p>
          <h2
            className="font-display text-3xl sm:text-4xl md:text-5xl font-semibold text-gray-900 tracking-tight leading-tight whitespace-pre-line"
          >
            {narrative.heading}
          </h2>
          {/* Decorative underline */}
          <div className="flex justify-center mt-5 gap-1.5">
            <span className="block w-8 h-0.5 rounded-full" style={{ backgroundColor: theme.primary, opacity: 0.35 }} />
            <span className="block w-2 h-0.5 rounded-full" style={{ backgroundColor: theme.secondary, opacity: 0.3 }} />
          </div>
        </div>

        {/* ─── Story blocks ─── */}
        <div className="relative space-y-20 sm:space-y-28">
          {narrative.blocks.map((block, i) => {
            const color = BLOCK_COLORS[i] || theme.primary;
            const Scene = SCENES[i];
            const isEven = i % 2 === 0;
            const blockVis = vis[i];

            return (
              <div
                key={i}
                ref={setRef(i)}
                className={`relative flex flex-col gap-6 ${
                  isEven
                    ? 'md:flex-row'
                    : 'md:flex-row-reverse'
                } items-center`}
              >
                {/* ─── Illustration panel ─── */}
                <div
                  className="w-full md:w-[48%] flex-shrink-0"
                  style={{
                    opacity: blockVis ? 1 : 0,
                    transform: blockVis
                      ? 'scale(1) translateY(0)'
                      : 'scale(0.92) translateY(12px)',
                    transition: 'all 0.8s cubic-bezier(0.4, 0, 0.2, 1)',
                  }}
                >
                  <div
                    className="relative rounded-2xl overflow-hidden"
                    style={{
                      background: `linear-gradient(135deg, ${color}06, ${color}03)`,
                      border: `1px solid ${color}10`,
                    }}
                  >
                    {/* Corner accent */}
                    <div
                      className="absolute top-0 left-0 w-12 h-12 rounded-br-2xl"
                      style={{
                        background: `linear-gradient(135deg, ${color}12, transparent)`,
                      }}
                    />
                    <div className="p-3 sm:p-4">
                      {Scene && <Scene visible={blockVis} />}
                    </div>
                  </div>
                </div>

                {/* ─── Center node (desktop only) ─── */}
                <div className="hidden md:flex flex-col items-center absolute left-1/2 -translate-x-1/2 top-1/2 -translate-y-1/2 z-10">
                  <div
                    className="w-4 h-4 rounded-full border-2 shadow-sm"
                    style={{
                      borderColor: color,
                      backgroundColor: blockVis ? color : 'white',
                      opacity: blockVis ? 1 : 0.3,
                      transition: 'all 0.5s ease 0.3s',
                    }}
                  />
                  {/* Chapter number */}
                  <span
                    className="mt-1 text-[10px] font-bold tracking-wider"
                    style={{
                      color,
                      opacity: blockVis ? 0.5 : 0,
                      transition: 'opacity 0.5s ease 0.5s',
                    }}
                  >
                    {String(i + 1).padStart(2, '0')}
                  </span>
                </div>

                {/* ─── Text panel ─── */}
                <div
                  className="w-full md:w-[48%] flex-shrink-0"
                  style={{
                    opacity: blockVis ? 1 : 0,
                    transform: blockVis
                      ? 'translateY(0)'
                      : 'translateY(18px)',
                    transition: 'all 0.7s cubic-bezier(0.4, 0, 0.2, 1) 0.2s',
                  }}
                >
                  {/* Mobile chapter number */}
                  <span
                    className="md:hidden text-[10px] font-bold tracking-wider mb-2 block"
                    style={{ color, opacity: 0.4 }}
                  >
                    Chapter {String(i + 1).padStart(2, '0')}
                  </span>

                  <div className="flex items-start gap-3 mb-3">
                    {/* Accent bar */}
                    <div
                      className="w-1 rounded-full flex-shrink-0 mt-1.5"
                      style={{
                        backgroundColor: color,
                        opacity: 0.3,
                        height: blockVis ? '28px' : '0px',
                        transition: 'height 0.5s ease 0.4s',
                      }}
                    />
                    <h3 className="font-display text-xl sm:text-2xl font-semibold text-gray-900 leading-snug">
                      {block.title}
                    </h3>
                  </div>

                  <p className="text-gray-500 leading-[1.85] text-[15px] sm:text-base pl-4">
                    {block.text}
                  </p>

                  {/* Subtle bottom accent */}
                  <div
                    className="mt-4 pl-4 flex gap-1"
                    style={{
                      opacity: blockVis ? 1 : 0,
                      transition: 'opacity 0.5s ease 0.6s',
                    }}
                  >
                    {[0, 1, 2].map(j => (
                      <div
                        key={j}
                        className="rounded-full"
                        style={{
                          width: j === 0 ? '16px' : '4px',
                          height: '3px',
                          backgroundColor: color,
                          opacity: 0.2 - j * 0.05,
                        }}
                      />
                    ))}
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
