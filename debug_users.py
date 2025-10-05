"""
Debug script to see what users are in the system
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from DefHack.clarity_opsbot.user_roles import user_manager

def debug_users():
    """Debug what users are in the system"""
    print("🔍 Debugging User Database")
    print("=" * 40)
    
    # Get all users from internal storage
    print("\n👥 All Users in Internal Storage:")
    all_users = list(user_manager.users.values())
    for user in all_users:
        print(f"   ID: {user.user_id} | Username: {user.username} | Role: {user.role.value} | Unit: {user.unit}")
    
    print(f"\nTotal Users in Memory: {len(all_users)}")
    
    # Check for Alpha Platoon users specifically
    print("\n🎯 Alpha Platoon Users:")
    alpha_users = [user for user in all_users if user.unit == "Alpha Platoon"]
    for user in alpha_users:
        print(f"   ID: {user.user_id} | Username: {user.username} | Role: {user.role.value}")
    
    print(f"Alpha Platoon Users: {len(alpha_users)}")
    
    # Check tactical leaders
    print("\n📍 Tactical Leaders for Alpha Platoon:")
    tactical_leaders = user_manager.get_tactical_leaders_for_unit("Alpha Platoon")
    for leader in tactical_leaders:
        print(f"   ID: {leader.user_id} | Username: {leader.username} | Role: {leader.role.value}")
    
    print(f"Tactical Leaders Count: {len(tactical_leaders)}")
    
    # Check logistics leaders  
    print("\n📦 Logistics Leaders for Alpha Platoon:")
    logistics_leaders = user_manager.get_logistics_support_leaders_for_unit("Alpha Platoon")
    for leader in logistics_leaders:
        print(f"   ID: {leader.user_id} | Username: {leader.username} | Role: {leader.role.value}")
    
    print(f"Logistics Leaders Count: {len(logistics_leaders)}")

if __name__ == "__main__":
    debug_users()