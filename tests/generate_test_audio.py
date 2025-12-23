"""
Generate a test audio file for ASR testing
Uses macOS 'say' command for simple TTS
"""

import subprocess
from pathlib import Path

def generate_test_audio():
    """Generate a test audio file using macOS say command"""
    
    # Create uploads directory
    upload_dir = Path(__file__).parent.parent / "uploads" / "audio"
    upload_dir.mkdir(parents=True, exist_ok=True)
    
    # Test phrases
    test_phrases = {
        "en": {
            "text": "I want to donate fifty dollars to the water project in Tanzania",
            "filename": "test_english_donation.wav"
        }
    }
    
    for lang, data in test_phrases.items():
        output_file = upload_dir / data["filename"]
        temp_aiff = upload_dir / f"temp_{data['filename'].replace('.wav', '.aiff')}"
        
        try:
            # Step 1: Generate AIFF (macOS say default)
            subprocess.run([
                "say",
                "-o", str(temp_aiff),
                data["text"]
            ], check=True)
            
            # Step 2: Convert AIFF to WAV using ffmpeg
            subprocess.run([
                "ffmpeg",
                "-i", str(temp_aiff),
                "-ar", "16000",  # 16kHz sample rate
                "-ac", "1",      # Mono
                "-y",            # Overwrite
                str(output_file)
            ], check=True, capture_output=True)
            
            # Clean up temp file
            temp_aiff.unlink()
            
            print(f"✅ Generated: {output_file}")
            print(f"   Text: \"{data['text']}\"")
            print(f"   Size: {output_file.stat().st_size / 1024:.2f} KB")
            
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to generate {lang} audio: {e}")
            if temp_aiff.exists():
                temp_aiff.unlink()
        except FileNotFoundError:
            print("❌ 'say' or 'ffmpeg' command not found (macOS only)")
            return False
    
    return True


if __name__ == "__main__":
    print("🎙️  Generating test audio files...\n")
    
    if generate_test_audio():
        print("\n✅ Test audio files ready!")
        print("\n💡 Now run:")
        print("   python tests/test_voice_asr.py uploads/audio/test_english_donation.wav en")
    else:
        print("\n⚠️  Could not generate test audio")
        print("   Alternative: Record your own audio or download a sample WAV file")
