import asyncio
import os
import signal
import sys
from DefHack.clarity_opsbot.integrated_system import get_system

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("dotenv not available, using system environment variables")


def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"\n🛑 Received signal {signum}, shutting down...")
    sys.exit(0)


def main():
    """Main entry point for DefHack bot"""
    print("🚀 Starting DefHack bot...")
    
    # Set up signal handlers for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    print(f"✅ Bot token loaded: {token[:10]}...")
    
    # Create system
    print("📦 Creating system...")
    system = get_system(token)
    
    # Initialize system in a new event loop
    print("⚡ Initializing system...")
    async def init():
        await system.initialize()
    
    asyncio.run(init())
    print("🚀 Starting bot polling...")
    
    # Start polling - this manages its own event loop
    system.app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
