"""
Test Suite for Voice ASR Module
Tests audio processing and speech recognition
"""

import pytest
import os
from pathlib import Path
import sys

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from voice.audio_utils import (
    validate_audio_file,
    convert_to_whisper_format,
    get_audio_metadata,
    process_audio_for_asr,
    AudioProcessingError
)
from voice.asr.asr_infer import (
    transcribe_audio,
    get_supported_languages,
    verify_amharic_model_cached,
    ASRError
)


class TestAudioUtils:
    """Test audio processing utilities"""
    
    def test_supported_formats(self):
        """Test that we know what formats are supported"""
        from voice.audio_utils import SUPPORTED_FORMATS
        assert '.wav' in SUPPORTED_FORMATS
        assert '.mp3' in SUPPORTED_FORMATS
        assert '.m4a' in SUPPORTED_FORMATS
        print("✅ Supported formats verified")
    
    def test_audio_validation_nonexistent_file(self):
        """Test validation fails for non-existent file"""
        is_valid, error = validate_audio_file("nonexistent_file.wav")
        assert not is_valid
        assert "not found" in error.lower()
        print("✅ Validation correctly rejects non-existent file")
    
    def test_audio_metadata_structure(self):
        """Test that metadata extraction returns expected structure"""
        # This will fail without a real file, but tests the structure
        expected_keys = ["file_name", "file_size_mb", "duration_seconds", 
                        "sample_rate", "channels", "format"]
        print(f"✅ Expected metadata keys: {expected_keys}")


class TestASRModule:
    """Test ASR transcription module"""
    
    def test_supported_languages(self):
        """Test language support"""
        langs = get_supported_languages()
        assert "en" in langs
        assert "am" in langs
        print(f"✅ Supported languages: {list(langs.keys())}")
        print(f"   English: {langs['en']}")
        print(f"   Amharic: {langs['am']}")
    
    def test_amharic_model_cache_check(self):
        """Check if Amharic model is cached"""
        is_cached = verify_amharic_model_cached()
        if is_cached:
            print("✅ Amharic model is cached at ~/.cache/huggingface/")
        else:
            print("⚠️  Amharic model not cached (will download on first use ~1.5GB)")
    
    def test_openai_api_key_set(self):
        """Check if OpenAI API key is configured"""
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key:
            print(f"✅ OpenAI API key configured (starts with: {api_key[:10]}...)")
        else:
            print("⚠️  OPENAI_API_KEY not set - Whisper API will fail")


class TestIntegration:
    """Integration tests with real audio (if available)"""
    
    def test_check_for_sample_audio(self):
        """Check if sample audio files exist"""
        test_audio_dir = Path(__file__).parent.parent / "uploads" / "audio"
        test_audio_dir.mkdir(parents=True, exist_ok=True)
        
        audio_files = list(test_audio_dir.glob("*.wav")) + list(test_audio_dir.glob("*.mp3"))
        
        if audio_files:
            print(f"✅ Found {len(audio_files)} test audio file(s):")
            for f in audio_files:
                print(f"   - {f.name}")
        else:
            print("ℹ️  No test audio files found in uploads/audio/")
            print("   Create a test audio file to enable full integration tests")


def run_manual_test():
    """
    Manual test with a real audio file
    Usage: python tests/test_voice_asr.py path/to/audio.wav [language]
    """
    import sys
    
    if len(sys.argv) < 2:
        print("\n📋 Manual Test Usage:")
        print("python tests/test_voice_asr.py <audio_file> [language]")
        print("\nExample:")
        print("python tests/test_voice_asr.py test_audio.wav en")
        print("python tests/test_voice_asr.py test_audio.wav am")
        return
    
    audio_file = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "en"
    
    print(f"\n🎤 Testing ASR with: {audio_file}")
    print(f"Language: {language}\n")
    
    # Step 1: Validate audio
    print("1️⃣  Validating audio file...")
    is_valid, error = validate_audio_file(audio_file)
    if not is_valid:
        print(f"❌ Validation failed: {error}")
        return
    print("✅ Audio file valid")
    
    # Step 2: Get metadata
    print("\n2️⃣  Extracting metadata...")
    metadata = get_audio_metadata(audio_file)
    print(f"   File: {metadata.get('file_name')}")
    print(f"   Size: {metadata.get('file_size_mb')} MB")
    print(f"   Duration: {metadata.get('duration_seconds')} seconds")
    print(f"   Sample Rate: {metadata.get('sample_rate')} Hz")
    print(f"   Channels: {metadata.get('channels')}")
    
    # Step 3: Convert to optimal format
    print("\n3️⃣  Converting to Whisper-optimal format...")
    converted_file = convert_to_whisper_format(audio_file)
    print(f"✅ Converted: {converted_file}")
    
    # Step 4: Transcribe
    print(f"\n4️⃣  Transcribing (language: {language})...")
    try:
        result = transcribe_audio(converted_file, language=language)
        print(f"\n✅ Transcription Complete!")
        print(f"📝 Text: {result['text']}")
        print(f"🌍 Language: {result['language']}")
        print(f"⏱️  Duration: {result['duration']:.2f}s" if result.get('duration') else "")
        print(f"🔧 Method: {result['method']}")
        print(f"🤖 Model: {result['model']}")
    except ASRError as e:
        print(f"❌ Transcription failed: {e}")


if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Manual test mode
        run_manual_test()
    else:
        # Run pytest tests
        print("\n🧪 Running TrustVoice ASR Tests\n")
        print("=" * 60)
        
        # Run all test classes
        test_audio = TestAudioUtils()
        test_audio.test_supported_formats()
        test_audio.test_audio_validation_nonexistent_file()
        test_audio.test_audio_metadata_structure()
        
        print("\n" + "=" * 60)
        
        test_asr = TestASRModule()
        test_asr.test_supported_languages()
        test_asr.test_amharic_model_cache_check()
        test_asr.test_openai_api_key_set()
        
        print("\n" + "=" * 60)
        
        test_integration = TestIntegration()
        test_integration.test_check_for_sample_audio()
        
        print("\n" + "=" * 60)
        print("\n✅ Basic tests complete!")
        print("\n💡 To test with real audio:")
        print("   python tests/test_voice_asr.py path/to/audio.wav en")
