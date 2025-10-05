"""
Simple test for role-based targeting without Telegram bot initialization
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from DefHack.clarity_opsbot.user_roles import user_manager, UserRole

def test_role_targeting():
    """Test role-based targeting functionality"""
    print("🎯 Testing Role-Based Targeting System")
    print("=" * 50)
    
    # Clear any existing test users
    print("🧹 Cleaning up existing test users...")
    
    # Register test users with different roles
    print("\n👥 Registering Test Users:")
    user_manager.register_user(20001, "platoon_leader", "John Smith", "Alpha Platoon", UserRole.PLATOON_LEADER)
    user_manager.register_user(20002, "platoon_2ic", "Jane Doe", "Alpha Platoon", UserRole.PLATOON_2IC)
    user_manager.register_user(20003, "observer1", "Mike Observer", "Alpha Platoon", UserRole.SOLDIER)
    user_manager.register_user(20004, "observer2", "Sarah Observer", "Alpha Platoon", UserRole.SOLDIER)
    
    print(f"   ✅ Platoon Leader registered (ID: 20001)")
    print(f"   ✅ Platoon 2IC registered (ID: 20002)")
    print(f"   ✅ Observer 1 registered (ID: 20003)")
    print(f"   ✅ Observer 2 registered (ID: 20004)")
    
    # Test role verification
    print("\n🔍 Verifying Role Assignments:")
    
    users = [
        (20001, "Platoon Leader", UserRole.PLATOON_LEADER),
        (20002, "Platoon 2IC", UserRole.PLATOON_2IC),
        (20003, "Observer 1", UserRole.SOLDIER),
        (20004, "Observer 2", UserRole.SOLDIER)
    ]
    
    for user_id, expected_title, expected_role in users:
        user = user_manager.get_user(user_id)
        if user:
            actual_role = user.role
            status = "✅" if actual_role == expected_role else "❌"
            print(f"   {status} {expected_title}: {actual_role.value} (expected {expected_role.value})")
        else:
            print(f"   ❌ {expected_title}: User not found!")
    
    # Test role-specific targeting methods
    print("\n🎯 Testing Role-Specific Targeting Methods:")
    
    # Test tactical leaders (should get Platoon Leader)
    print("\n   📍 Tactical Leaders (for enemy/combat reports):")
    tactical_leaders = user_manager.get_tactical_leaders_for_unit("Alpha Platoon")
    for leader in tactical_leaders:
        print(f"      - {leader.username} ({leader.full_name}) - Role: {leader.role.value}")
    
    # Test logistics/support leaders (should get Platoon 2IC)
    print("\n   📦 Logistics/Support Leaders (for supply/maintenance reports):")
    logistics_leaders = user_manager.get_logistics_support_leaders_for_unit("Alpha Platoon")
    for leader in logistics_leaders:
        print(f"      - {leader.username} ({leader.full_name}) - Role: {leader.role.value}")
    
    # Test Platoon 2ICs specifically
    print("\n   ⚡ Platoon 2ICs:")
    platoon_2ics = user_manager.get_platoon_2ics()
    for leader in platoon_2ics:
        print(f"      - {leader.username} ({leader.full_name}) - Role: {leader.role.value}")
    
    # Test routing logic summary
    print("\n📊 Message Routing Summary:")
    print("   🎖️ TACTICAL messages → Platoon Leader")
    print("   📦 LOGISTICS messages → Platoon 2IC")
    print("   🔧 SUPPORT messages → Platoon 2IC")
    print("   💬 BANTER messages → Ignored")
    
    # Verify expected counts
    print("\n📈 Targeting Verification:")
    expected_tactical = 1  # Only Platoon Leader
    expected_logistics = 1  # Only Platoon 2IC
    expected_2ics = 1  # Only Platoon 2IC
    
    actual_tactical = len(tactical_leaders)
    actual_logistics = len(logistics_leaders)
    actual_2ics = len(platoon_2ics)
    
    results = [
        ("Tactical Leaders", expected_tactical, actual_tactical),
        ("Logistics Leaders", expected_logistics, actual_logistics),
        ("Platoon 2ICs", expected_2ics, actual_2ics)
    ]
    
    all_correct = True
    for name, expected, actual in results:
        status = "✅" if expected == actual else "❌"
        print(f"   {status} {name}: {actual} (expected {expected})")
        if expected != actual:
            all_correct = False
    
    print(f"\n{'✅ All role targeting tests PASSED!' if all_correct else '❌ Some role targeting tests FAILED!'}")
    
    return all_correct

if __name__ == "__main__":
    test_role_targeting()