#!/usr/bin/env python3
"""
Simple bot launcher that works better with different Python environments
"""
import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Import the bot system
from DefHack.clarity_opsbot.integrated_system import create_defhack_telegram_system

async def main():
    """Main function to run the bot"""
    try:
        print("🚀 Starting DefHack Telegram Bot...")
        system = create_defhack_telegram_system()
        
        print("🔧 Initializing system...")
        await system.initialize()
        
        if not system.app:
            raise RuntimeError("❌ Failed to create Telegram application")
            
        print("✅ Bot initialized, starting polling...")
        
        # Use run_polling with proper event loop handling
        await system.app.run_polling(
            allowed_updates=['message', 'edited_message', 'callback_query'],
            drop_pending_updates=True,
            close_loop=False
        )
        
    except KeyboardInterrupt:
        print("\n👋 DefHack Telegram Bot shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Check if token exists
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN not found in environment variables")
        sys.exit(1)
    
    print(f"✅ Found Telegram token (length: {len(token)})")
    
    # Run the bot asynchronously
    asyncio.run(main())