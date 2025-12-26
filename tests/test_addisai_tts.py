"""
Test AddisAI TTS API integration.

This script tests the AddisAI TTS endpoint directly to diagnose authentication issues.
"""

import asyncio
import os
import sys
import logging
import httpx
from dotenv import load_dotenv

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))


async def test_addisai_tts_direct():
    """Test AddisAI TTS API directly with different authentication methods."""
    
    logger.info("=" * 60)
    logger.info("Testing AddisAI TTS API")
    logger.info("=" * 60)
    
    # Get config from environment
    api_key = os.getenv("ADDIS_AI_API_KEY")
    base_url = os.getenv("ADDIS_AI_BASE_URL", "https://api.addisassistant.com/api")
    tts_endpoint = os.getenv("ADDIS_AI_TTS_ENDPOINT", "/v1/audio")
    
    if not api_key:
        logger.error("❌ ADDIS_AI_API_KEY not set in .env")
        return False
    
    logger.info(f"API Key: {api_key[:20]}...")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"TTS Endpoint: {tts_endpoint}")
    logger.info(f"Full URL: {base_url}{tts_endpoint}")
    logger.info("")
    
    test_text = "ሰላም! ይህ የአማርኛ የድምጽ ፈተና ነው።"
    
    # Test 1: Bearer token authentication (current method)
    logger.info("=" * 60)
    logger.info("TEST 1: Bearer Token Authentication")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}{tts_endpoint}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "text": test_text,
                    "language": "am"
                }
            )
            
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Headers: {dict(response.headers)}")
            logger.info(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                logger.info(f"✅ TEST 1 PASSED: Bearer auth works!")
                logger.info(f"   Audio size: {len(response.content)} bytes")
                
                # Save test audio
                test_file = "test_addisai_output.mp3"
                with open(test_file, "wb") as f:
                    f.write(response.content)
                logger.info(f"   Saved to: {test_file}")
                return True
            else:
                logger.error(f"❌ TEST 1 FAILED: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ TEST 1 ERROR: {str(e)}")
    
    # Test 2: API Key in header (alternative method)
    logger.info("\n" + "=" * 60)
    logger.info("TEST 2: API-Key Header Authentication")
    logger.info("=" * 60)
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}{tts_endpoint}",
                headers={
                    "API-Key": api_key,
                    "Content-Type": "application/json"
                },
                json={
                    "text": test_text,
                    "language": "am"
                }
            )
            
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                logger.info(f"✅ TEST 2 PASSED: API-Key header works!")
                logger.info(f"   Audio size: {len(response.content)} bytes")
                return True
            else:
                logger.error(f"❌ TEST 2 FAILED: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ TEST 2 ERROR: {str(e)}")
    
    # Test 3: Try different endpoint variations
    logger.info("\n" + "=" * 60)
    logger.info("TEST 3: Try Alternative Endpoints")
    logger.info("=" * 60)
    
    endpoints = [
        "/v1/audio",
        "/v1/audio/speech",
        "/v1/tts",
        "/tts",
        "/audio/speech"
    ]
    
    for endpoint in endpoints:
        logger.info(f"\nTrying: {base_url}{endpoint}")
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(
                    f"{base_url}{endpoint}",
                    headers={
                        "Authorization": f"Bearer {api_key}",
                        "Content-Type": "application/json"
                    },
                    json={
                        "text": test_text,
                        "language": "am"
                    }
                )
                
                logger.info(f"  Status: {response.status_code}")
                
                if response.status_code == 200:
                    logger.info(f"✅ TEST 3 PASSED: Endpoint {endpoint} works!")
                    logger.info(f"   Audio size: {len(response.content)} bytes")
                    logger.info(f"   UPDATE .env with: ADDIS_AI_TTS_ENDPOINT={endpoint}")
                    return True
                elif response.status_code == 404:
                    logger.info(f"  ❌ Not found")
                else:
                    logger.info(f"  ❌ Error: {response.text[:200]}")
                    
        except Exception as e:
            logger.info(f"  ❌ Error: {str(e)}")
    
    # Test 4: Test the chat endpoint to verify API key is valid
    logger.info("\n" + "=" * 60)
    logger.info("TEST 4: Verify API Key with Chat Endpoint")
    logger.info("=" * 60)
    
    chat_endpoint = os.getenv("ADDIS_AI_CHAT_ENDPOINT", "/v1/chat_generate")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                f"{base_url}{chat_endpoint}",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "message": "ሰላም",
                    "language": "am"
                }
            )
            
            logger.info(f"Status: {response.status_code}")
            logger.info(f"Response: {response.text[:500]}")
            
            if response.status_code == 200:
                logger.info(f"✅ TEST 4 PASSED: API key is VALID (chat works)")
                logger.info(f"   This means TTS endpoint/format is wrong")
            elif response.status_code == 401 or response.status_code == 403:
                logger.error(f"❌ TEST 4 FAILED: API key is INVALID")
            else:
                logger.info(f"⚠️  Unexpected status: {response.status_code}")
                
    except Exception as e:
        logger.error(f"❌ TEST 4 ERROR: {str(e)}")
    
    logger.info("\n" + "=" * 60)
    logger.info("DIAGNOSIS COMPLETE")
    logger.info("=" * 60)
    logger.info("")
    logger.info("If no tests passed, possible issues:")
    logger.info("1. API key expired or invalid")
    logger.info("2. TTS endpoint path is wrong")
    logger.info("3. Authentication method is different")
    logger.info("4. TTS feature not enabled for your API key")
    logger.info("")
    logger.info("Next steps:")
    logger.info("- Check AddisAI documentation for correct TTS endpoint")
    logger.info("- Contact AddisAI support to verify TTS access")
    logger.info("- Check if API key needs different permissions")
    
    return False


async def test_addisai_via_provider():
    """Test AddisAI TTS through the TTSProvider class."""
    
    logger.info("\n" + "=" * 60)
    logger.info("TEST 5: AddisAI via TTSProvider")
    logger.info("=" * 60)
    
    try:
        from voice.tts.tts_provider import TTSProvider
        
        provider = TTSProvider()
        logger.info("✅ TTSProvider initialized")
        
        # Test Amharic TTS
        text = "ሰላም! ይህ የአማርኛ የድምጽ ፈተና ነው።"
        logger.info(f"Generating TTS for: {text}")
        
        success, audio_path, error = await provider.generate_speech(text, language="am")
        
        if success:
            logger.info(f"✅ TEST 5 PASSED: TTS generated successfully")
            logger.info(f"   Audio file: {audio_path}")
            logger.info(f"   File exists: {os.path.exists(audio_path)}")
            if os.path.exists(audio_path):
                logger.info(f"   File size: {os.path.getsize(audio_path)} bytes")
            return True
        else:
            logger.error(f"❌ TEST 5 FAILED: {error}")
            return False
            
    except Exception as e:
        logger.error(f"❌ TEST 5 ERROR: {str(e)}", exc_info=True)
        return False


async def main():
    """Run all tests."""
    
    # Test direct API access
    api_success = await test_addisai_tts_direct()
    
    # Test through provider
    provider_success = await test_addisai_via_provider()
    
    logger.info("\n" + "=" * 60)
    logger.info("FINAL RESULTS")
    logger.info("=" * 60)
    logger.info(f"Direct API Tests: {'✅ PASSED' if api_success else '❌ FAILED'}")
    logger.info(f"Provider Test: {'✅ PASSED' if provider_success else '❌ FAILED'}")
    
    return api_success or provider_success


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
