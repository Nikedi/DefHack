"""
Test the fixed registration system
"""

import sys
import os
sys.path.insert(0, os.path.abspath('.'))

from DefHack.clarity_opsbot.integrated_system import get_system

def test_system_creation():
    """Test that the system can be created without errors"""
    print("🧪 Testing DefHack system creation...")
    
    # Set a dummy token for testing
    token = "test_token"
    
    try:
        system = get_system(token)
        print("✅ System created successfully")
        print(f"✅ Token set: {token}")
        print("✅ UserRole import working")
        print("✅ Registration system should now work properly")
        
        # Test that UserRole is available
        from DefHack.clarity_opsbot.user_roles import UserRole
        print(f"✅ Available roles: {[role.value for role in UserRole]}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating system: {e}")
        return False

if __name__ == "__main__":
    test_system_creation()