#!/usr/bin/env python3
"""
Debug script to check leader notification system
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Debug leader notification issues"""
    try:
        from DefHack.clarity_opsbot.user_roles import UserRoleManager
        
        # Create a separate instance to avoid interfering with the running bot
        user_manager = UserRoleManager()
        
        print("🔍 DefHack Leader Notification Debug")
        print("=" * 50)
        
        # Check all registered users
        print("📊 Registered Users:")
        stats = user_manager.get_user_statistics()
        for role, count in stats.items():
            if count > 0:
                print(f"   {role.replace('_', ' ').title()}: {count}")
        
        print(f"\nTotal users: {stats['total']}")
        print()
        
        # List all users with details
        print("👥 User Details:")
        for user_id, profile in user_manager.users.items():
            print(f"   User ID: {user_id}")
            print(f"   Name: {profile.full_name}")
            print(f"   Username: @{profile.username}")
            print(f"   Role: {profile.role.value}")
            print(f"   Unit: {profile.unit}")
            print(f"   Is Leader: {user_manager.is_leader(user_id)}")
            print()
        
        # Test leader lookup for different units
        print("🎯 Leader Lookup Test:")
        test_units = ["Alpha Company", "Bravo Company", "Charlie Company", "Unknown"]
        
        # Add all actual user units to the test
        actual_units = set()
        for profile in user_manager.users.values():
            actual_units.add(profile.unit)
        test_units.extend(list(actual_units))
        
        for unit in test_units:
            leaders = user_manager.get_leaders_for_unit(unit)
            print(f"   Unit '{unit}': {len(leaders)} leaders")
            for leader in leaders:
                print(f"      - {leader.full_name} ({leader.role.value})")
        
        print("\n✅ Debug completed!")
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()