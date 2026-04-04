/**
 * MoringaOasisInvestor -- cinematic 3D investor experience.
 *
 * Post-processing (bloom, SSAO, vignette, tone-mapping), animated wind,
 * water ripples, dust particles, contact shadows, rolling terrain, and
 * procedural material details on all structures.
 */
import {
  Suspense, useRef, useState, useCallback, useMemo, useEffect,
} from 'react';
import { Canvas, useFrame, useThree } from '@react-three/fiber';
import {
  OrbitControls, Html, useTexture,
} from '@react-three/drei';
import {
  EffectComposer, Vignette, ToneMapping,
} from '@react-three/postprocessing';
import { ToneMappingMode } from 'postprocessing';
import { createNoise2D } from 'simplex-noise';
import * as THREE from 'three';
import { Link } from 'react-router-dom';

/* ── CDN ── */
const R2 = 'https://pub-d7d5ddc508cf4600aa65de6f72991926.r2.dev/oasis';

/* ── Palette ── */
const EMERALD = '#059669';
const AMBER   = '#D97706';

function createSeededRandom(seed) {
  let t = seed >>> 0;
  return () => {
    t += 0x6D2B79F5;
    let v = Math.imul(t ^ (t >>> 15), 1 | t);
    v ^= v + Math.imul(v ^ (v >>> 7), 61 | v);
    return ((v ^ (v >>> 14)) >>> 0) / 4294967296;
  };
}

/* ━━━━━━━  INVESTMENT DATA  ━━━━━━━ */
const HOTSPOTS = [
  { id: 'farm', label: 'Moringa Plantation', position: [-10, 1.5, 6], milestone: 1, budget: '$110,000', detail: '10-hectare high-density Moringa oleifera plantation with solar-powered drip irrigation, borehole, and fencing. 12,000+ trees producing year-round leaf harvests.', status: 'Active', color: EMERALD, icon: 'leaf' },
  { id: 'plant', label: 'Processing Plant', position: [0, 3.5, -2], milestone: 2, budget: '$50,000', detail: 'Industrial-grade dehydrators, hammer mill, cold-press oil expeller, capsule filler, and packaging line. Transforms raw leaf into export-ready powder, oil, capsules, and tea.', status: 'Funded', color: '#2563EB', icon: 'factory' },
  { id: 'shop', label: 'Farm Shop & Visitor Center', position: [10, 2, 6], milestone: 2, budget: '$15,000', detail: 'On-site retail store selling Moringa products direct to visitors. Tasting bar, product education, and branded packaging. Gateway to the eco-tourism experience.', status: 'Planned', color: AMBER, icon: 'shop' },
  { id: 'lodge', label: 'Eco-Lodge Village', position: [16, 2, -8], milestone: 3, budget: '$180,000', detail: '6 solar-powered cottages for investors, volunteers, and eco-tourists. The "Live-Work-Learn" experience, driving recurring revenue and community engagement.', status: 'Planned', color: EMERALD, icon: 'lodge' },
  { id: 'ops', label: 'Certification & Market Access', position: [-2, 2.5, -16], milestone: 4, budget: '$45,000', detail: 'EU Organic, HACCP food safety, and Fair Trade certification. Opens access to premium European, UK, and Middle-Eastern distribution channels.', status: 'Planned', color: '#7C3AED', icon: 'shield' },
];

const UNIT_ECONOMICS = {
  treeDensityPerHa: 1000,
  yieldPerTreeFreshKg: 16,
  conversionFreshToPowderKg: 7,
  powderPerTreeKg: 2.3,
  hybridPriceEurPerKg: 20,
  revenuePerTreeEur: 46,
  revenuePerHaEur: 46000,
  fullCapacityHa: 15,
  fullCapacityPowderKg: 34286,
  fullCapacityPowderRevenueEur: 685720,
};

const REVENUE_STACK = {
  powderEur: 685720,
  oilRangeEur: [70000, 100000],
  lodgingRangeEur: [120000, 150000],
  retailRangeEur: [60000, 100000],
  experiencesRangeEur: [25000, 40000],
  totalRangeEur: [960000, 1050000],
  ebitdaRangeEur: [400000, 450000],
};

const YEAR_PROJECTION = [
  { year: 1, ha: 10, revenue: 400000, costs: 280000, ebitda: 120000 },
  { year: 2, ha: 10, revenue: 650000, costs: 390000, ebitda: 260000 },
  { year: 3, ha: 15, revenue: 1000000, costs: 580000, ebitda: 420000 },
  { year: 4, ha: 15, revenue: 1100000, costs: 600000, ebitda: 500000 },
  { year: 5, ha: 15, revenue: 1200000, costs: 650000, ebitda: 550000 },
  { year: 6, ha: 15, revenue: 1300000, costs: 700000, ebitda: 600000 },
  { year: 7, ha: 15, revenue: 1400000, costs: 750000, ebitda: 650000 },
];

const PHASE_ECONOMICS = {
  1: {
    label: 'Base Agriculture',
    ha: 10,
    revenueFloor: 400000,
    ebitdaFloor: 120000,
    focus: 'Cultivation + irrigation + baseline harvest',
  },
  2: {
    label: 'Processing & Retail Activation',
    ha: 10,
    revenueFloor: 650000,
    ebitdaFloor: 260000,
    focus: 'Plant throughput + on-site shop + product mix uplift',
  },
  3: {
    label: 'Eco-Lodge Live-Work-Learn',
    ha: 15,
    revenueFloor: 1000000,
    ebitdaFloor: 420000,
    focus: 'Hospitality + experiences + full farm utilization',
  },
  4: {
    label: 'Certification & Market Access',
    ha: 15,
    revenueFloor: 1100000,
    ebitdaFloor: 500000,
    focus: 'Export readiness + distributor scale + pricing power',
  },
};

const MODE_OPTIONS = [
  { id: 'visual', label: 'Visual' },
  { id: 'investor', label: 'Business' },
  { id: 'proof', label: 'Proof' },
];

const PROOF_ARTIFACTS = {
  1: [
    { item: 'Unit economics and business model finalized', budget: 110000, spent: 0, progress: 100, proof: 'documentation/business/MORINGA_VERTICAL_INTEGRATION.md' },
    { item: 'Site masterplan and irrigation concept drafted', budget: 28000, spent: 0, progress: 65, proof: 'web-frontend/src/projects/MoringaOasisInvestor.jsx' },
  ],
  2: [
    { item: 'Processing line specification and layout design', budget: 50000, spent: 0, progress: 35, proof: 'documentation/TRANSPARENCY_TAX_RECEIPTS_DESIGN.md' },
    { item: 'Farm shop concept, SKU and visitor flow design', budget: 15000, spent: 0, progress: 42, proof: 'documentation/business/MORINGA_VERTICAL_INTEGRATION.md' },
  ],
  3: [
    { item: 'Eco-lodge architectural concept and phasing', budget: 180000, spent: 0, progress: 28, proof: 'documentation/business/MORINGA_VERTICAL_INTEGRATION.md' },
    { item: 'Live-Work-Learn program framework', budget: 20000, spent: 0, progress: 33, proof: 'documentation/business/MORINGA_VERTICAL_INTEGRATION.md' },
  ],
  4: [
    { item: 'HACCP + organic certification preparation', budget: 45000, spent: 0, progress: 22, proof: 'documentation/TRANSPARENCY_AND_TAX_RECEIPTS_OVERVIEW.md' },
    { item: 'Export onboarding and dispatch SOP draft', budget: 15000, spent: 0, progress: 20, proof: 'documentation/business/MORINGA_VERTICAL_INTEGRATION.md' },
  ],
};

const CURRENT_PROJECT_STATE = {
  lifecycle: 'Pre-Live (Design and Fundraising)',
  asOf: '2026-04-04',
  irrigationUptime: 0,
  baselineHarvestTons: 0,
  processingQA: 0,
  packagingReady: false,
  certificationReady: false,
  distributorLOIs: 0,
  designReadiness: 0.68,
  fundingReadiness: 0.42,
};

function formatEur(value) {
  return `EUR ${Math.round(value / 1000)}K`;
}

function SiteIcon({ name, className = 'w-4 h-4', stroke = 'currentColor' }) {
  const common = { className, fill: 'none', stroke, strokeWidth: 1.8, strokeLinecap: 'round', strokeLinejoin: 'round', viewBox: '0 0 24 24' };
  if (name === 'leaf') {
    return <svg {...common}><path d="M6 18c6 0 10-4 12-10-6 0-10 4-12 10Z" /><path d="M9 15c2-2 4-3 7-4" /></svg>;
  }
  if (name === 'factory') {
    return <svg {...common}><path d="M3 21h18" /><path d="M4 21V9l5 3V9l5 3V6h6v15" /></svg>;
  }
  if (name === 'shop') {
    return <svg {...common}><path d="M3 9h18" /><path d="M5 9l1-4h12l1 4" /><path d="M5 9v10h14V9" /><path d="M9 19v-5h6v5" /></svg>;
  }
  if (name === 'lodge') {
    return <svg {...common}><path d="M3 11l9-7 9 7" /><path d="M5 10v10h14V10" /><path d="M10 20v-6h4v6" /></svg>;
  }
  return <svg {...common}><path d="M12 3l7 3v6c0 5-3 8-7 9-4-1-7-4-7-9V6l7-3Z" /><path d="M9 12l2 2 4-4" /></svg>;
}

function AgronomyLayout({ showDetail = false }) {
  return (
    <group>
      {/* Nursery + transplant blocks */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-15, 0.06, 9]}>
        <planeGeometry args={[8, 4]} />
        <meshStandardMaterial color="#6B8E23" roughness={0.9} metalness={0} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[-15, 0.065, 4]}>
        <planeGeometry args={[8, 4]} />
        <meshStandardMaterial color="#556B2F" roughness={0.9} metalness={0} />
      </mesh>

      {/* Irrigation sectors */}
      {[[-7, 0], [7, 0], [-7, -9], [7, -9]].map(([x, z], idx) => (
        <mesh key={`sector-${idx}`} rotation={[-Math.PI / 2, 0, 0]} position={[x, 0.045, z]}>
          <planeGeometry args={[13, 8]} />
          <meshBasicMaterial color={idx % 2 ? '#2E5F50' : '#39695A'} transparent opacity={0.08} />
        </mesh>
      ))}

      {/* Harvest lanes */}
      {Array.from({ length: 8 }).map((_, i) => (
        <mesh key={`lane-${i}`} rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.07, -10 + i * 2.3]}>
          <planeGeometry args={[44, 0.12]} />
          <meshBasicMaterial color="#A67C52" transparent opacity={0.35} />
        </mesh>
      ))}

      {showDetail && (
        <Html position={[-15, 0.5, 11]} center distanceFactor={14} style={{ pointerEvents: 'none' }}>
          <div className="bg-black/85 border border-white/30 rounded-md px-2.5 py-1.5 text-[11px] text-white/95 shadow-xl whitespace-nowrap">
            Nursery + Transplant Blocks
          </div>
        </Html>
      )}
    </group>
  );
}

function LiveWorkLearnRoute({ visible = false }) {
  if (!visible) return null;
  const waypoints = [
    [0, 0.09, 22],
    [-8, 0.09, 6],
    [0, 0.09, -2],
    [10, 0.09, 6],
    [16, 0.09, -10],
  ];
  return (
    <group>
      {waypoints.slice(0, -1).map((a, i) => {
        const b = waypoints[i + 1];
        const dx = b[0] - a[0];
        const dz = b[2] - a[2];
        const len = Math.sqrt(dx * dx + dz * dz);
        return (
          <mesh key={`route-${i}`} position={[(a[0] + b[0]) / 2, 0.09, (a[2] + b[2]) / 2]} rotation={[-Math.PI / 2, 0, -Math.atan2(dx, dz)]}>
            <planeGeometry args={[0.35, len]} />
            <meshBasicMaterial color="#22D3EE" transparent opacity={0.45} />
          </mesh>
        );
      })}
      {waypoints.map((p, i) => (
        <mesh key={`wp-${i}`} position={[p[0], 0.11, p[2]]} rotation={[-Math.PI / 2, 0, 0]}>
          <circleGeometry args={[0.25, 20]} />
          <meshBasicMaterial color="#06B6D4" />
        </mesh>
      ))}
      <Html position={[6, 0.8, 12]} center distanceFactor={15} style={{ pointerEvents: 'none' }}>
        <div className="bg-cyan-950/85 border border-cyan-400/45 rounded-md px-2.5 py-1.5 text-[11px] text-cyan-100 shadow-xl whitespace-nowrap">
          Live-Work-Learn Journey Route
        </div>
      </Html>
    </group>
  );
}

function ZoneKPIAnchors({ mode, phase }) {
  if (mode === 'visual') return null;
  const items = [
    { pos: [-9, 1.6, 5], label: 'Plantation', text: '15k trees @ full scale | 2.3kg powder/tree' },
    { pos: [0, 4.5, -2], label: 'Processing', text: 'Line flow: wash > dry > mill/press > pack' },
    { pos: [10, 2.8, 7], label: 'Shop', text: 'SKUs: powder, oil, tea, capsules, bundles' },
    { pos: [16, 3.2, -9], label: 'Eco-Lodge', text: '6 lodges | ADR EUR 140 | 40-50% occupancy' },
  ];

  return (
    <group>
      {items.map((it, i) => (
        <Html key={i} position={it.pos} center distanceFactor={14} style={{ pointerEvents: 'none' }}>
          <div className="bg-black/88 border border-white/28 rounded-md px-2.5 py-1.5 text-[11px] text-white/95 shadow-xl max-w-[260px] leading-snug">
            <span className="text-white/95 font-semibold">{it.label}:</span> {it.text}
          </div>
        </Html>
      ))}
      {phase >= 4 && (
        <Html position={[-2, 3, -16]} center distanceFactor={14} style={{ pointerEvents: 'none' }}>
          <div className="bg-violet-950/85 border border-violet-400/40 rounded-md px-2.5 py-1.5 text-[11px] text-violet-100 shadow-xl max-w-[280px] leading-snug">
            Export Readiness: HACCP + Organic + Dispatch SOP
          </div>
        </Html>
      )}
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  FLOATING DUST PARTICLES
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function DustParticles({ count = 200 }) {
  const mesh = useRef();
  const { positions, speeds } = useMemo(() => {
    const p = new Float32Array(count * 3);
    const s = new Float32Array(count);
    for (let i = 0; i < count; i++) {
      p[i * 3]     = (Math.random() - 0.5) * 60;
      p[i * 3 + 1] = 0.5 + Math.random() * 12;
      p[i * 3 + 2] = (Math.random() - 0.5) * 60;
      s[i] = 0.2 + Math.random() * 0.6;
    }
    return { positions: p, speeds: s };
  }, [count]);

  useFrame(({ clock }) => {
    if (!mesh.current) return;
    const t = clock.getElapsedTime();
    const pos = mesh.current.geometry.attributes.position.array;
    for (let i = 0; i < count; i++) {
      pos[i * 3]     += Math.sin(t * 0.3 + i) * 0.003 * speeds[i];
      pos[i * 3 + 1] += Math.sin(t * 0.5 + i * 2) * 0.002;
      pos[i * 3 + 2] += Math.cos(t * 0.2 + i) * 0.003 * speeds[i];
      // wrap
      if (pos[i * 3] > 30) pos[i * 3] = -30;
      if (pos[i * 3] < -30) pos[i * 3] = 30;
      if (pos[i * 3 + 2] > 30) pos[i * 3 + 2] = -30;
      if (pos[i * 3 + 2] < -30) pos[i * 3 + 2] = 30;
    }
    mesh.current.geometry.attributes.position.needsUpdate = true;
  });

  return (
    <points ref={mesh}>
      <bufferGeometry>
        <bufferAttribute attach="attributes-position" count={count} array={positions} itemSize={3} />
      </bufferGeometry>
      <pointsMaterial size={0.06} color="#E8D8C0" transparent opacity={0.35} sizeAttenuation depthWrite={false} />
    </points>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  TERRAIN WITH HEIGHT VARIATION
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function Terrain() {
  const farmTex  = useTexture(`${R2}/Oasis1.jpeg`);
  const outerTex = useTexture(`${R2}/FarmNew1.jpeg`);
  const noise2D = useMemo(() => createNoise2D(createSeededRandom(20260404)), []);

  useMemo(() => {
    [farmTex, outerTex].forEach((t) => {
      t.colorSpace = THREE.SRGBColorSpace;
      t.wrapS = t.wrapT = THREE.ClampToEdgeWrapping;
    });
    outerTex.wrapS = outerTex.wrapT = THREE.MirroredRepeatWrapping;
    outerTex.repeat.set(3, 3);
  }, [farmTex, outerTex]);

  // Create displaced outer terrain geometry
  const outerGeo = useMemo(() => {
    const geo = new THREE.PlaneGeometry(140, 140, 64, 64);
    const pos = geo.attributes.position.array;
    for (let i = 0; i < pos.length; i += 3) {
      const x = pos[i], y = pos[i + 1];
      const dist = Math.sqrt(x * x + y * y);
      // gentle rolling outside the farm area
      if (dist > 22) {
        const ridge = noise2D(x * 0.035, y * 0.035) * 2.4;
        const detail = noise2D(x * 0.09 + 13, y * 0.09 - 7) * 0.8;
        pos[i + 2] = (ridge + detail) * Math.min((dist - 22) / 20, 1);
      }
    }
    geo.computeVertexNormals();
    return geo;
  }, [noise2D]);

  return (
    <group>
      {/* Main farm area -- photo texture, flat */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0, 0]} receiveShadow>
        <planeGeometry args={[48, 40, 1, 1]} />
        <meshStandardMaterial map={farmTex} roughness={1} metalness={0} envMapIntensity={0} />
      </mesh>

      {/* Open-source detail overlay */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.015, 0]}>
        <planeGeometry args={[48, 40, 1, 1]} />
        <meshStandardMaterial map={outerTex} color="#8A7A5A" roughness={1} metalness={0} transparent opacity={0.1} depthWrite={false} />
      </mesh>

      {/* Outer rolling terrain */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.1, 0]} receiveShadow geometry={outerGeo}>
        <meshStandardMaterial map={outerTex} roughness={1} metalness={0} envMapIntensity={0} color="#B8A080" />
      </mesh>

      {/* Safety floor -- prevents sky showing through any gaps */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.5, 0]}>
        <planeGeometry args={[300, 300]} />
        <meshBasicMaterial color="#5A6B45" />
      </mesh>

      {/* Roads */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 28]}>
        <planeGeometry args={[3.5, 20]} />
        <meshStandardMaterial color="#A89070" roughness={1} metalness={0} envMapIntensity={0} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, 0.05, 8]}>
        <planeGeometry args={[32, 2.5]} />
        <meshStandardMaterial color="#9A8565" roughness={1} metalness={0} envMapIntensity={0} />
      </mesh>
      <mesh rotation={[-Math.PI / 2, 0, Math.PI * 0.18]} position={[10, 0.05, 0]}>
        <planeGeometry args={[1.8, 18]} />
        <meshStandardMaterial color="#A89070" roughness={1} metalness={0} envMapIntensity={0} />
      </mesh>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  PHOTO PANORAMA BACKDROP
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function Panoramas() {
  const t2 = useTexture(`${R2}/Oasis2.jpeg`);
  const t3 = useTexture(`${R2}/Oasis3.jpeg`);
  const t4 = useTexture(`${R2}/Oasis4.jpeg`);
  const t5 = useTexture(`${R2}/Oasis5.jpeg`);
  const t6 = useTexture(`${R2}/Oasis6.jpeg`);
  useMemo(() => { [t2, t3, t4, t5, t6].forEach((t) => { t.colorSpace = THREE.SRGBColorSpace; }); }, [t2, t3, t4, t5, t6]);

  const panels = [
    { t: t2, pos: [0, 7, -55], rot: [0, 0, 0], w: 80 },
    { t: t3, pos: [55, 7, 0], rot: [0, -Math.PI / 2, 0], w: 80 },
    { t: t4, pos: [-55, 7, 0], rot: [0, Math.PI / 2, 0], w: 80 },
    { t: t5, pos: [0, 7, 55], rot: [0, Math.PI, 0], w: 80 },
    { t: t6, pos: [40, 7, -40], rot: [0, -Math.PI / 4, 0], w: 50 },
  ];
  return (
    <group>
      {panels.map((p, i) => (
        <mesh key={i} position={p.pos} rotation={p.rot}>
          <planeGeometry args={[p.w, 20]} />
          <meshBasicMaterial map={p.t} transparent opacity={0.45} side={THREE.DoubleSide} depthWrite={false} />
        </mesh>
      ))}
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  MORINGA TREE WITH WIND ANIMATION
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function MoringaTree({ position, height = 4, scale = 1 }) {
  const group = useRef();
  const windOffset = useMemo(() => Math.random() * 100, []);

  const bark = useMemo(() => {
    const c = new THREE.Color('#C8C0B8');
    c.offsetHSL(0, 0, (Math.random() - 0.5) * 0.08);
    return c;
  }, []);

  const canopyColor = useMemo(() => {
    const c = new THREE.Color(Math.random() > 0.4 ? '#4FAE4C' : '#2E7D32');
    c.offsetHSL((Math.random() - 0.5) * 0.05, 0, (Math.random() - 0.5) * 0.1);
    return c;
  }, []);

  const canopyTexture = useMemo(() => {
    const size = 256;
    const canvas = document.createElement('canvas');
    canvas.width = size;
    canvas.height = size;
    const ctx = canvas.getContext('2d');
    if (!ctx) return null;

    ctx.clearRect(0, 0, size, size);
    const cx = size / 2;
    const cy = size / 2;

    for (let i = 0; i < 70; i++) {
      const r = 20 + Math.random() * 52;
      const x = cx + (Math.random() - 0.5) * 90;
      const y = cy + (Math.random() - 0.5) * 90;
      const g = ctx.createRadialGradient(x, y, 0, x, y, r);
      g.addColorStop(0, `rgba(80, ${120 + Math.floor(Math.random() * 80)}, 70, 0.95)`);
      g.addColorStop(1, 'rgba(0,0,0,0)');
      ctx.fillStyle = g;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();
    }

    const tex = new THREE.CanvasTexture(canvas);
    tex.colorSpace = THREE.SRGBColorSpace;
    tex.needsUpdate = true;
    return tex;
  }, []);

  const stems = useMemo(() => {
    const n = 2 + Math.floor(Math.random() * 4);
    return Array.from({ length: n }).map((_, i) => ({
      a: (i / n) * Math.PI * 2 + (Math.random() - 0.5) * 0.6,
      lean: 0.08 + Math.random() * 0.3,
      h: height * (0.6 + Math.random() * 0.4),
      layers: 2 + Math.floor(Math.random() * 3),
    }));
  }, [height]);

  // Wind sway
  useFrame(({ clock }) => {
    if (!group.current) return;
    const t = clock.getElapsedTime();
    group.current.rotation.x = Math.sin(t * 0.8 + windOffset) * 0.02;
    group.current.rotation.z = Math.cos(t * 0.6 + windOffset * 0.7) * 0.015;
  });

  return (
    <group position={position} scale={scale} ref={group}>
      {stems.map((s, i) => (
        <group key={i} rotation={[s.lean * Math.cos(s.a), 0, s.lean * Math.sin(s.a)]}>
          <mesh position={[0, s.h / 2, 0]} castShadow>
            <cylinderGeometry args={[0.025 * scale, 0.08 * scale, s.h, 7]} />
            <meshStandardMaterial color={bark} roughness={0.6} />
          </mesh>
          {Array.from({ length: s.layers }).map((_, j) => {
            const y = s.h * (0.68 + j * 0.1);
            const w = (1 + Math.random() * 0.8) * scale;
            const h = (1.2 + Math.random() * 1.2) * scale;
            return (
              <group key={j} position={[(Math.random() - 0.5) * 0.5, y, (Math.random() - 0.5) * 0.5]}>
                {/* Volumetric leaf mass keeps trees visible from all angles */}
                <mesh castShadow>
                  <sphereGeometry args={[0.45 * scale, 8, 8]} />
                  <meshStandardMaterial color={canopyColor} roughness={0.9} />
                </mesh>
                {[0, Math.PI / 3, -Math.PI / 3].map((ry, idx) => (
                  <mesh key={idx} rotation={[0, ry, 0]} castShadow>
                    <planeGeometry args={[w, h]} />
                    <meshStandardMaterial
                      map={canopyTexture || undefined}
                      alphaMap={canopyTexture || undefined}
                      alphaTest={0.35}
                      color={canopyColor}
                      side={THREE.DoubleSide}
                      roughness={0.95}
                    />
                  </mesh>
                ))}
              </group>
            );
          })}
        </group>
      ))}
    </group>
  );
}

function GroundVegetation() {
  const noise2D = useMemo(() => createNoise2D(createSeededRandom(5150)), []);
  const patches = useMemo(() => {
    const out = [];
    for (let i = 0; i < 280; i++) {
      const x = (Math.random() - 0.5) * 52;
      const z = (Math.random() - 0.5) * 42;
      if (Math.abs(x) < 4.5 && Math.abs(z) < 4.5) continue;
      if (x > 6 && x < 14 && z > 2 && z < 10) continue;
      const d = noise2D(x * 0.18, z * 0.18);
      if (d < 0.05) continue;
      out.push({ x, z, h: 0.18 + Math.random() * 0.25, w: 0.03 + Math.random() * 0.04, c: Math.random() > 0.5 ? '#547D3A' : '#6B8F44' });
    }
    return out;
  }, [noise2D]);

  return (
    <group>
      {patches.map((g, i) => (
        <mesh key={i} position={[g.x, g.h * 0.5, g.z]} rotation={[0, Math.random() * Math.PI, 0]}>
          <coneGeometry args={[g.w, g.h, 4]} />
          <meshStandardMaterial color={g.c} roughness={1} metalness={0} />
        </mesh>
      ))}
    </group>
  );
}

function TreeGrid() {
  const noise2D = useMemo(() => createNoise2D(createSeededRandom(9090)), []);
  const trees = useMemo(() => {
    const r = [];
    for (let row = -8; row <= 7; row += 1.8) {
      for (let col = -20; col <= 20; col += 2.2) {
        const density = noise2D(col * 0.12, row * 0.12);
        if (density < -0.18) continue;
        if (Math.abs(col) < 5 && Math.abs(row) < 5) continue;
        if (col > 6 && col < 14 && row > 2 && row < 10) continue;
        if (col > 11 && row < -3 && row > -14) continue;
        if (Math.abs(col) < 2 && row > 6) continue;
        r.push({ key: `${row}-${col}`, x: col + (Math.random() - 0.5) * 0.4, z: row + (Math.random() - 0.5) * 0.4, h: 3 + Math.random() * 3, s: 0.7 + Math.random() * 0.5 });
      }
    }
    return r;
  }, [noise2D]);
  return <group>{trees.map((t) => <MoringaTree key={t.key} position={[t.x, 0, t.z]} height={t.h} scale={t.s} />)}</group>;
}

/* ── Scrub bushes for surrounding terrain ── */
function ScrubBushes() {
  const noise2D = useMemo(() => createNoise2D(createSeededRandom(1776)), []);
  const bushes = useMemo(() => {
    const r = [];
    for (let i = 0; i < 60; i++) {
      const angle = Math.random() * Math.PI * 2;
      const dist = 24 + Math.random() * 22;
      const x = Math.cos(angle) * dist;
      const z = Math.sin(angle) * dist;
      const mask = noise2D(x * 0.08, z * 0.08);
      if (mask < -0.1) continue;
      r.push({
        x,
        z,
        s: 0.3 + Math.random() * 0.6,
        color: `hsl(${75 + Math.random() * 50}, ${25 + Math.random() * 25}%, ${22 + Math.random() * 18}%)`,
      });
    }
    return r;
  }, [noise2D]);

  return (
    <group>
      {bushes.map((b, i) => (
        <mesh key={i} position={[b.x, b.s * 0.4, b.z]} castShadow>
          <sphereGeometry args={[b.s, 8, 6]} />
          <meshStandardMaterial color={b.color} roughness={0.9} />
        </mesh>
      ))}
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  PROCESSING PLANT
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function ProcessingPlant() {
  // Smoke/steam from vent
  const smokeRef = useRef();
  useFrame(({ clock }) => {
    if (!smokeRef.current) return;
    const t = clock.getElapsedTime();
    smokeRef.current.position.y = 5.5 + Math.sin(t * 0.5) * 0.3;
    smokeRef.current.material.opacity = 0.08 + Math.sin(t * 0.8) * 0.04;
    smokeRef.current.scale.setScalar(1 + Math.sin(t * 0.3) * 0.2);
  });

  return (
    <group position={[0, 0, -2]}>
      {/* Foundation */}
      <mesh position={[0, 0.08, 0]} receiveShadow>
        <boxGeometry args={[10, 0.16, 7]} />
        <meshStandardMaterial color="#B0B0B0" roughness={0.7} />
      </mesh>

      {/* Main walls with corrugated look (slight metalness) */}
      <mesh position={[0, 2, 0]} castShadow>
        <boxGeometry args={[8, 3.6, 5.5]} />
        <meshStandardMaterial color="#E0D8CC" roughness={0.45} metalness={0.08} />
      </mesh>


      {/* Metal roof */}
      <mesh position={[0, 4.2, 0]}>
        <boxGeometry args={[8.6, 0.12, 6.2]} />
        <meshStandardMaterial color="#5A5A5A" roughness={0.2} metalness={0.7} />
      </mesh>
      <mesh position={[0, 4.6, 0]}>
        <boxGeometry args={[8.6, 0.5, 0.6]} />
        <meshStandardMaterial color="#4A4A4A" roughness={0.25} metalness={0.65} />
      </mesh>

      {/* Solar panels on roof */}
      {[-2.5, 0, 2.5].map((x) => (
        <group key={`sp-${x}`}>
          <mesh position={[x, 4.5, 0.8]} rotation={[-0.35, 0, 0]}>
            <boxGeometry args={[2, 0.04, 1.3]} />
            <meshStandardMaterial color="#1a237e" roughness={0.08} metalness={0.85} />
          </mesh>
          <mesh position={[x, 4.48, 0.8]} rotation={[-0.35, 0, 0]}>
            <boxGeometry args={[2.05, 0.02, 1.35]} />
            <meshStandardMaterial color="#A0A0A0" roughness={0.15} metalness={0.85} />
          </mesh>
        </group>
      ))}

      {/* Loading dock */}
      <mesh position={[-4.3, 1, 0]} castShadow>
        <boxGeometry args={[0.8, 1.8, 4]} />
        <meshStandardMaterial color="#C8C0B0" roughness={0.6} />
      </mesh>
      <mesh position={[-5.2, 0.5, 0]} rotation={[0, 0, 0.3]}>
        <boxGeometry args={[1.5, 0.1, 3]} />
        <meshStandardMaterial color="#999" roughness={0.7} metalness={0.2} />
      </mesh>

      {/* Doors */}
      <mesh position={[0, 1, 2.76]}><planeGeometry args={[2.4, 2]} /><meshStandardMaterial color="#555" roughness={0.25} metalness={0.5} /></mesh>
      <mesh position={[2.5, 0.95, 2.76]}><planeGeometry args={[0.9, 1.9]} /><meshStandardMaterial color="#8B6914" roughness={0.6} /></mesh>

      {/* Windows */}
      {[-2, -0.8, 0.8].map((x) => (
        <mesh key={`pw-${x}`} position={[x, 2.8, 2.77]}>
          <planeGeometry args={[0.7, 0.5]} />
          <meshStandardMaterial color="#87CEEB" roughness={0.05} metalness={0.25} transparent opacity={0.6} />
        </mesh>
      ))}

      {/* Chimney/vent */}
      <mesh position={[3, 4.9, -1]}>
        <cylinderGeometry args={[0.2, 0.25, 1.2, 8]} />
        <meshStandardMaterial color="#606060" roughness={0.25} metalness={0.6} />
      </mesh>
      {/* Animated steam */}
      <mesh ref={smokeRef} position={[3, 5.5, -1]}>
        <sphereGeometry args={[0.4, 8, 6]} />
        <meshStandardMaterial color="#FFFFFF" transparent opacity={0.1} depthWrite={false} />
      </mesh>

      {/* Storage tanks */}
      {[1.2, -1.2].map((z) => (
        <mesh key={`tank-${z}`} position={[5.5, 1.2, z]}>
          <cylinderGeometry args={[0.5, 0.5, 2.2, 16]} />
          <meshStandardMaterial color="#C0C0C0" roughness={0.15} metalness={0.75} />
        </mesh>
      ))}

      {/* Label */}
      <Html position={[0, 5.8, 0]} center distanceFactor={18} style={{ pointerEvents: 'none' }}>
        <div className="bg-emerald-900/80 backdrop-blur text-emerald-100 text-[11px] font-bold px-3 py-1.5 rounded-lg whitespace-nowrap border border-emerald-700/30 shadow-lg">
          Processing Plant
        </div>
      </Html>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  FARM SHOP & VISITOR CENTER
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function FarmShop() {
  return (
    <group position={[10, 0, 6]}>
      <mesh position={[0, 0.06, 0]} receiveShadow>
        <boxGeometry args={[6, 0.12, 4.5]} />
        <meshStandardMaterial color="#B8B0A0" roughness={0.7} />
      </mesh>
      {/* Adobe walls */}
      <mesh position={[0, 1.4, 0]} castShadow>
        <boxGeometry args={[5.5, 2.5, 4]} />
        <meshStandardMaterial color="#E6D5B8" roughness={0.75} />
      </mesh>
      {/* Flat roof with parapet */}
      <mesh position={[0, 2.8, 0]}>
        <boxGeometry args={[5.8, 0.15, 4.3]} />
        <meshStandardMaterial color="#8B7355" roughness={0.55} metalness={0.1} />
      </mesh>

      {/* Covered veranda */}
      <mesh position={[0, 2.3, 2.3]}>
        <boxGeometry args={[5.5, 0.08, 1.5]} />
        <meshStandardMaterial color="#6D4C2F" roughness={0.7} />
      </mesh>
      {[-2, 0, 2].map((x) => (
        <mesh key={`vp-${x}`} position={[x, 1.2, 2.8]}>
          <cylinderGeometry args={[0.06, 0.06, 2.2, 8]} />
          <meshStandardMaterial color="#5C3A1E" roughness={0.7} />
        </mesh>
      ))}

      {/* Glass storefront */}
      <mesh position={[0, 1.3, 2.01]}>
        <planeGeometry args={[3.5, 2]} />
        <meshStandardMaterial color="#87CEEB" roughness={0.1} metalness={0.15} transparent opacity={0.5} envMapIntensity={0} />
      </mesh>
      {[-0.9, 0, 0.9].map((x) => (
        <mesh key={`m-${x}`} position={[x, 1.3, 2.02]}>
          <boxGeometry args={[0.04, 2, 0.02]} />
          <meshStandardMaterial color="#333" />
        </mesh>
      ))}
      <mesh position={[-0.45, 0.9, 2.02]}>
        <planeGeometry args={[0.85, 1.8]} />
        <meshStandardMaterial color="#4A6741" roughness={0.5} />
      </mesh>

      {/* Outdoor tasting bar */}
      <mesh position={[0, 0.65, 3.5]}>
        <boxGeometry args={[5, 0.06, 0.8]} />
        <meshStandardMaterial color="#6D4C2F" roughness={0.6} />
      </mesh>
      {[-1.5, 0, 1.5].map((x) => (
        <group key={`seat-${x}`} position={[x, 0, 3.5]}>
          <mesh position={[0, 0.4, 0]}><cylinderGeometry args={[0.4, 0.4, 0.04, 8]} /><meshStandardMaterial color="#D2B48C" roughness={0.7} /></mesh>
          <mesh position={[0, 0.2, 0]}><cylinderGeometry args={[0.04, 0.04, 0.4, 6]} /><meshStandardMaterial color="#555" roughness={0.3} metalness={0.5} /></mesh>
        </group>
      ))}

      {/* Potted plants (greenery by the entrance) */}
      {[-2, 2].map((x) => (
        <group key={`pot-${x}`} position={[x, 0, 2.6]}>
          <mesh position={[0, 0.2, 0]}><cylinderGeometry args={[0.2, 0.18, 0.4, 8]} /><meshStandardMaterial color="#8B5A2B" roughness={0.8} /></mesh>
          <mesh position={[0, 0.6, 0]}><sphereGeometry args={[0.3, 8, 6]} /><meshStandardMaterial color="#3B8C3F" roughness={0.7} /></mesh>
        </group>
      ))}

      <Html position={[0, 4, 0]} center distanceFactor={18} style={{ pointerEvents: 'none' }}>
        <div className="bg-amber-900/80 backdrop-blur text-amber-100 text-[11px] font-bold px-3 py-1.5 rounded-lg whitespace-nowrap border border-amber-700/30 shadow-lg">
          Farm Shop &amp; Tasting Bar
        </div>
      </Html>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  ECO-LODGE VILLAGE
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function Cottage({ position, rotation = 0 }) {
  return (
    <group position={position} rotation={[0, rotation, 0]}>
      <mesh position={[0, 0.25, 0]} receiveShadow><boxGeometry args={[3.6, 0.5, 2.8]} /><meshStandardMaterial color="#8B8070" roughness={0.8} /></mesh>
      <mesh position={[0, 1.2, 0]} castShadow><boxGeometry args={[3.2, 1.6, 2.4]} /><meshStandardMaterial color="#D2B48C" roughness={0.7} /></mesh>
      {/* Thatch roof */}
      <mesh position={[0, 2.4, 0]}><coneGeometry args={[2.6, 1.5, 4]} /><meshStandardMaterial color="#8B7355" roughness={0.95} /></mesh>
      {/* Solar */}
      <mesh position={[0.6, 2.8, -0.5]} rotation={[-0.45, 0, 0]}><boxGeometry args={[1, 0.03, 0.6]} /><meshStandardMaterial color="#1a237e" roughness={0.08} metalness={0.85} /></mesh>
      {/* Porch */}
      <mesh position={[0, 1.85, 1.5]}><boxGeometry args={[2.4, 0.06, 1]} /><meshStandardMaterial color="#6D4C2F" roughness={0.7} /></mesh>
      {[-0.9, 0.9].map((x) => (
        <mesh key={`pp-${x}`} position={[x, 1.1, 1.9]}><cylinderGeometry args={[0.04, 0.04, 1.5, 6]} /><meshStandardMaterial color="#5C3A1E" roughness={0.7} /></mesh>
      ))}
      <mesh position={[0, 0.8, 1.21]}><planeGeometry args={[0.7, 1.3]} /><meshStandardMaterial color="#5C3A1E" roughness={0.6} /></mesh>
      {[-1, 1].map((x) => (
        <mesh key={`cw-${x}`} position={[x, 1.2, 1.21]}><planeGeometry args={[0.5, 0.45]} /><meshStandardMaterial color="#87CEEB" roughness={0.05} transparent opacity={0.5} /></mesh>
      ))}
    </group>
  );
}

function EcoLodgeVillage() {
  const cottages = [
    { pos: [14, 0, -5], rot: -0.2 }, { pos: [17, 0, -7], rot: 0.3 },
    { pos: [14, 0, -10], rot: -0.4 }, { pos: [18, 0, -11], rot: 0.5 },
    { pos: [15, 0, -14], rot: -0.1 }, { pos: [19, 0, -14], rot: 0.3 },
  ];
  return (
    <group>
      {cottages.map((c, i) => <Cottage key={i} position={c.pos} rotation={c.rot} />)}
      {/* Fire pit with subtle glow */}
      <mesh position={[16.5, 0.1, -10]} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[0.8, 16]} />
        <meshStandardMaterial color="#3A2510" roughness={0.9} />
      </mesh>
      <mesh position={[16.5, 0.12, -10]} rotation={[-Math.PI / 2, 0, 0]}>
        <ringGeometry args={[0.6, 0.8, 16]} />
        <meshStandardMaterial color="#888" roughness={0.5} metalness={0.3} />
      </mesh>
      {/* Fire glow (emissive) */}
      <mesh position={[16.5, 0.25, -10]}>
        <sphereGeometry args={[0.15, 8, 6]} />
        <meshStandardMaterial color="#FF6B00" emissive="#FF4500" emissiveIntensity={3} transparent opacity={0.6} />
      </mesh>
      {/* Paths */}
      {cottages.slice(0, -1).map((c, i) => {
        const n = cottages[i + 1];
        const mid = [(c.pos[0] + n.pos[0]) / 2, 0.02, (c.pos[2] + n.pos[2]) / 2];
        const dx = n.pos[0] - c.pos[0], dz = n.pos[2] - c.pos[2];
        const len = Math.sqrt(dx * dx + dz * dz);
        return (
          <mesh key={`lp-${i}`} rotation={[-Math.PI / 2, 0, -Math.atan2(dx, dz)]} position={mid}>
            <planeGeometry args={[0.6, len]} />
            <meshStandardMaterial color="#C4B8A0" roughness={0.9} />
          </mesh>
        );
      })}
      {/* Garden area with planters */}
      {cottages.map((c, i) => (
        <mesh key={`gdn-${i}`} position={[c.pos[0] + 1.5, 0.15, c.pos[2] + 0.5]}>
          <boxGeometry args={[0.6, 0.2, 0.6]} />
          <meshStandardMaterial color="#4A7A3E" roughness={0.8} />
        </mesh>
      ))}
      <Html position={[16, 4.5, -9.5]} center distanceFactor={22} style={{ pointerEvents: 'none' }}>
        <div className="bg-emerald-900/80 backdrop-blur text-emerald-100 text-[11px] font-bold px-3 py-1.5 rounded-lg whitespace-nowrap border border-emerald-700/30 shadow-lg">Eco-Lodge Village</div>
      </Html>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  WATER FEATURES
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function Reservoir() {
  const waterRef = useRef();
  useFrame(({ clock }) => {
    if (!waterRef.current) return;
    const t = clock.getElapsedTime();
    // Gentle ripple by rotating and slightly scaling
    waterRef.current.rotation.z = Math.sin(t * 0.4) * 0.003;
    waterRef.current.material.opacity = 0.55 + Math.sin(t * 0.8) * 0.08;
  });

  return (
    <group position={[-16, -0.15, -12]}>
      <mesh ref={waterRef} rotation={[-Math.PI / 2, 0, 0]}>
        <circleGeometry args={[3, 32]} />
        <meshStandardMaterial color="#2B6B8A" roughness={0.08} metalness={0.3} transparent opacity={0.6} />
      </mesh>
      {/* Embankment */}
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -0.02, 0]}>
        <ringGeometry args={[2.8, 3.8, 32]} />
        <meshStandardMaterial color="#8B7355" roughness={0.8} />
      </mesh>
      {/* Reeds around edge */}
      {Array.from({ length: 12 }).map((_, i) => {
        const a = (i / 12) * Math.PI * 2;
        return (
          <mesh key={i} position={[Math.cos(a) * 3.2, 0.5, Math.sin(a) * 3.2]}>
            <cylinderGeometry args={[0.02, 0.01, 1, 4]} />
            <meshStandardMaterial color="#5A7A3A" roughness={0.8} />
          </mesh>
        );
      })}
      <Html position={[0, 1.5, 0]} center distanceFactor={22} style={{ pointerEvents: 'none' }}>
        <div className="bg-blue-900/60 backdrop-blur text-blue-200 text-[9px] font-semibold px-2 py-1 rounded whitespace-nowrap">Irrigation Reservoir</div>
      </Html>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  INFRASTRUCTURE
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function Borehole() {
  return (
    <group position={[-18, 0, 0]}>
      <mesh position={[0, 0.6, 0]}><cylinderGeometry args={[0.3, 0.4, 1.2, 12]} /><meshStandardMaterial color="#707070" roughness={0.3} metalness={0.6} /></mesh>
      <mesh position={[0, 1.5, 0]}><boxGeometry args={[0.6, 0.5, 0.5]} /><meshStandardMaterial color="#888" roughness={0.3} metalness={0.5} /></mesh>
      <group position={[2, 0, 0]}>
        {[[-0.4, -0.4], [0.4, -0.4], [-0.4, 0.4], [0.4, 0.4]].map(([x, z], i) => (
          <mesh key={i} position={[x, 1.5, z]}><cylinderGeometry args={[0.05, 0.06, 3, 6]} /><meshStandardMaterial color="#555" roughness={0.3} metalness={0.5} /></mesh>
        ))}
        <mesh position={[0, 3.3, 0]}><cylinderGeometry args={[0.7, 0.7, 1.2, 16]} /><meshStandardMaterial color="#2E7D32" roughness={0.4} /></mesh>
      </group>
      <Html position={[1, 5, 0]} center distanceFactor={22} style={{ pointerEvents: 'none' }}>
        <div className="bg-blue-900/70 backdrop-blur text-blue-200 text-[9px] font-semibold px-2 py-1 rounded whitespace-nowrap">Borehole &amp; Tank</div>
      </Html>
    </group>
  );
}

function IrrigationLines() {
  return (
    <group>
      {Array.from({ length: 12 }).map((_, i) => (
        <mesh key={`drip-${i}`} position={[0, 0.03, -7 + i * 1.5]}>
          <boxGeometry args={[36, 0.015, 0.03]} />
          <meshStandardMaterial color="#1a1a1a" roughness={0.3} />
        </mesh>
      ))}
      <mesh position={[-18, 0.04, -3]}><boxGeometry args={[0.06, 0.03, 18]} /><meshStandardMaterial color="#222" roughness={0.3} /></mesh>
    </group>
  );
}

function FenceLine() {
  const posts = useMemo(() => {
    const r = [];
    for (let a = 0; a < Math.PI * 2; a += 0.1) r.push({ x: Math.cos(a) * 24, z: Math.sin(a) * 20 + 2, a });
    return r;
  }, []);
  return (
    <group>
      {posts.map((p, i) => (
        <group key={i}>
          <mesh position={[p.x, 0.55, p.z]}><cylinderGeometry args={[0.05, 0.06, 1.1, 6]} /><meshStandardMaterial color="#6D4C2F" roughness={0.8} /></mesh>
          {i < posts.length - 1 && [0.3, 0.6, 0.9].map((h) => {
            const n = posts[(i + 1) % posts.length];
            const dx = n.x - p.x, dz = n.z - p.z;
            const len = Math.sqrt(dx * dx + dz * dz);
            return (
              <mesh key={`w-${i}-${h}`} position={[(p.x + n.x) / 2, h, (p.z + n.z) / 2]} rotation={[0, -Math.atan2(dx, dz) + Math.PI / 2, 0]}>
                <boxGeometry args={[len, 0.012, 0.012]} />
                <meshStandardMaterial color="#999" roughness={0.5} metalness={0.3} />
              </mesh>
            );
          })}
        </group>
      ))}
      {/* Gate */}
      <group position={[0, 0, 22]}>
        {[-1.2, 1.2].map((x) => (
          <mesh key={x} position={[x, 0.7, 0]}><cylinderGeometry args={[0.08, 0.08, 1.4, 8]} /><meshStandardMaterial color="#555" metalness={0.6} roughness={0.3} /></mesh>
        ))}
        <Html position={[0, 2, 0]} center distanceFactor={22} style={{ pointerEvents: 'none' }}>
          <div className="bg-stone-800/70 backdrop-blur text-stone-200 text-[9px] font-bold px-2 py-0.5 rounded whitespace-nowrap">Main Gate</div>
        </Html>
      </group>
    </group>
  );
}

function SolarField() {
  return (
    <group position={[-14, 0, 10]}>
      {Array.from({ length: 3 }).map((_, row) =>
        Array.from({ length: 4 }).map((_, col) => (
          <group key={`sf-${row}-${col}`} position={[col * 2, 0, row * 1.8]}>
            <mesh position={[0, 1.2, 0]} rotation={[-0.4, 0, 0]}><boxGeometry args={[1.6, 0.04, 1]} /><meshStandardMaterial color="#1a237e" roughness={0.08} metalness={0.85} /></mesh>
            <mesh position={[0, 1.18, 0]} rotation={[-0.4, 0, 0]}><boxGeometry args={[1.65, 0.02, 1.05]} /><meshStandardMaterial color="#AAA" roughness={0.15} metalness={0.85} /></mesh>
            <mesh position={[0, 0.6, 0]}><cylinderGeometry args={[0.04, 0.04, 1.2, 6]} /><meshStandardMaterial color="#666" roughness={0.3} metalness={0.5} /></mesh>
          </group>
        ))
      )}
      <Html position={[3, 3, 1.5]} center distanceFactor={22} style={{ pointerEvents: 'none' }}>
        <div className="bg-indigo-900/70 backdrop-blur text-indigo-200 text-[9px] font-semibold px-2 py-1 rounded whitespace-nowrap">Solar Array · 12kW</div>
      </Html>
    </group>
  );
}

function DistantHills() {
  return (
    <group>
      {[[-40, -50, 16, 4], [35, -52, 20, 3.5], [-10, -58, 25, 5], [48, -42, 14, 3], [-45, 35, 18, 3.5], [42, 40, 16, 2.5]].map(([x, z, sx, sy], i) => (
        <mesh key={i} position={[x, 0, z]} scale={[sx, sy, sx * 0.5]}>
          <sphereGeometry args={[1, 16, 12, 0, Math.PI * 2, 0, Math.PI / 2]} />
          <meshStandardMaterial color={i % 2 === 0 ? '#7A8B6D' : '#6A7B5D'} roughness={1} />
        </mesh>
      ))}
    </group>
  );
}

function Vehicles() {
  return (
    <group>
      <group position={[-6.5, 0, -2]}>
        <mesh position={[0, 0.45, 0]} castShadow><boxGeometry args={[1.8, 0.7, 0.85]} /><meshStandardMaterial color="#E8E8E8" roughness={0.35} metalness={0.35} /></mesh>
        <mesh position={[-0.35, 0.75, 0]}><boxGeometry args={[0.8, 0.4, 0.8]} /><meshStandardMaterial color="#E8E8E8" roughness={0.35} metalness={0.35} /></mesh>
        {/* Windshield */}
        <mesh position={[-0.05, 0.78, 0]}><boxGeometry args={[0.08, 0.32, 0.72]} /><meshStandardMaterial color="#87CEEB" roughness={0.03} transparent opacity={0.4} /></mesh>
        {[[-0.6, 0.2, 0.45], [-0.6, 0.2, -0.45], [0.6, 0.2, 0.45], [0.6, 0.2, -0.45]].map(([x, y, z], i) => (
          <mesh key={i} position={[x, y, z]} rotation={[Math.PI / 2, 0, 0]}><cylinderGeometry args={[0.18, 0.18, 0.08, 10]} /><meshStandardMaterial color="#222" roughness={0.8} /></mesh>
        ))}
      </group>
    </group>
  );
}

function FutureFootprints({ phase }) {
  const footprints = [
    { id: 'plant', minPhase: 2, pos: [0, 0.05, -2], size: [10.5, 7.5], color: '#60A5FA', label: 'Processing Plant' },
    { id: 'shop', minPhase: 2, pos: [10, 0.05, 6], size: [6.5, 5], color: '#F59E0B', label: 'Farm Shop' },
    { id: 'lodge', minPhase: 3, pos: [16.5, 0.05, -9.8], size: [10, 11], color: '#34D399', label: 'Eco-Lodge Village' },
    { id: 'ops', minPhase: 4, pos: [-2, 0.05, -16], size: [5.5, 4], color: '#A78BFA', label: 'Certification Hub' },
  ];

  return (
    <group>
      {footprints
        .filter((f) => phase < f.minPhase)
        .map((f) => (
          <group key={f.id} position={f.pos}>
            <mesh rotation={[-Math.PI / 2, 0, 0]}>
              <planeGeometry args={f.size} />
              <meshBasicMaterial color={f.color} transparent opacity={0.15} depthWrite={false} />
            </mesh>
            <mesh position={[0, 0.03, 0]} rotation={[-Math.PI / 2, 0, 0]}>
              <ringGeometry args={[Math.min(f.size[0], f.size[1]) * 0.38, Math.min(f.size[0], f.size[1]) * 0.42, 32]} />
              <meshBasicMaterial color={f.color} transparent opacity={0.4} depthWrite={false} />
            </mesh>
            <Html position={[0, 0.2, 0]} center distanceFactor={20} style={{ pointerEvents: 'none' }}>
              <div className="bg-black/65 border border-white/10 rounded-md px-2 py-1 text-[10px] text-white/75 whitespace-nowrap">
                Planned: {f.label}
              </div>
            </Html>
          </group>
        ))}
    </group>
  );
}

/* ── Birds circling overhead ── */
function Birds() {
  const count = 8;
  const birdsRef = useRef([]);
  const data = useMemo(() => Array.from({ length: count }).map((_, i) => ({
    radius: 15 + Math.random() * 20,
    height: 12 + Math.random() * 8,
    speed: 0.15 + Math.random() * 0.2,
    phase: Math.random() * Math.PI * 2,
  })), []);

  return (
    <group>
      {data.map((b, i) => (
        <BirdMesh key={i} data={b} />
      ))}
    </group>
  );
}

function BirdMesh({ data }) {
  const ref = useRef();
  useFrame(({ clock }) => {
    if (!ref.current) return;
    const t = clock.getElapsedTime() * data.speed + data.phase;
    ref.current.position.set(
      Math.cos(t) * data.radius,
      data.height + Math.sin(t * 2) * 1.5,
      Math.sin(t) * data.radius,
    );
    ref.current.rotation.y = -t + Math.PI / 2;
  });

  return (
    <group ref={ref}>
      {/* Simple bird shape -- two triangular wings */}
      <mesh rotation={[0, 0, Math.PI * 0.1]}>
        <boxGeometry args={[0.6, 0.02, 0.15]} />
        <meshStandardMaterial color="#333" roughness={0.8} />
      </mesh>
      <mesh rotation={[0, 0, -Math.PI * 0.1]}>
        <boxGeometry args={[0.6, 0.02, 0.15]} />
        <meshStandardMaterial color="#333" roughness={0.8} />
      </mesh>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  HOTSPOT MARKER
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function HotspotMarker({ hotspot, active, onClick }) {
  const sphere = useRef();
  const ring = useRef();
  const [hovered, setHovered] = useState(false);

  useFrame(({ clock }) => {
    const t = clock.getElapsedTime();
    if (sphere.current) sphere.current.scale.setScalar(1 + Math.sin(t * 2.5 + hotspot.position[0]) * 0.18);
    if (ring.current) { ring.current.rotation.y = t * 0.6; ring.current.scale.setScalar(1 + Math.sin(t * 1.5) * 0.12); }
  });

  return (
    <group position={hotspot.position}>
      <mesh ref={sphere} onClick={(e) => { e.stopPropagation(); onClick(hotspot.id); }} onPointerOver={() => setHovered(true)} onPointerOut={() => setHovered(false)}>
        <sphereGeometry args={[0.35, 16, 16]} />
        <meshStandardMaterial color={hotspot.color} emissive={hotspot.color} emissiveIntensity={hovered || active ? 2.5 : 1} transparent opacity={0.92} />
      </mesh>
      <mesh ref={ring}><torusGeometry args={[0.6, 0.025, 8, 32]} /><meshStandardMaterial color={hotspot.color} emissive={hotspot.color} emissiveIntensity={0.6} transparent opacity={0.5} /></mesh>
      <mesh position={[0, -hotspot.position[1] / 2, 0]}><cylinderGeometry args={[0.012, 0.012, hotspot.position[1], 4]} /><meshStandardMaterial color={hotspot.color} transparent opacity={0.3} /></mesh>
      <mesh rotation={[-Math.PI / 2, 0, 0]} position={[0, -hotspot.position[1] + 0.03, 0]}><ringGeometry args={[0.3, 0.55, 32]} /><meshStandardMaterial color={hotspot.color} emissive={hotspot.color} emissiveIntensity={0.3} transparent opacity={0.25} /></mesh>
    </group>
  );
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  CAMERA
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
function AutoOrbit({ enabled }) {
  const { camera } = useThree();
  const a = useRef(0);
  useFrame((_, dt) => {
    if (!enabled) return;
    a.current += dt * 0.035;
    camera.position.set(
      Math.cos(a.current) * 42,
      24 + Math.sin(a.current * 0.25) * 4,
      Math.sin(a.current) * 42,
    );
    camera.lookAt(0, 2, 0);
  });
  return null;
}


/* ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
 *  PAGE
 * ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ */
export default function MoringaOasisInvestor() {
  const [active, setActive]   = useState(null);
  const [orbit, setOrbit]     = useState(true);
  const [mode, setMode]       = useState('visual');
  const [phase, setPhase]     = useState(1);
  const [showEconomics, setShowEconomics] = useState(false);
  const [showProofPanel, setShowProofPanel] = useState(false);
  const [loaded, setLoaded]   = useState(false);

  const toggle = useCallback((id) => { setActive((p) => (p === id ? null : id)); setOrbit(false); }, []);
  const data = HOTSPOTS.find((h) => h.id === active);
  const phaseData = PHASE_ECONOMICS[phase];
  const projection = YEAR_PROJECTION[Math.max(0, phase - 1)];

  useEffect(() => { const t = setTimeout(() => setLoaded(true), 800); return () => clearTimeout(t); }, []);

  return (
    <div className="relative w-screen h-screen bg-stone-950 overflow-hidden select-none">
      <Canvas
        shadows
        camera={{ position: [35, 26, 35], fov: 40, near: 0.1, far: 300 }}
        gl={{ antialias: true, alpha: false, powerPreference: 'high-performance' }}
      >
        <Suspense fallback={null}>
          {/* Warm sky gradient via scene background */}
          <color attach="background" args={['#A4C4A8']} />
          <fog attach="fog" args={['#A4C4A8', 60, 120]} />

          {/* Lighting */}
          <directionalLight
            position={[30, 35, 20]} intensity={2.5} color="#FFE4B5" castShadow
            shadow-mapSize-width={2048} shadow-mapSize-height={2048}
            shadow-camera-far={120} shadow-camera-left={-40} shadow-camera-right={40}
            shadow-camera-top={40} shadow-camera-bottom={-40} shadow-bias={-0.0002}
          />
          <directionalLight position={[-25, 18, -15]} intensity={0.35} color="#B4D7FF" />
          <hemisphereLight args={['#87CEEB', '#8B5A2B', 0.45]} />

          {/* Scene */}
          <Terrain />
          <AgronomyLayout showDetail={mode !== 'visual'} />
          <TreeGrid />
          <GroundVegetation />
          <ScrubBushes />
          <LiveWorkLearnRoute visible={mode !== 'visual'} />
          <ZoneKPIAnchors mode={mode} phase={phase} />
          <FutureFootprints phase={phase} />
          {phase >= 2 && <ProcessingPlant />}
          {phase >= 2 && <FarmShop />}
          {phase >= 3 && <EcoLodgeVillage />}
          <Borehole />
          <Reservoir />
          <IrrigationLines />
          <FenceLine />
          <SolarField />
          <DistantHills />
          <Vehicles />
          <DustParticles />
          <Birds />

          {/* Hotspots */}
          {HOTSPOTS.map((h) => (
            <HotspotMarker key={h.id} hotspot={h} active={active === h.id} onClick={toggle} />
          ))}

          {/* Camera */}
          <AutoOrbit enabled={orbit} />
          <OrbitControls
            enablePan={false} minDistance={10} maxDistance={75}
            maxPolarAngle={Math.PI / 2.05} minPolarAngle={0.1}
            onStart={() => setOrbit(false)}
          />

          {/* ── Post-processing -- minimal to avoid flicker ── */}
          <EffectComposer multisampling={4}>
            <Vignette eskil={false} offset={0.25} darkness={0.45} />
            <ToneMapping mode={ToneMappingMode.AGX} />
          </EffectComposer>
        </Suspense>
      </Canvas>

      {/* ── UI OVERLAY ── */}
      <div className={`absolute inset-0 z-20 pointer-events-none transition-opacity duration-1000 ${loaded ? 'opacity-100' : 'opacity-0'}`}>

        {/* Top bar */}
        <div className="absolute top-0 inset-x-0 p-3 sm:p-6 flex items-start justify-between pointer-events-auto">
          <div className="max-w-[min(72vw,32rem)] bg-black/25 backdrop-blur-sm rounded-lg px-3 py-2 border border-white/10">
            <Link to="/project/ukulima" className="inline-flex items-center gap-1.5 text-white/40 hover:text-white/70 text-xs transition mb-2">
              <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" /></svg>
              Back to Ukulima
            </Link>
            <h1 className="font-display text-xl sm:text-2xl font-bold text-white tracking-tight drop-shadow-lg">
              Moringa Oasis Zimbabwe
            </h1>
            <p className="text-white/40 text-xs sm:text-sm mt-0.5 drop-shadow leading-snug break-words">
              Interactive Site Plan · 10 Hectares
            </p>
          </div>
          <button
            onClick={() => setOrbit((p) => !p)}
            className={`px-3 py-1.5 rounded-lg text-xs font-medium transition ${orbit
              ? 'bg-emerald-600/25 text-emerald-300 ring-1 ring-emerald-500/25'
              : 'bg-white/10 text-white/40 hover:text-white/60'}`}
          >
            {orbit ? 'Orbiting' : 'Orbit'}
          </button>
        </div>

        <div className="absolute top-14 right-4 sm:right-6 pointer-events-auto flex flex-col items-end gap-2 max-w-[92vw]">
          <div className="flex flex-wrap justify-end items-center gap-2">
            <div className="bg-black/50 border border-white/10 rounded-lg p-1 flex gap-1">
              {MODE_OPTIONS.map((m) => (
                <button
                  key={m.id}
                  onClick={() => setMode(m.id)}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-semibold ${mode === m.id ? 'bg-emerald-600 text-white' : 'text-white/65 hover:text-white bg-white/5'}`}
                >
                  {m.label}
                </button>
              ))}
            </div>
            <button
              onClick={() => setShowEconomics((v) => !v)}
              className="px-3 py-1.5 rounded-lg text-xs font-medium bg-black/45 text-white/70 hover:text-white border border-white/10"
            >
              {showEconomics ? 'Hide Stats' : 'Show Stats'}
            </button>
            {mode === 'proof' && (
              <button
                onClick={() => setShowProofPanel((v) => !v)}
                className="px-3 py-1.5 rounded-lg text-xs font-medium bg-black/45 text-white/70 hover:text-white border border-white/10"
              >
                {showProofPanel ? 'Hide Proof' : 'Show Proof'}
              </button>
            )}
          </div>

          <div className="bg-black/55 backdrop-blur-xl rounded-xl p-2 border border-white/[0.06] shadow-2xl">
            <div className="text-[9px] tracking-[0.16em] uppercase text-white/35 px-2 pb-1">Future State</div>
            <div className="flex gap-1">
              {[1, 2, 3, 4].map((p) => (
                <button
                  key={p}
                  onClick={() => setPhase(p)}
                  className={`px-2.5 py-1 rounded-md text-[10px] font-semibold transition ${phase === p ? 'bg-emerald-600 text-white' : 'bg-white/8 text-white/55 hover:text-white/85'}`}
                >
                  P{p}
                </button>
              ))}
            </div>
            <div className="mt-2 text-[10px] text-white/55 px-1">Select a phase to preview planned build-out.</div>
          </div>
        </div>

        {/* Investment summary */}
        <div className="absolute top-[176px] sm:top-[156px] left-3 sm:left-6 pointer-events-none max-w-[calc(100vw-1rem)]">
          <div className="bg-black/60 backdrop-blur-xl rounded-2xl p-4 text-white border border-white/[0.06] shadow-2xl w-[min(18rem,calc(100vw-1.5rem))]">
            <p className="text-[9px] tracking-[0.2em] uppercase text-white/35 mb-1">Total Capital Raise</p>
            <p className="text-3xl font-bold tracking-tight" style={{ color: EMERALD }}>$675K</p>
            <div className="mt-2 space-y-1">
              <div className="flex justify-between text-[10px]"><span className="text-white/40">Milestones</span><span className="text-white/60">4 phases</span></div>
              <div className="flex justify-between text-[10px]"><span className="text-white/40">Release</span><span className="text-white/60">Gated / verified</span></div>
              <div className="flex justify-between text-[10px]"><span className="text-white/40">Target ROI</span><span className="text-emerald-400 font-semibold">18-24% p.a.</span></div>
            </div>
          </div>
        </div>

        {showEconomics && mode !== 'visual' && (
          <div className="absolute top-[255px] left-4 sm:left-6 pointer-events-auto w-[300px]">
            <div className="bg-black/62 backdrop-blur-xl rounded-2xl p-4 text-white border border-white/[0.08] shadow-2xl">
              <p className="text-[9px] tracking-[0.2em] uppercase text-white/35 mb-2">Unit Economics</p>
              <div className="text-xs text-white/75 mb-2">Phase {phase}: {phaseData.label}</div>
              <div className="space-y-1.5 text-[11px]">
                <div className="flex justify-between"><span className="text-white/40">Land Active</span><span>{phaseData.ha} ha</span></div>
                <div className="flex justify-between"><span className="text-white/40">Tree Density</span><span>{UNIT_ECONOMICS.treeDensityPerHa}/ha</span></div>
                <div className="flex justify-between"><span className="text-white/40">Powder / Tree</span><span>{UNIT_ECONOMICS.powderPerTreeKg} kg/yr</span></div>
                <div className="flex justify-between"><span className="text-white/40">Price (Hybrid)</span><span>EUR {UNIT_ECONOMICS.hybridPriceEurPerKg}/kg</span></div>
                <div className="flex justify-between"><span className="text-white/40">Revenue Floor</span><span className="text-emerald-300">{formatEur(phaseData.revenueFloor)}</span></div>
                <div className="flex justify-between"><span className="text-white/40">EBITDA Floor</span><span className="text-emerald-300">{formatEur(phaseData.ebitdaFloor)}</span></div>
              </div>

              <div className="mt-3 pt-3 border-t border-white/10">
                <p className="text-[10px] uppercase tracking-wider text-white/35 mb-2">Revenue Stack at 15 ha</p>
                <div className="space-y-1 text-[11px]">
                  <div className="flex justify-between"><span className="text-white/40">Powder</span><span>{formatEur(REVENUE_STACK.powderEur)}</span></div>
                  <div className="flex justify-between"><span className="text-white/40">Oil</span><span>{formatEur(REVENUE_STACK.oilRangeEur[0])}-{formatEur(REVENUE_STACK.oilRangeEur[1])}</span></div>
                  <div className="flex justify-between"><span className="text-white/40">Eco-Lodging</span><span>{formatEur(REVENUE_STACK.lodgingRangeEur[0])}-{formatEur(REVENUE_STACK.lodgingRangeEur[1])}</span></div>
                  <div className="flex justify-between"><span className="text-white/40">Retail + Experiences</span><span>{formatEur(REVENUE_STACK.retailRangeEur[0] + REVENUE_STACK.experiencesRangeEur[0])}-{formatEur(REVENUE_STACK.retailRangeEur[1] + REVENUE_STACK.experiencesRangeEur[1])}</span></div>
                  <div className="flex justify-between font-semibold"><span className="text-white/55">Total</span><span className="text-emerald-300">{formatEur(REVENUE_STACK.totalRangeEur[0])}-{formatEur(REVENUE_STACK.totalRangeEur[1])}</span></div>
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-white/10 text-[11px]">
                <div className="flex justify-between"><span className="text-white/40">Projection Anchor</span><span>Year {projection.year}</span></div>
                <div className="flex justify-between"><span className="text-white/40">Projected Revenue</span><span>{formatEur(projection.revenue)}</span></div>
                <div className="flex justify-between"><span className="text-white/40">Projected EBITDA</span><span className="text-emerald-300">{formatEur(projection.ebitda)}</span></div>
                <p className="text-white/35 mt-2 leading-relaxed">{phaseData.focus}</p>
                <p className="text-white/30 mt-2">Status: {CURRENT_PROJECT_STATE.lifecycle}</p>
              </div>
            </div>
          </div>
        )}

        {mode === 'proof' && showProofPanel && (
          <div className="absolute top-[88px] right-4 sm:right-6 w-[330px] pointer-events-auto">
            <div className="bg-black/70 backdrop-blur-xl rounded-2xl p-4 text-white border border-white/[0.08] shadow-2xl">
              <p className="text-[9px] tracking-[0.2em] uppercase text-white/35 mb-2">Proof Mode · Phase {phase}</p>
              <div className="space-y-2">
                {(PROOF_ARTIFACTS[phase] || []).map((a, idx) => (
                  <div key={idx} className="border border-white/10 rounded-lg p-2 bg-white/[0.03]">
                    <div className="text-[11px] text-white/90">{a.item}</div>
                    <div className="mt-1 flex justify-between text-[10px] text-white/60"><span>Planned Budget {formatEur(a.budget)}</span><span>Spent {formatEur(a.spent)}</span></div>
                    <div className="mt-1 h-1.5 bg-white/10 rounded overflow-hidden"><div className="h-full bg-emerald-500" style={{ width: `${a.progress}%` }} /></div>
                    <div className="mt-1 text-[10px] text-cyan-300 flex items-center gap-1">
                      <span>Proof:</span>
                      <a
                        href={a.proof}
                        target="_blank"
                        rel="noreferrer"
                        className="underline decoration-cyan-400/60 hover:text-cyan-200 break-all"
                      >
                        {a.proof}
                      </a>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* Bottom milestones */}
        <div className="absolute bottom-0 inset-x-0 p-4 sm:p-6">
          <div className="flex flex-wrap gap-2 pointer-events-auto">
            {HOTSPOTS.map((h) => (
              <button
                key={h.id}
                onClick={() => toggle(h.id)}
                className={`group flex items-center gap-1.5 px-3 py-2 rounded-xl text-xs font-medium transition-all backdrop-blur-md border ${active === h.id ? 'text-white scale-[1.03] shadow-xl border-white/20' : 'bg-black/35 text-white/55 hover:text-white/80 border-white/[0.04]'}`}
                style={active === h.id ? { background: h.color, borderColor: `${h.color}66` } : h.milestone > phase ? { opacity: 0.5 } : undefined}
              >
                <SiteIcon name={h.icon} className="w-3.5 h-3.5" /><span>{h.label}</span>
                <span className="text-white/30 group-hover:text-white/50 ml-1">{h.budget}</span>
              </button>
            ))}
          </div>
        </div>

        {/* Detail card */}
        {data && (
          <div className="absolute top-[88px] right-4 sm:right-6 w-72 sm:w-80 pointer-events-auto">
            <div className="rounded-2xl p-5 text-white shadow-2xl border border-white/[0.08]" style={{ background: 'rgba(0,0,0,0.78)', backdropFilter: 'blur(20px)' }}>
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-2">
                  <SiteIcon name={data.icon} className="w-4 h-4" />
                  <span className="text-[10px] font-bold tracking-widest uppercase" style={{ color: data.color }}>Milestone {data.milestone}</span>
                </div>
                <button onClick={() => setActive(null)} className="text-white/25 hover:text-white/50 transition p-1">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" /></svg>
                </button>
              </div>
              <h3 className="text-lg font-bold mb-1.5">{data.label}</h3>
              <p className="text-white/45 text-sm leading-relaxed mb-3">{data.detail}</p>
              <div className="flex items-center justify-between">
                <span className="text-white/70 text-base font-bold">{data.budget}</span>
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold tracking-wide" style={{
                  background: data.status === 'Active' ? 'rgba(5,150,105,0.2)' : data.status === 'Funded' ? 'rgba(37,99,235,0.2)' : 'rgba(255,255,255,0.08)',
                  color: data.status === 'Active' ? EMERALD : data.status === 'Funded' ? '#60A5FA' : 'rgba(255,255,255,0.45)',
                }}>{data.status}</span>
              </div>
            </div>
          </div>
        )}

        <div className="absolute bottom-14 right-4 pointer-events-none">
          <p className="text-[8px] text-white/15">Real photography · Moringa Oasis, Zimbabwe</p>
        </div>
      </div>

      {/* Loading */}
      {!loaded && (
        <div className="absolute inset-0 bg-stone-950 flex items-center justify-center z-50">
          <div className="text-center">
            <div className="w-10 h-10 rounded-full border-2 border-emerald-500 border-t-transparent animate-spin mx-auto mb-4" />
            <p className="text-white/40 text-sm font-medium">Loading the Oasis</p>
            <p className="text-white/20 text-xs mt-1">Fetching farm imagery...</p>
          </div>
        </div>
      )}
    </div>
  );
}
