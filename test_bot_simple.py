#!/usr/bin/env python3
"""
Simple test script to start the DefHack Telegram bot
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

async def main():
    """Test the bot startup"""
    try:
        from DefHack.clarity_opsbot.integrated_system import DefHackIntegratedSystem
        
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            print("❌ No TELEGRAM_BOT_TOKEN found in environment")
            return
        
        print("🚀 Creating DefHack Telegram Bot...")
        system = DefHackIntegratedSystem(token)
        
        print("✅ Bot created, initializing...")
        await system.initialize()
        
        print("🎯 Bot initialized successfully!")
        print("📡 Starting polling...")        
        
        # Start the bot with proper event loop handling
        await system.app.initialize()
        await system.app.start()
        
        print("✅ Bot is now running and listening for messages!")
        print("Press Ctrl+C to stop...")
        
        # Run the updater
        await system.app.updater.start_polling()
        
        # Keep running until interrupted
        try:
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            print("\n👋 Stopping bot...")
        finally:
            await system.app.updater.stop()
            await system.app.stop()
            await system.app.shutdown()
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())