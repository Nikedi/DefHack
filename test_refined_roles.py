#!/usr/bin/env python3
"""
Test the refined role system with Platoon 2IC for logistics/support
"""

import asyncio
import os
import logging
from DefHack.clarity_opsbot.integrated_system import get_system
from DefHack.clarity_opsbot.user_roles import user_manager, UserRole
from DefHack.clarity_opsbot.leader_notifications import LeaderNotificationSystem

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("dotenv not available, using system environment variables")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

async def test_refined_roles():
    """Test the refined role system with Platoon 2IC"""
    print("⚡ Testing DefHack Refined Role System")
    print("=" * 50)
    
    # Get bot token from environment
    token = os.getenv("TELEGRAM_BOT_TOKEN")
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
        return
    
    # Create system instance
    system = get_system(token)
    await system.initialize()
    
    # User manager is directly imported from user_roles module
    
    # Register test users with different roles
    print("👥 Registering Test Users:")
    user_manager.register_user(10001, "platoon_leader", "John Smith", "Alpha Platoon", UserRole.PLATOON_LEADER)
    user_manager.register_user(10002, "platoon_2ic", "Jane Doe", "Alpha Platoon", UserRole.PLATOON_2IC)
    user_manager.register_user(10003, "observer", "Mike Observer", "Alpha Platoon", UserRole.SOLDIER)
    
    print(f"   ✅ Platoon Leader registered (ID: 10001)")
    print(f"   ✅ Platoon 2IC registered (ID: 10002)")  
    print(f"   ✅ Observer registered (ID: 10003)")
    
    # Test role-specific methods
    print("\n🎯 Testing Role-Specific Targeting:")
    tactical_leaders = user_manager.get_tactical_leaders_for_unit("Alpha Platoon")
    logistics_leaders = user_manager.get_logistics_support_leaders_for_unit("Alpha Platoon")
    
    print(f"   📍 Tactical Leaders (should get enemy reports):")
    for leader in tactical_leaders:
        print(f"      - {leader.username} ({leader.role.value})")
    
    print(f"   📦 Logistics/Support Leaders (should get supply/maintenance reports):")
    for leader in logistics_leaders:
        print(f"      - {leader.username} ({leader.role.value})")
    
    # Test message routing logic
    print("\n📨 Testing Message Routing Logic:")
    
    test_scenarios = [
        ("Enemy spotted in sector 7", "TACTICAL", "Platoon Leader"),
        ("We need MRE resupply", "LOGISTICS", "Platoon 2IC"),
        ("Radio needs maintenance", "SUPPORT", "Platoon 2IC"),
        ("lol that's funny", "BANTER", "Nobody (ignored)"),
    ]
    
    for message, expected_type, expected_recipient in test_scenarios:
        print(f"\n   📝 Message: '{message}'")
        print(f"      Expected Type: {expected_type}")
        print(f"      Expected Recipient: {expected_recipient}")
        
        try:
            # Create mock message
            class MockMessage:
                def __init__(self, text):
                    self.text = text
                    self.photo = []
                    self.location = None
                    from datetime import datetime, timezone
                    self.date = datetime.now(timezone.utc)
            
            # Process message with observer user
            mock_message = MockMessage(message)
            observation = await system.message_processor.process_message(
                mock_message, 10003, 20001, "Alpha Platoon", "observer"
            )
            
            if observation:
                actual_type = getattr(observation, 'message_type', 'TACTICAL').upper()
                print(f"      Actual Type: {actual_type}")
                
                if actual_type == expected_type:
                    print(f"      ✅ Correct classification")
                else:
                    print(f"      ❌ Wrong classification")
                
                # Show routing logic
                if actual_type == "BANTER":
                    print(f"      → Would be ignored completely")
                elif actual_type == "TACTICAL":
                    leaders = user_manager.get_tactical_leaders_for_unit("Alpha Platoon")
                    recipients = [f"{l.username}" for l in leaders]
                    print(f"      → Would notify: {', '.join(recipients) if recipients else 'No tactical leaders'}")
                elif actual_type in ["LOGISTICS", "SUPPORT"]:
                    leaders = user_manager.get_logistics_support_leaders_for_unit("Alpha Platoon")
                    recipients = [f"{l.username}" for l in leaders]
                    print(f"      → Would notify: {', '.join(recipients) if recipients else 'No logistics/support leaders'}")
            else:
                print(f"      ❌ No observation created")
                
        except Exception as e:
            print(f"      ❌ Error: {str(e)}")
    
    print("\n📊 Role System Summary:")
    print("   🎖️ Platoon Leader → Receives TACTICAL observations (enemy activity)")
    print("   ⚡ Platoon 2IC → Receives LOGISTICS & SUPPORT observations (supply/maintenance)")
    print("   🔍 Observer → Sends all types of observations")
    print("   💬 BANTER → Ignored completely by system")
    
    print("\n✅ Refined role system test completed!")

if __name__ == "__main__":
    asyncio.run(test_refined_roles())