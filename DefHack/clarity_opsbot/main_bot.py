#!/usr/bin/env python3
"""
DefHack Telegram Bot - Complete Military Intelligence System
Main entry point for the integrated tactical intelligence bot
"""

import sys
import os
import logging
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    env_file = project_root / ".env"
    if env_file.exists():
        load_dotenv(env_file)
        print(f"✅ Loaded environment variables from {env_file}")
    else:
        print(f"⚠️ No .env file found at {env_file}")
except ImportError:
    print("⚠️ python-dotenv not installed, skipping .env file loading")
except Exception as e:
    print(f"❌ Error loading .env file: {e}")

def main():
    """Main entry point for DefHack Telegram Bot"""
    
    try:
        # Import the integrated system
        from DefHack.clarity_opsbot.integrated_system import create_defhack_telegram_system
        
        print("🚀 Starting DefHack Military Intelligence Telegram Bot...")
        print("=" * 60)
        
        # Create and start the system
        system = create_defhack_telegram_system()
        
        print("✅ DefHack Telegram System Initialized")
        print("🎯 Bot Features Active:")
        print("   • Tactical message processing (text, photos, locations)")
        print("   • Automatic leader notifications")
        print("   • FRAGO generation on demand")
        print("   • Intelligence summaries for higher echelon")
        print("   • User role management and permissions")
        print("   • Integration with DefHack database")
        print("   • OpenAI-powered analysis")
        print("")
        print("📱 Add bot to Telegram groups and start tactical operations!")
        print("🔐 Users must register with /register in private messages")
        print("")
        print("🎖️ DefHack Military Intelligence Bot - OPERATIONAL")
        print("=" * 60)
        
        # Start the bot
        system.run()
        
    except KeyboardInterrupt:
        print("\n👋 DefHack Telegram Bot shutting down...")
        print("🎯 System stopped by user")
        
    except Exception as e:
        print(f"❌ Critical error starting DefHack Telegram Bot: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()