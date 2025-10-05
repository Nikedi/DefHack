#!/usr/bin/env python3
"""
Test the DefHack message classification system
"""

import asyncio
import os
import logging
from DefHack.clarity_opsbot.integrated_system import get_system

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("dotenv not available, using system environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_classification():
    """Test the message classification without running the full bot"""
    print("🧪 Testing DefHack Message Classification System")
    print("=" * 50)
    
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    # Create system instance
    system = get_system(token)
    await system.initialize()
    
    # Test messages
    test_messages = [
        "We're out of MREs",
        "50cal low on ammo", 
        "I want home",
        "Enemy contact at grid 123456",
        "Need toilet paper",
        "Radio is broken",
        "Spotted enemy movement north",
        "Water supply running low",
        "Vehicle needs repair"
    ]
    
    print("\n🔍 Testing Message Classification:")
    print("-" * 30)
    
    for message in test_messages:
        # Test relevance filter
        is_relevant = system._is_relevant_message(message)
        
        if is_relevant:
            # Test classification
            message_type = system._classify_message_type(message)
            
            print(f"📝 '{message}'")
            print(f"   → Relevant: ✅")
            print(f"   → Type: {message_type.upper()}")
            
            if message_type == "logistics":
                print(f"   → Action: Store in database with 'LOGISTICS:' prefix, no leader notifications")
            elif message_type == "support":
                print(f"   → Action: Store in database with 'SUPPORT:' prefix, no leader notifications")
            else:
                print(f"   → Action: Process as tactical, send leader notifications")
        else:
            print(f"📝 '{message}'")
            print(f"   → Relevant: ❌ (filtered out)")
            print(f"   → Action: Ignored completely")
        
        print()
    
    print("✅ Classification system test completed!")
    print("\n📊 Summary:")
    print("• Logistics messages: Prefixed and stored in database only")
    print("• Support messages: Prefixed and stored in database only") 
    print("• Tactical messages: Processed normally with leader notifications")
    print("• Irrelevant messages: Filtered out completely")

if __name__ == "__main__":
    asyncio.run(test_classification())