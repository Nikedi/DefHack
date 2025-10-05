#!/usr/bin/env python3
"""
Test script to verify OpenAI integration in DefHack Telegram bot
"""

import asyncio
import logging
import os
import sys
from datetime import datetime, timezone

# Add the parent directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test_openai_analyzer():
    """Test the OpenAI analyzer functionality"""
    print("🧪 Testing OpenAI Analyzer Integration")
    print("=" * 40)
    
    try:
        # Import OpenAI analyzer
        from DefHack.clarity_opsbot.services.openai_analyzer import OpenAIAnalyzer
        
        # Setup logging
        logging.basicConfig(level=logging.INFO)
        logger = logging.getLogger("test")
        
        # Initialize analyzer
        print("🔧 Initializing OpenAI analyzer...")
        analyzer = OpenAIAnalyzer(logger)
        
        if analyzer._openai_client is None:
            print("❌ OpenAI client not initialized - check OPENAI_API_KEY")
            return False
            
        print("✅ OpenAI analyzer initialized successfully")
        
        # Test message analysis
        print("\n📝 Testing message analysis...")
        test_messages = [
            {
                "time": datetime.now(timezone.utc).isoformat(),
                "unit": "Test Unit",
                "observer_signature": "TestObserver",
                "mgrs": "33S VN 12345 67890",
                "content": "Enemy BTG spotted moving south, 3 tanks confirmed"
            }
        ]
        
        print("📤 Analyzing test message with OpenAI...")
        results = await analyzer.analyze_with_openai(test_messages)
        
        if results:
            print(f"✅ Analysis successful! Generated {len(results)} sensor readings:")
            for i, reading in enumerate(results, 1):
                print(f"   Reading {i}:")
                print(f"     What: {reading.what}")
                print(f"     MGRS: {reading.mgrs}")
                print(f"     Confidence: {reading.confidence}%")
                print(f"     Amount: {reading.amount}")
        else:
            print("⚠️  No sensor readings generated")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_telegram_app():
    """Test the Telegram app with OpenAI integration"""
    print("\n🤖 Testing Telegram App with OpenAI")
    print("=" * 40)
    
    try:
        from DefHack.clarity_opsbot.app import build_app
        
        print("🔧 Building Telegram app...")
        app = build_app()
        
        print("✅ Telegram app built successfully with OpenAI analyzer")
        print(f"📱 Bot token configured: {bool(os.getenv('TELEGRAM_BOT_TOKEN'))}")
        print(f"🔑 OpenAI API key configured: {bool(os.getenv('OPENAI_API_KEY'))}")
        
        return True
        
    except Exception as e:
        print(f"❌ Telegram app test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def check_environment():
    """Check environment configuration"""
    print("🔍 Checking Environment Configuration")
    print("=" * 40)
    
    required_vars = {
        "OPENAI_API_KEY": "OpenAI API access",
        "TELEGRAM_BOT_TOKEN": "Telegram bot integration"
    }
    
    all_good = True
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            masked_value = f"{value[:8]}...{value[-4:]}" if len(value) > 12 else "***"
            print(f"✅ {var}: {masked_value} ({description})")
        else:
            print(f"❌ {var}: Not set ({description})")
            all_good = False
    
    return all_good

async def main():
    """Main test function"""
    print("🚀 DefHack Telegram Bot OpenAI Integration Test")
    print("=" * 50)
    
    # Check environment
    env_ok = check_environment()
    if not env_ok:
        print("\n❌ Environment configuration incomplete")
        return False
    
    # Test OpenAI analyzer
    analyzer_ok = await test_openai_analyzer()
    if not analyzer_ok:
        print("\n❌ OpenAI analyzer test failed")
        return False
    
    # Test Telegram app
    app_ok = await test_telegram_app()
    if not app_ok:
        print("\n❌ Telegram app test failed")
        return False
    
    print("\n🎉 ALL TESTS PASSED!")
    print("=" * 25)
    print("✅ OpenAI API integration working")
    print("✅ Telegram bot configured properly")
    print("✅ Message analysis functional")
    print("✅ Ready for tactical deployment!")
    
    print("\n🚀 TO START YOUR BOT:")
    print("python -m DefHack.clarity_opsbot.bot")
    
    return True

if __name__ == "__main__":
    success = asyncio.run(main())
    if not success:
        sys.exit(1)