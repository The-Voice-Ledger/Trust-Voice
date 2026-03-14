import { useState, useRef, useEffect, useCallback, lazy, Suspense, Component } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { textAgent } from '../api/voice';
import useAuthStore from '../stores/authStore';
import useVoiceStore from '../stores/voiceStore';
import Markdown from 'react-markdown';
import ProgressBar from '../components/ProgressBar';
import {
  HiOutlinePaperAirplane, HiOutlineSparkles,
  HiOutlineCheckBadge, HiOutlineMapPin,
  HiOutlineChartBarSquare, HiOutlineUserGroup,
  HiOutlineArrowRight, HiOutlineClock,
  HiOutlineXMark, HiOutlineMagnifyingGlass,
  HiOutlineGlobeAlt, HiOutlineQuestionMarkCircle,
  HiOutlineSpeakerWave, HiOutlineSpeakerXMark,
  HiOutlineMicrophone,
} from '../components/icons';
import HexIcon from '../components/HexIcon';

// Lazy-load LiveVoicePanel so its heavy LiveKit deps don't block the
// initial render or inject global CSS that conflicts with Tailwind.
const LiveVoicePanel = lazy(() => import('../components/LiveVoicePanel'));

// ── Error boundary — prevents white-screen crashes ─────────────
class VoicePanelErrorBoundary extends Component {
  state = { hasError: false, error: null };
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  componentDidCatch(err, info) {
    console.error('[VoicePanelErrorBoundary]', err, info);
  }
  render() {
    if (this.state.hasError) {
      return (
        <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-gray-950/95 backdrop-blur-xl">
          <div className="text-center space-y-4 max-w-sm px-6">
            <div className="w-12 h-12 mx-auto rounded-full bg-red-500/20 flex items-center justify-center">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="#F87171" strokeWidth="2" strokeLinecap="round">
                <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
              </svg>
            </div>
            <p className="text-white/80 text-sm">Voice session encountered an error</p>
            <p className="text-white/30 text-xs font-mono">{this.state.error?.message}</p>
            <button
              onClick={() => this.setState({ hasError: false, error: null })}
              className="px-4 py-2 rounded-lg bg-white/10 text-white/70 text-sm hover:bg-white/15 transition-colors"
            >
              Dismiss
            </button>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ── Chat message store (local, per-session) ────────────────────
function useChat() {
  const [messages, setMessages] = useState([]);
  const [conversationId, setConversationId] = useState(null);
  const [loading, setLoading] = useState(false);

  const addMessage = useCallback((msg) => {
    setMessages((prev) => [...prev, { ...msg, id: Date.now() + Math.random() }]);
  }, []);

  const clear = useCallback(() => {
    setMessages([]);
    setConversationId(null);
  }, []);

  return { messages, conversationId, setConversationId, loading, setLoading, addMessage, clear };
}

// ── Main Page ──────────────────────────────────────────────────
export default function Assistant() {
  const { t } = useTranslation();
  const user = useAuthStore((s) => s.user);
  const language = useVoiceStore((s) => s.language);
  const { messages, conversationId, setConversationId, loading, setLoading, addMessage, clear } = useChat();
  const [input, setInput] = useState('');
  const [autoSpeak, setAutoSpeak] = useState(true);
  const [liveVoiceOpen, setLiveVoiceOpen] = useState(false);
  const scrollRef = useRef(null);
  const inputRef = useRef(null);
  const audioRef = useRef(null);

  const userId = user?.id || user?.telegram_user_id || 'web_anonymous';
  const [searchParams, setSearchParams] = useSearchParams();

  // Auto-scroll on new messages
  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages, loading]);

  // ── Play TTS audio ───────────────────────────────────────────
  const playAudio = useCallback(async (url) => {
    if (!url || !autoSpeak) return;
    try {
      // Stop any current playback
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current = null;
      }
      const audio = new Audio(url);
      audioRef.current = audio;
      await audio.play();
      await new Promise((resolve) => {
        audio.onended = resolve;
        audio.onerror = resolve;
      });
      audioRef.current = null;
    } catch { /* non-fatal */ }
  }, [autoSpeak]);

  // Stop playback helper
  const stopAudio = useCallback(() => {
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current = null;
    }
  }, []);

  // ── Send text message ────────────────────────────────────────
  const sendText = useCallback(async (text) => {
    if (!text.trim() || loading) return;

    addMessage({ role: 'user', text: text.trim() });
    setInput('');
    setLoading(true);

    try {
      const res = await textAgent(text.trim(), userId, language, conversationId);
      if (res.conversation_id) setConversationId(res.conversation_id);

      addMessage({
        role: 'assistant',
        text: res.response_text,
        responseType: res.response_type || 'text',
        data: res.data || {},
        audioUrl: res.audio_url,
        toolsUsed: res.tools_used || [],
      });

      // Play TTS
      await playAudio(res.audio_url);
    } catch (err) {
      addMessage({ role: 'assistant', text: err.message || 'Something went wrong. Please try again.', responseType: 'error' });
    } finally {
      setLoading(false);
    }
  }, [loading, userId, language, conversationId, addMessage, setConversationId, setLoading, playAudio]);

  // Deep-link: ?campaign=<id> auto-asks about the campaign
  const deepLinkHandled = useRef(false);
  useEffect(() => {
    const campaignId = searchParams.get('campaign');
    if (campaignId && !deepLinkHandled.current) {
      deepLinkHandled.current = true;
      setSearchParams({}, { replace: true });
      const timeout = setTimeout(() => {
        sendText(`Tell me about campaign #${campaignId}`);
      }, 300);
      return () => clearTimeout(timeout);
    }
  }, [searchParams, setSearchParams, sendText]);

  // ── Submit on Enter ──────────────────────────────────────────
  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendText(input);
    }
  };

  // ── Open LiveKit voice panel ──────────────────────────────────
  const openVoice = useCallback(() => {
    stopAudio();
    setLiveVoiceOpen(true);
  }, [stopAudio]);

  // ── Render ───────────────────────────────────────────────────
  return (
    <div className="relative max-w-3xl mx-auto px-4 sm:px-6 flex flex-col h-full">
      {/* Background — Ukulima landscape: rolling hills, moringa leaves, warm sun */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none -z-10" viewBox="0 0 600 800" fill="none" preserveAspectRatio="xMidYMax slice">
        <defs>
          <radialGradient id="asst-sun" cx="85%" cy="12%" r="20%">
            <stop offset="0%" stopColor="#D97706" stopOpacity="0.08" />
            <stop offset="60%" stopColor="#F59E0B" stopOpacity="0.03" />
            <stop offset="100%" stopColor="transparent" />
          </radialGradient>
          <radialGradient id="asst-orb1"><stop offset="0%" stopColor="#059669" stopOpacity="0.05" /><stop offset="100%" stopColor="transparent" /></radialGradient>
          <linearGradient id="asst-hill" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="#059669" stopOpacity="0.06" />
            <stop offset="100%" stopColor="#78716C" stopOpacity="0.03" />
          </linearGradient>
        </defs>
        {/* Warm sun glow — top right */}
        <rect width="600" height="800" fill="url(#asst-sun)" />
        {/* Soft emerald orb — top left */}
        <circle cx="60" cy="100" r="120" fill="url(#asst-orb1)" />
        {/* Topography contour lines — earthy */}
        <g stroke="#78716C" strokeWidth="0.6" fill="none" opacity="0.04">
          <path d="M-20 600C60 560 180 640 300 600s240-80 620-20" />
          <path d="M-20 640C80 600 160 680 280 640s200-60 640-10" />
          <path d="M-20 680C40 640 200 720 320 680s220-100 600-30" />
        </g>
        {/* Rolling hills at bottom */}
        <path d="M0 750 Q100 700 200 720 Q350 690 450 710 Q550 695 600 720 L600 800 L0 800Z" fill="url(#asst-hill)" />
        <path d="M0 770 Q150 740 300 755 Q450 735 600 760 L600 800 L0 800Z" fill="#059669" opacity="0.03" />
        {/* Moringa leaf shapes — scattered, very subtle */}
        <g opacity="0.04" fill="#059669">
          <ellipse cx="520" cy="180" rx="8" ry="3" transform="rotate(-30 520 180)" />
          <ellipse cx="530" cy="172" rx="6" ry="2.5" transform="rotate(-50 530 172)" />
          <ellipse cx="525" cy="190" rx="7" ry="2.5" transform="rotate(-10 525 190)" />
          <ellipse cx="80" cy="350" rx="7" ry="2.5" transform="rotate(20 80 350)" />
          <ellipse cx="72" cy="358" rx="6" ry="2" transform="rotate(40 72 358)" />
          <ellipse cx="90" cy="355" rx="5" ry="2" transform="rotate(-5 90 355)" />
        </g>
      </svg>

      {/* ── Compact Header ───────────────────────────── */}
      <div className="relative flex items-center justify-between py-2 flex-shrink-0 border-b border-stone-200/50">
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-emerald-500/25 via-amber-500/15 to-transparent" />
        <div className="flex items-center gap-2.5">
          <div className="relative">
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-600 to-amber-600 flex items-center justify-center shadow-sm shadow-amber-200/30">
              <HiOutlineSparkles className="w-3.5 h-3.5 text-white" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-2 h-2 rounded-full bg-amber-400 border-[1.5px] border-white" />
          </div>
          <h1 className="text-sm font-bold text-stone-800 font-display">{t('assistant.title', 'VBV Assistant')}</h1>
        </div>
        <div className="flex items-center gap-1">
          <button
            onClick={() => { setAutoSpeak((v) => !v); stopAudio(); }}
            className={`p-1.5 rounded-lg transition-all ${
              autoSpeak
                ? 'text-amber-600 hover:bg-amber-50'
                : 'text-stone-300 hover:bg-stone-50'
            }`}
            title={autoSpeak ? 'Voice responses ON' : 'Voice responses OFF'}
          >
            {autoSpeak
              ? <HiOutlineSpeakerWave className="w-4 h-4" />
              : <HiOutlineSpeakerXMark className="w-4 h-4" />
            }
          </button>
          {messages.length > 0 && (
            <button
              onClick={() => { clear(); stopAudio(); }}
              className="p-1.5 rounded-lg text-stone-300 hover:text-red-500 hover:bg-red-50 transition-all"
              title="New conversation"
            >
              <HiOutlineXMark className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 py-3 scrollbar-thin">
        {messages.length === 0 && !loading && (
          <WelcomeScreen onSuggestion={sendText} onVoice={openVoice} t={t} />
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} msg={msg} onPlayAudio={playAudio} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="w-8 h-8 flex-shrink-0 rounded-lg bg-gradient-to-br from-emerald-600 to-amber-600 flex items-center justify-center shadow-sm shadow-amber-200/30">
              <HiOutlineSparkles className="w-4 h-4 text-white animate-pulse" />
            </div>
            <div className="relative bg-white/80 backdrop-blur-sm rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-stone-100/80 overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/30 via-amber-500/20 to-transparent" />
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-amber-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="relative flex-shrink-0 pb-3 pt-2 border-t border-stone-200/50">
        <div className="absolute -top-px left-0 right-0 h-px bg-gradient-to-r from-emerald-500/20 via-amber-500/15 to-transparent" />

        <div className="flex items-end gap-2 mt-1.5">
          {/* Voice button — opens LiveKit voice panel */}
          <button
            onClick={openVoice}
            className="flex-shrink-0 w-11 h-11 rounded-2xl flex items-center justify-center transition-all duration-200 bg-gradient-to-br from-emerald-500 via-green-600 to-amber-600 text-white shadow-md shadow-amber-200/40 hover:shadow-lg hover:shadow-amber-300/50 hover:scale-105 active:scale-95"
            aria-label="Start voice conversation"
          >
            <HiOutlineMicrophone className="w-5 h-5" />
          </button>

          {/* Text input */}
          <div className="flex-1 relative">
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('assistant.placeholder', 'Type a message or tap the mic...')}
              rows={1}
              className="w-full resize-none rounded-2xl border border-stone-200/70 bg-white/60 backdrop-blur-sm px-4 py-2.5 pr-11 text-sm text-stone-900 placeholder-stone-400 focus:outline-none focus:ring-2 focus:ring-amber-500/15 focus:border-amber-300/60 focus:bg-white/80 shadow-sm transition-all"
              style={{ maxHeight: '120px' }}
              disabled={loading}
            />
            <button
              onClick={() => sendText(input)}
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-1.5 p-2 rounded-xl bg-gradient-to-br from-emerald-600 to-amber-600 text-white disabled:opacity-20 disabled:cursor-not-allowed hover:shadow-md active:scale-95 transition-all shadow-sm"
              aria-label="Send"
            >
              <HiOutlinePaperAirplane className="w-4 h-4" />
            </button>
          </div>
        </div>
        <p className="text-[10px] text-stone-300 text-center mt-1.5 select-none">
          {t('assistant.disclaimer', 'AI assistant. Verify important information independently')}
        </p>
      </div>

      {/* ── Live Voice Panel (full-screen overlay) ──────────── */}
      {liveVoiceOpen && (
        <VoicePanelErrorBoundary>
          <Suspense fallback={
            <div className="fixed inset-0 z-50 flex items-center justify-center bg-gray-950/95 backdrop-blur-xl">
              <div className="flex flex-col items-center gap-3">
                <div className="w-8 h-8 border-2 border-emerald-400 border-t-transparent rounded-full animate-spin" />
                <p className="text-white/40 text-xs">Loading voice session…</p>
              </div>
            </div>
          }>
            <LiveVoicePanel
              userId={userId}
              userName={user?.full_name || user?.username || 'Guest'}
              userRole={user?.role || 'DONOR'}
              onClose={() => setLiveVoiceOpen(false)}
            />
          </Suspense>
        </VoicePanelErrorBoundary>
      )}
    </div>
  );
}


// ── Welcome Screen — Voice-First Hero (Ukulima Theme) ──────────
function WelcomeScreen({ onSuggestion, onVoice, t }) {
  const suggestions = [
    { text: 'Tell me about Moringa Oasis Zimbabwe', Icon: HiOutlineMagnifyingGlass, color: 'emerald' },
    { text: 'How much has been raised this month?', Icon: HiOutlineChartBarSquare, color: 'amber' },
    { text: 'Show me water projects', Icon: HiOutlineGlobeAlt, color: 'sky' },
    { text: "What can you do?", Icon: HiOutlineQuestionMarkCircle, color: 'stone' },
  ];

  const borderMap = {
    emerald: 'hover:border-emerald-300/60',
    amber: 'hover:border-amber-300/60',
    sky: 'hover:border-sky-300/60',
    stone: 'hover:border-stone-300/60',
  };
  const iconColorMap = {
    emerald: 'text-emerald-600',
    amber: 'text-amber-600',
    sky: 'text-sky-500',
    stone: 'text-stone-500',
  };

  return (
    <div className="flex flex-col items-center justify-center flex-1 min-h-0 py-6 text-center">

      {/* ── Voice Hero Orb — warm emerald/amber gradient ─── */}
      <div className="relative mb-8 group cursor-pointer" onClick={onVoice}>
        {/* Outer warm pulse rings */}
        <div className="absolute inset-0 -m-6 rounded-full bg-amber-400/8 animate-[ping_3s_ease-in-out_infinite]" />
        <div className="absolute inset-0 -m-4 rounded-full bg-emerald-500/6 animate-[ping_3s_ease-in-out_1s_infinite]" />
        {/* Orbit rings with moringa-leaf inspired dashes */}
        <svg className="absolute -inset-10 w-[calc(100%+80px)] h-[calc(100%+80px)] pointer-events-none" viewBox="0 0 180 180" fill="none">
          <circle cx="90" cy="90" r="80" stroke="url(#uk-ring1)" strokeWidth="0.5" strokeDasharray="5 8" opacity="0.25">
            <animateTransform attributeName="transform" type="rotate" values="0 90 90;360 90 90" dur="25s" repeatCount="indefinite" />
          </circle>
          <circle cx="90" cy="90" r="65" stroke="url(#uk-ring2)" strokeWidth="0.4" strokeDasharray="3 10" opacity="0.15">
            <animateTransform attributeName="transform" type="rotate" values="360 90 90;0 90 90" dur="18s" repeatCount="indefinite" />
          </circle>
          {/* Orbiting amber dot (like a seed) */}
          <circle r="2.5" fill="#D97706" opacity="0.5">
            <animateMotion dur="25s" repeatCount="indefinite" path="M90,10 A80,80 0 1,1 89.99,10" />
          </circle>
          {/* Orbiting emerald dot (opposite) */}
          <circle r="1.8" fill="#059669" opacity="0.4">
            <animateMotion dur="18s" repeatCount="indefinite" path="M90,25 A65,65 0 1,0 90.01,25" />
          </circle>
          <defs>
            <linearGradient id="uk-ring1" x1="0%" y1="0%" x2="100%" y2="100%">
              <stop offset="0%" stopColor="#059669" />
              <stop offset="100%" stopColor="#D97706" />
            </linearGradient>
            <linearGradient id="uk-ring2" x1="100%" y1="0%" x2="0%" y2="100%">
              <stop offset="0%" stopColor="#D97706" />
              <stop offset="100%" stopColor="#059669" />
            </linearGradient>
          </defs>
        </svg>
        {/* Main orb — emerald heart, amber rim */}
        <div className="relative w-24 h-24 sm:w-28 sm:h-28 rounded-full bg-gradient-to-br from-emerald-600 via-green-600 to-amber-500 flex items-center justify-center shadow-2xl shadow-amber-500/20 group-hover:shadow-amber-500/40 group-hover:scale-105 transition-all duration-300">
          {/* Inner glass ring */}
          <div className="absolute inset-1.5 rounded-full bg-gradient-to-br from-white/15 via-transparent to-amber-400/10" />
          {/* Warm inner glow */}
          <div className="absolute inset-0 rounded-full bg-gradient-to-t from-amber-500/10 to-transparent" />
          {/* Mic icon */}
          <HiOutlineMicrophone className="relative w-10 h-10 sm:w-12 sm:h-12 text-white drop-shadow-lg" />
          {/* Bottom shimmer — warm */}
          <div className="absolute bottom-0 left-1/2 -translate-x-1/2 w-16 h-1 rounded-full bg-amber-300/25 blur-sm" />
        </div>
      </div>

      {/* Text — warmer tone */}
      <h2 className="text-xl sm:text-2xl font-bold text-stone-800 mb-1.5 font-display">
        {t('assistant.welcome', 'How can I help?')}
      </h2>
      <p className="text-sm text-stone-500 max-w-xs mb-1">
        {t('assistant.welcome_voice_cta', 'Tap the orb to start a voice conversation')}
      </p>
      <p className="text-xs text-stone-400 mb-6">
        {t('assistant.welcome_or_type', 'or type below')}
      </p>

      {/* Decorative divider — emerald ◆ amber */}
      <div className="flex items-center gap-3 max-w-[160px] mx-auto mb-6">
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-emerald-400/35 to-amber-400/20" />
        <svg width="6" height="6" viewBox="0 0 6 6" fill="none">
          <path d="M3 0L6 3L3 6L0 3Z" fill="url(#uk-diamond)" />
          <defs><linearGradient id="uk-diamond" x1="0" y1="0" x2="6" y2="6"><stop stopColor="#059669" stopOpacity="0.4" /><stop offset="1" stopColor="#D97706" stopOpacity="0.4" /></linearGradient></defs>
        </svg>
        <div className="flex-1 h-px bg-gradient-to-r from-amber-400/20 via-emerald-400/35 to-transparent" />
      </div>

      {/* ── Suggestion chips — warm cards ──────────── */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 w-full max-w-md">
        {suggestions.map(({ text, Icon, color }) => (
          <button
            key={text}
            onClick={() => onSuggestion(text)}
            className={`group relative flex items-center gap-2.5 px-3.5 py-2.5 rounded-xl border border-stone-100 bg-white/60 backdrop-blur-sm text-sm text-stone-600 ${borderMap[color]} hover:text-stone-800 hover:bg-white/80 transition-all text-left shadow-sm hover:shadow-md`}
          >
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/10 via-amber-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <Icon className={`w-4 h-4 flex-shrink-0 ${iconColorMap[color]} transition-colors`} />
            <span className="leading-snug text-[13px]">{text}</span>
            <HiOutlineArrowRight className="w-3.5 h-3.5 ml-auto text-stone-200 group-hover:text-amber-400 transition-colors flex-shrink-0" />
          </button>
        ))}
      </div>
    </div>
  );
}


// ── Chat Message ───────────────────────────────────────────────
function ChatMessage({ msg, onPlayAudio }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end gap-3">
        <div className="relative max-w-[85%] bg-gradient-to-br from-emerald-600 via-emerald-700 to-amber-700 text-white rounded-2xl rounded-tr-md px-4 py-3 shadow-sm overflow-hidden">
          {/* Subtle inner glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
          <p className="relative text-sm whitespace-pre-wrap">{msg.text}</p>
          {msg.isVoice && (
            <div className="relative flex items-center gap-1 mt-1.5 text-emerald-200 text-[10px]">
              <HiOutlineMicrophone className="w-3 h-3" />
              voice
            </div>
          )}
        </div>
      </div>
    );
  }

  // Assistant message
  return (
    <div className="flex gap-3">
      <div className="w-7 h-7 flex-shrink-0 mt-0.5 rounded-lg bg-gradient-to-br from-emerald-600 to-amber-600 flex items-center justify-center shadow-sm shadow-amber-200/30">
        <HiOutlineSparkles className="w-3.5 h-3.5 text-white" />
      </div>
      <div className="max-w-[85%] space-y-2">
        {/* Text response */}
        {msg.text && (
          <div className="relative bg-white/75 backdrop-blur-sm rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-stone-100/70 overflow-hidden">
            {/* Top accent */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/25 via-amber-500/15 to-transparent" />
            <div className="relative text-sm text-stone-700 leading-relaxed prose prose-sm prose-stone max-w-none
                prose-p:my-1 prose-ol:my-1 prose-ul:my-1 prose-li:my-0.5
                prose-strong:text-stone-900 prose-strong:font-semibold
                prose-a:text-emerald-600 prose-a:no-underline hover:prose-a:underline">
              <Markdown>
                {msg.text}
              </Markdown>
            </div>
            {/* Replay audio button */}
            {msg.audioUrl && (
              <button
                onClick={() => onPlayAudio(msg.audioUrl)}
                className="relative mt-2 flex items-center gap-1.5 text-[11px] text-emerald-500 hover:text-emerald-700 transition"
              >
                <HiOutlineSpeakerWave className="w-3.5 h-3.5" />
                Play response
              </button>
            )}
          </div>
        )}

        {/* Rich data renderers */}
        {msg.responseType === 'campaign_list' && msg.data?.campaigns && (
          <CampaignListCard campaigns={msg.data.campaigns} />
        )}
        {msg.responseType === 'campaign_detail' && msg.data?.campaign && (
          <CampaignDetailCard campaign={msg.data.campaign} />
        )}
        {msg.responseType === 'donation_confirmation' && (
          <DonationConfirmationCard data={msg.data} />
        )}
        {msg.responseType === 'donation_history' && msg.data?.donations && (
          <DonationHistoryCard donations={msg.data.donations} />
        )}
        {msg.responseType === 'analytics_summary' && msg.data?.stats && (
          <AnalyticsSummaryCard stats={msg.data.stats} />
        )}
      </div>
    </div>
  );
}


// ── Rich Response Cards ────────────────────────────────────────

function CampaignListCard({ campaigns }) {
  if (!campaigns.length) return null;
  return (
    <div className="space-y-2">
      {campaigns.slice(0, 5).map((c) => (
        <Link
          key={c.id}
          to={`/campaign/${c.id}`}
          className="group relative flex items-center gap-3 bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-100/80 p-3 hover:border-emerald-200 hover:shadow-md transition-all overflow-hidden"
        >
          {/* Top line accent */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/15 via-green-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          {/* Corner decoration */}
          <svg className="absolute -top-1 -right-1 w-12 h-12 pointer-events-none" viewBox="0 0 48 48" fill="none">
            <circle cx="36" cy="12" r="8" stroke="#10B981" strokeWidth="0.4" opacity="0.05" />
            <circle cx="36" cy="12" r="3" stroke="#10B981" strokeWidth="0.3" strokeDasharray="1 2" opacity="0.04" />
          </svg>
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-emerald-50 to-green-50 flex items-center justify-center flex-shrink-0 text-emerald-600 font-bold text-sm border border-emerald-100/50">
            #{c.id}
          </div>
          <div className="relative flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-gray-900 truncate group-hover:text-emerald-600 transition-colors">
              {c.title}
            </h4>
            <div className="flex items-center gap-2 mt-0.5">
              <ProgressBar percentage={c.progress_pct} className="flex-1" />
              <span className="text-[10px] font-medium text-emerald-600 flex-shrink-0">{c.progress_pct}%</span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-[10px] text-gray-400">
              {c.category && <span className="capitalize">{c.category}</span>}
              {c.location && c.location !== 'N/A' && (
                <span className="flex items-center gap-0.5"><HiOutlineMapPin className="w-3 h-3" />{c.location}</span>
              )}
              <span>${fmt(c.raised_usd)} / ${fmt(c.goal_usd)}</span>
            </div>
          </div>
          <HiOutlineArrowRight className="relative w-4 h-4 text-gray-300 group-hover:text-emerald-500 group-hover:translate-x-0.5 transition-all flex-shrink-0" />
        </Link>
      ))}
      {campaigns.length > 5 && (
        <p className="text-[10px] text-gray-400 text-center">+{campaigns.length - 5} more campaigns</p>
      )}
    </div>
  );
}

function CampaignDetailCard({ campaign }) {
  const c = campaign;
  return (
    <Link
      to={`/campaign/${c.id}`}
      className="group relative block bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-100/80 overflow-hidden hover:border-emerald-200 hover:shadow-md transition-all"
    >
      {/* Gradient banner */}
      <div className="relative h-10 bg-gradient-to-r from-emerald-500/8 via-green-500/5 to-transparent">
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/30 via-green-500/20 to-transparent" />
        <svg className="absolute right-2 top-0 w-16 h-10 pointer-events-none" viewBox="0 0 64 40" fill="none">
          <circle cx="48" cy="20" r="12" stroke="#10B981" strokeWidth="0.4" opacity="0.06" />
          <path d="M42 20 L48 14 L54 20 L48 26 Z" stroke="#14B8A6" strokeWidth="0.3" opacity="0.05" />
        </svg>
      </div>
      <div className="p-4 -mt-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h4 className="font-semibold text-gray-900 group-hover:text-emerald-600 transition-colors">{c.title}</h4>
            <p className="text-xs text-gray-500 mt-1 line-clamp-2">{c.description}</p>
          </div>
          <span className={`text-[10px] font-bold px-2 py-1 rounded-lg flex-shrink-0 ${
            c.status === 'active' ? 'bg-green-50 text-green-700' : 'bg-gray-100 text-gray-500'
          }`}>
            {c.status}
          </span>
        </div>
        <div className="mt-3">
          <ProgressBar percentage={c.progress_pct} className="mb-2" />
          <div className="flex items-center justify-between text-xs">
            <span className="font-bold text-emerald-600">${fmt(c.raised_usd)}</span>
            <span className="text-gray-400">of ${fmt(c.goal_usd)}</span>
          </div>
        </div>
        <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
          {c.category && <span className="capitalize bg-gray-50 px-2 py-0.5 rounded">{c.category}</span>}
          {c.location && c.location !== 'N/A' && (
            <span className="flex items-center gap-0.5"><HiOutlineMapPin className="w-3 h-3" />{c.location}</span>
          )}
        </div>
      </div>
    </Link>
  );
}

function DonationConfirmationCard({ data }) {
  return (
    <div className="relative rounded-2xl bg-gradient-to-br from-green-50 to-emerald-50 border border-green-200/80 p-4 overflow-hidden">
      {/* Celebration SVG */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none" viewBox="0 0 300 120" fill="none">
        <circle cx="260" cy="20" r="20" stroke="#10B981" strokeWidth="0.4" opacity="0.08" />
        <circle cx="260" cy="20" r="8" stroke="#10B981" strokeWidth="0.3" strokeDasharray="2 3" opacity="0.06" />
        <path d="M30 100 L35 90 L40 100" stroke="#10B981" strokeWidth="0.5" opacity="0.06" />
        <circle cx="20" cy="30" r="2" fill="#10B981" opacity="0.08"><animate attributeName="opacity" values="0.08;0.15;0.08" dur="2s" repeatCount="indefinite" /></circle>
        <circle cx="280" cy="90" r="1.5" fill="#059669" opacity="0.08"><animate attributeName="opacity" values="0.08;0.14;0.08" dur="2.5s" repeatCount="indefinite" /></circle>
      </svg>
      <div className="relative flex items-center gap-2 mb-3">
        <HexIcon Icon={HiOutlineCheckBadge} accent="#059669" size="xs" bespoke="check" />
        <span className="font-semibold text-green-800 text-sm">Donation Initiated</span>
      </div>
      {data.donation_id && (
        <p className="relative text-xs text-gray-500 mb-3 font-mono bg-green-100/50 px-2 py-1 rounded inline-block">ID: {String(data.donation_id).slice(0, 8)}…</p>
      )}
      <div className="relative grid grid-cols-2 gap-3 text-xs">
        {data.campaign_title && (
          <div className="bg-white/60 rounded-lg p-2"><span className="text-gray-400 text-[10px]">Campaign</span><p className="font-medium text-gray-700 mt-0.5">{data.campaign_title}</p></div>
        )}
        {data.amount && (
          <div className="bg-white/60 rounded-lg p-2"><span className="text-gray-400 text-[10px]">Amount</span><p className="font-medium text-gray-700 mt-0.5">{data.amount} {data.currency || 'USD'}</p></div>
        )}
        {data.payment_method && (
          <div className="bg-white/60 rounded-lg p-2"><span className="text-gray-400 text-[10px]">Method</span><p className="font-medium text-gray-700 mt-0.5 uppercase">{data.payment_method}</p></div>
        )}
      </div>
      {data.instructions && (
        <p className="relative text-xs text-green-700 mt-3 bg-green-100/50 px-3 py-2 rounded-lg">{data.instructions}</p>
      )}
    </div>
  );
}

function DonationHistoryCard({ donations }) {
  if (!donations.length) return null;
  return (
    <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-100/80 overflow-hidden">
      <div className="relative px-4 py-2.5 bg-gradient-to-r from-gray-50 to-transparent border-b border-gray-100/80">
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-emerald-500/15 via-green-500/10 to-transparent" />
        <span className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
          <HiOutlineClock className="w-3.5 h-3.5" />
          Donation History
        </span>
      </div>
      <div className="divide-y divide-gray-50">
        {donations.slice(0, 5).map((d) => (
          <div key={d.id} className="relative px-4 py-2.5 flex items-center justify-between gap-3 group hover:bg-gray-50/50 transition-colors">
            <svg className="absolute bottom-0 right-0 w-8 h-8 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" viewBox="0 0 32 32" fill="none">
              <path d="M32 0v32H0" stroke="#10B981" strokeWidth="0.3" opacity="0.05" />
            </svg>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">{d.campaign_title}</p>
              <p className="text-[10px] text-gray-400">{d.date ? new Date(d.date).toLocaleDateString() : ''}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-xs font-bold text-emerald-600">{d.amount} {d.currency}</p>
              <span className={`text-[10px] font-medium ${
                d.status === 'completed' ? 'text-green-600' : d.status === 'pending' ? 'text-yellow-600' : 'text-gray-400'
              }`}>
                {d.status}
              </span>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function AnalyticsSummaryCard({ stats }) {
  const items = [
    { label: 'Active Campaigns', value: stats.active_campaigns, icon: HiOutlineChartBarSquare, color: 'blue' },
    { label: 'Total Donated', value: `$${fmt(stats.total_raised_usd)}`, icon: HiOutlineCheckBadge, color: 'green' },
    { label: 'Total Donations', value: stats.total_donations, icon: HiOutlineArrowRight, color: 'green' },
    { label: 'Total Donors', value: stats.total_donors, icon: HiOutlineUserGroup, color: 'amber' },
  ];

  const colorMap = {
    blue:  { bg: 'bg-emerald-50', text: 'text-emerald-600', stroke: '#10B981' },
    green: { bg: 'bg-green-50', text: 'text-green-600', stroke: '#16A34A' },
    amber: { bg: 'bg-amber-50', text: 'text-amber-600', stroke: '#D97706' },
  };

  const svgByColor = {
    blue: (s) => (<>{/* bar chart */}<rect x="4" y="16" width="5" height="14" rx="1" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><rect x="13" y="10" width="5" height="20" rx="1" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><rect x="22" y="4" width="5" height="26" rx="1" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/></>),
    green: (s) => (<>{/* dollar */}<circle cx="16" cy="16" r="12" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><path d="M16 6v20M12 10.5h5.5a3 3 0 010 6H12h6a3 3 0 010 6H12" stroke={s} strokeWidth="0.5" fill="none" opacity="0.08"/></>),
    amber: (s) => (<>{/* people */}<circle cx="11" cy="10" r="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><circle cx="21" cy="10" r="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><path d="M4 26c0-4 3.5-7 7-7s7 3 7 7M16 26c0-4 3.5-7 7-7s5 3 5 7" stroke={s} strokeWidth="0.5" fill="none" opacity="0.08"/></>),
  };

  const ANALYTICS_ACCENTS = { blue: '#10B981', green: '#16A34A', amber: '#D97706' };
  const ANALYTICS_BESPS = { blue: 'chart', green: 'trending', amber: 'users' };

  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(({ label, value, icon: Icon, color }) => {
        const cm = colorMap[color];
        return (
          <div key={label} className="relative bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-100/80 p-3 overflow-hidden group hover:border-gray-200/80 transition-colors">
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-transparent via-gray-200/50 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <svg className="absolute bottom-0 right-0 w-8 h-8 pointer-events-none" viewBox="0 0 32 32" fill="none">
              {svgByColor[color]?.(cm.stroke)}
            </svg>
            <HexIcon Icon={Icon} accent={ANALYTICS_ACCENTS[color]} bespoke={ANALYTICS_BESPS[color]} size="xs" className="mb-2" />
            <p className="text-lg font-bold text-gray-900">{value}</p>
            <p className="text-[10px] text-gray-400">{label}</p>
          </div>
        );
      })}
    </div>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}
