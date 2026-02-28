import { useTranslation } from 'react-i18next';
import useVoice from '../voice/useVoice';
import useVoiceStore from '../stores/voiceStore';

/**
 * VoiceButton — hold-to-record microphone button.
 *
 * @param {Function} apiCall   Voice API function (e.g. voiceSearchCampaigns)
 * @param {Array}    apiArgs   Extra args to pass after blob
 * @param {Function} onResult  Called with API response
 * @param {string}   className Extra CSS classes
 */
export default function VoiceButton({ apiCall, apiArgs = [], onResult, className = '' }) {
  const { t } = useTranslation();
  const { status, start, stop, cancel } = useVoice(apiCall, apiArgs, onResult);
  const error = useVoiceStore((s) => s.error);

  const stateStyles = {
    idle: 'bg-blue-600 hover:bg-blue-700 text-white',
    recording: 'bg-red-500 animate-pulse text-white',
    processing: 'bg-yellow-500 text-white cursor-wait',
    playing: 'bg-green-500 text-white',
  };

  const stateLabels = {
    idle: t('voice.tap_to_speak'),
    recording: t('voice.listening'),
    processing: t('voice.processing'),
    playing: t('voice.playing'),
  };

  const handlePointerDown = (e) => {
    e.preventDefault();
    if (status === 'idle') start();
  };

  const handlePointerUp = (e) => {
    e.preventDefault();
    if (status === 'recording') stop();
  };

  return (
    <div className={`flex flex-col items-center gap-1 ${className}`}>
      <button
        onPointerDown={handlePointerDown}
        onPointerUp={handlePointerUp}
        onPointerLeave={handlePointerUp}
        disabled={status === 'processing'}
        className={`
          flex items-center justify-center gap-2 rounded-full px-5 py-3
          font-medium text-sm transition-all shadow-lg select-none
          ${stateStyles[status]}
        `}
        aria-label={stateLabels[status]}
      >
        <MicIcon status={status} />
        <span>{stateLabels[status]}</span>
      </button>
      {error && (
        <p className="text-xs text-red-500 mt-1">{error}</p>
      )}
    </div>
  );
}

function MicIcon({ status }) {
  if (status === 'processing') {
    return (
      <svg className="animate-spin h-5 w-5" viewBox="0 0 24 24" fill="none">
        <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
        <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
      </svg>
    );
  }
  return (
    <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 24 24" fill="none"
      stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
      <path d="M12 1a3 3 0 00-3 3v8a3 3 0 006 0V4a3 3 0 00-3-3z" />
      <path d="M19 10v2a7 7 0 01-14 0v-2" />
      <line x1="12" y1="19" x2="12" y2="23" />
      <line x1="8" y1="23" x2="16" y2="23" />
    </svg>
  );
}
