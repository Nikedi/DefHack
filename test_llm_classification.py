#!/usr/bin/env python3
"""
Test the new LLM-based DefHack message classification system
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

async def test_llm_classification():
    """Test the LLM-based message classification system"""
    print("🤖 Testing LLM-Based DefHack Message Classification")
    print("=" * 60)
    
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    # Create system instance
    system = get_system(token)
    await system.initialize()
    
    # Register a test user to avoid registration warnings
    from DefHack.clarity_opsbot.user_roles import user_manager
    user_manager.register_user(12345, "test_user", "Observer", "Test Unit")
    
    # Comprehensive test messages covering all categories
    test_messages = [
        # BANTER - Should be ignored completely
        ("lol that's funny", "BANTER"),
        ("I want to go home", "BANTER"),
        ("This is boring", "BANTER"),
        ("haha nice one 😂", "BANTER"),
        ("What time do we get off?", "BANTER"),
        ("Anyone seen my phone?", "BANTER"),
        ("Good morning guys", "BANTER"),
        
        # LOGISTICS - Should get LOGISTICS prefix and database-only storage
        ("We're out of MREs", "LOGISTICS"),
        ("50cal is low on ammo", "LOGISTICS"),
        ("Need water resupply", "LOGISTICS"),
        ("Fuel truck hasn't arrived", "LOGISTICS"),
        ("Medical supplies running low", "LOGISTICS"),
        ("Request ammunition resupply", "LOGISTICS"),
        ("Food rations depleted", "LOGISTICS"),
        
        # SUPPORT - Should get SUPPORT prefix and database-only storage
        ("Radio is broken", "SUPPORT"),
        ("Vehicle needs maintenance", "SUPPORT"),
        ("Generator won't start", "SUPPORT"),
        ("Need a medic over here", "SUPPORT"),
        ("Toilet paper is out", "SUPPORT"),
        ("Weapon needs repair", "SUPPORT"),
        ("Communications down", "SUPPORT"),
        
        # TACTICAL - Should trigger leader notifications
        ("Enemy contact at grid 123456", "TACTICAL"),
        ("Spotted hostile patrol north", "TACTICAL"),
        ("Taking fire from building", "TACTICAL"),
        ("Movement in the treeline", "TACTICAL"),
        ("Possible IED on main road", "TACTICAL"),
        ("Sniper activity reported", "TACTICAL"),
        ("Civilian evacuation needed", "TACTICAL"),
    ]
    
    print("\n🔍 Testing LLM Classification vs Expected Results:")
    print("-" * 60)
    
    correct = 0
    total = len(test_messages)
    
    for message, expected_type in test_messages:
        try:
            # Create a simple mock message for testing
            class MockMessage:
                def __init__(self, text):
                    self.text = text
                    self.photo = []
                    self.location = None
                    self.date = asyncio.get_event_loop().time()
                    from datetime import datetime, timezone
                    self.date = datetime.now(timezone.utc)
            
            mock_message = MockMessage(message)
            
            # Process with enhanced processor (this does the LLM classification)
            observation = await system.message_processor.process_message(
                mock_message, 12345, 67890, "Test Group", "test_user"
            )
            
            if observation:
                actual_type = getattr(observation, 'message_type', 'TACTICAL').upper()
                
                # Check if classification matches expected
                is_correct = actual_type == expected_type
                if is_correct:
                    correct += 1
                    status = "✅ CORRECT"
                else:
                    status = "❌ WRONG"
                
                print(f"📝 '{message}'")
                print(f"   Expected: {expected_type} | Actual: {actual_type} | {status}")
                
                # Show what would happen
                if actual_type == "BANTER":
                    print(f"   → Action: Message ignored completely")
                elif actual_type == "LOGISTICS":
                    what = observation.formatted_data.get('what', 'Unknown')
                    print(f"   → Action: Store in DB with 'LOGISTICS:' prefix: {what}")
                elif actual_type == "SUPPORT":
                    what = observation.formatted_data.get('what', 'Unknown')
                    print(f"   → Action: Store in DB with 'SUPPORT:' prefix: {what}")
                elif actual_type == "TACTICAL":
                    print(f"   → Action: Send leader notifications, threat: {observation.threat_level}")
                    
            else:
                print(f"📝 '{message}'")
                print(f"   Expected: {expected_type} | Actual: NO OBSERVATION | ❌ FAILED")
                
            print()
            
        except Exception as e:
            print(f"📝 '{message}'")
            print(f"   Expected: {expected_type} | Error: {str(e)} | ❌ ERROR")
            print()
    
    # Calculate accuracy
    accuracy = (correct / total) * 100
    
    print("📊 LLM Classification Test Results:")
    print(f"   Correct: {correct}/{total}")
    print(f"   Accuracy: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("   🎉 EXCELLENT! LLM classification is working well")
    elif accuracy >= 60:
        print("   ✅ GOOD! LLM classification is mostly working")
    else:
        print("   ⚠️ NEEDS IMPROVEMENT: LLM classification accuracy is low")
    
    print("\n🔧 System Status:")
    print("• LLM-based classification replaces keyword matching")
    print("• BANTER messages are intelligently filtered out")
    print("• LOGISTICS/SUPPORT messages get proper prefixes")
    print("• TACTICAL messages trigger leader notifications")
    print("• Classification happens during JSON conversion phase")

if __name__ == "__main__":
    asyncio.run(test_llm_classification())