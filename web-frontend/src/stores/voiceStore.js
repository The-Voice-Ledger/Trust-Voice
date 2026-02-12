import { create } from 'zustand';

const useVoiceStore = create((set) => ({
  /** 'idle' | 'recording' | 'processing' | 'playing' */
  status: 'idle',
  language: localStorage.getItem('tv_lang') || 'en',
  lastTranscription: '',
  error: null,

  setStatus: (status) => set({ status }),
  setLanguage: (lang) => {
    localStorage.setItem('tv_lang', lang);
    set({ language: lang });
  },
  setTranscription: (text) => set({ lastTranscription: text }),
  setError: (err) => set({ error: err, status: 'idle' }),
  reset: () => set({ status: 'idle', lastTranscription: '', error: null }),
}));

export default useVoiceStore;
