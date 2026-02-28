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
} from 'react-icons/hi2';
import {
  HiOutlineMicrophone,
} from 'react-icons/hi';

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
    <div className="max-w-3xl mx-auto px-4 sm:px-6 flex flex-col" style={{ height: 'calc(100dvh - 8rem)' }}>
      {/* Header */}
      <div className="flex items-center justify-between py-4 flex-shrink-0 border-b border-gray-100/80">
        <div className="flex items-center gap-3">
          <div className="relative">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-md shadow-indigo-200/50">
              <HiOutlineSparkles className="w-5 h-5 text-white" />
            </div>
            <div className="absolute -bottom-0.5 -right-0.5 w-3 h-3 rounded-full bg-green-400 border-2 border-white" />
          </div>
          <div>
            <h1 className="text-lg font-bold text-gray-900">{t('assistant.title', 'TrustVoice Assistant')}</h1>
            <p className="text-xs text-gray-400">{t('assistant.subtitle', 'Search, donate, and manage by voice or text')}</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          {/* Auto-speak toggle */}
          <button
            onClick={() => { setAutoSpeak((v) => !v); stopAudio(); }}
            className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all border ${
              autoSpeak
                ? 'bg-indigo-50 text-indigo-700 border-indigo-200'
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
            <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0">
              <HiOutlineSparkles className="w-4 h-4 text-white" />
            </div>
            <div className="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100">
              <div className="flex items-center gap-1.5">
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }} />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '150ms' }} />
                <div className="w-2 h-2 bg-indigo-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }} />
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Input bar */}
      <div className="flex-shrink-0 pb-4 pt-2 border-t border-gray-100/80">
        {/* Voice recording overlay */}
        {voiceStatus === 'recording' && (
          <div className="mb-3 mt-2 flex items-center gap-3 bg-red-50 border border-red-200 rounded-2xl px-4 py-3">
            <div className="w-3 h-3 bg-red-500 rounded-full animate-pulse" />
            <span className="text-sm font-medium text-red-700 flex-1">{t('voice.listening', 'Listening...')}</span>
            <button onClick={cancelVoice} className="text-xs text-red-500 font-medium hover:underline">{t('common.cancel', 'Cancel')}</button>
          </div>
        )}
        {voiceStatus === 'processing' && (
          <div className="mb-3 mt-2 flex items-center gap-3 bg-amber-50 border border-amber-200 rounded-2xl px-4 py-3">
            <div className="w-4 h-4 border-2 border-amber-300 border-t-amber-600 rounded-full animate-spin" />
            <span className="text-sm font-medium text-amber-700">{t('voice.processing', 'Processing...')}</span>
          </div>
        )}

        <div className="flex items-end gap-2 mt-2">
          {/* Voice button */}
          <button
            onPointerDown={(e) => { e.preventDefault(); if (voiceStatus === 'idle' && !loading) startVoice(); }}
            onPointerUp={(e) => { e.preventDefault(); if (voiceStatus === 'recording') stopVoice(); }}
            onPointerLeave={(e) => { e.preventDefault(); if (voiceStatus === 'recording') stopVoice(); }}
            disabled={loading || voiceStatus === 'processing'}
            className={`flex-shrink-0 w-12 h-12 rounded-2xl flex items-center justify-center transition-all duration-200 ${
              voiceStatus === 'recording'
                ? 'bg-red-500 text-white shadow-lg shadow-red-200/60 scale-110 ring-4 ring-red-100'
                : voiceStatus === 'processing'
                  ? 'bg-amber-500 text-white cursor-wait shadow-md'
                  : 'bg-gradient-to-br from-indigo-500 to-purple-600 text-white shadow-md shadow-indigo-200/50 hover:shadow-lg hover:scale-105 active:scale-95'
            }`}
            aria-label={voiceStatus === 'recording' ? 'Release to send' : 'Hold to speak'}
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
              placeholder={t('assistant.placeholder', 'Type a message or hold the mic...')}
              rows={1}
              className="w-full resize-none rounded-2xl border border-gray-200 bg-gray-50/50 px-4 py-3 pr-12 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-300 focus:bg-white shadow-sm transition-all"
              style={{ maxHeight: '120px' }}
              disabled={loading}
            />
            <button
              onClick={() => sendText(input)}
              disabled={!input.trim() || loading}
              className="absolute right-2 bottom-2 p-2 rounded-xl bg-indigo-600 text-white disabled:opacity-20 disabled:cursor-not-allowed hover:bg-indigo-700 active:scale-95 transition-all shadow-sm"
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
    { text: 'Find education campaigns in Kenya', Icon: HiOutlineMagnifyingGlass, color: 'indigo' },
    { text: 'How much has been raised this month?', Icon: HiOutlineChartBarSquare, color: 'emerald' },
    { text: 'Show me water projects', Icon: HiOutlineGlobeAlt, color: 'sky' },
    { text: "What can you do?", Icon: HiOutlineQuestionMarkCircle, color: 'amber' },
  ];

  const colorMap = {
    indigo: 'bg-indigo-50 text-indigo-600 group-hover:bg-indigo-100',
    emerald: 'bg-emerald-50 text-emerald-600 group-hover:bg-emerald-100',
    sky: 'bg-sky-50 text-sky-600 group-hover:bg-sky-100',
    amber: 'bg-amber-50 text-amber-600 group-hover:bg-amber-100',
  };

  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="relative mb-6">
        <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-xl shadow-indigo-200/50">
          <HiOutlineSparkles className="w-8 h-8 text-white" />
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-green-400 border-2 border-white animate-pulse" />
      </div>
      <h2 className="text-xl font-bold text-gray-900 mb-2">{t('assistant.welcome', 'How can I help?')}</h2>
      <p className="text-sm text-gray-400 max-w-sm mb-8">{t('assistant.welcome_desc', 'Search campaigns, make donations, check analytics, or ask anything about TrustVoice.')}</p>
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5 w-full max-w-md">
        {suggestions.map(({ text, Icon, color }) => (
          <button
            key={text}
            onClick={() => onSuggestion(text)}
            className="group flex items-center gap-3 px-4 py-3.5 rounded-xl border border-gray-100 bg-white text-sm text-gray-600 hover:border-indigo-200 hover:text-gray-900 transition-all text-left shadow-sm hover:shadow-md"
          >
            <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 transition-colors ${colorMap[color]}`}>
              <Icon className="w-4 h-4" />
            </div>
            <span className="leading-snug">{text}</span>
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
        <div className="max-w-[85%] bg-indigo-600 text-white rounded-2xl rounded-tr-md px-4 py-3 shadow-sm">
          <p className="text-sm whitespace-pre-wrap">{msg.text}</p>
          {msg.isVoice && (
            <div className="flex items-center gap-1 mt-1 text-indigo-200 text-[10px]">
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
      <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center flex-shrink-0 mt-0.5">
        <HiOutlineSparkles className="w-4 h-4 text-white" />
      </div>
      <div className="max-w-[85%] space-y-2">
        {/* Text response */}
        {msg.text && (
          <div className="bg-white rounded-2xl rounded-tl-md px-4 py-3 shadow-sm border border-gray-100">
            <p className="text-sm text-gray-700 whitespace-pre-wrap leading-relaxed">{msg.text}</p>
            {/* Replay audio button */}
            {msg.audioUrl && (
              <button
                onClick={() => onPlayAudio(msg.audioUrl)}
                className="mt-2 flex items-center gap-1.5 text-[11px] text-indigo-500 hover:text-indigo-700 transition"
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
          className="flex items-center gap-3 bg-white rounded-xl border border-gray-100 p-3 hover:border-indigo-200 hover:shadow-sm transition-all group"
        >
          <div className="w-10 h-10 rounded-lg bg-indigo-50 flex items-center justify-center flex-shrink-0 text-indigo-600 font-bold text-sm">
            #{c.id}
          </div>
          <div className="flex-1 min-w-0">
            <h4 className="text-sm font-semibold text-gray-900 truncate group-hover:text-indigo-600 transition-colors">
              {c.title}
            </h4>
            <div className="flex items-center gap-2 mt-0.5">
              <ProgressBar percentage={c.progress_pct} className="flex-1" />
              <span className="text-[10px] font-medium text-indigo-600 flex-shrink-0">{c.progress_pct}%</span>
            </div>
            <div className="flex items-center gap-3 mt-1 text-[10px] text-gray-400">
              {c.category && <span className="capitalize">{c.category}</span>}
              {c.location && c.location !== 'N/A' && (
                <span className="flex items-center gap-0.5"><HiOutlineMapPin className="w-3 h-3" />{c.location}</span>
              )}
              <span>${fmt(c.raised_usd)} / ${fmt(c.goal_usd)}</span>
            </div>
          </div>
          <HiOutlineArrowRight className="w-4 h-4 text-gray-300 group-hover:text-indigo-500 transition-colors flex-shrink-0" />
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
      className="block bg-white rounded-xl border border-gray-100 p-4 hover:border-indigo-200 hover:shadow-sm transition-all group"
    >
      <div className="flex items-start justify-between gap-3">
        <div>
          <h4 className="font-semibold text-gray-900 group-hover:text-indigo-600 transition-colors">{c.title}</h4>
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
          <span className="font-bold text-indigo-600">${fmt(c.raised_usd)}</span>
          <span className="text-gray-400">of ${fmt(c.goal_usd)}</span>
        </div>
      </div>
      <div className="flex items-center gap-3 mt-2 text-[10px] text-gray-400">
        {c.category && <span className="capitalize bg-gray-50 px-2 py-0.5 rounded">{c.category}</span>}
        {c.location && c.location !== 'N/A' && (
          <span className="flex items-center gap-0.5"><HiOutlineMapPin className="w-3 h-3" />{c.location}</span>
        )}
      </div>
    </Link>
  );
}

function DonationConfirmationCard({ data }) {
  return (
    <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-xl border border-green-200 p-4">
      <div className="flex items-center gap-2 mb-2">
        <HiOutlineCheckBadge className="w-5 h-5 text-green-600" />
        <span className="font-semibold text-green-800 text-sm">Donation Initiated</span>
      </div>
      {data.donation_id && (
        <p className="text-xs text-gray-500 mb-2">ID: {String(data.donation_id).slice(0, 8)}…</p>
      )}
      <div className="grid grid-cols-2 gap-2 text-xs">
        {data.campaign_title && (
          <div><span className="text-gray-400">Campaign</span><p className="font-medium text-gray-700">{data.campaign_title}</p></div>
        )}
        {data.amount && (
          <div><span className="text-gray-400">Amount</span><p className="font-medium text-gray-700">{data.amount} {data.currency || 'USD'}</p></div>
        )}
        {data.payment_method && (
          <div><span className="text-gray-400">Method</span><p className="font-medium text-gray-700 uppercase">{data.payment_method}</p></div>
        )}
      </div>
      {data.instructions && (
        <p className="text-xs text-green-700 mt-2 bg-green-100/50 px-3 py-2 rounded-lg">{data.instructions}</p>
      )}
    </div>
  );
}

function DonationHistoryCard({ donations }) {
  if (!donations.length) return null;
  return (
    <div className="bg-white rounded-xl border border-gray-100 overflow-hidden">
      <div className="px-4 py-2 bg-gray-50 border-b border-gray-100">
        <span className="text-xs font-semibold text-gray-600 flex items-center gap-1.5">
          <HiOutlineClock className="w-3.5 h-3.5" />
          Donation History
        </span>
      </div>
      <div className="divide-y divide-gray-50">
        {donations.slice(0, 5).map((d) => (
          <div key={d.id} className="px-4 py-2.5 flex items-center justify-between gap-3">
            <div className="min-w-0">
              <p className="text-xs font-medium text-gray-700 truncate">{d.campaign_title}</p>
              <p className="text-[10px] text-gray-400">{d.date ? new Date(d.date).toLocaleDateString() : ''}</p>
            </div>
            <div className="text-right flex-shrink-0">
              <p className="text-xs font-bold text-indigo-600">{d.amount} {d.currency}</p>
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
    { label: 'Active Campaigns', value: stats.active_campaigns, icon: HiOutlineChartBarSquare, color: 'indigo' },
    { label: 'Total Donated', value: `$${fmt(stats.total_raised_usd)}`, icon: HiOutlineCheckBadge, color: 'green' },
    { label: 'Total Donations', value: stats.total_donations, icon: HiOutlineArrowRight, color: 'purple' },
    { label: 'Total Donors', value: stats.total_donors, icon: HiOutlineUserGroup, color: 'pink' },
  ];

  const colorMap = {
    indigo: 'bg-indigo-50 text-indigo-600',
    green: 'bg-green-50 text-green-600',
    purple: 'bg-purple-50 text-purple-600',
    pink: 'bg-pink-50 text-pink-600',
  };

  return (
    <div className="grid grid-cols-2 gap-2">
      {items.map(({ label, value, icon: Icon, color }) => (
        <div key={label} className="bg-white rounded-xl border border-gray-100 p-3">
          <div className={`w-7 h-7 rounded-lg ${colorMap[color]} flex items-center justify-center mb-2`}>
            <Icon className="w-4 h-4" />
          </div>
          <p className="text-lg font-bold text-gray-900">{value}</p>
          <p className="text-[10px] text-gray-400">{label}</p>
        </div>
      ))}
    </div>
  );
}

function fmt(n) {
  if (n == null) return '0';
  return Number(n).toLocaleString('en-US', { maximumFractionDigits: 0 });
}
