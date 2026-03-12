import { useState, useRef, useEffect, useCallback } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { textAgent, voiceAgent } from '../api/voice';
import useAuthStore from '../stores/authStore';
import useVoiceStore from '../stores/voiceStore';
import voiceManager from '../voice/VoiceManager';
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
  const [voiceStatus, setVoiceStatus] = useState('idle'); // idle | recording | processing
  const [autoSpeak, setAutoSpeak] = useState(true);
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

  // ── Voice recording ──────────────────────────────────────────
  const startVoice = useCallback(async () => {
    try {
      stopAudio();
      setVoiceStatus('recording');
      await voiceManager.startRecording();
    } catch {
      setVoiceStatus('idle');
    }
  }, [stopAudio]);

  const stopVoice = useCallback(async () => {
    if (voiceStatus !== 'recording') return;
    setVoiceStatus('processing');

    try {
      const blob = await voiceManager.stopRecording();
      if (!blob) { setVoiceStatus('idle'); return; }

      const hasAudio = await voiceManager.hasSound(blob);
      if (!hasAudio) { setVoiceStatus('idle'); return; }

      setLoading(true);
      const res = await voiceAgent(blob, userId, language, conversationId);
      if (res.conversation_id) setConversationId(res.conversation_id);

      // Show user's transcribed message
      if (res.transcription) {
        addMessage({ role: 'user', text: res.transcription, isVoice: true });
      }

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
      addMessage({ role: 'assistant', text: err.message || 'Voice processing failed.', responseType: 'error' });
    } finally {
      setVoiceStatus('idle');
      setLoading(false);
    }
  }, [voiceStatus, userId, language, conversationId, addMessage, setConversationId, setLoading, playAudio]);

  const cancelVoice = useCallback(() => {
    voiceManager.stopRecording();
    setVoiceStatus('idle');
  }, []);

  // ── Render ───────────────────────────────────────────────────
  return (
    <div className="relative max-w-3xl mx-auto px-4 sm:px-6 flex flex-col" style={{ height: 'calc(100dvh - 8rem)' }}>
      {/* Background ambient SVG decoration */}
      <svg className="absolute inset-0 w-full h-full pointer-events-none -z-10" viewBox="0 0 600 800" fill="none" preserveAspectRatio="none">
        <circle cx="80" cy="120" r="100" fill="url(#asst-orb1)" opacity="0.04" />
        <circle cx="520" cy="680" r="120" fill="url(#asst-orb2)" opacity="0.03" />
        <defs>
          <radialGradient id="asst-orb1"><stop offset="0%" stopColor="#2563EB" /><stop offset="100%" stopColor="transparent" /></radialGradient>
          <radialGradient id="asst-orb2"><stop offset="0%" stopColor="#0D9488" /><stop offset="100%" stopColor="transparent" /></radialGradient>
        </defs>
      </svg>

      {/* ── Header ───────────────────────────── */}
      <div className="relative flex items-center justify-between py-4 flex-shrink-0 border-b border-gray-100/80">
        {/* Subtle header accent line */}
        <div className="absolute bottom-0 left-0 right-0 h-px bg-gradient-to-r from-blue-500/20 via-teal-500/20 to-transparent" />
        <div className="flex items-center gap-3">
          <div className="relative">
            <HexIcon Icon={HiOutlineSparkles} accent="#2563EB" size="sm" bespoke="sparkles" gradient gradientTo="#0D9488" spin />
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-400 border-2 border-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900 font-display">{t('assistant.title', 'TrustVoice Assistant')}</h1>
            <p className="text-xs text-gray-400">{t('assistant.subtitle', 'Search, donate, and manage by voice or text')}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Auto-speak toggle */}
          <button
            onClick={() => { setAutoSpeak((v) => !v); stopAudio(); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              autoSpeak
                ? 'bg-blue-50 text-blue-700 border-blue-200'
                : 'bg-gray-50 text-gray-400 border-gray-200'
            }`}
            title={autoSpeak ? 'Voice responses ON' : 'Voice responses OFF'}
          >
            {autoSpeak
              ? <HiOutlineSpeakerWave className="w-3.5 h-3.5" />
              : <HiOutlineSpeakerXMark className="w-3.5 h-3.5" />
            }
            {autoSpeak ? t('assistant.auto_speak', 'Auto-speak') : t('assistant.muted', 'Muted')}
          </button>
          {messages.length > 0 && (
            <button
              onClick={() => { clear(); stopAudio(); }}
              className="p-2 rounded-lg text-gray-400 hover:text-red-500 hover:bg-red-50 transition-all"
              title="New conversation"
            >
              <HiOutlineXMark className="w-4 h-4" />
            </button>
          )}
        </div>
      </div>

      {/* Messages area */}
      <div ref={scrollRef} className="flex-1 overflow-y-auto space-y-4 py-4 scrollbar-thin">
        {messages.length === 0 && !loading && (
          <WelcomeScreen onSuggestion={sendText} t={t} />
        )}

        {messages.map((msg) => (
          <ChatMessage key={msg.id} msg={msg} onPlayAudio={playAudio} />
        ))}

        {loading && (
          <div className="flex gap-3">
            <div className="relative w-8 h-8 flex-shrink-0">
              <HexIcon Icon={HiOutlineSparkles} accent="#2563EB" size="xs" bespoke="sparkles" gradient gradientTo="#0D9488" spin />
            </div>
            <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100/80 overflow-hidden">
              <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/30 via-teal-500/30 to-transparent" />
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-teal-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-blue-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="relative flex-shrink-0 pb-4 pt-2 border-t border-gray-100/80">
        {/* Subtle top gradient */}
        <div className="absolute -top-px left-0 right-0 h-px bg-gradient-to-r from-blue-500/15 via-teal-500/15 to-transparent" />

        {/* Voice recording overlay */}
        {voiceStatus === 'recording' && (
          <div className="mb-3 mt-2 relative flex items-center gap-3 bg-red-50/80 backdrop-blur-sm border border-red-200 rounded-2xl px-4 py-3 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 to-transparent pointer-events-none" />
            <div className="relative w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            <span className="relative text-sm font-medium text-red-700 flex-1">{t('voice.listening', 'Listening...')}</span>
            <button onClick={cancelVoice} className="relative text-xs text-red-500 font-medium hover:underline">{t('common.cancel', 'Cancel')}</button>
          </div>
        )}
        {voiceStatus === 'processing' && (
          <div className="mb-3 mt-2 relative flex items-center gap-3 bg-amber-50/80 backdrop-blur-sm border border-amber-200 rounded-2xl px-4 py-3 overflow-hidden">
            <div className="absolute inset-0 bg-gradient-to-r from-amber-500/5 to-transparent pointer-events-none" />
            <div className="relative w-4 h-4 border-2 border-amber-300 border-t-amber-600 rounded-full animate-spin" />
            <span className="relative text-sm font-medium text-amber-700">{t('voice.processing', 'Processing...')}</span>
          </div>
        )}

        <div className="relative flex items-end gap-2 mt-2">
          {/* Voice button with ring decoration */}
          <div className="relative flex-shrink-0">
            <svg className="absolute -inset-1 w-[calc(100%+8px)] h-[calc(100%+8px)] pointer-events-none" viewBox="0 0 56 56" fill="none">
              <circle cx="28" cy="28" r="26" stroke={voiceStatus === 'recording' ? '#EF4444' : '#2563EB'} strokeWidth="0.4" strokeDasharray="2 4"
                opacity={voiceStatus === 'recording' ? '0.4' : '0.15'}>
                <animateTransform attributeName="transform" type="rotate" values="0 28 28;360 28 28" dur="12s" repeatCount="indefinite" />
              </circle>
            </svg>
            <button
              onPointerDown={(e) => { e.preventDefault(); if (voiceStatus === 'idle' && !loading) startVoice(); }}
              onPointerUp={(e) => { e.preventDefault(); if (voiceStatus === 'recording') stopVoice(); }}
              onPointerLeave={(e) => { e.preventDefault(); if (voiceStatus === 'recording') stopVoice(); }}
              disabled={loading || voiceStatus === 'processing'}
              className={`w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-200 ${
                voiceStatus === 'recording'
                  ? 'bg-red-500 text-white shadow-lg shadow-red-200/60 scale-110 ring-4 ring-red-100'
                  : voiceStatus === 'processing'
                    ? 'bg-amber-500 text-white cursor-wait shadow-md'
                    : 'bg-gradient-to-br from-blue-500 to-teal-600 text-white shadow-md shadow-blue-200/50 hover:shadow-lg hover:scale-105 active:scale-95'
              }`}
              aria-label={voiceStatus === 'recording' ? 'Release to send' : 'Hold to speak'}
            >
              <HiOutlineMicrophone className="w-5 h-5" />
            </button>
          </div>

          {/* Text input with decoration */}
          <div className="flex-1 relative">
            <div className="absolute top-0 left-4 right-12 h-px bg-gradient-to-r from-blue-500/10 via-transparent to-teal-500/10 pointer-events-none rounded-full" />
            <textarea
              ref={inputRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={t('assistant.placeholder', 'Type a message or hold the mic...')}
              rows={1}
              className="w-full resize-none rounded-2xl border border-gray-200/80 bg-white/70 backdrop-blur-sm px-4 py-3 pr-12 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500/20 focus:border-blue-300 focus:bg-white shadow-sm transition-all"
              style={{ maxHeight: '120px' }}
              disabled={loading}
            />
            <button
              onClick={() => sendText(input)}
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-2 p-2 rounded-xl bg-gradient-to-br from-blue-600 to-teal-600 text-white disabled:opacity-20 disabled:cursor-not-allowed hover:shadow-md active:scale-95 transition-all shadow-sm"
              aria-label="Send"
            >
              <HiOutlinePaperAirplane className="w-4 h-4" />
            </button>
          </div>
        </div>
        <p className="text-[10px] text-gray-300 text-center mt-2 select-none">
          {t('assistant.disclaimer', 'AI assistant. Verify important information independently')}
        </p>
      </div>
    </div>
  );
}


// ── Welcome Screen ─────────────────────────────────────────────
function WelcomeScreen({ onSuggestion, t }) {
  const suggestions = [
    {
      text: 'Find education campaigns in Kenya',
      Icon: HiOutlineMagnifyingGlass,
      color: 'blue',
      svg: (
        <svg className="absolute top-2 right-2 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
          <circle cx="30" cy="28" r="12" stroke="#2563EB" strokeWidth="0.8" opacity="0.08" />
          <path d="M38 36 L48 46" stroke="#2563EB" strokeWidth="0.8" opacity="0.08" />
          <circle cx="30" cy="28" r="6" stroke="#2563EB" strokeWidth="0.4" strokeDasharray="2 2" opacity="0.05" />
        </svg>
      ),
    },
    {
      text: 'How much has been raised this month?',
      Icon: HiOutlineChartBarSquare,
      color: 'emerald',
      svg: (
        <svg className="absolute top-2 right-2 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
          <rect x="22" y="30" width="6" height="16" rx="1" stroke="#059669" strokeWidth="0.5" opacity="0.07" />
          <rect x="32" y="22" width="6" height="24" rx="1" stroke="#059669" strokeWidth="0.5" opacity="0.07" />
          <rect x="42" y="16" width="6" height="30" rx="1" stroke="#059669" strokeWidth="0.5" opacity="0.07" />
          <path d="M20 48 L50 48" stroke="#059669" strokeWidth="0.4" opacity="0.05" />
        </svg>
      ),
    },
    {
      text: 'Show me water projects',
      Icon: HiOutlineGlobeAlt,
      color: 'sky',
      svg: (
        <svg className="absolute top-2 right-2 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
          <circle cx="36" cy="30" r="14" stroke="#0284C7" strokeWidth="0.5" opacity="0.07" />
          <ellipse cx="36" cy="30" rx="8" ry="14" stroke="#0284C7" strokeWidth="0.4" opacity="0.05" />
          <path d="M22 30 L50 30" stroke="#0284C7" strokeWidth="0.3" opacity="0.05" />
          <path d="M25 22 L47 22" stroke="#0284C7" strokeWidth="0.3" opacity="0.04" />
          <path d="M25 38 L47 38" stroke="#0284C7" strokeWidth="0.3" opacity="0.04" />
        </svg>
      ),
    },
    {
      text: "What can you do?",
      Icon: HiOutlineQuestionMarkCircle,
      color: 'amber',
      svg: (
        <svg className="absolute top-2 right-2 w-16 h-16 pointer-events-none" viewBox="0 0 64 64" fill="none">
          <circle cx="36" cy="28" r="12" stroke="#D97706" strokeWidth="0.5" opacity="0.06" />
          <path d="M32 24 Q32 20, 36 20 Q40 20, 40 24 Q40 27, 36 28 L36 32" stroke="#D97706" strokeWidth="0.6" opacity="0.07" />
          <circle cx="36" cy="36" r="1" fill="#D97706" opacity="0.08" />
        </svg>
      ),
    },
  ];

  const colorMap = {
    blue: 'bg-blue-50 text-blue-600 group-hover:bg-blue-100',
    emerald: 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100',
    sky: 'bg-sky-50 text-sky-600 group-hover:bg-sky-100',
    amber: 'bg-amber-50 text-amber-600 group-hover:bg-amber-100',
  };

  const borderColors = {
    blue: 'hover:border-blue-200',
    emerald: 'hover:border-emerald-200',
    sky: 'hover:border-sky-200',
    amber: 'hover:border-amber-200',
  };

  const SUGGESTION_ACCENTS = { blue: '#2563EB', emerald: '#059669', sky: '#0284C7', amber: '#D97706' };
  const SUGGESTION_BESPS = { blue: 'search', emerald: 'chart', sky: 'globe', amber: 'question' };

  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      {/* Central icon with animated rings */}
      <div className="relative mb-6">
        <HexIcon Icon={HiOutlineSparkles} accent="#2563EB" size="lg" bespoke="sparkles" gradient gradientTo="#0D9488" spin />
      </div>

      <h2 className="text-xl font-bold text-gray-900 mb-2 font-display">{t('assistant.welcome', 'How can I help?')}</h2>
      <p className="text-sm text-gray-400 max-w-sm mb-3">{t('assistant.welcome_desc', 'Search campaigns, make donations, check analytics, or ask anything about TrustVoice.')}</p>

      {/* Decorative divider */}
      <div className="flex items-center gap-3 max-w-[180px] mx-auto mb-8">
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-blue-300/50 to-transparent" />
        <svg width="6" height="6" viewBox="0 0 6 6" fill="none"><path d="M3 0L6 3L3 6L0 3Z" fill="#2563EB" opacity="0.3" /></svg>
        <div className="flex-1 h-px bg-gradient-to-r from-transparent via-teal-300/50 to-transparent" />
      </div>

      {/* Suggestion cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-md">
        {suggestions.map(({ text, Icon, color, svg }) => (
          <button
            key={text}
            onClick={() => onSuggestion(text)}
            className={`group relative flex items-center gap-3 px-4 py-3.5 rounded-2xl border border-gray-100 bg-white/80 backdrop-blur-sm text-sm text-gray-600 ${borderColors[color]} hover:text-gray-900 transition-all text-left shadow-sm hover:shadow-md overflow-hidden`}
          >
            {/* Bespoke SVG per card */}
            {svg}
            {/* Top accent */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/10 via-teal-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            <HexIcon Icon={Icon} accent={SUGGESTION_ACCENTS[color]} bespoke={SUGGESTION_BESPS[color]} size="xs" />
            <span className="relative leading-snug">{text}</span>
          </button>
        ))}
      </div>

      {/* Voice hint */}
      <div className="mt-8 flex items-center gap-2 text-[11px] text-gray-300">
        <svg width="16" height="16" viewBox="0 0 16 16" fill="none">
          <rect x="6" y="2" width="4" height="8" rx="2" stroke="currentColor" strokeWidth="1" />
          <path d="M4 8a4 4 0 008 0" stroke="currentColor" strokeWidth="1" fill="none" />
          <path d="M8 12v2" stroke="currentColor" strokeWidth="1" />
        </svg>
        Hold the mic button to speak
      </div>
    </div>
  );
}


// ── Chat Message ───────────────────────────────────────────────
function ChatMessage({ msg, onPlayAudio }) {
  if (msg.role === 'user') {
    return (
      <div className="flex justify-end gap-3">
        <div className="relative max-w-[85%] bg-gradient-to-br from-blue-600 to-blue-700 text-white rounded-2xl rounded-tr-md px-4 py-3 shadow-sm overflow-hidden">
          {/* Subtle inner glow */}
          <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent pointer-events-none" />
          <p className="relative text-sm whitespace-pre-wrap">{msg.text}</p>
          {msg.isVoice && (
            <div className="relative flex items-center gap-1 mt-1.5 text-blue-200 text-[10px]">
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
      <div className="relative w-8 h-8 flex-shrink-0 mt-0.5">
        <HexIcon Icon={HiOutlineSparkles} accent="#2563EB" size="xs" bespoke="sparkles" gradient gradientTo="#0D9488" spin />
      </div>
      <div className="max-w-[85%] space-y-2">
        {/* Text response */}
        {msg.text && (
          <div className="relative bg-white/90 backdrop-blur-sm rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100/80 overflow-hidden">
            {/* Top accent */}
            <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/20 via-teal-500/20 to-transparent" />
            <p className="relative text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{msg.text}</p>
            {/* Replay audio button */}
            {msg.audioUrl && (
              <button
                onClick={() => onPlayAudio(msg.audioUrl)}
                className="relative mt-2 flex items-center gap-1.5 text-[11px] text-blue-500 hover:text-blue-700 transition"
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
          className="group relative flex items-center gap-3 bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-100/80 p-3 hover:border-blue-200 hover:shadow-md transition-all overflow-hidden"
        >
          {/* Top line accent */}
          <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/15 via-teal-500/10 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
          {/* Corner decoration */}
          <svg className="absolute -top-1 -right-1 w-12 h-12 pointer-events-none" viewBox="0 0 48 48" fill="none">
            <circle cx="36" cy="12" r="8" stroke="#2563EB" strokeWidth="0.4" opacity="0.05" />
            <circle cx="36" cy="12" r="3" stroke="#2563EB" strokeWidth="0.3" strokeDasharray="1 2" opacity="0.04" />
          </svg>
          <div className="relative w-10 h-10 rounded-xl bg-gradient-to-br from-blue-50 to-teal-50 flex items-center justify-center flex-shrink-0 text-blue-600 font-bold text-sm border border-blue-100/50">
            #{c.id}
          </div>
          <div className="relative flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-gray-900 truncate group-hover:text-blue-600 transition-colors">
              {c.title}
            </h4>
            <div className="flex items-center gap-2 mt-0.5">
              <ProgressBar percentage={c.progress_pct} className="flex-1" />
              <span className="text-[10px] font-medium text-blue-600 flex-shrink-0">{c.progress_pct}%</span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-[10px] text-gray-400">
              {c.category && <span className="capitalize">{c.category}</span>}
              {c.location && c.location !== 'N/A' && (
                <span className="flex items-center gap-0.5"><HiOutlineMapPin className="w-3 h-3" />{c.location}</span>
              )}
              <span>${fmt(c.raised_usd)} / ${fmt(c.goal_usd)}</span>
            </div>
          </div>
          <HiOutlineArrowRight className="relative w-4 h-4 text-gray-300 group-hover:text-blue-500 group-hover:translate-x-0.5 transition-all flex-shrink-0" />
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
      className="group relative block bg-white/90 backdrop-blur-sm rounded-2xl border border-gray-100/80 overflow-hidden hover:border-blue-200 hover:shadow-md transition-all"
    >
      {/* Gradient banner */}
      <div className="relative h-10 bg-gradient-to-r from-blue-500/8 via-teal-500/5 to-transparent">
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/30 via-teal-500/20 to-transparent" />
        <svg className="absolute right-2 top-0 w-16 h-10 pointer-events-none" viewBox="0 0 64 40" fill="none">
          <circle cx="48" cy="20" r="12" stroke="#2563EB" strokeWidth="0.4" opacity="0.06" />
          <path d="M42 20 L48 14 L54 20 L48 26 Z" stroke="#0D9488" strokeWidth="0.3" opacity="0.05" />
        </svg>
      </div>
      <div className="p-4 -mt-2">
        <div className="flex items-start justify-between gap-3">
          <div>
            <h4 className="font-semibold text-gray-900 group-hover:text-blue-600 transition-colors">{c.title}</h4>
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
            <span className="font-bold text-blue-600">${fmt(c.raised_usd)}</span>
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
        <div className="absolute top-0 left-0 right-0 h-[1px] bg-gradient-to-r from-blue-500/15 via-teal-500/10 to-transparent" />
        <span className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
          <HiOutlineClock className="w-3.5 h-3.5" />
          Donation History
        </span>
      </div>
      <div className="divide-y divide-gray-50">
        {donations.slice(0, 5).map((d) => (
          <div key={d.id} className="relative px-4 py-2.5 flex items-center justify-between gap-3 group hover:bg-gray-50/50 transition-colors">
            <svg className="absolute bottom-0 right-0 w-8 h-8 pointer-events-none opacity-0 group-hover:opacity-100 transition-opacity" viewBox="0 0 32 32" fill="none">
              <path d="M32 0v32H0" stroke="#2563EB" strokeWidth="0.3" opacity="0.05" />
            </svg>
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">{d.campaign_title}</p>
              <p className="text-[10px] text-gray-400">{d.date ? new Date(d.date).toLocaleDateString() : ''}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-xs font-bold text-blue-600">{d.amount} {d.currency}</p>
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
    { label: 'Total Donations', value: stats.total_donations, icon: HiOutlineArrowRight, color: 'teal' },
    { label: 'Total Donors', value: stats.total_donors, icon: HiOutlineUserGroup, color: 'amber' },
  ];

  const colorMap = {
    blue:  { bg: 'bg-blue-50', text: 'text-blue-600', stroke: '#2563EB' },
    green: { bg: 'bg-green-50', text: 'text-green-600', stroke: '#16A34A' },
    teal:  { bg: 'bg-teal-50', text: 'text-teal-600', stroke: '#0D9488' },
    amber: { bg: 'bg-amber-50', text: 'text-amber-600', stroke: '#D97706' },
  };

  const svgByColor = {
    blue: (s) => (<>{/* bar chart */}<rect x="4" y="16" width="5" height="14" rx="1" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><rect x="13" y="10" width="5" height="20" rx="1" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><rect x="22" y="4" width="5" height="26" rx="1" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/></>),
    green: (s) => (<>{/* dollar */}<circle cx="16" cy="16" r="12" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><path d="M16 6v20M12 10.5h5.5a3 3 0 010 6H12h6a3 3 0 010 6H12" stroke={s} strokeWidth="0.5" fill="none" opacity="0.08"/></>),
    teal: (s) => (<>{/* stack/layers */}<ellipse cx="16" cy="22" rx="11" ry="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><ellipse cx="16" cy="16" rx="11" ry="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><ellipse cx="16" cy="10" rx="11" ry="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/></>),
    amber: (s) => (<>{/* people */}<circle cx="11" cy="10" r="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><circle cx="21" cy="10" r="4" stroke={s} strokeWidth="0.6" fill="none" opacity="0.08"/><path d="M4 26c0-4 3.5-7 7-7s7 3 7 7M16 26c0-4 3.5-7 7-7s5 3 5 7" stroke={s} strokeWidth="0.5" fill="none" opacity="0.08"/></>),
  };

  const ANALYTICS_ACCENTS = { blue: '#2563EB', green: '#16A34A', teal: '#0D9488', amber: '#D97706' };
  const ANALYTICS_BESPS = { blue: 'chart', green: 'money', teal: 'trending', amber: 'users' };

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
