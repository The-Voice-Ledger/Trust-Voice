/**
 * VoiceManager — singleton that handles recording, sending to backend,
 * and playing back TTS responses.
 *
 * Designed to persist across page navigations in the SPA so a user
 * can issue voice commands seamlessly.
 */

class VoiceManager {
  constructor() {
    this.mediaRecorder = null;
    this.chunks = [];
    this.stream = null;
    this.currentAudio = null;
  }

  /** Request microphone access (call once on first interaction) */
  async init() {
    if (this.stream) return;
    this.stream = await navigator.mediaDevices.getUserMedia({ audio: true });
  }

  /** Start recording audio */
  async startRecording() {
    await this.init();
    this.chunks = [];

    // Prefer webm, fall back to ogg or default
    const mimeType = MediaRecorder.isTypeSupported('audio/webm;codecs=opus')
      ? 'audio/webm;codecs=opus'
      : MediaRecorder.isTypeSupported('audio/ogg;codecs=opus')
        ? 'audio/ogg;codecs=opus'
        : undefined;

    this.mediaRecorder = new MediaRecorder(this.stream, mimeType ? { mimeType } : {});

    this.mediaRecorder.ondataavailable = (e) => {
      if (e.data.size > 0) this.chunks.push(e.data);
    };

    return new Promise((resolve) => {
      this.mediaRecorder.onstart = () => resolve();
      this.mediaRecorder.start(100); // collect in 100ms chunks
    });
  }

  /** Stop recording and return the audio Blob */
  stopRecording() {
    return new Promise((resolve) => {
      if (!this.mediaRecorder || this.mediaRecorder.state === 'inactive') {
        resolve(null);
        return;
      }
      this.mediaRecorder.onstop = () => {
        const blob = new Blob(this.chunks, { type: this.mediaRecorder.mimeType || 'audio/webm' });
        this.chunks = [];
        resolve(blob);
      };
      this.mediaRecorder.stop();
    });
  }

  /** Play a TTS audio URL */
  play(url) {
    this.stopPlayback();
    return new Promise((resolve, reject) => {
      this.currentAudio = new Audio(url);
      this.currentAudio.onended = () => {
        this.currentAudio = null;
        resolve();
      };
      this.currentAudio.onerror = (e) => {
        this.currentAudio = null;
        reject(e);
      };
      this.currentAudio.play();
    });
  }

  /** Stop any currently playing audio */
  stopPlayback() {
    if (this.currentAudio) {
      this.currentAudio.pause();
      this.currentAudio.currentTime = 0;
      this.currentAudio = null;
    }
  }

  /** Check if an audio blob has actual sound (not silence) */
  async hasSound(blob) {
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const buf = await blob.arrayBuffer();
      const audio = await ctx.decodeAudioData(buf);
      const data = audio.getChannelData(0);
      let sum = 0;
      for (let i = 0; i < data.length; i++) sum += data[i] * data[i];
      const rms = Math.sqrt(sum / data.length);
      ctx.close();
      return rms > 0.01;
    } catch {
      return true; // assume sound on error
    }
  }

  /** Clean up resources */
  destroy() {
    this.stopPlayback();
    if (this.stream) {
      this.stream.getTracks().forEach((t) => t.stop());
      this.stream = null;
    }
  }
}

// Singleton
const voiceManager = new VoiceManager();
export default voiceManager;
