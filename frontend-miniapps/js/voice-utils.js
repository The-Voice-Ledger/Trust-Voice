/**
 * Voice Utilities - Shared Voice Components
 * 
 * LAB 25 Voice Ledger compliant utilities
 */

console.log('🎤 Loading voice-utils.js...');

// Voice Error Class
class VoiceError extends Error {
    static NETWORK = 'NETWORK';
    static TIMEOUT = 'TIMEOUT';
    static VALIDATION = 'VALIDATION';
    static SERVER = 'SERVER';
    static ASR = 'ASR';
    static UNKNOWN = 'UNKNOWN';
    
    constructor(message, type, context = {}) {
        super(message);
        this.name = 'VoiceError';
        this.type = type;
        this.context = context;
        this.timestamp = Date.now();
    }
    
    isRetryable() {
        return [
            VoiceError.NETWORK,
            VoiceError.TIMEOUT,
            VoiceError.SERVER
        ].includes(this.type);
    }
    
    getUserMessage() {
        const messages = {
            [VoiceError.NETWORK]: '📡 No Connection\n\nPlease check your internet and try again.',
            [VoiceError.TIMEOUT]: '⏱️ Request Timed Out\n\nThe server took too long to respond.',
            [VoiceError.VALIDATION]: this.message,
            [VoiceError.SERVER]: '🔧 Server Error\n\nPlease try again in a moment.',
            [VoiceError.ASR]: '🎤 Speech Recognition Error\n\n' + this.message,
            [VoiceError.UNKNOWN]: '❌ Unexpected Error\n\nPlease try again.'
        };
        return messages[this.type] || messages[VoiceError.UNKNOWN];
    }
}

// TTS Controller
class TTSController {
    constructor(apiBase = '') {
        this.currentAudio = null;
        this.audioUrl = null;
        this.isPlaying = false;
        this.controls = null;
        this.apiBase = apiBase;
    }
    
    play(audioUrl) {
        this.stop();
        
        this.audioUrl = audioUrl.startsWith('http') ? audioUrl : `${this.apiBase}${audioUrl}`;
        this.currentAudio = new Audio(this.audioUrl);
        
        this.currentAudio.onplay = () => {
            this.isPlaying = true;
            this.showControls();
            this.updateControlsState();
        };
        
        this.currentAudio.onpause = () => {
            this.isPlaying = false;
            this.updateControlsState();
        };
        
        this.currentAudio.onended = () => {
            this.isPlaying = false;
            this.hideControls();
        };
        
        this.currentAudio.onerror = (error) => {
            console.error('Audio playback error:', error);
            this.hideControls();
        };
        
        this.currentAudio.play().catch(e => {
            console.error('Failed to play audio:', e);
            this.hideControls();
        });
    }
    
    pause() {
        if (this.currentAudio && this.isPlaying) {
            this.currentAudio.pause();
        }
    }
    
    resume() {
        if (this.currentAudio && !this.isPlaying) {
            this.currentAudio.play().catch(e => {
                console.error('Failed to resume audio:', e);
            });
        }
    }
    
    stop() {
        if (this.currentAudio) {
            this.currentAudio.pause();
            this.currentAudio.currentTime = 0;
            this.currentAudio = null;
            this.hideControls();
        }
    }
    
    replay() {
        if (this.audioUrl) {
            this.play(this.audioUrl);
        }
    }
    
    showControls() {
        if (!this.controls) {
            this.controls = document.createElement('div');
            this.controls.id = 'tts-controls';
            this.controls.style.cssText = `
                position: fixed;
                bottom: 20px;
                left: 50%;
                transform: translateX(-50%);
                background: var(--tg-theme-bg-color, white);
                border-radius: 24px;
                padding: 12px 20px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.15);
                display: flex;
                align-items: center;
                gap: 12px;
                z-index: 1000;
            `;
            
            this.controls.innerHTML = `
                <button id="tts-pause" style="background: none; border: none; font-size: 24px; cursor: pointer;">⏸️</button>
                <button id="tts-replay" style="background: none; border: none; font-size: 24px; cursor: pointer;">🔄</button>
                <button id="tts-stop" style="background: none; border: none; font-size: 24px; cursor: pointer;">⏹️</button>
            `;
            
            document.body.appendChild(this.controls);
            
            document.getElementById('tts-pause').addEventListener('click', () => {
                if (this.isPlaying) {
                    this.pause();
                } else {
                    this.resume();
                }
            });
            
            document.getElementById('tts-replay').addEventListener('click', () => {
                this.replay();
            });
            
            document.getElementById('tts-stop').addEventListener('click', () => {
                this.stop();
            });
        }
        
        this.controls.style.display = 'flex';
    }
    
    hideControls() {
        if (this.controls) {
            this.controls.style.display = 'none';
        }
    }
    
    updateControlsState() {
        const pauseBtn = document.getElementById('tts-pause');
        if (pauseBtn) {
            pauseBtn.textContent = this.isPlaying ? '⏸️' : '▶️';
        }
    }
}

// Silent Audio Detection
async function checkAudioHasSound(audioBlob) {
    return new Promise((resolve) => {
        const audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const reader = new FileReader();
        
        reader.onload = async (e) => {
            try {
                const arrayBuffer = e.target.result;
                const audioBuffer = await audioContext.decodeAudioData(arrayBuffer);
                
                const channelData = audioBuffer.getChannelData(0);
                
                let sum = 0;
                for (let i = 0; i < channelData.length; i++) {
                    sum += channelData[i] * channelData[i];
                }
                const rms = Math.sqrt(sum / channelData.length);
                
                const hasSound = rms > 0.01;
                
                console.log(`Audio analysis: RMS=${rms.toFixed(4)}, hasSound=${hasSound}`);
                resolve(hasSound);
            } catch (error) {
                console.error('Audio analysis error:', error);
                resolve(true);
            }
        };
        
        reader.onerror = () => {
            console.error('FileReader error');
            resolve(true);
        };
        
        reader.readAsArrayBuffer(audioBlob);
    });
}

// Export utilities
window.VoiceUtils = {
    VoiceError,
    TTSController,
    checkAudioHasSound
};

console.log('✅ voice-utils.js loaded successfully');
console.log('✅ window.VoiceUtils available:', !!window.VoiceUtils);
