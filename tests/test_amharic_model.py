"""
Quick check: Verify Amharic model can be loaded
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from voice.asr.asr_infer import load_amharic_model, verify_amharic_model_cached

print("🔍 Checking Amharic Model...\n")

# Check if cached
print("1️⃣  Checking cache...")
is_cached = verify_amharic_model_cached()

if is_cached:
    print("✅ Model found in cache\n")
else:
    print("⚠️  Model not cached - will download on first use (~1.5GB)\n")

# Try to load the model
print("2️⃣  Loading Amharic model...")
print("   (This may take a few minutes on first run)\n")

try:
    processor, model, device = load_amharic_model()
    print(f"✅ Amharic model loaded successfully!")
    print(f"   Device: {device}")
    print(f"   Model: b1n1yam/shook-medium-amharic-2k")
    print(f"   Ready for Amharic transcription!")
    
except Exception as e:
    print(f"❌ Failed to load model: {e}")

print("\n💡 To test with Amharic audio:")
print("   python tests/test_voice_asr.py path/to/amharic_audio.wav am")
