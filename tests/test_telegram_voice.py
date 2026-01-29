#!/usr/bin/env python3
"""
Test script to send voice messages to Telegram bot
Requires your Telegram user ID and the bot's credentials
"""
import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv
from telegram import Bot
import openai

load_dotenv()

# Your credentials
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
YOUR_TELEGRAM_USER_ID = os.getenv("TEST_USER_ID", "5753848438")  # Your Telegram ID

# Test scenarios
TEST_SCENARIOS = [
    {
        "name": "Create Campaign - Multi-turn",
        "messages": [
            "I want to create a campaign",
            # Bot should ask: "What is the campaign title?"
            "Clean Water for Congo Villages",
            # Bot should ask for more details
        ]
    },
    {
        "name": "Donate - Complete Info",
        "messages": [
            "I want to donate 50 dollars to campaign number one"
        ]
    },
    {
        "name": "Search Campaigns",
        "messages": [
            "Show me water campaigns in Kenya"
        ]
    }
]


async def generate_voice_from_text(text: str, output_path: Path) -> bool:
    """Generate voice file from text using OpenAI TTS"""
    try:
        client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        
        response.stream_to_file(str(output_path))
        return True
    except Exception as e:
        print(f"❌ Error generating voice: {e}")
        return False


async def send_voice_to_bot(bot: Bot, chat_id: str, voice_file: Path, text: str):
    """Send a voice message to the bot"""
    print(f"\n📤 Sending: \"{text}\"")
    
    with open(voice_file, 'rb') as audio:
        message = await bot.send_voice(
            chat_id=chat_id,
            voice=audio,
            caption=f"Test: {text}"
        )
    
    print(f"✅ Sent message ID: {message.message_id}")
    return message


async def test_scenario(bot: Bot, scenario: dict, temp_dir: Path):
    """Test a complete scenario"""
    print("\n" + "="*60)
    print(f"🧪 Testing: {scenario['name']}")
    print("="*60)
    
    for idx, message_text in enumerate(scenario['messages'], 1):
        # Generate voice file
        voice_file = temp_dir / f"test_{idx}.ogg"
        
        print(f"\n{idx}. Generating voice for: \"{message_text}\"")
        if not await generate_voice_from_text(message_text, voice_file):
            print("❌ Failed to generate voice")
            continue
        
        # Send to bot
        await send_voice_to_bot(bot, YOUR_TELEGRAM_USER_ID, voice_file, message_text)
        
        # Wait for bot response
        print("⏳ Waiting for bot response (check Telegram)...")
        await asyncio.sleep(5)  # Give bot time to process
        
        # Clean up
        voice_file.unlink()
    
    print(f"\n✅ Scenario complete: {scenario['name']}")
    print("Check your Telegram for the bot's responses!")


async def main():
    """Main test function"""
    if not TELEGRAM_BOT_TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN not set in .env")
        return
    
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ OPENAI_API_KEY not set in .env")
        return
    
    print("🤖 TrustVoice Bot - Voice Message Tester")
    print(f"📱 Sending to Telegram user: {YOUR_TELEGRAM_USER_ID}")
    print()
    
    # Create temp directory for voice files
    temp_dir = Path("temp_test_audio")
    temp_dir.mkdir(exist_ok=True)
    
    # Initialize bot
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    
    try:
        # Test each scenario
        for scenario in TEST_SCENARIOS:
            await test_scenario(bot, scenario, temp_dir)
            print("\n⏸️  Pausing 10 seconds before next scenario...")
            await asyncio.sleep(10)
        
        print("\n" + "="*60)
        print("✅ All tests completed!")
        print("Check your Telegram conversation with the bot for results.")
        print("="*60)
        
    finally:
        # Cleanup
        if temp_dir.exists():
            for file in temp_dir.glob("*"):
                file.unlink()
            temp_dir.rmdir()


if __name__ == "__main__":
    asyncio.run(main())
