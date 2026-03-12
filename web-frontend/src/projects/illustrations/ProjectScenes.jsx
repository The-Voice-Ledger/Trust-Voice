/**
 * ProjectScenes -- hand-crafted SVG landscape illustrations
 * for the Ukulima project landing page.
 *
 * Medium-detail, warm, geometric style with CSS micro-animations.
 * Each scene is composable and accepts className + theme colour props.
 */
import './SceneStyles.css';

/* ─── Shared palette helpers ─── */
const e600 = '#059669'; // emerald primary
const a600 = '#D97706'; // amber secondary
const sky  = '#E0F2FE'; // light blue
const soil = '#78716C'; // warm stone
const dSoil= '#57534E'; // dark earth

/* ========================================================
 *  1. HERO PANORAMIC
 *     Wide mountain + moringa grove + cottage rooftops
 *     Sits at the bottom of the hero, just above the fade
 * ======================================================== */
export function HeroPanorama({ className = '' }) {
  /* Sun positioned east (right), nestled at ~x=980 behind the mountain ridge at ~y=145 */
  const sunX = 980;
  const sunY = 145;

  return (
    <svg
      viewBox="0 0 1200 340"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`w-full ${className}`}
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      <defs>
        {/* Mountain fill */}
        <linearGradient id="hp-mtn" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#1a3a2e" />
          <stop offset="100%" stopColor="#0d1f17" />
        </linearGradient>
        {/* Sun radial glow -- smaller, tighter */}
        <radialGradient id="hp-sun-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#FDE68A" stopOpacity="0.4" />
          <stop offset="30%" stopColor={a600} stopOpacity="0.18" />
          <stop offset="100%" stopColor={a600} stopOpacity="0" />
        </radialGradient>
        {/* Warm sky wash -- anchored to the east */}
        <radialGradient id="hp-sky-warm" cx="82%" cy="50%" r="50%">
          <stop offset="0%" stopColor={a600} stopOpacity="0.1" />
          <stop offset="40%" stopColor="#F59E0B" stopOpacity="0.04" />
          <stop offset="100%" stopColor={a600} stopOpacity="0" />
        </radialGradient>
        {/* Rim light gradient -- stronger toward the east */}
        <linearGradient id="hp-rim" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor={a600} stopOpacity="0" />
          <stop offset="50%" stopColor={a600} stopOpacity="0.2" />
          <stop offset="75%" stopColor="#FDE68A" stopOpacity="0.7" />
          <stop offset="90%" stopColor="#FDE68A" stopOpacity="0.9" />
          <stop offset="100%" stopColor={a600} stopOpacity="0.4" />
        </linearGradient>
      </defs>

      {/* ── Warm sky wash (fades in from east) ── */}
      <rect x="0" y="0" width="1200" height="340" fill="url(#hp-sky-warm)" className="scene-sky-warm" />

      {/* ── Sun group (rises from behind the eastern ridge) ── */}
      <g className="scene-sunrise">
        {/* Outer halo -- soft, atmospheric */}
        <circle cx={sunX} cy={sunY} r="90" fill="url(#hp-sun-glow)" className="scene-halo" />
        {/* Inner warmth */}
        <circle cx={sunX} cy={sunY} r="40" fill={a600} opacity="0.06" className="scene-halo" />
        {/* Sun disc -- small, suggestive */}
        <circle cx={sunX} cy={sunY} r="16" fill={a600} opacity="0.25" />
        <circle cx={sunX} cy={sunY} r="10" fill="#FDE68A" opacity="0.2" />

        {/* Delicate rays -- fewer, shorter, radiating from the small disc */}
        <g className="scene-rays-rotate" style={{ transformOrigin: `${sunX}px ${sunY}px` }}>
          {Array.from({ length: 16 }, (_, i) => {
            const angle = i * 22.5;
            const len = i % 3 === 0 ? 45 : 28;
            const w = i % 3 === 0 ? 0.8 : 0.5;
            const op = i % 3 === 0 ? 0.08 : 0.04;
            return (
              <line
                key={i}
                x1={sunX} y1={sunY - 20}
                x2={sunX} y2={sunY - 20 - len}
                stroke={a600}
                strokeWidth={w}
                opacity={op}
                transform={`rotate(${angle} ${sunX} ${sunY})`}
              />
            );
          })}
        </g>
      </g>

      {/* ── Distant mountain range (back layer) ── */}
      <path
        d="M0 230 L100 150 L200 190 L350 110 L500 170 L600 100 L700 140 L850 80 L950 130 L1100 90 L1200 160 L1200 340 L0 340Z"
        fill="url(#hp-mtn)" opacity="0.45"
      />

      {/* ── Closer mountain range ── */}
      <path
        d="M0 260 L150 170 L300 220 L420 150 L550 200 L650 140 L780 190 L900 130 L1020 180 L1150 150 L1200 175 L1200 340 L0 340Z"
        fill="url(#hp-mtn)" opacity="0.7"
      />

      {/* ── Mountain rim light (golden edge -- brightest toward east) ── */}
      <path
        d="M0 260 L150 170 L300 220 L420 150 L550 200 L650 140 L780 190 L900 130 L1020 180 L1150 150 L1200 175"
        fill="none"
        stroke="url(#hp-rim)"
        strokeWidth="1.5"
        className="scene-rim-light"
        strokeDasharray="2000"
      />

      {/* Back ridge rim (subtler, also east-biased) */}
      <path
        d="M500 170 L600 100 L700 140 L850 80 L950 130 L1100 90 L1200 160"
        fill="none"
        stroke={a600}
        strokeWidth="0.8"
        opacity="0.12"
        className="scene-rim-light"
        strokeDasharray="2000"
      />

      {/* ── Ground plane ── */}
      <rect x="0" y="290" width="1200" height="50" fill="#0d1f17" opacity="0.8" />

      {/* ── Moringa trees (swaying) ── */}
      {[100, 220, 360, 500, 660, 800, 940, 1080].map((x, i) => {
        const h = 55 + (i % 3) * 18;
        const cls = i % 3 === 0 ? 'scene-sway' : i % 3 === 1 ? 'scene-sway-slow' : 'scene-sway-delay';
        return (
          <g key={i} className={cls}>
            <rect x={x - 1.5} y={290 - h} width="3" height={h} rx="1.5" fill={e600} opacity="0.5" />
            <ellipse cx={x} cy={290 - h - 7} rx={12 + (i % 2) * 5} ry={9 + (i % 2) * 3} fill={e600} opacity={0.25 + (i % 3) * 0.08} />
            <ellipse cx={x - 6} cy={290 - h + 2} rx={8} ry={5} fill={e600} opacity={0.2} />
            <ellipse cx={x + 6} cy={290 - h + 2} rx={8} ry={5} fill={e600} opacity={0.18} />
          </g>
        );
      })}

      {/* ── Eco-cottages with warm glow ── */}
      {[
        { x: 160, w: 38, h: 30 },
        { x: 420, w: 34, h: 26 },
        { x: 740, w: 40, h: 28 },
        { x: 980, w: 36, h: 27 },
      ].map((c, i) => (
        <g key={`c${i}`}>
          <rect x={c.x} y={290 - c.h} width={c.w} height={c.h} rx="2" fill="#1a2e24" opacity="0.85" />
          <polygon
            points={`${c.x - 4},${290 - c.h} ${c.x + c.w / 2},${290 - c.h - 15} ${c.x + c.w + 4},${290 - c.h}`}
            fill="#2d1f0e" opacity="0.9"
          />
          <rect x={c.x + c.w / 2 - 5} y={290 - c.h + 8} width="10" height="8" rx="1" fill={a600} className="scene-glow" opacity="0.7" />
          <rect x={c.x + 5} y={290 - c.h + 10} width="6" height="5" rx="1" fill={a600} className="scene-glow-slow" opacity="0.5" />
          {/* Chimney */}
          <rect x={c.x + c.w - 10} y={290 - c.h - 15 - 8} width="5" height="12" rx="1" fill="#2d1f0e" opacity="0.6" />
          <circle cx={c.x + c.w - 7.5} cy={290 - c.h - 15 - 10} r="3" fill="white" opacity="0.06" className="scene-steam" />
        </g>
      ))}

      {/* ── Birds silhouettes (appear late, near the sun) ── */}
      <g className="scene-birds">
        <path d="M880 100 Q884 95 888 100 Q892 95 896 100" stroke="white" strokeWidth="1" fill="none" opacity="0.3" />
        <path d="M900 92 Q903 88 906 92 Q909 88 912 92" stroke="white" strokeWidth="0.8" fill="none" opacity="0.2" />
      </g>
      <g className="scene-birds-delay">
        <path d="M920 110 Q924 105 928 110 Q932 105 936 110" stroke="white" strokeWidth="1" fill="none" opacity="0.25" />
        <path d="M850 115 Q853 111 856 115 Q859 111 862 115" stroke="white" strokeWidth="0.8" fill="none" opacity="0.15" />
      </g>

      {/* Falling leaves */}
      <circle cx="350" cy="200" r="2" fill={e600} opacity="0.4" className="scene-leaf-fall" />
      <circle cx="700" cy="180" r="1.5" fill={e600} opacity="0.3" className="scene-leaf-fall-delay" />
      <circle cx="1000" cy="190" r="1.5" fill={e600} opacity="0.25" className="scene-leaf-fall" />
    </svg>
  );
}

/* ========================================================
 *  2. VISION VIGNETTES
 *     Three small illustrations for vision cards:
 *     - Seedling / sprouting
 *     - Community / hands holding leaf
 *     - Growth / upward sprout with coin
 * ======================================================== */
export function VisionSeedling({ className = '' }) {
  return (
    <svg viewBox="0 0 120 80" fill="none" className={`${className}`} aria-hidden="true">
      {/* Soil */}
      <ellipse cx="60" cy="68" rx="40" ry="8" fill={soil} opacity="0.15" />
      {/* Stem */}
      <path d="M60 68 Q58 50 60 38" stroke={e600} strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.6" />
      {/* Leaves (animated) */}
      <g className="scene-sway-slow">
        <ellipse cx="52" cy="38" rx="8" ry="4" fill={e600} opacity="0.4" transform="rotate(-30 52 38)" />
      </g>
      <g className="scene-sway-delay">
        <ellipse cx="68" cy="34" rx="9" ry="4.5" fill={e600} opacity="0.35" transform="rotate(25 68 34)" />
      </g>
      {/* Small new leaf at top */}
      <g className="scene-sway">
        <ellipse cx="60" cy="28" rx="5" ry="3" fill={e600} opacity="0.5" />
      </g>
      {/* Water drops */}
      <circle cx="48" cy="56" r="1.5" fill="#93C5FD" opacity="0.4" className="scene-shimmer" />
      <circle cx="72" cy="60" r="1" fill="#93C5FD" opacity="0.3" className="scene-shimmer-delay" />
    </svg>
  );
}

export function VisionCommunity({ className = '' }) {
  return (
    <svg viewBox="0 0 120 80" fill="none" className={`${className}`} aria-hidden="true">
      {/* Two hands cupping a leaf */}
      {/* Left hand */}
      <path d="M30 60 Q35 42 50 40 Q55 38 58 44" stroke={a600} strokeWidth="1.5" fill="none" opacity="0.4" />
      {/* Right hand */}
      <path d="M90 60 Q85 42 70 40 Q65 38 62 44" stroke={a600} strokeWidth="1.5" fill="none" opacity="0.4" />
      {/* Moringa leaf compound */}
      <g className="scene-sway-slow">
        <path d="M60 44 L60 22" stroke={e600} strokeWidth="1.5" fill="none" opacity="0.5" />
        {[22, 28, 34].map((y, i) => (
          <g key={i}>
            <ellipse cx={54} cy={y} rx="5" ry="2.5" fill={e600} opacity={0.35 + i * 0.05} transform={`rotate(-15 54 ${y})`} />
            <ellipse cx={66} cy={y} rx="5" ry="2.5" fill={e600} opacity={0.35 + i * 0.05} transform={`rotate(15 66 ${y})`} />
          </g>
        ))}
        <ellipse cx="60" cy="18" rx="4" ry="2.5" fill={e600} opacity="0.45" />
      </g>
      {/* Connection lines */}
      <path d="M40 65 Q60 55 80 65" stroke={a600} strokeWidth="0.8" fill="none" opacity="0.2" strokeDasharray="3 3" />
    </svg>
  );
}

export function VisionGrowth({ className = '' }) {
  return (
    <svg viewBox="0 0 120 80" fill="none" className={`${className}`} aria-hidden="true">
      {/* Soil */}
      <ellipse cx="60" cy="70" rx="35" ry="6" fill={soil} opacity="0.12" />
      {/* Upward sprout growth chart shape */}
      <path d="M30 65 L45 55 L55 48 L65 35 L80 26 L90 18" stroke={e600} strokeWidth="2" strokeLinecap="round" fill="none" opacity="0.4" />
      {/* Dots on path */}
      {[{x:30,y:65},{x:45,y:55},{x:65,y:35},{x:90,y:18}].map((pt, i) => (
        <circle key={i} cx={pt.x} cy={pt.y} r="3" fill={e600} opacity={0.25 + i * 0.1} />
      ))}
      {/* Coin shape at peak */}
      <circle cx="90" cy="18" r="8" fill={a600} opacity="0.25" className="scene-glow-slow" />
      <circle cx="90" cy="18" r="5" stroke={a600} strokeWidth="1" fill="none" opacity="0.35" />
      {/* Leaf at peak */}
      <g className="scene-sway">
        <ellipse cx="95" cy="12" rx="4" ry="2" fill={e600} opacity="0.5" transform="rotate(30 95 12)" />
      </g>
    </svg>
  );
}

/* ========================================================
 *  3. NARRATIVE SCENES
 *     Four scenes matching the Ukulima story blocks:
 *     0 - Vast farmland / rows of trees
 *     1 - Harvest / workers picking
 *     2 - Processing facility
 *     3 - Global reach / distribution
 * ======================================================== */
export function NarrativeFarmland({ className = '' }) {
  return (
    <svg viewBox="0 0 240 140" fill="none" className={`${className}`} aria-hidden="true">
      {/* Sky */}
      <rect width="240" height="140" fill={sky} opacity="0.3" rx="8" />
      {/* Sun */}
      <circle cx="200" cy="30" r="16" fill={a600} opacity="0.2" className="scene-glow-slow" />
      <circle cx="200" cy="30" r="10" fill={a600} opacity="0.15" className="scene-sun-rotate" />
      {/* Rolling hills */}
      <path d="M0 100 Q60 70 120 90 Q180 80 240 95 L240 140 L0 140Z" fill={e600} opacity="0.12" />
      <path d="M0 110 Q80 85 160 100 Q200 95 240 105 L240 140 L0 140Z" fill={e600} opacity="0.18" />
      {/* Rows of moringa */}
      {[30, 60, 90, 120, 150, 180, 210].map((x, i) => (
        <g key={i} className={i % 2 === 0 ? 'scene-sway' : 'scene-sway-delay'}>
          <rect x={x - 1} y={105 - (i % 3) * 3} width="2" height={16 + (i % 3) * 4} rx="1" fill={e600} opacity="0.35" />
          <ellipse cx={x} cy={103 - (i % 3) * 3 - 5} rx={6 + (i % 2) * 2} ry={4} fill={e600} opacity="0.25" />
        </g>
      ))}
      {/* Path/road */}
      <path d="M0 130 Q60 122 120 128 Q180 124 240 132" stroke={soil} strokeWidth="3" fill="none" opacity="0.1" />
    </svg>
  );
}

export function NarrativeHarvest({ className = '' }) {
  return (
    <svg viewBox="0 0 240 140" fill="none" className={`${className}`} aria-hidden="true">
      <rect width="240" height="140" fill={sky} opacity="0.3" rx="8" />
      {/* Tree with branches full of leaves */}
      <g className="scene-sway-slow">
        <rect x="70" y="50" width="4" height="60" rx="2" fill={e600} opacity="0.4" />
        {/* Branches */}
        <path d="M72 70 Q50 55 40 50" stroke={e600} strokeWidth="2" fill="none" opacity="0.3" />
        <path d="M72 60 Q95 45 105 42" stroke={e600} strokeWidth="2" fill="none" opacity="0.3" />
        {/* Leaf clusters */}
        <ellipse cx="38" cy="46" rx="12" ry="8" fill={e600} opacity="0.25" />
        <ellipse cx="72" cy="40" rx="15" ry="10" fill={e600} opacity="0.2" />
        <ellipse cx="107" cy="38" rx="12" ry="8" fill={e600} opacity="0.25" />
      </g>
      {/* Person figure (simple geometric) */}
      <g>
        {/* Head */}
        <circle cx="150" cy="72" r="6" fill={a600} opacity="0.3" />
        {/* Body */}
        <rect x="147" y="78" width="6" height="18" rx="3" fill={a600} opacity="0.25" />
        {/* Arm reaching to tree */}
        <path d="M150 84 Q130 75 115 68" stroke={a600} strokeWidth="2" fill="none" opacity="0.25" strokeLinecap="round" />
        {/* Basket */}
        <path d="M155 92 L165 92 L163 104 L157 104Z" fill={a600} opacity="0.2" />
      </g>
      {/* Ground */}
      <path d="M0 115 Q120 108 240 115 L240 140 L0 140Z" fill={e600} opacity="0.1" />
      {/* Scattered leaves falling */}
      <circle cx="100" cy="70" r="1.5" fill={e600} opacity="0.35" className="scene-leaf-fall" />
      <circle cx="85" cy="55" r="1" fill={e600} opacity="0.25" className="scene-leaf-fall-delay" />
    </svg>
  );
}

export function NarrativeProcessing({ className = '' }) {
  return (
    <svg viewBox="0 0 240 140" fill="none" className={`${className}`} aria-hidden="true">
      <rect width="240" height="140" fill="#FAFAF9" opacity="0.5" rx="8" />
      {/* Processing building */}
      <rect x="40" y="50" width="80" height="55" rx="3" fill={soil} opacity="0.15" />
      {/* Roof */}
      <polygon points="35,50 80,25 125,50" fill={soil} opacity="0.2" />
      {/* Windows */}
      <rect x="52" y="65" width="12" height="10" rx="1" fill={a600} opacity="0.25" className="scene-glow" />
      <rect x="72" y="65" width="12" height="10" rx="1" fill={a600} opacity="0.2" className="scene-glow-slow" />
      <rect x="92" y="65" width="12" height="10" rx="1" fill={a600} opacity="0.25" className="scene-glow" />
      {/* Door */}
      <rect x="74" y="85" width="14" height="20" rx="2" fill={dSoil} opacity="0.2" />
      {/* Chimney with steam */}
      <rect x="95" y="30" width="8" height="20" rx="1" fill={soil} opacity="0.2" />
      <circle cx="99" cy="25" r="4" fill="white" opacity="0.15" className="scene-steam" />
      <circle cx="102" cy="20" r="3" fill="white" opacity="0.1" className="scene-steam-delay" />
      {/* Drying racks (right side) */}
      {[150, 170, 190].map((x, i) => (
        <g key={i}>
          <rect x={x} y={70 + i * 5} width="30" height="2" rx="1" fill={soil} opacity="0.15" />
          {/* Moringa on rack */}
          {[0, 8, 16, 24].map((dx, j) => (
            <circle key={j} cx={x + 3 + dx} cy={69 + i * 5} r="1.5" fill={e600} opacity={0.2 + j * 0.03} />
          ))}
          {/* Legs */}
          <rect x={x + 2} y={70 + i * 5} width="1.5" height={30 - i * 5} fill={soil} opacity="0.1" />
          <rect x={x + 27} y={70 + i * 5} width="1.5" height={30 - i * 5} fill={soil} opacity="0.1" />
        </g>
      ))}
      {/* Ground */}
      <rect x="0" y="105" width="240" height="35" rx="0" fill={e600} opacity="0.06" />
    </svg>
  );
}

export function NarrativeDistribution({ className = '' }) {
  return (
    <svg viewBox="0 0 240 140" fill="none" className={`${className}`} aria-hidden="true">
      <rect width="240" height="140" fill={sky} opacity="0.2" rx="8" />
      {/* Simple globe outline */}
      <circle cx="60" cy="70" r="35" stroke={e600} strokeWidth="1" fill="none" opacity="0.15" />
      <ellipse cx="60" cy="70" rx="20" ry="35" stroke={e600} strokeWidth="0.8" fill="none" opacity="0.1" />
      <path d="M25 70 Q60 60 95 70" stroke={e600} strokeWidth="0.8" fill="none" opacity="0.1" />
      <path d="M25 85 Q60 78 95 85" stroke={e600} strokeWidth="0.5" fill="none" opacity="0.08" />
      {/* Africa outline (simplified) */}
      <path d="M55 48 Q65 50 68 58 Q70 68 68 78 Q62 85 56 82 Q50 75 52 65 Q50 55 55 48Z" fill={e600} opacity="0.12" />
      {/* Arrow from Africa outward */}
      <path d="M80 65 Q120 50 170 55" stroke={a600} strokeWidth="1.5" fill="none" opacity="0.3" strokeDasharray="4 3" />
      <path d="M80 75 Q130 85 175 78" stroke={a600} strokeWidth="1.5" fill="none" opacity="0.25" strokeDasharray="4 3" />
      {/* Packages / boxes on right */}
      <g className="scene-drift">
        <rect x="170" y="48" width="16" height="14" rx="2" fill={a600} opacity="0.2" />
        <rect x="190" y="52" width="14" height="12" rx="2" fill={a600} opacity="0.15" />
        <rect x="175" y="66" width="18" height="14" rx="2" fill={e600} opacity="0.15" />
      </g>
      {/* Small truck */}
      <g className="scene-drift">
        <rect x="155" y="95" width="30" height="16" rx="3" fill={soil} opacity="0.2" />
        <rect x="185" y="100" width="14" height="11" rx="2" fill={soil} opacity="0.15" />
        <circle cx="165" cy="113" r="4" fill={dSoil} opacity="0.2" />
        <circle cx="185" cy="113" r="4" fill={dSoil} opacity="0.2" />
        <circle cx="195" cy="113" r="4" fill={dSoil} opacity="0.2" />
      </g>
      {/* Road */}
      <path d="M0 118 L240 118" stroke={soil} strokeWidth="2" fill="none" opacity="0.08" />
    </svg>
  );
}

/* ========================================================
 *  4. PILLAR SCENES
 *     - Eco-lodge with warm lights
 *     - Factory / processing
 *     - Trade / truck & packaging
 * ======================================================== */
export function PillarLodge({ className = '' }) {
  return (
    <svg viewBox="0 0 200 120" fill="none" className={`${className}`} aria-hidden="true">
      {/* Sky gradient */}
      <defs>
        <linearGradient id="pl-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#FDE68A" stopOpacity="0.15" />
          <stop offset="100%" stopColor="white" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect width="200" height="120" fill="url(#pl-sky)" rx="8" />
      {/* Main cottage */}
      <rect x="50" y="55" width="60" height="40" rx="3" fill={soil} opacity="0.15" />
      {/* A-frame roof */}
      <polygon points="44,55 80,25 116,55" fill="#78350F" opacity="0.15" />
      {/* Porch columns */}
      <rect x="52" y="55" width="2" height="40" fill={soil} opacity="0.12" />
      <rect x="106" y="55" width="2" height="40" fill={soil} opacity="0.12" />
      {/* Veranda */}
      <rect x="44" y="53" width="72" height="3" rx="1" fill={soil} opacity="0.1" />
      {/* Windows with warm glow */}
      <rect x="60" y="65" width="14" height="10" rx="2" fill={a600} opacity="0.35" className="scene-glow" />
      <rect x="86" y="65" width="14" height="10" rx="2" fill={a600} opacity="0.3" className="scene-glow-slow" />
      {/* Door with light spill */}
      <rect x="76" y="72" width="10" height="23" rx="2" fill={a600} opacity="0.25" className="scene-glow" />
      {/* Chimney */}
      <rect x="92" y="30" width="6" height="25" rx="1" fill={soil} opacity="0.15" />
      <circle cx="95" cy="26" r="3" fill="white" opacity="0.1" className="scene-steam" />
      {/* Surrounding trees */}
      <g className="scene-sway-slow">
        <rect x="24" y="50" width="2" height="45" rx="1" fill={e600} opacity="0.3" />
        <ellipse cx="25" cy="45" rx="10" ry="8" fill={e600} opacity="0.15" />
      </g>
      <g className="scene-sway-delay">
        <rect x="140" y="55" width="2" height="40" rx="1" fill={e600} opacity="0.3" />
        <ellipse cx="141" cy="50" rx="8" ry="7" fill={e600} opacity="0.15" />
      </g>
      {/* Ground */}
      <ellipse cx="100" cy="98" rx="80" ry="8" fill={e600} opacity="0.06" />
    </svg>
  );
}

export function PillarFactory({ className = '' }) {
  return (
    <svg viewBox="0 0 200 120" fill="none" className={`${className}`} aria-hidden="true">
      <rect width="200" height="120" fill="#FAFAF9" opacity="0.4" rx="8" />
      {/* Main building */}
      <rect x="30" y="40" width="70" height="50" rx="2" fill={soil} opacity="0.15" />
      {/* Saw-tooth roof */}
      <polygon points="30,40 50,22 70,40" fill={soil} opacity="0.2" />
      <polygon points="70,40 90,22 100,40" fill={soil} opacity="0.18" />
      {/* Windows */}
      {[38, 56, 74].map((x, i) => (
        <rect key={i} x={x} y={52} width="10" height="8" rx="1" fill={a600} opacity={0.2 + i * 0.03} className="scene-glow" />
      ))}
      {/* Conveyor belt */}
      <rect x="100" y="72" width="60" height="4" rx="2" fill={soil} opacity="0.12" />
      {/* Items on conveyor */}
      <g className="scene-drift">
        <rect x="110" y="67" width="8" height="6" rx="1" fill={e600} opacity="0.2" />
        <rect x="125" y="67" width="8" height="6" rx="1" fill={e600} opacity="0.18" />
        <rect x="140" y="67" width="8" height="6" rx="1" fill={e600} opacity="0.15" />
      </g>
      {/* Vats */}
      <ellipse cx="45" cy="78" rx="8" ry="5" fill={dSoil} opacity="0.12" />
      <rect x="37" y="78" width="16" height="10" rx="1" fill={dSoil} opacity="0.1" />
      {/* Steam from vat */}
      <circle cx="45" cy="73" r="3" fill="white" opacity="0.08" className="scene-steam" />
      {/* Ground */}
      <rect x="0" y="92" width="200" height="28" fill={e600} opacity="0.04" />
    </svg>
  );
}

export function PillarTrade({ className = '' }) {
  return (
    <svg viewBox="0 0 200 120" fill="none" className={`${className}`} aria-hidden="true">
      <rect width="200" height="120" fill={sky} opacity="0.2" rx="8" />
      {/* Road */}
      <rect x="0" y="88" width="200" height="12" rx="0" fill={soil} opacity="0.08" />
      <path d="M0 94 L200 94" stroke="white" strokeWidth="1" strokeDasharray="8 6" opacity="0.15" />
      {/* Truck */}
      <g className="scene-drift">
        <rect x="55" y="62" width="50" height="28" rx="4" fill={e600} opacity="0.2" />
        <rect x="105" y="70" width="22" height="20" rx="3" fill={e600} opacity="0.15" />
        {/* Windshield */}
        <rect x="108" y="72" width="16" height="10" rx="2" fill={sky} opacity="0.3" />
        {/* Wheels */}
        <circle cx="72" cy="92" r="5" fill={dSoil} opacity="0.25" />
        <circle cx="95" cy="92" r="5" fill={dSoil} opacity="0.25" />
        <circle cx="118" cy="92" r="5" fill={dSoil} opacity="0.25" />
        {/* Packages in truck */}
        <rect x="60" y="67" width="10" height="8" rx="1" fill={a600} opacity="0.2" />
        <rect x="73" y="65" width="10" height="10" rx="1" fill={a600} opacity="0.15" />
        <rect x="86" y="67" width="10" height="8" rx="1" fill={a600} opacity="0.2" />
      </g>
      {/* Warehouse in background */}
      <rect x="150" y="48" width="35" height="42" rx="2" fill={soil} opacity="0.1" />
      <rect x="150" y="46" width="35" height="4" rx="1" fill={soil} opacity="0.13" />
      {/* Trees */}
      <g className="scene-sway">
        <rect x="19" y="52" width="2" height="38" rx="1" fill={e600} opacity="0.25" />
        <ellipse cx="20" cy="47" rx="8" ry="7" fill={e600} opacity="0.12" />
      </g>
    </svg>
  );
}

/* ========================================================
 *  5. EXPERIENCE SCENES
 *     - Day 1: Sunrise over farm
 *     - Day 2: Hands in soil, midday work
 *     - Day 3: Sunset from cottage veranda
 * ======================================================== */
export function ExperienceSunrise({ className = '' }) {
  return (
    <svg viewBox="0 0 200 110" fill="none" className={`${className}`} aria-hidden="true">
      <defs>
        <linearGradient id="es-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={a600} stopOpacity="0.12" />
          <stop offset="60%" stopColor={sky} stopOpacity="0.2" />
          <stop offset="100%" stopColor="white" stopOpacity="0" />
        </linearGradient>
      </defs>
      <rect width="200" height="110" fill="url(#es-sky)" rx="8" />
      {/* Sun rising over horizon */}
      <circle cx="100" cy="62" r="18" fill={a600} opacity="0.2" className="scene-glow-slow" />
      <circle cx="100" cy="62" r="12" fill={a600} opacity="0.15" />
      {/* Sun rays */}
      <g className="scene-sun-rotate" style={{ transformOrigin: '100px 62px' }}>
        {[0, 45, 90, 135, 180, 225, 270, 315].map((angle, i) => (
          <line
            key={i}
            x1="100" y1="38" x2="100" y2="32"
            stroke={a600} strokeWidth="1" opacity="0.1"
            transform={`rotate(${angle} 100 62)`}
          />
        ))}
      </g>
      {/* Hills */}
      <path d="M0 75 Q50 55 100 68 Q150 58 200 72 L200 110 L0 110Z" fill={e600} opacity="0.12" />
      {/* Farm rows */}
      {[30, 60, 90, 120, 150, 170].map((x, i) => (
        <g key={i} className="scene-sway-delay">
          <rect x={x} y={80 - (i % 2) * 3} width="1.5" height={12} rx="0.75" fill={e600} opacity="0.3" />
          <ellipse cx={x + 0.75} cy={78 - (i % 2) * 3} rx="4" ry="3" fill={e600} opacity="0.15" />
        </g>
      ))}
    </svg>
  );
}

export function ExperienceFieldwork({ className = '' }) {
  return (
    <svg viewBox="0 0 200 110" fill="none" className={`${className}`} aria-hidden="true">
      <rect width="200" height="110" fill={sky} opacity="0.25" rx="8" />
      {/* Ground soil */}
      <ellipse cx="100" cy="95" rx="90" ry="15" fill={soil} opacity="0.1" />
      {/* Person kneeling */}
      <circle cx="90" cy="58" r="6" fill={a600} opacity="0.25" />
      <rect x="87" y="64" width="6" height="15" rx="3" fill={a600} opacity="0.2" />
      {/* Arms reaching down */}
      <path d="M87 70 Q78 80 75 85" stroke={a600} strokeWidth="2" fill="none" opacity="0.2" strokeLinecap="round" />
      <path d="M93 70 Q100 80 103 85" stroke={a600} strokeWidth="2" fill="none" opacity="0.2" strokeLinecap="round" />
      {/* Planted seedlings around hands */}
      {[65, 78, 113, 128].map((x, i) => (
        <g key={i} className="scene-sway">
          <rect x={x} y={80} width="1.5" height="8" rx="0.75" fill={e600} opacity="0.35" />
          <ellipse cx={x + 0.75} cy={78} rx="4" ry="2.5" fill={e600} opacity="0.2" />
        </g>
      ))}
      {/* Watering can */}
      <rect x="120" y="72" width="12" height="10" rx="2" fill={soil} opacity="0.15" />
      <path d="M132 74 L138 70" stroke={soil} strokeWidth="1.5" fill="none" opacity="0.12" />
      {/* Water drops from can */}
      <circle cx="137" cy="73" r="1" fill="#93C5FD" opacity="0.3" className="scene-shimmer" />
      <circle cx="135" cy="76" r="0.8" fill="#93C5FD" opacity="0.25" className="scene-shimmer-delay" />
    </svg>
  );
}

export function ExperienceSunset({ className = '' }) {
  return (
    <svg viewBox="0 0 200 110" fill="none" className={`${className}`} aria-hidden="true">
      <defs>
        <linearGradient id="ess-sky" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor={a600} stopOpacity="0.2" />
          <stop offset="50%" stopColor="#F59E0B" stopOpacity="0.1" />
          <stop offset="100%" stopColor={e600} stopOpacity="0.05" />
        </linearGradient>
      </defs>
      <rect width="200" height="110" fill="url(#ess-sky)" rx="8" />
      {/* Setting sun */}
      <circle cx="160" cy="35" r="16" fill={a600} opacity="0.25" className="scene-glow-slow" />
      {/* Mountains silhouette */}
      <path d="M0 70 Q40 50 80 65 Q120 45 160 60 Q180 55 200 65 L200 110 L0 110Z" fill="#1a2e24" opacity="0.15" />
      {/* Cottage veranda view (foreground frame) */}
      {/* Left column */}
      <rect x="10" y="20" width="4" height="90" fill={soil} opacity="0.15" />
      {/* Right column */}
      <rect x="186" y="20" width="4" height="90" fill={soil} opacity="0.15" />
      {/* Railing */}
      <rect x="10" y="80" width="180" height="3" rx="1" fill={soil} opacity="0.1" />
      {/* Vertical railings */}
      {[30, 55, 80, 105, 130, 155].map((x, i) => (
        <rect key={i} x={x} y={80} width="1.5" height="15" fill={soil} opacity="0.08" />
      ))}
      {/* Overhead beam */}
      <rect x="8" y="18" width="184" height="4" rx="1" fill={soil} opacity="0.12" />
      {/* Moringa tree canopy peeking in */}
      <g className="scene-sway-slow">
        <ellipse cx="175" cy="60" rx="18" ry="14" fill={e600} opacity="0.12" />
        <ellipse cx="165" cy="55" rx="12" ry="10" fill={e600} opacity="0.1" />
      </g>
      {/* Warm floor glow */}
      <rect x="14" y="95" width="172" height="15" rx="0" fill={a600} opacity="0.04" />
    </svg>
  );
}

/* ========================================================
 *  6. CTA HORIZON
 *     Sun setting behind moringa canopy, warm and inviting
 * ======================================================== */
export function CtaHorizon({ className = '' }) {
  return (
    <svg
      viewBox="0 0 800 160"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`w-full ${className}`}
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      {/* Sun */}
      <circle cx="400" cy="100" r="50" fill={a600} opacity="0.12" className="scene-glow-slow" />
      <circle cx="400" cy="100" r="30" fill={a600} opacity="0.08" />
      {/* Rays */}
      <g className="scene-sun-rotate" style={{ transformOrigin: '400px 100px' }}>
        {[0, 30, 60, 90, 120, 150, 180, 210, 240, 270, 300, 330].map((a, i) => (
          <line key={i} x1="400" y1="45" x2="400" y2="35" stroke={a600} strokeWidth="1" opacity="0.06" transform={`rotate(${a} 400 100)`} />
        ))}
      </g>
      {/* Moringa canopy silhouettes */}
      {[80, 180, 300, 420, 540, 650, 740].map((x, i) => (
        <g key={i} className={i % 2 === 0 ? 'scene-sway' : 'scene-sway-delay'}>
          <rect x={x - 1.5} y={110 - 12 - (i % 3) * 6} width="3" height={30 + (i % 3) * 6} rx="1.5" fill={e600} opacity="0.15" />
          <ellipse cx={x} cy={110 - 18 - (i % 3) * 6} rx={14 + (i % 2) * 6} ry={10 + (i % 2) * 3} fill={e600} opacity="0.1" />
        </g>
      ))}
      {/* Ground */}
      <path d="M0 120 Q200 110 400 118 Q600 110 800 120 L800 160 L0 160Z" fill={e600} opacity="0.08" />
    </svg>
  );
}

/* ========================================================
 *  8. FOOTER MOONSCAPE
 *     Night mountain range with a crescent moon peeking
 *     behind the western (left) peaks. Subtle stars.
 * ======================================================== */
export function FooterMoonscape({ className = '' }) {
  const moonX = 180;
  const moonY = 42;

  return (
    <svg
      viewBox="0 0 1200 140"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={`w-full ${className}`}
      preserveAspectRatio="xMidYMax slice"
      aria-hidden="true"
    >
      <defs>
        {/* Moon glow */}
        <radialGradient id="ft-moon-glow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stopColor="#E0E7FF" stopOpacity="0.12" />
          <stop offset="40%" stopColor="#C7D2FE" stopOpacity="0.05" />
          <stop offset="100%" stopColor="#818CF8" stopOpacity="0" />
        </radialGradient>
        {/* Mountain gradient (night) */}
        <linearGradient id="ft-mtn" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#111827" />
          <stop offset="100%" stopColor="#030712" />
        </linearGradient>
        {/* Rim light from the moonlit side (left-biased) */}
        <linearGradient id="ft-rim" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stopColor="#818CF8" stopOpacity="0.5" />
          <stop offset="15%" stopColor="#C7D2FE" stopOpacity="0.35" />
          <stop offset="35%" stopColor="#818CF8" stopOpacity="0.12" />
          <stop offset="60%" stopColor="#818CF8" stopOpacity="0.04" />
          <stop offset="100%" stopColor="#818CF8" stopOpacity="0" />
        </linearGradient>
      </defs>

      {/* ── Stars (tiny, scattered) ── */}
      {[
        { x: 60, y: 18, r: 1.2, o: 0.25 },
        { x: 140, y: 10, r: 0.8, o: 0.2 },
        { x: 310, y: 22, r: 1, o: 0.15 },
        { x: 480, y: 12, r: 0.7, o: 0.12 },
        { x: 620, y: 28, r: 0.9, o: 0.1 },
        { x: 780, y: 16, r: 1.1, o: 0.14 },
        { x: 890, y: 8, r: 0.6, o: 0.1 },
        { x: 1020, y: 20, r: 0.8, o: 0.08 },
        { x: 1140, y: 14, r: 0.7, o: 0.1 },
        { x: 260, y: 6, r: 0.5, o: 0.18 },
        { x: 550, y: 4, r: 0.6, o: 0.12 },
        { x: 950, y: 30, r: 0.9, o: 0.09 },
      ].map((s, i) => (
        <circle key={i} cx={s.x} cy={s.y} r={s.r} fill="white" opacity={s.o}
          className={i % 3 === 0 ? 'scene-glow-slow' : ''} />
      ))}

      {/* ── Moon (crescent, behind western peaks) ── */}
      <g>
        {/* Outer glow */}
        <circle cx={moonX} cy={moonY} r="55" fill="url(#ft-moon-glow)" />
        {/* Moon disc */}
        <circle cx={moonX} cy={moonY} r="14" fill="#E0E7FF" opacity="0.18" />
        <circle cx={moonX} cy={moonY} r="10" fill="#EEF2FF" opacity="0.12" />
        {/* Crescent shadow (overlapping disc to create crescent shape) */}
        <circle cx={moonX + 5} cy={moonY - 2} r="10" fill="#030712" opacity="0.2" />
      </g>

      {/* ── Distant mountain range ── */}
      <path
        d="M0 90 L80 55 L160 72 L260 40 L380 65 L480 48 L580 58 L700 35 L820 55 L920 42 L1040 52 L1120 60 L1200 50 L1200 140 L0 140Z"
        fill="url(#ft-mtn)" opacity="0.5"
      />

      {/* ── Closer mountain range ── */}
      <path
        d="M0 105 L100 70 L200 88 L320 58 L440 78 L540 62 L660 75 L780 52 L900 72 L1000 60 L1100 68 L1200 75 L1200 140 L0 140Z"
        fill="url(#ft-mtn)" opacity="0.8"
      />

      {/* ── Mountain rim light (moonlit from left) ── */}
      <path
        d="M0 105 L100 70 L200 88 L320 58 L440 78 L540 62 L660 75 L780 52 L900 72 L1000 60 L1100 68 L1200 75"
        fill="none"
        stroke="url(#ft-rim)"
        strokeWidth="1"
        opacity="0.6"
      />

      {/* ── Thin tree silhouettes on the ridge ── */}
      {[120, 250, 400, 560, 710, 860, 1000, 1130].map((x, i) => {
        const baseY = 75 + (i % 3) * 8;
        const h = 14 + (i % 3) * 5;
        return (
          <g key={i}>
            <rect x={x - 0.8} y={baseY - h} width="1.6" height={h} rx="0.8" fill="#111827" opacity="0.6" />
            <ellipse cx={x} cy={baseY - h - 3} rx={5 + (i % 2) * 3} ry={4 + (i % 2) * 2} fill="#111827" opacity="0.4" />
          </g>
        );
      })}
    </svg>
  );
}

/* ─── Convenience mapping for config-driven usage ─── */
export const NARRATIVE_SCENES = [NarrativeFarmland, NarrativeHarvest, NarrativeProcessing, NarrativeDistribution];
export const VISION_SCENES    = [VisionSeedling, VisionCommunity, VisionGrowth];
export const PILLAR_SCENES    = [PillarLodge, PillarFactory, PillarTrade];
export const EXPERIENCE_SCENES = [ExperienceSunrise, ExperienceFieldwork, ExperienceSunset];
