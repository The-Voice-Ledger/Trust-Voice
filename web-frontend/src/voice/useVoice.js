import { useCallback, useRef } from 'react';
import voiceManager from './VoiceManager';
import useVoiceStore from '../stores/voiceStore';

/**
 * useVoice — React hook for voice interactions.
 *
 * @param {Function} onResult  Called with the API response JSON after recording.
 * @param {Function} apiCall   The API function to call with (blob, ...args).
 *                              e.g. voiceSearchCampaigns
 * @param {Array}    apiArgs   Extra arguments to pass after the blob.
 */
export default function useVoice(apiCall, apiArgs = [], onResult) {
  const { status, language, setStatus, setTranscription, setError, reset } = useVoiceStore();
  const recordingRef = useRef(false);

  const start = useCallback(async () => {
    try {
      reset();
      setStatus('recording');
      recordingRef.current = true;
      await voiceManager.startRecording();
    } catch (err) {
      setError(err.message || 'Microphone access denied');
    }
  }, [reset, setStatus, setError]);

  const stop = useCallback(async () => {
    if (!recordingRef.current) return;
    recordingRef.current = false;
    setStatus('processing');

    try {
      const blob = await voiceManager.stopRecording();
      if (!blob) { reset(); return; }

      // Check for silence
      const hasAudio = await voiceManager.hasSound(blob);
      if (!hasAudio) {
        setError('No speech detected. Please try again');
        return;
      }

      // Send to backend
      const result = await apiCall(blob, ...apiArgs, language);
      setTranscription(result.transcription || '');

      // Play TTS response if available
      if (result.audio_url) {
        setStatus('playing');
        try {
          await voiceManager.play(result.audio_url);
        } catch { /* playback error is non-fatal */ }
      }

      setStatus('idle');
      if (onResult) onResult(result);
    } catch (err) {
      setError(err.message || 'Voice processing failed');
    }
  }, [apiCall, apiArgs, language, setStatus, setTranscription, setError, reset, onResult]);

  const cancel = useCallback(() => {
    voiceManager.stopRecording();
    voiceManager.stopPlayback();
    reset();
  }, [reset]);

  return { status, language, start, stop, cancel };
}
