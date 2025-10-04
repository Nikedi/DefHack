"""
User Role Management System for DefHack Telegram Bot
Handles Platoon Leaders, Higher Echelon, and regular soldiers
"""

import json
import logging
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, asdict
import os

class UserRole(Enum):
    """User roles in the military hierarchy"""
    SOLDIER = "soldier"
    PLATOON_LEADER = "platoon_leader"
    PLATOON_2IC = "platoon_2ic"  # Platoon Second in Command
    COMPANY_COMMANDER = "company_commander"
    BATTALION_STAFF = "battalion_staff"
    HIGHER_ECHELON = "higher_echelon"
    ADMIN = "admin"

@dataclass
class UserProfile:
    """User profile with military role and metadata"""
    user_id: int
    username: str
    full_name: str
    role: UserRole
    unit: str
    rank: Optional[str] = None
    callsign: Optional[str] = None
    registered_at: Optional[datetime] = None
    last_active: Optional[datetime] = None
    phone_number: Optional[str] = None
    
    def to_dict(self) -> dict:
        data = asdict(self)
        data['role'] = self.role.value
        if self.registered_at:
            data['registered_at'] = self.registered_at.isoformat()
        if self.last_active:
            data['last_active'] = self.last_active.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: dict) -> 'UserProfile':
        # Convert role string back to enum
        if 'role' in data:
            data['role'] = UserRole(data['role'])
        # Convert datetime strings back to datetime objects
        if 'registered_at' in data and isinstance(data['registered_at'], str):
            data['registered_at'] = datetime.fromisoformat(data['registered_at'])
        if 'last_active' in data and isinstance(data['last_active'], str):
            data['last_active'] = datetime.fromisoformat(data['last_active'])
        return cls(**data)

class UserRoleManager:
    """Manages user roles and permissions for the DefHack Telegram bot"""
    
    def __init__(self, storage_file: str = "user_roles.json"):
        self.storage_file = storage_file
        self.users: Dict[int, UserProfile] = {}
        self.logger = logging.getLogger(__name__)
        self.load_users()
    
    def load_users(self) -> None:
        """Load user profiles from storage"""
        try:
            if os.path.exists(self.storage_file):
                with open(self.storage_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    for user_id_str, user_data in data.items():
                        user_id = int(user_id_str)
                        self.users[user_id] = UserProfile.from_dict(user_data)
                self.logger.info(f"Loaded {len(self.users)} user profiles")
            else:
                self.logger.info("No existing user profiles found, starting fresh")
        except Exception as e:
            self.logger.error(f"Failed to load user profiles: {e}")
    
    def save_users(self) -> None:
        """Save user profiles to storage"""
        try:
            data = {}
            for user_id, profile in self.users.items():
                data[str(user_id)] = profile.to_dict()
            
            with open(self.storage_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.debug(f"Saved {len(self.users)} user profiles")
        except Exception as e:
            self.logger.error(f"Failed to save user profiles: {e}")
    
    def register_user(self, user_id: int, username: str, full_name: str, 
                     unit: str, role: UserRole = UserRole.SOLDIER,
                     rank: Optional[str] = None, callsign: Optional[str] = None,
                     phone_number: Optional[str] = None) -> UserProfile:
        """Register a new user or update existing user"""
        now = datetime.now(timezone.utc)
        
        if user_id in self.users:
            # Update existing user
            profile = self.users[user_id]
            profile.username = username
            profile.full_name = full_name
            profile.unit = unit
            profile.role = role
            if rank:
                profile.rank = rank
            if callsign:
                profile.callsign = callsign
            if phone_number:
                profile.phone_number = phone_number
            profile.last_active = now
        else:
            # Create new user
            profile = UserProfile(
                user_id=user_id,
                username=username,
                full_name=full_name,
                role=role,
                unit=unit,
                rank=rank,
                callsign=callsign,
                registered_at=now,
                last_active=now,
                phone_number=phone_number
            )
            self.users[user_id] = profile
        
        self.save_users()
        self.logger.info(f"Registered user {username} ({user_id}) as {role.value}")
        return profile
    
    def get_user(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile by ID"""
        return self.users.get(user_id)
    
    def update_user_activity(self, user_id: int) -> None:
        """Update user's last activity timestamp"""
        if user_id in self.users:
            self.users[user_id].last_active = datetime.now(timezone.utc)
            self.save_users()
    
    def set_user_role(self, user_id: int, role: UserRole) -> bool:
        """Change a user's role"""
        if user_id in self.users:
            self.users[user_id].role = role
            self.save_users()
            self.logger.info(f"Updated user {user_id} role to {role.value}")
            return True
        return False
    
    def get_users_by_role(self, role: UserRole) -> List[UserProfile]:
        """Get all users with a specific role"""
        return [profile for profile in self.users.values() if profile.role == role]
    
    def get_platoon_leaders(self) -> List[UserProfile]:
        """Get all platoon leaders"""
        return self.get_users_by_role(UserRole.PLATOON_LEADER)
    
    def get_platoon_2ics(self) -> List[UserProfile]:
        """Get all platoon 2ICs (Second in Command)"""
        return self.get_users_by_role(UserRole.PLATOON_2IC)
    
    def get_higher_echelon_users(self) -> List[UserProfile]:
        """Get all higher echelon users (company commander and above)"""
        higher_roles = [
            UserRole.COMPANY_COMMANDER,
            UserRole.BATTALION_STAFF, 
            UserRole.HIGHER_ECHELON
        ]
        return [profile for profile in self.users.values() if profile.role in higher_roles]
    
    def get_leaders_for_unit(self, unit: str) -> List[UserProfile]:
        """Get leaders (platoon leader and above) for a specific unit"""
        leader_roles = [
            UserRole.PLATOON_LEADER,
            UserRole.PLATOON_2IC,
            UserRole.COMPANY_COMMANDER,
            UserRole.BATTALION_STAFF,
            UserRole.HIGHER_ECHELON
        ]
        return [
            profile for profile in self.users.values() 
            if profile.role in leader_roles and profile.unit == unit
        ]
    
    def is_leader(self, user_id: int) -> bool:
        """Check if user is a leader (platoon leader or higher)"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        leader_roles = [
            UserRole.PLATOON_LEADER,
            UserRole.PLATOON_2IC,
            UserRole.COMPANY_COMMANDER,
            UserRole.BATTALION_STAFF,
            UserRole.HIGHER_ECHELON,
            UserRole.ADMIN
        ]
        return user.role in leader_roles
    
    def get_tactical_leaders_for_unit(self, unit: str) -> List[UserProfile]:
        """Get leaders who should receive tactical observations (Platoon Leaders) for a specific unit"""
        tactical_leader_roles = [UserRole.PLATOON_LEADER]
        return [
            profile for profile in self.users.values() 
            if profile.role in tactical_leader_roles and profile.unit == unit
        ]
    
    def get_logistics_support_leaders_for_unit(self, unit: str) -> List[UserProfile]:
        """Get leaders who should receive logistics/support observations (Platoon 2ICs) for a specific unit"""
        logistics_support_roles = [UserRole.PLATOON_2IC]
        return [
            profile for profile in self.users.values() 
            if profile.role in logistics_support_roles and profile.unit == unit
        ]
    
    def is_higher_echelon(self, user_id: int) -> bool:
        """Check if user is higher echelon (company commander and above)"""
        user = self.get_user(user_id)
        if not user:
            return False
        
        higher_roles = [
            UserRole.COMPANY_COMMANDER,
            UserRole.BATTALION_STAFF,
            UserRole.HIGHER_ECHELON,
            UserRole.ADMIN
        ]
        return user.role in higher_roles
    
    def can_request_frago(self, user_id: int) -> bool:
        """Check if user can request FRAGO generation"""
        return self.is_leader(user_id)
    
    def can_request_intelligence_summary(self, user_id: int) -> bool:
        """Check if user can request intelligence summaries"""
        return self.is_higher_echelon(user_id)
    
    def get_user_statistics(self) -> Dict[str, int]:
        """Get statistics about registered users"""
        stats = {}
        for role in UserRole:
            stats[role.value] = len(self.get_users_by_role(role))
        stats['total'] = len(self.users)
        return stats
    
    def format_user_info(self, user_id: int) -> str:
        """Format user information for display"""
        user = self.get_user(user_id)
        if not user:
            return "❌ User not registered"
        
        info = [
            f"👤 **User Profile**",
            f"📛 Name: {user.full_name}",
            f"🆔 Username: @{user.username}",
            f"🎖️ Role: {user.role.value.replace('_', ' ').title()}",
            f"🏛️ Unit: {user.unit}"
        ]
        
        if user.rank:
            info.append(f"📊 Rank: {user.rank}")
        if user.callsign:
            info.append(f"📻 Callsign: {user.callsign}")
        if user.registered_at:
            info.append(f"📅 Registered: {user.registered_at.strftime('%Y-%m-%d %H:%M')}")
        if user.last_active:
            info.append(f"🕐 Last Active: {user.last_active.strftime('%Y-%m-%d %H:%M')}")
        
        return "\n".join(info)

# Global instance for easy access
user_manager = UserRoleManager()