/**
 * TrustPipeline — animated SVG showing the donation-to-verification cycle.
 * 6 nodes: Donate → Record → Transfer → Verify → Impact → Receipt
 * Cubic-Bézier connections, animated travelling dot, CSS-only animation.
 */
import { useEffect, useRef, useState } from 'react';

const NODES = [
  { label: 'Donate',   sub: 'Voice or card',        color: '#818CF8' },
  { label: 'Record',   sub: 'Blockchain ledger',     color: '#A78BFA' },
  { label: 'Transfer', sub: 'Funds dispatched',      color: '#C084FC' },
  { label: 'Verify',   sub: 'Field agent proof',     color: '#E879F9' },
  { label: 'Impact',   sub: 'Transparent report',    color: '#A78BFA' },
  { label: 'Receipt',  sub: 'NFT tax receipt',       color: '#818CF8' },
];

/* Mini SVG icons for each node */
const nodeIcons = [
  /* Donate — heart */
  <path key="ic0" d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z" />,
  /* Record — chain link */
  <path key="ic1" d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71" />,
  /* Transfer — send arrow */
  <path key="ic2" d="M5 12h14M19 12l-6-6M19 12l-6 6" />,
  /* Verify — shield check */
  <><path key="ic3a" d="M9 12.75L11.25 15 15 9.75" /><path key="ic3b" d="M12 2.714A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.75c0 5.592 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751A11.959 11.959 0 0012 2.714z" /></>,
  /* Impact — chart rising */
  <path key="ic4" d="M3 20h18M5 20V10M9 20V4M13 20v-8M17 20V7M21 20v-5" />,
  /* Receipt — document */
  <path key="ic5" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z" />,
];

export default function TrustPipeline() {
  const ref = useRef(null);
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (!ref.current) return;
    const io = new IntersectionObserver(
      ([e]) => { if (e.isIntersecting) { setVisible(true); io.disconnect(); } },
      { threshold: 0.25 },
    );
    io.observe(ref.current);
    return () => io.disconnect();
  }, []);

  /* Layout constants */
  const W = 900, H = 200;
  const padX = 75, padY = 80;
  const gap = (W - 2 * padX) / (NODES.length - 1);

  /* Build cubic-bézier path connecting all node centres */
  const pts = NODES.map((_, i) => ({ x: padX + i * gap, y: padY }));
  let pathD = `M${pts[0].x},${pts[0].y}`;
  for (let i = 0; i < pts.length - 1; i++) {
    const cpOff = gap * 0.4;
    pathD += ` C${pts[i].x + cpOff},${pts[i].y} ${pts[i + 1].x - cpOff},${pts[i + 1].y} ${pts[i + 1].x},${pts[i + 1].y}`;
  }

  return (
    <section ref={ref} className="relative py-20 overflow-hidden bg-indigo-950">
      {/* subtle grid background */}
      <div className="absolute inset-0 opacity-[0.04]"
        style={{ backgroundImage: 'linear-gradient(rgba(255,255,255,.5) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,.5) 1px, transparent 1px)', backgroundSize: '40px 40px' }} />

      <div className="max-w-5xl mx-auto px-4">
        <p className="text-center text-xs font-semibold tracking-[0.2em] uppercase text-violet-400 mb-2 font-display">
          How It Works
        </p>
        <h2 className="section-heading text-3xl md:text-4xl text-center text-white mb-12">
          The <span className="text-gradient-animated">Trust Pipeline</span>
        </h2>

        {/* Pipeline SVG */}
        <div className="overflow-x-auto scrollbar-hide -mx-4 px-4">
          <svg viewBox={`0 0 ${W} ${H + 65}`} className="mx-auto w-full min-w-[650px]" style={{ maxWidth: W }}>
            <defs>
              {/* glow filter */}
              <filter id="glow">
                <feGaussianBlur stdDeviation="3" result="b" />
                <feMerge><feMergeNode in="b" /><feMergeNode in="SourceGraphic" /></feMerge>
              </filter>
              {/* gradient for the path */}
              <linearGradient id="pipeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
                <stop offset="0%" stopColor="#6366F1" />
                <stop offset="50%" stopColor="#A855F7" />
                <stop offset="100%" stopColor="#6366F1" />
              </linearGradient>
            </defs>

            {/* Connection path — background track */}
            <path d={pathD} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth="2" strokeLinecap="round" />

            {/* Connection path — animated glow */}
            <path d={pathD} fill="none" stroke="url(#pipeGrad)" strokeWidth="2"
              strokeDasharray="8 6" strokeLinecap="round" filter="url(#glow)"
              className={visible ? 'animate-dash' : ''} style={{ opacity: visible ? 1 : 0 }} />

            {/* Travelling dot */}
            {visible && (
              <circle r="5" fill="#8B5CF6" filter="url(#glow)">
                <animateMotion dur="4s" repeatCount="indefinite" path={pathD} />
              </circle>
            )}

            {/* Nodes */}
            {NODES.map((n, i) => {
              const x = pts[i].x, y = pts[i].y;
              const delay = `${i * 0.15}s`;
              return (
                <g key={i} className={visible ? 'animate-nodeIn' : 'opacity-0'}
                  style={{ animationDelay: delay }}>
                  {/* outer ring */}
                  <circle cx={x} cy={y} r="28" fill="rgba(255,255,255,0.03)"
                    stroke={n.color} strokeWidth="1.5" opacity="0.6" />
                  {/* inner filled circle */}
                  <circle cx={x} cy={y} r="20" fill={n.color} opacity="0.15" />
                  {/* icon */}
                  <svg x={x - 10} y={y - 10} width="20" height="20" viewBox="0 0 24 24"
                    fill="none" stroke={n.color} strokeWidth="1.75"
                    strokeLinecap="round" strokeLinejoin="round">
                    {nodeIcons[i]}
                  </svg>
                  {/* label */}
                  <text x={x} y={y + 46} textAnchor="middle"
                    className="fill-white text-[13px] font-display font-semibold">{n.label}</text>
                  <text x={x} y={y + 61} textAnchor="middle"
                    className="fill-violet-300 text-[10px]">{n.sub}</text>
                </g>
              );
            })}
          </svg>
        </div>
      </div>

      {/* CSS — scoped via class names */}
      <style>{`
        @keyframes dashMove { to { stroke-dashoffset: -56; } }
        .animate-dash { animation: dashMove 2s linear infinite; }
        @keyframes nodeIn {
          from { opacity: 0; transform: translateY(12px) scale(0.85); }
          to   { opacity: 1; transform: translateY(0) scale(1); }
        }
        .animate-nodeIn { animation: nodeIn 0.5s ease-out both; }
      `}</style>
    </section>
  );
}
