#!/usr/bin/env python3
"""
Master Test Runner for Trust-Voice

Runs all test suites and provides comprehensive report.
"""

import asyncio
import sys
import os
import logging
from pathlib import Path
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add project to path
sys.path.insert(0, str(Path(__file__).parent.parent))


async def run_all_tests():
    """Run all test suites and generate report."""
    
    print("\n" + "=" * 80)
    print("🚀 TRUST-VOICE COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"📅 Started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("")
    
    test_results = {}
    
    # Test 1: TTS Providers
    print("📦 TEST SUITE 1: TTS Providers (OpenAI & AddisAI)")
    print("-" * 80)
    try:
        from tests.test_tts_providers import test_tts_providers
        result = await test_tts_providers()
        test_results['TTS Providers'] = result
        print("")
    except Exception as e:
        print(f"❌ TTS Providers test failed: {str(e)}")
        test_results['TTS Providers'] = False
        print("")
    
    # Test 2: Language Detection
    print("\n📦 TEST SUITE 2: Language Detection")
    print("-" * 80)
    try:
        from tests.test_language_detection import test_language_detection
        result = test_language_detection()
        test_results['Language Detection'] = result
        print("")
    except Exception as e:
        print(f"❌ Language Detection test failed: {str(e)}")
        test_results['Language Detection'] = False
        print("")
    
    # Test 3: Text Cleaning
    print("\n📦 TEST SUITE 3: Text Cleaning for TTS")
    print("-" * 80)
    try:
        from tests.test_text_cleaning import test_text_cleaning
        result = test_text_cleaning()
        test_results['Text Cleaning'] = result
        print("")
    except Exception as e:
        print(f"❌ Text Cleaning test failed: {str(e)}")
        test_results['Text Cleaning'] = False
        print("")
    
    # Test 4: Dual Delivery (if TEST_TELEGRAM_CHAT_ID is set)
    if os.getenv("TEST_TELEGRAM_CHAT_ID"):
        print("\n📦 TEST SUITE 4: Dual Delivery (Text + Voice)")
        print("-" * 80)
        try:
            from tests.test_dual_delivery_comprehensive import test_dual_delivery
            result = await test_dual_delivery()
            test_results['Dual Delivery'] = result
            print("")
        except Exception as e:
            print(f"❌ Dual Delivery test failed: {str(e)}")
            test_results['Dual Delivery'] = False
            print("")
    else:
        print("\n⏭️  TEST SUITE 4: Dual Delivery - SKIPPED")
        print("-" * 80)
        print("   Set TEST_TELEGRAM_CHAT_ID in .env to run this test")
        print("")
        test_results['Dual Delivery'] = None
    
    # Final Report
    print("\n" + "=" * 80)
    print("📊 FINAL TEST REPORT")
    print("=" * 80)
    print("")
    
    passed = sum(1 for result in test_results.values() if result is True)
    failed = sum(1 for result in test_results.values() if result is False)
    skipped = sum(1 for result in test_results.values() if result is None)
    total = len(test_results)
    
    for suite_name, result in test_results.items():
        if result is True:
            status = "✅ PASSED"
        elif result is False:
            status = "❌ FAILED"
        else:
            status = "⏭️  SKIPPED"
        print(f"  {status:12} │ {suite_name}")
    
    print("")
    print("-" * 80)
    print(f"  Total Suites: {total}")
    print(f"  ✅ Passed: {passed}")
    print(f"  ❌ Failed: {failed}")
    print(f"  ⏭️  Skipped: {skipped}")
    print(f"  📈 Success Rate: {passed/(total-skipped)*100:.1f}%" if total > skipped else "  📈 Success Rate: N/A")
    print("-" * 80)
    print("")
    
    if failed == 0 and passed > 0:
        print("🎉 ALL TESTS PASSED! System is healthy!")
    elif failed == 0:
        print("⚠️  No tests executed. Check configuration.")
    else:
        print(f"⚠️  {failed} test suite(s) failed. Review logs above.")
    
    print("")
    print("=" * 80)
    print(f"📅 Completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 80)
    print("")
    
    # Summary of what was tested
    print("🔍 Test Coverage:")
    print("  • TTS Providers: OpenAI (English) & AddisAI (Amharic)")
    print("  • Language Detection: Auto-detection from text")
    print("  • Text Cleaning: HTML/Markdown removal for TTS")
    print("  • Dual Delivery: Text + Voice integration (if configured)")
    print("")
    
    # System status
    print("📌 System Status:")
    print(f"  • OpenAI TTS: {'✅ Configured' if os.getenv('OPENAI_API_KEY') else '❌ Missing'}")
    print(f"  • AddisAI TTS: {'✅ Configured' if os.getenv('ADDIS_AI_API_KEY') else '❌ Missing'}")
    print(f"  • Telegram Bot: {'✅ Configured' if os.getenv('TELEGRAM_BOT_TOKEN') else '❌ Missing'}")
    print(f"  • Database: {'✅ Configured' if os.getenv('DATABASE_URL') else '❌ Missing'}")
    print("")
    
    return failed == 0 and passed > 0


if __name__ == "__main__":
    try:
        success = asyncio.run(run_all_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Tests interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test runner failed: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
