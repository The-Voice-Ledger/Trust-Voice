/**
 * Bold decorative SVG elements — visible, distinctive patterns for each page.
 * These are NOT subtle. Each pattern gives its page a unique techno-organic identity.
 */
import { useId } from 'react';

/* ─── Circuit Trace Background (VISIBLE — used in footer, proven to work) ── */
export function CircuitTrace({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 400 200" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <g stroke="currentColor" strokeWidth="1.2" opacity="0.10">
        <path d="M0 40h120l20-20h60l20 20h180" />
        <path d="M0 80h60l15 15h90l15-15h220" />
        <path d="M0 120h200l20 20h40l20-20h120" />
        <path d="M0 160h80l25-25h50l25 25h220" />
        <path d="M140 20v40M220 60v40M280 100v40M100 140v40" />
        <circle cx="140" cy="40" r="4" fill="currentColor" opacity="0.20" />
        <circle cx="220" cy="80" r="4" fill="currentColor" opacity="0.20" />
        <circle cx="280" cy="120" r="4" fill="currentColor" opacity="0.20" />
        <circle cx="100" cy="160" r="4" fill="currentColor" opacity="0.20" />
        <circle cx="140" cy="20" r="2.5" fill="currentColor" opacity="0.15" />
        <circle cx="220" cy="60" r="2.5" fill="currentColor" opacity="0.15" />
        <circle cx="280" cy="100" r="2.5" fill="currentColor" opacity="0.15" />
        <circle cx="100" cy="140" r="2.5" fill="currentColor" opacity="0.15" />
      </g>
    </svg>
  );
}

/* ─── Hexagonal Grid — VISIBLE at ~0.08 opacity ────────────── */
export function HexGrid({ className = '' }) {
  const pid = useId();
  return (
    <svg className={className} width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <pattern id={`hex-${pid}`} width="56" height="100" patternUnits="userSpaceOnUse" patternTransform="scale(0.8)">
          <path d="M28 66L0 50V16L28 0l28 16v34L28 66zM28 100L0 84V66l28 16 28-16v18L28 100z"
            fill="none" stroke="currentColor" strokeWidth="0.8" opacity="0.10" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#hex-${pid})`} />
    </svg>
  );
}

/* ─── Topography Lines — organic contour map ──────────────── */
export function TopographyBg({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 600 400" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" preserveAspectRatio="xMidYMid slice">
      <g stroke="currentColor" strokeWidth="0.8" opacity="0.10" fill="none">
        <path d="M-20 200C60 160 180 240 300 200s240-80 320-20" />
        <path d="M-20 180C80 140 160 220 280 180s200-60 340-10" />
        <path d="M-20 220C40 180 200 260 320 220s220-100 300-30" />
        <path d="M-20 160C100 120 140 200 260 160s260-40 360 0" />
        <path d="M-20 240C60 200 220 280 340 240s200-120 280-40" />
        <path d="M-20 140C120 100 120 180 240 140s280-20 380 10" />
        <path d="M-20 260C40 220 240 300 360 260s180-140 260-50" />
        <path d="M-20 120C140 80 100 160 220 120s300 0 400 20" />
      </g>
    </svg>
  );
}

/* ─── Node Network — connected circles (for analytics/data pages) ─ */
export function NodeNetwork({ className = '' }) {
  const nodes = [
    { x: 60, y: 40, r: 5 }, { x: 180, y: 60, r: 4 }, { x: 300, y: 30, r: 6 },
    { x: 420, y: 70, r: 4 }, { x: 540, y: 45, r: 5 }, { x: 120, y: 110, r: 3 },
    { x: 240, y: 130, r: 5 }, { x: 360, y: 100, r: 4 }, { x: 480, y: 120, r: 3 },
    { x: 90, y: 170, r: 4 }, { x: 210, y: 190, r: 3 }, { x: 330, y: 160, r: 5 },
    { x: 450, y: 180, r: 4 }, { x: 570, y: 150, r: 3 },
  ];
  const edges = [
    [0,1],[1,2],[2,3],[3,4],[0,5],[1,6],[2,7],[3,8],[5,6],[6,7],[7,8],
    [5,9],[6,10],[7,11],[8,12],[9,10],[10,11],[11,12],[12,13],[4,13],
  ];
  return (
    <svg className={className} viewBox="0 0 600 220" fill="none" xmlns="http://www.w3.org/2000/svg" aria-hidden="true" preserveAspectRatio="xMidYMid slice">
      <g opacity="0.08">
        {edges.map(([a,b], i) => (
          <line key={i} x1={nodes[a].x} y1={nodes[a].y} x2={nodes[b].x} y2={nodes[b].y}
            stroke="currentColor" strokeWidth="1" />
        ))}
        {nodes.map((n, i) => (
          <circle key={i} cx={n.x} cy={n.y} r={n.r} fill="currentColor" opacity="0.5" />
        ))}
      </g>
    </svg>
  );
}

/* ─── Isometric Grid — 3D tiled pattern ──────────────────── */
export function IsometricGrid({ className = '' }) {
  const pid = useId();
  return (
    <svg className={className} width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <pattern id={`iso-${pid}`} width="60" height="52" patternUnits="userSpaceOnUse">
          <path d="M30 0L60 17.3V34.6L30 52 0 34.6V17.3z" fill="none" stroke="currentColor" strokeWidth="0.6" opacity="0.07" />
          <path d="M30 0v52M0 17.3L60 17.3M0 34.6L60 34.6" stroke="currentColor" strokeWidth="0.3" opacity="0.04" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#iso-${pid})`} />
    </svg>
  );
}

/* ─── Blueprint Grid — precise engineering grid ──────────── */
export function BlueprintGrid({ className = '' }) {
  const pid = useId();
  return (
    <svg className={className} width="100%" height="100%" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <defs>
        <pattern id={`bp-${pid}`} width="40" height="40" patternUnits="userSpaceOnUse">
          <path d="M40 0H0v40" fill="none" stroke="currentColor" strokeWidth="0.5" opacity="0.06" />
          <path d="M20 0v40M0 20h40" fill="none" stroke="currentColor" strokeWidth="0.25" opacity="0.03" />
        </pattern>
        <pattern id={`bpl-${pid}`} width="200" height="200" patternUnits="userSpaceOnUse">
          <rect width="200" height="200" fill={`url(#bp-${pid})`} />
          <path d="M200 0H0v200" fill="none" stroke="currentColor" strokeWidth="1" opacity="0.08" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#bpl-${pid})`} />
    </svg>
  );
}

/* ─── Gradient Mesh Orbs (top-right + bottom-left visible color washes) ── */
export function GradientMesh({ className = '', colorA = '#2563EB', colorB = '#0D9488' }) {
  return (
    <div className={`pointer-events-none ${className}`} aria-hidden="true">
      <div className="absolute -top-40 -right-40 w-[500px] h-[500px] rounded-full opacity-[0.07]"
        style={{ background: `radial-gradient(circle, ${colorA} 0%, transparent 70%)` }} />
      <div className="absolute -bottom-40 -left-40 w-[400px] h-[400px] rounded-full opacity-[0.05]"
        style={{ background: `radial-gradient(circle, ${colorB} 0%, transparent 70%)` }} />
      <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] rounded-full opacity-[0.03]"
        style={{ background: `radial-gradient(circle, ${colorA} 0%, transparent 70%)` }} />
    </div>
  );
}

/* ─── Section Header Accent Line ─────────────────────────── */
export function SectionAccent({ className = '' }) {
  return (
    <div className={`flex items-center gap-3 ${className}`} aria-hidden="true">
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-blue-300/30 to-transparent" />
      <div className="flex gap-1.5">
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500/40" />
        <div className="w-1.5 h-1.5 rounded-full bg-teal-500/40" />
        <div className="w-1.5 h-1.5 rounded-full bg-blue-500/40" />
      </div>
      <div className="h-px flex-1 bg-gradient-to-r from-transparent via-teal-300/30 to-transparent" />
    </div>
  );
}

/* ─── Glowing Orb (for hero) ──────────────────── */
export function GlowOrb({ className = '', color = '#2563EB' }) {
  return (
    <div className={className} aria-hidden="true"
      style={{
        background: `radial-gradient(circle, ${color}30 0%, ${color}10 40%, transparent 70%)`,
        filter: 'blur(60px)',
        borderRadius: '50%',
      }}
    />
  );
}

/* ─── Animated Pulse Ring ─────────────────────────────────── */
export function PulseRing({ className = '', color = '#2563EB' }) {
  return (
    <svg className={className} viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <circle cx="50" cy="50" r="20" fill="none" stroke={color} strokeWidth="0.5" opacity="0.3">
        <animate attributeName="r" from="20" to="45" dur="3s" repeatCount="indefinite" />
        <animate attributeName="opacity" from="0.3" to="0" dur="3s" repeatCount="indefinite" />
      </circle>
      <circle cx="50" cy="50" r="20" fill="none" stroke={color} strokeWidth="0.5" opacity="0.3">
        <animate attributeName="r" from="20" to="45" dur="3s" begin="1s" repeatCount="indefinite" />
        <animate attributeName="opacity" from="0.3" to="0" dur="3s" begin="1s" repeatCount="indefinite" />
      </circle>
      <circle cx="50" cy="50" r="20" fill="none" stroke={color} strokeWidth="0.5" opacity="0.3">
        <animate attributeName="r" from="20" to="45" dur="3s" begin="2s" repeatCount="indefinite" />
        <animate attributeName="opacity" from="0.3" to="0" dur="3s" begin="2s" repeatCount="indefinite" />
      </circle>
      <circle cx="50" cy="50" r="4" fill={color} opacity="0.2" />
    </svg>
  );
}

/* ─── Wave Section Divider ────────────────────────────────── */
export function WaveDivider({ className = '', flip = false }) {
  return (
    <svg className={className} viewBox="0 0 1440 80" preserveAspectRatio="none" xmlns="http://www.w3.org/2000/svg"
      aria-hidden="true" style={flip ? { transform: 'rotate(180deg)' } : undefined}>
      <path d="M0 40C240 80 480 0 720 40s480 40 720 0v40H0z" fill="currentColor" opacity="0.04" />
      <path d="M0 50C360 80 600 20 900 50s420 20 540 0v30H0z" fill="currentColor" opacity="0.03" />
    </svg>
  );
}

/* ─── Animated Data Particles (floating dots) ─────────────── */
export function DataParticles({ className = '' }) {
  return (
    <svg className={className} viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      {[
        { cx: 30, cy: 40, r: 2, dur: '7s', dx: 15, dy: -20 },
        { cx: 80, cy: 120, r: 1.5, dur: '9s', dx: -10, dy: 25 },
        { cx: 150, cy: 60, r: 2.5, dur: '6s', dx: 20, dy: 15 },
        { cx: 170, cy: 150, r: 1.8, dur: '8s', dx: -15, dy: -20 },
        { cx: 50, cy: 170, r: 2, dur: '10s', dx: 25, dy: -10 },
        { cx: 120, cy: 30, r: 1.5, dur: '7.5s', dx: -20, dy: 20 },
      ].map((p, i) => (
        <circle key={i} cx={p.cx} cy={p.cy} r={p.r} fill="currentColor" opacity="0.15">
          <animate attributeName="cx" values={`${p.cx};${p.cx + p.dx};${p.cx}`} dur={p.dur} repeatCount="indefinite" />
          <animate attributeName="cy" values={`${p.cy};${p.cy + p.dy};${p.cy}`} dur={p.dur} repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.15;0.3;0.15" dur={p.dur} repeatCount="indefinite" />
        </circle>
      ))}
      <g stroke="currentColor" strokeWidth="0.3" opacity="0.06">
        <line x1="30" y1="40" x2="80" y2="120" />
        <line x1="80" y1="120" x2="150" y2="60" />
        <line x1="150" y1="60" x2="170" y2="150" />
        <line x1="120" y1="30" x2="50" y2="170" />
      </g>
    </svg>
  );
}

/* ─── Page Background Shell — wraps a page with visible pattern + gradient orbs ─ */
export function PageBg({ children, pattern = 'topography', colorA = '#2563EB', colorB = '#0D9488' }) {
  const patterns = {
    topography: TopographyBg,
    circuit: CircuitTrace,
    hex: HexGrid,
    nodes: NodeNetwork,
    isometric: IsometricGrid,
    blueprint: BlueprintGrid,
  };
  const Pattern = patterns[pattern] || TopographyBg;

  return (
    <div className="relative min-h-screen">
      {/* Fixed gradient orbs */}
      <div className="fixed inset-0 pointer-events-none -z-20" aria-hidden="true">
        <div className="absolute -top-40 -right-40 w-[600px] h-[600px] rounded-full opacity-[0.10]"
          style={{ background: `radial-gradient(circle, ${colorA} 0%, transparent 70%)` }} />
        <div className="absolute -bottom-40 -left-40 w-[500px] h-[500px] rounded-full opacity-[0.08]"
          style={{ background: `radial-gradient(circle, ${colorB} 0%, transparent 70%)` }} />
        <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-[400px] h-[400px] rounded-full opacity-[0.05]"
          style={{ background: `radial-gradient(circle, ${colorA} 0%, transparent 60%)` }} />
      </div>
      {/* Fixed SVG pattern */}
      <Pattern className="fixed inset-0 pointer-events-none -z-10 text-slate-400" />
      {/* Gentle gradient wash — not too white, allows pattern to show */}
      <div className="fixed inset-0 pointer-events-none -z-10 bg-gradient-to-b from-white/60 via-transparent to-white/40" aria-hidden="true" />
      {children}
    </div>
  );
}

/* ─── Page Header Block — gradient accent bar + title ─────── */
export function PageHeader({ icon: Icon, title, subtitle, accentColor = 'blue' }) {
  const colorMap = {
    blue: 'from-blue-500 to-blue-600',
    teal: 'from-teal-500 to-teal-600',
    rose: 'from-rose-500 to-rose-600',
    amber: 'from-amber-500 to-amber-600',
    violet: 'from-violet-500 to-violet-600',
    emerald: 'from-emerald-500 to-emerald-600',
  };
  const glowMap = {
    blue: 'shadow-blue-200/50',
    teal: 'shadow-teal-200/50',
    rose: 'shadow-rose-200/50',
    amber: 'shadow-amber-200/50',
    violet: 'shadow-violet-200/50',
    emerald: 'shadow-emerald-200/50',
  };

  return (
    <div className="mb-8 sm:mb-10">
      <div className="flex items-center gap-4">
        {Icon && (
          <div className={`w-12 h-12 rounded-xl bg-gradient-to-br ${colorMap[accentColor]} flex items-center justify-center shadow-lg ${glowMap[accentColor]} flex-shrink-0`}>
            <Icon className="w-6 h-6 text-white" />
          </div>
        )}
        <div>
          <h1 className="font-display text-2xl sm:text-3xl font-bold text-gray-900 tracking-tight">{title}</h1>
          {subtitle && <p className="text-gray-500 text-sm mt-1">{subtitle}</p>}
        </div>
      </div>
      <SectionAccent className="mt-4" />
    </div>
  );
}

/* Keep old names exported for backwards compat (Landing, Footer still use them) */
export function DotGrid({ className }) {
  return <TopographyBg className={className} />;
}
export function CornerAccent({ className }) {
  return null; /* Replaced by PageBg / PageHeader system — no-render gracefully */
}
export function CardTechCorner({ className }) {
  return null;
}
export function DiagonalLines({ className }) {
  return <IsometricGrid className={className} />;
}
export function CardGlowBorder({ className }) {
  return null;
}
