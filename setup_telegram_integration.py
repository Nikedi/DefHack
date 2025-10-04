#!/usr/bin/env python3
"""
DefHack Telegram Bot Integration Setup and Test Script
Installs dependencies and tests the integration between military LLM functions and Telegram bot
"""

import subprocess
import sys
import os
import asyncio
import logging
from datetime import datetime, timezone

def install_telegram_dependencies():
    """Install required Telegram bot dependencies"""
    print("📦 Installing Telegram bot dependencies...")
    
    packages = [
        "python-telegram-bot[all]",
        "asyncio",
        "python-dotenv"
    ]
    
    for package in packages:
        try:
            print(f"   Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"   ✅ {package} installed successfully")
        except subprocess.CalledProcessError as e:
            print(f"   ❌ Failed to install {package}: {e}")
            return False
    
    print("✅ All dependencies installed successfully!")
    return True

def check_environment_setup():
    """Check if environment variables are properly configured"""
    print("🔧 Checking environment configuration...")
    
    required_vars = [
        "OPENAI_API_KEY",
        "DATABASE_URL"
    ]
    
    optional_vars = [
        "TELEGRAM_BOT_TOKEN",
        "GEMINI_API_KEY"
    ]
    
    missing_required = []
    missing_optional = []
    
    for var in required_vars:
        if not os.getenv(var):
            missing_required.append(var)
        else:
            print(f"   ✅ {var} is set")
    
    for var in optional_vars:
        if not os.getenv(var):
            missing_optional.append(var)
        else:
            print(f"   ✅ {var} is set")
    
    if missing_required:
        print(f"   ❌ Missing required environment variables: {missing_required}")
        print("   💡 Add these to your .env file or environment")
        return False
    
    if missing_optional:
        print(f"   ⚠️  Missing optional environment variables: {missing_optional}")
        print("   💡 These are needed for full Telegram bot functionality")
    
    print("✅ Environment configuration check completed!")
    return True

async def test_defhack_integration():
    """Test the DefHack military LLM integration"""
    print("🧪 Testing DefHack military LLM integration...")
    
    try:
        # Add current directory to Python path
        current_dir = os.path.dirname(os.path.abspath(__file__))
        if current_dir not in sys.path:
            sys.path.insert(0, current_dir)
        
        # Test importing DefHack components
        print("   📦 Testing DefHack imports...")
        
        try:
            from military_operations_integration import DefHackMilitaryOperations
            print("   ✅ Military operations integration imported")
        except ImportError as e:
            print(f"   ❌ Failed to import military operations: {e}")
            return False
        
        try:
            from defhack_unified_input import DefHackClient
            print("   ✅ DefHack client imported")
        except ImportError as e:
            print(f"   ❌ Failed to import DefHack client: {e}")
            return False
        
        # Test DefHack bridge
        print("   🔗 Testing DefHack Telegram bridge...")
        try:
            from DefHack.clarity_opsbot.defhack_bridge import DefHackTelegramBridge
            bridge = DefHackTelegramBridge()
            print("   ✅ DefHack Telegram bridge initialized")
        except Exception as e:
            print(f"   ❌ Failed to initialize bridge: {e}")
            return False
        
        # Test observation processing
        print("   📥 Testing observation processing...")
        test_observation = {
            'target': 'Test Enemy Unit',
            'location': '33S VN 12345 67890',
            'confidence': 75,
            'observer': 'TestScript',
            'time': datetime.now(timezone.utc)
        }
        
        results = await bridge.process_telegram_observation(test_observation)
        
        if results['stored']:
            print("   ✅ Test observation processed and stored")
            print(f"   📤 Telegram message: {results['telegram_message'][:100]}...")
            print(f"   📋 FRAGO generated: {'Yes' if 'FRAGO' in results['frago_order'] else 'No'}")
        else:
            print(f"   ❌ Failed to process observation: {results.get('error', 'Unknown error')}")
            return False
        
        print("✅ DefHack integration test completed successfully!")
        return True
        
    except Exception as e:
        print(f"❌ DefHack integration test failed: {e}")
        return False

def create_sample_env_file():
    """Create a sample .env file with required variables"""
    print("📝 Creating sample .env file...")
    
    env_content = """# DefHack Telegram Bot Environment Configuration
# Copy this to .env and fill in your actual values

# Required for DefHack military LLM functions
OPENAI_API_KEY=your_openai_api_key_here
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/defhack

# Required for Telegram bot functionality  
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here

# Optional - can use OpenAI instead of Gemini
GEMINI_API_KEY=your_gemini_api_key_here

# Bot configuration
BATCH_WINDOW_SECONDS=20
LOG_LEVEL=INFO

# DefHack configuration
MINIO_ENDPOINT=localhost:9000
MINIO_ACCESS_KEY=minio
MINIO_SECRET_KEY=minio123
"""
    
    try:
        with open(".env.sample", "w") as f:
            f.write(env_content)
        print("✅ Sample .env file created as '.env.sample'")
        print("💡 Copy this to '.env' and add your actual API keys")
        return True
    except Exception as e:
        print(f"❌ Failed to create sample .env file: {e}")
        return False

def show_integration_summary():
    """Show summary of integration features and capabilities"""
    print("""
🎉 DEFHACK TELEGRAM BOT INTEGRATION READY!
==========================================

✅ COMPLETED FEATURES:
======================
• Telegram bot merged from telegram_bot branch
• DefHack military LLM functions integrated
• Automatic FRAGO generation from observations
• 24-hour intelligence report generation
• Tactical message analysis and alerting
• Location-based observation processing
• Document citation system ([D:5 p1 ¶4] format)

🤖 AVAILABLE TELEGRAM COMMANDS:
===============================
• /frago  - Generate fragmentary order from recent observations
• /intrep - Generate 24-hour intelligence report
• Location sharing - Automatically logged as MGRS coordinates
• Tactical messages - Auto-analyzed for threats and opportunities

📱 TELEGRAM BOT CAPABILITIES:
============================
• Group chat monitoring for tactical messages
• Automatic threat detection and alerting
• MGRS coordinate extraction from location shares
• Military-grade FRAGO and INTREP generation
• Integration with PostgreSQL DefHack database
• Document-backed intelligence analysis

🔗 INTEGRATION ARCHITECTURE:
============================
• DefHackTelegramBridge: Connects military LLM with Telegram
• Enhanced group handlers: Tactical message processing
• Military operations integration: FRAGO/INTREP generation  
• Document citations: Intelligence document references
• PostgreSQL storage: All observations stored in DefHack DB

🚀 TO START THE TELEGRAM BOT:
============================
1. Set up environment variables in .env file
2. Install dependencies: pip install python-telegram-bot[all]
3. Run: python -m DefHack.clarity_opsbot.bot
4. Add bot to Telegram groups for tactical monitoring

💡 NEXT STEPS:
==============
• Configure Telegram bot token in .env
• Test bot in Telegram group with tactical messages
• Customize FRAGO templates in military_prompt_templates.py
• Add more tactical keywords in enhanced_group.py
• Train team on /frago and /intrep commands

🎯 MILITARY USE CASES:
=====================
• Real-time tactical communications via Telegram
• Automated FRAGO generation from field observations
• 24-hour intelligence summaries for command briefings
• Location-based situational awareness
• Document-backed threat analysis and recommendations
""")

def main():
    """Main setup and test function"""
    print("🚀 DefHack Telegram Bot Integration Setup")
    print("=" * 50)
    
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Step 1: Install dependencies
    if not install_telegram_dependencies():
        print("❌ Setup failed during dependency installation")
        return False
    
    # Step 2: Check environment
    if not check_environment_setup():
        print("⚠️  Environment setup incomplete - bot may not work fully")
    
    # Step 3: Create sample environment file
    create_sample_env_file()
    
    # Step 4: Test DefHack integration
    try:
        success = asyncio.run(test_defhack_integration())
        if not success:
            print("❌ DefHack integration test failed")
            return False
    except Exception as e:
        print(f"❌ Failed to run integration test: {e}")
        return False
    
    # Step 5: Show integration summary
    show_integration_summary()
    
    print("✅ DefHack Telegram Bot integration setup completed successfully!")
    print("🔗 Your military LLM functions are now ready for Telegram integration!")
    
    return True

if __name__ == "__main__":
    success = main()
    if not success:
        sys.exit(1)