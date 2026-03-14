/**
 * LiveVoicePanel – Real-time voice conversation with the VBV AI agent
 * powered by LiveKit.
 *
 * Uses useSession + useAgent + BarVisualizer from @livekit/components-react
 * to manage the Room lifecycle, track agent state, and render audio
 * visualization with rich animated SVG artwork.
 */

import { useState, useCallback, useMemo, useEffect, useRef } from 'react';
import { TokenSource } from 'livekit-client';
import {
  useSession,
  useAgent,
  useVoiceAssistant,
  SessionProvider,
  BarVisualizer,
  RoomAudioRenderer,
  TrackToggle,
} from '@livekit/components-react';
import { Track } from 'livekit-client';
// NOTE: We do NOT import @livekit/components-styles globally — its CSS
// resets conflict with Tailwind 4. Custom styles are in the <style> block below.

// ── State label map ─────────────────────────────────────────────
const STATE_LABELS = {
  disconnected:           'Offline',
  connecting:             'Connecting…',
  'pre-connect-buffering':'Speak now…',
  initializing:           'Starting up…',
  idle:                   'Ready',
  listening:              'Listening…',
  thinking:               'Thinking…',
  speaking:               'Speaking…',
  failed:                 'Connection failed',
};

const STATE_COLORS = {
  disconnected:           { ring: '#6B7280', dot: '#9CA3AF', glow: 'rgba(107,114,128,0.15)' },
  connecting:             { ring: '#F59E0B', dot: '#FBBF24', glow: 'rgba(245,158,11,0.2)'  },
  'pre-connect-buffering':{ ring: '#10B981', dot: '#34D399', glow: 'rgba(16,185,129,0.25)' },
  initializing:           { ring: '#F59E0B', dot: '#FBBF24', glow: 'rgba(245,158,11,0.2)'  },
  idle:                   { ring: '#10B981', dot: '#34D399', glow: 'rgba(16,185,129,0.2)'  },
  listening:              { ring: '#10B981', dot: '#34D399', glow: 'rgba(16,185,129,0.35)' },
  thinking:               { ring: '#8B5CF6', dot: '#A78BFA', glow: 'rgba(139,92,246,0.25)' },
  speaking:               { ring: '#06B6D4', dot: '#22D3EE', glow: 'rgba(6,182,212,0.3)'  },
  failed:                 { ring: '#EF4444', dot: '#F87171', glow: 'rgba(239,68,68,0.2)'  },
};

// ── Outer wrapper — manages session lifecycle ───────────────────
export default function LiveVoicePanel({ userId, userName, userRole, onClose }) {
  const tokenSource = useMemo(
    () =>
      TokenSource.custom(async () => {
        const res = await fetch('/api/livekit/token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            user_id: userId || 'web_anonymous',
            user_name: userName || 'Guest',
            user_role: userRole || 'DONOR',
          }),
        });
        if (!res.ok) throw new Error('Failed to get voice token');
        const data = await res.json();
        return { participantToken: data.token, serverUrl: data.url };
      }),
    [userId, userName, userRole],
  );

  const session = useSession(tokenSource);

  return (
    <SessionProvider session={session}>
      <VoicePanelInner session={session} onClose={onClose} userName={userName} />
    </SessionProvider>
  );
}

// ── Inner panel (has access to SessionContext) ──────────────────
function VoicePanelInner({ session, onClose, userName }) {
  const agent = useAgent(session);
  const { state: agentState, audioTrack, agentTranscriptions } = useVoiceAssistant();
  const [isStarted, setIsStarted] = useState(false);
  const [showTranscript, setShowTranscript] = useState(false);
  const transcriptRef = useRef(null);

  // Color palette for current state
  const colors = STATE_COLORS[agentState] || STATE_COLORS.disconnected;
  const label = STATE_LABELS[agentState] || agentState;

  // Gather transcription lines
  const transcriptions = agentTranscriptions || [];

  // Auto-scroll transcript
  useEffect(() => {
    if (transcriptRef.current) {
      transcriptRef.current.scrollTop = transcriptRef.current.scrollHeight;
    }
  }, [transcriptions]);

  // ── Connect / Disconnect ──────────────────────────────────
  const [startError, setStartError] = useState(null);

  const handleStart = useCallback(async () => {
    setStartError(null);
    try {
      console.log('[LiveVoice] session object:', session);
      console.log('[LiveVoice] session.start:', typeof session?.start);
      console.log('[LiveVoice] connectionState:', session?.connectionState);

      // Guard: make sure session object is ready
      if (!session || typeof session.start !== 'function') {
        throw new Error('Voice session not ready — try again in a moment.');
      }
      await session.start({ tracks: { microphone: { enabled: true } } });
      setIsStarted(true);
    } catch (err) {
      console.error('LiveKit connect failed:', err);
      setStartError(err.message || String(err));
    }
  }, [session]);

  const handleEnd = useCallback(async () => {
    try {
      await session.end();
    } catch { /* ignore */ }
    setIsStarted(false);
    onClose?.();
  }, [session, onClose]);

  // ── Full-screen overlay ───────────────────────────────────
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-950/95 backdrop-blur-xl">
      {/* Render remote audio */}
      <RoomAudioRenderer />

      {/* ── Ambient SVG Background ─────────────────────────── */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" preserveAspectRatio="xMidYMid slice" viewBox="0 0 800 800">
        {/* Grid pattern */}
        <defs>
          <pattern id="vp-grid" x="0" y="0" width="40" height="40" patternUnits="userSpaceOnUse">
            <path d="M 40 0 L 0 0 0 40" fill="none" stroke="#10B981" strokeWidth="0.15" opacity="0.08" />
          </pattern>
          <radialGradient id="vp-glow1" cx="50%" cy="45%" r="35%">
            <stop offset="0%" stopColor={colors.glow} />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <radialGradient id="vp-glow2" cx="25%" cy="70%" r="25%">
            <stop offset="0%" stopColor="rgba(16,185,129,0.06)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <radialGradient id="vp-glow3" cx="75%" cy="30%" r="20%">
            <stop offset="0%" stopColor="rgba(6,182,212,0.04)" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
        </defs>
        <rect width="800" height="800" fill="url(#vp-grid)" />
        <rect width="800" height="800" fill="url(#vp-glow1)" />
        <rect width="800" height="800" fill="url(#vp-glow2)" />
        <rect width="800" height="800" fill="url(#vp-glow3)" />

        {/* Orbital rings */}
        <circle cx="400" cy="360" r="180" fill="none" stroke="#10B981" strokeWidth="0.3" opacity="0.06">
          <animateTransform attributeName="transform" type="rotate" values="0 400 360;360 400 360" dur="60s" repeatCount="indefinite" />
        </circle>
        <circle cx="400" cy="360" r="220" fill="none" stroke="#14B8A6" strokeWidth="0.2" strokeDasharray="4 12" opacity="0.05">
          <animateTransform attributeName="transform" type="rotate" values="360 400 360;0 400 360" dur="45s" repeatCount="indefinite" />
        </circle>
        <circle cx="400" cy="360" r="260" fill="none" stroke="#06B6D4" strokeWidth="0.15" strokeDasharray="2 18" opacity="0.04">
          <animateTransform attributeName="transform" type="rotate" values="0 400 360;360 400 360" dur="80s" repeatCount="indefinite" />
        </circle>

        {/* Corner accents */}
        <path d="M0 0 L60 0 L0 60Z" fill="#10B981" opacity="0.03" />
        <path d="M800 0 L740 0 L800 60Z" fill="#14B8A6" opacity="0.02" />
        <path d="M0 800 L60 800 L0 740Z" fill="#06B6D4" opacity="0.02" />
        <path d="M800 800 L740 800 L800 740Z" fill="#10B981" opacity="0.03" />

        {/* Floating particles */}
        <circle cx="120" cy="200" r="1.5" fill="#10B981" opacity="0.15">
          <animate attributeName="cy" values="200;180;200" dur="4s" repeatCount="indefinite" />
          <animate attributeName="opacity" values="0.15;0.3;0.15" dur="4s" repeatCount="indefinite" />
        </circle>
        <circle cx="680" cy="500" r="1" fill="#14B8A6" opacity="0.12">
          <animate attributeName="cy" values="500;480;500" dur="5s" repeatCount="indefinite" />
        </circle>
        <circle cx="300" cy="650" r="1.2" fill="#06B6D4" opacity="0.1">
          <animate attributeName="cy" values="650;635;650" dur="3.5s" repeatCount="indefinite" />
        </circle>
        <circle cx="550" cy="150" r="0.8" fill="#10B981" opacity="0.12">
          <animate attributeName="cy" values="150;135;150" dur="6s" repeatCount="indefinite" />
        </circle>

        {/* Hexagonal accent at center */}
        <polygon points="400,310 432,328 432,364 400,382 368,364 368,328"
          fill="none" stroke="#10B981" strokeWidth="0.4" opacity="0.04">
          <animateTransform attributeName="transform" type="rotate" values="0 400 346;360 400 346" dur="30s" repeatCount="indefinite" />
        </polygon>
      </svg>

      {/* ── Close button ───────────────────────────────────── */}
      <button
        onClick={handleEnd}
        className="absolute top-6 right-6 z-10 p-2.5 rounded-xl bg-white/5 hover:bg-white/10 text-white/50 hover:text-white transition-all group"
        aria-label="End voice session"
      >
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
          <path d="M5 5l10 10M15 5L5 15" />
        </svg>
      </button>

      {/* ── Title ──────────────────────────────────────────── */}
      <div className="absolute top-6 left-6 z-10">
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <svg width="28" height="28" viewBox="0 0 28 28" fill="none">
              <polygon points="14,1 26,7.5 26,20.5 14,27 2,20.5 2,7.5"
                fill="none" stroke="#10B981" strokeWidth="0.8" opacity="0.5" />
              <polygon points="14,5 22,9.5 22,18.5 14,23 6,18.5 6,9.5"
                fill="none" stroke="#14B8A6" strokeWidth="0.5" opacity="0.3" />
              <circle cx="14" cy="14" r="3" fill="#10B981" opacity="0.6" />
            </svg>
            {/* Pulse dot */}
            <div
              className="absolute -bottom-0.5 -right-0.5 w-2.5 h-2.5 rounded-full border border-gray-950"
              style={{ backgroundColor: colors.dot, boxShadow: `0 0 6px ${colors.glow}` }}
            />
          </div>
          <div>
            <h2 className="text-sm font-semibold text-white/90 tracking-wide">VBV Voice</h2>
            <p className="text-[10px] text-white/30 font-mono">{label}</p>
          </div>
        </div>
      </div>

      {/* ── Main Content ───────────────────────────────────── */}
      <div className="relative flex flex-col items-center gap-8 w-full max-w-lg px-6">

        {/* ── Central Orb + Visualizer ───────────────────── */}
        <div className="relative w-64 h-64 flex items-center justify-center">
          {/* Outer pulsing ring */}
          <div
            className="absolute inset-0 rounded-full transition-all duration-1000"
            style={{
              boxShadow: `0 0 40px 8px ${colors.glow}, 0 0 80px 16px ${colors.glow}`,
              opacity: agentState === 'speaking' || agentState === 'listening' ? 0.6 : 0.2,
            }}
          />

          {/* SVG rings */}
          <svg className="absolute inset-0 w-full h-full" viewBox="0 0 256 256">
            {/* Outer dashed ring */}
            <circle cx="128" cy="128" r="124" fill="none" stroke={colors.ring} strokeWidth="0.5"
              strokeDasharray="3 9" opacity="0.2">
              <animateTransform attributeName="transform" type="rotate"
                values="0 128 128;360 128 128" dur="20s" repeatCount="indefinite" />
            </circle>
            {/* Middle ring */}
            <circle cx="128" cy="128" r="108" fill="none" stroke={colors.ring} strokeWidth="0.8"
              opacity="0.15">
              <animateTransform attributeName="transform" type="rotate"
                values="360 128 128;0 128 128" dur="15s" repeatCount="indefinite" />
            </circle>
            {/* Inner glow circle */}
            <circle cx="128" cy="128" r="88" fill="none" stroke={colors.ring} strokeWidth="1.2"
              opacity={agentState === 'speaking' ? 0.4 : agentState === 'listening' ? 0.3 : 0.1}>
              <animate attributeName="r" values="85;91;85" dur="3s" repeatCount="indefinite" />
            </circle>
            {/* Small accent dots on orbital */}
            <circle cx="128" cy="4" r="2" fill={colors.dot} opacity="0.4">
              <animateTransform attributeName="transform" type="rotate"
                values="0 128 128;360 128 128" dur="8s" repeatCount="indefinite" />
            </circle>
            <circle cx="4" cy="128" r="1.5" fill={colors.dot} opacity="0.25">
              <animateTransform attributeName="transform" type="rotate"
                values="120 128 128;480 128 128" dur="12s" repeatCount="indefinite" />
            </circle>
          </svg>

          {/* BarVisualizer in the center */}
          {isStarted ? (
            <div className="relative z-10 w-40 h-20 flex items-center justify-center">
              <BarVisualizer
                state={agentState}
                barCount={7}
                track={audioTrack}
                className="lk-voice-bars"
                style={{ width: '100%', height: '100%' }}
              />
            </div>
          ) : (
            /* Idle orb before connecting */
            <div className="relative z-10 flex items-center justify-center">
              <svg width="80" height="80" viewBox="0 0 80 80" fill="none">
                <circle cx="40" cy="40" r="30" fill="url(#orb-idle)" opacity="0.8" />
                <circle cx="40" cy="40" r="30" fill="none" stroke="#10B981" strokeWidth="0.8" opacity="0.3" />
                {/* Microphone icon */}
                <rect x="36" y="28" width="8" height="14" rx="4" fill="none" stroke="#fff" strokeWidth="1.5" opacity="0.7" />
                <path d="M32 40a8 8 0 0016 0" fill="none" stroke="#fff" strokeWidth="1.5" opacity="0.7" />
                <path d="M40 48v5" stroke="#fff" strokeWidth="1.5" opacity="0.7" />
                <defs>
                  <radialGradient id="orb-idle" cx="50%" cy="40%">
                    <stop offset="0%" stopColor="#10B981" stopOpacity="0.25" />
                    <stop offset="100%" stopColor="#064E3B" stopOpacity="0.1" />
                  </radialGradient>
                </defs>
              </svg>
            </div>
          )}
        </div>

        {/* ── State Label ────────────────────────────────── */}
        <div className="flex flex-col items-center gap-1.5 -mt-2">
          <div className="flex items-center gap-2">
            <div
              className="w-2 h-2 rounded-full"
              style={{
                backgroundColor: colors.dot,
                boxShadow: `0 0 8px ${colors.glow}`,
                animation: (agentState === 'listening' || agentState === 'connecting' || agentState === 'thinking')
                  ? 'pulse 1.5s ease-in-out infinite' : 'none',
              }}
            />
            <span className="text-sm font-medium tracking-wide" style={{ color: colors.dot }}>
              {label}
            </span>
          </div>
          {userName && isStarted && (
            <p className="text-[11px] text-white/25 font-mono">
              {userName} • live session
            </p>
          )}
        </div>

        {/* ── Transcription Preview ──────────────────────── */}
        {isStarted && transcriptions.length > 0 && (
          <div className="w-full">
            <button
              onClick={() => setShowTranscript((v) => !v)}
              className="w-full flex items-center justify-center gap-1.5 text-[11px] text-white/30 hover:text-white/50 transition-colors mb-2"
            >
              <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth="1">
                <path d="M2 4h8M2 6h6M2 8h7" />
              </svg>
              {showTranscript ? 'Hide transcript' : 'Show transcript'}
            </button>
            {showTranscript && (
              <div
                ref={transcriptRef}
                className="max-h-32 overflow-y-auto rounded-xl bg-white/5 border border-white/5 px-4 py-3 space-y-1.5 scrollbar-thin"
              >
                {transcriptions.map((seg, i) => (
                  <p key={i} className={`text-xs leading-relaxed ${
                    seg.isAgent ? 'text-emerald-300/70' : 'text-white/50'
                  }`}>
                    <span className="font-mono text-[9px] text-white/20 mr-1.5">
                      {seg.isAgent ? 'AI' : 'You'}
                    </span>
                    {seg.text}
                  </p>
                ))}
              </div>
            )}
          </div>
        )}

        {/* ── Controls ───────────────────────────────────── */}
        <div className="flex flex-col items-center gap-3">
          <div className="flex items-center gap-4">
          {!isStarted ? (
            /* ── Start Button ── */
            <button
              onClick={handleStart}
              className="group relative px-8 py-4 rounded-2xl bg-gradient-to-br from-emerald-500 to-green-600 text-white font-semibold text-sm shadow-lg shadow-emerald-500/20 hover:shadow-emerald-500/40 hover:scale-105 active:scale-95 transition-all"
            >
              {/* Button glow ring */}
              <div className="absolute -inset-px rounded-2xl bg-gradient-to-br from-emerald-400/20 to-green-400/20 opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none" />
              <span className="relative flex items-center gap-2">
                <svg width="18" height="18" viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <rect x="6" y="3" width="6" height="8" rx="3" />
                  <path d="M4 9a5 5 0 0010 0" />
                  <path d="M9 14v2" />
                </svg>
                Start Voice Session
              </span>
            </button>
          ) : (
            <>
              {/* ── Mic Toggle ── */}
              <TrackToggle
                source={Track.Source.Microphone}
                className="relative w-14 h-14 rounded-full flex items-center justify-center bg-white/10 hover:bg-white/15 text-white/80 hover:text-white transition-all border border-white/5 hover:border-white/10"
              />

              {/* ── End Call ── */}
              <button
                onClick={handleEnd}
                className="relative w-14 h-14 rounded-full flex items-center justify-center bg-red-500/15 hover:bg-red-500/25 text-red-400 hover:text-red-300 transition-all border border-red-500/10 hover:border-red-500/20"
                aria-label="End voice session"
              >
                <svg width="20" height="20" viewBox="0 0 20 20" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round">
                  <path d="M2 8c0-1 2-4 8-4s8 3 8 4v1c0 1-1 2-2 2h-1l-1-3h-2v4h-4V8H6l-1 3H4c-1 0-2-1-2-2V8z" />
                </svg>
              </button>
            </>
          )}
          </div>

          {/* Inline error display */}
          {startError && (
            <p className="text-red-400 text-xs text-center max-w-xs px-3 py-1.5 rounded-lg bg-red-500/10 border border-red-500/20">
              {startError}
            </p>
          )}
        </div>
      </div>

      {/* ── Footer ─────────────────────────────────────────── */}
      <div className="absolute bottom-6 left-0 right-0 text-center">
        <p className="text-[10px] text-white/15 font-mono">
          Powered by LiveKit • Deepgram Nova-2 • OpenAI
        </p>
      </div>

      {/* ── Custom CSS for BarVisualizer ───────────────────── */}
      <style>{`
        .lk-voice-bars {
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 6px;
        }
        .lk-voice-bars .lk-audio-bar {
          width: 6px;
          border-radius: 3px;
          background: rgba(255,255,255,0.12);
          transition: height 0.12s ease, background 0.3s ease;
          min-height: 8px;
        }
        .lk-voice-bars .lk-audio-bar.lk-highlighted {
          background: linear-gradient(to top, #10B981, #06B6D4);
          box-shadow: 0 0 8px rgba(16,185,129,0.3);
        }
        @keyframes pulse {
          0%, 100% { opacity: 0.6; transform: scale(1); }
          50% { opacity: 1; transform: scale(1.3); }
        }
      `}</style>
    </div>
  );
}
