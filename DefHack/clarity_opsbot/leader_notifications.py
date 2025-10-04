"""
Leader Notification Workflow System for DefHack Telegram Bot
Handles automatic notifications to leaders and FRAGO request capability
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from enum import Enum
import json

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

class NotificationPriority(Enum):
    """Priority levels for leader notifications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class NotificationType(Enum):
    """Types of notifications"""
    NEW_OBSERVATION = "new_observation"
    THREAT_ALERT = "threat_alert"
    FRAGO_REQUEST = "frago_request"
    INTELLIGENCE_UPDATE = "intelligence_update"

class PendingFragoRequest:
    """Represents a pending FRAGO request"""
    def __init__(self, observation_id: str, leader_user_id: int, 
                 observation_data: dict, requested_at: datetime):
        self.observation_id = observation_id
        self.leader_user_id = leader_user_id
        self.observation_data = observation_data
        self.requested_at = requested_at
        self.status = "pending"  # pending, approved, denied, generated

class LeaderNotificationSystem:
    """Manages notifications to military leaders"""
    
    def __init__(self, bot_application, logger: logging.Logger):
        self.bot = bot_application.bot
        self.logger = logger
        self.pending_frago_requests: Dict[str, PendingFragoRequest] = {}
        
        # Import here to avoid circular imports
        try:
            from .user_roles import user_manager
            from .enhanced_processor import ProcessedObservation
            from .defhack_bridge import DefHackTelegramBridge
            
            self.user_manager = user_manager
            self.defhack_bridge = DefHackTelegramBridge()
        except ImportError as e:
            self.logger.error(f"Failed to import required modules: {e}")
    
    async def process_new_observation(self, observation: 'ProcessedObservation', 
                                    chat_id: int) -> None:
        """
        Process a new observation and send notifications to appropriate leaders
        """
        try:
            # Store observation in DefHack database first and capture raw data for debugging
            observation_id, raw_db_data = await self._store_observation_in_database(observation)
            
            # Determine notification priority based on threat level
            priority = self._determine_priority(observation)
            
            # Get appropriate leaders to notify
            leaders_to_notify = self._get_leaders_to_notify(observation)
            
            if not leaders_to_notify:
                self.logger.warning(f"No leaders found to notify for observation from {observation.username}")
                return
            
            # Send notifications to leaders
            for leader in leaders_to_notify:
                await self._send_leader_notification(
                    leader_user_id=leader.user_id,
                    observation=observation,
                    priority=priority,
                    original_chat_id=chat_id,
                    observation_id=observation_id,
                    raw_db_data=raw_db_data
                )
            
            self.logger.info(f"Sent notifications to {len(leaders_to_notify)} leaders for observation from {observation.username}")
            
        except Exception as e:
            self.logger.error(f"Failed to process observation notification: {e}")
    
    async def _store_observation_in_database(self, observation: 'ProcessedObservation') -> tuple[str, dict]:
        """Store observation in DefHack database and return observation ID and raw data"""
        try:
            # Convert ProcessedObservation to format expected by DefHack
            observation_data = {
                'what': observation.formatted_data.get('what', 'Unknown'),
                'mgrs': observation.mgrs,
                'confidence': observation.formatted_data.get('confidence', 50),
                'observer_signature': observation.username,
                'time': observation.timestamp,
                'amount': observation.formatted_data.get('amount'),
                'unit': observation.unit,
                'processing_method': observation.processing_method,
                'threat_level': observation.threat_level,
                'original_message': observation.original_message
            }
            
            # Use DefHack bridge to store the observation
            results = await self.defhack_bridge.process_telegram_observation(observation_data)
            
            if results.get('stored'):
                return results.get('observation_id', 'unknown'), observation_data
            else:
                raise Exception("Failed to store observation in database")
                
        except Exception as e:
            self.logger.error(f"Database storage failed: {e}")
            raise
    
    def _determine_priority(self, observation: 'ProcessedObservation') -> NotificationPriority:
        """Determine notification priority based on observation characteristics"""
        threat_level = observation.threat_level.upper()
        
        if threat_level == 'CRITICAL':
            return NotificationPriority.CRITICAL
        elif threat_level == 'HIGH':
            return NotificationPriority.HIGH
        elif threat_level == 'MEDIUM':
            return NotificationPriority.MEDIUM
        else:
            return NotificationPriority.LOW
    
    def _get_leaders_to_notify(self, observation: 'ProcessedObservation') -> List:
        """Get list of leaders who should be notified about this observation"""
        # Get leaders for the observer's unit
        unit_leaders = self.user_manager.get_leaders_for_unit(observation.unit)
        
        # For high-priority observations, also notify higher echelon
        if observation.threat_level in ['HIGH', 'CRITICAL']:
            higher_echelon = self.user_manager.get_higher_echelon_users()
            unit_leaders.extend(higher_echelon)
        
        # Remove duplicates
        seen_user_ids = set()
        unique_leaders = []
        for leader in unit_leaders:
            if leader.user_id not in seen_user_ids:
                unique_leaders.append(leader)
                seen_user_ids.add(leader.user_id)
        
        return unique_leaders
    
    async def _send_leader_notification(self, leader_user_id: int, 
                                      observation: 'ProcessedObservation',
                                      priority: NotificationPriority,
                                      original_chat_id: int,
                                      observation_id: str = None,
                                      raw_db_data: dict = None) -> None:
        """Send notification to a specific leader with debugging info"""
        try:
            # Format notification message
            notification_msg = self._format_leader_notification(observation, priority, observation_id)
            
            # Send notification
            await self.bot.send_message(
                chat_id=leader_user_id,
                text=notification_msg,
                parse_mode='HTML'
            )
            
            # Send debugging information with raw database data
            if raw_db_data and observation_id:
                debug_msg = f"🔧 <b>RAW DATABASE INPUT - Entry {observation_id}:</b>\n<code>"
                for key, value in raw_db_data.items():
                    if key == 'time' and hasattr(value, 'isoformat'):
                        debug_msg += f"{key}: {value.isoformat()}\n"
                    else:
                        debug_msg += f"{key}: {str(value)[:100]}{'...' if len(str(value)) > 100 else ''}\n"
                debug_msg += "</code>"
                
                await self.bot.send_message(
                    chat_id=leader_user_id,
                    text=debug_msg,
                    parse_mode='HTML'
                )
                
                # Send clean human-readable version without JSON formatting
                clean_msg = f"📋 <b>HUMAN READABLE - Entry {observation_id}:</b>\n\n"
                clean_msg += f"<b>What was seen:</b> {raw_db_data.get('what', 'Unknown')}\n"
                mgrs_value = raw_db_data.get('mgrs')
                clean_msg += f"<b>Location:</b> {mgrs_value if mgrs_value is not None else 'No location provided'}\n"
                clean_msg += f"<b>Observer:</b> {raw_db_data.get('observer_signature', 'Unknown')}\n"
                clean_msg += f"<b>Time:</b> {raw_db_data.get('time', 'Unknown')}\n"
                clean_msg += f"<b>Unit:</b> {raw_db_data.get('unit', 'Unknown')}\n"
                clean_msg += f"<b>Confidence:</b> {raw_db_data.get('confidence', 'Unknown')}%\n"
                clean_msg += f"<b>Threat Level:</b> {raw_db_data.get('threat_level', 'Unknown')}\n"
                if raw_db_data.get('amount'):
                    clean_msg += f"<b>Quantity:</b> {raw_db_data.get('amount')}\n"
                clean_msg += f"<b>Processing:</b> {raw_db_data.get('processing_method', 'Unknown')}\n"
                original_msg = raw_db_data.get('original_message')
                clean_msg += f"<b>Original Message:</b> {original_msg if original_msg is not None else 'N/A (sensor data)'}"
                
                await self.bot.send_message(
                    chat_id=leader_user_id,
                    text=clean_msg,
                    parse_mode='HTML'
                )
            
            self.logger.info(f"Sent {priority.value} priority notification to leader {leader_user_id}")
            
        except Exception as e:
            self.logger.error(f"Failed to send notification to leader {leader_user_id}: {e}")
    
    def _format_leader_notification(self, observation: 'ProcessedObservation', 
                                  priority: NotificationPriority, observation_id: str = None) -> str:
        """Format the notification message for leaders"""
        priority_emoji = {
            NotificationPriority.CRITICAL: "🚨",
            NotificationPriority.HIGH: "⚠️",
            NotificationPriority.MEDIUM: "📢",
            NotificationPriority.LOW: "ℹ️"
        }
        
        emoji = priority_emoji.get(priority, "📢")
        
        formatted_time = observation.timestamp.strftime("%H:%M %d-%m-%Y")
        
        message = f"{emoji} <b>TACTICAL OBSERVATION - {priority.value.upper()} PRIORITY</b>\n\n"
        message += f"<b>Observer:</b> {observation.username}\n"
        message += f"<b>Unit:</b> {observation.unit}\n"
        message += f"<b>Time:</b> {formatted_time}\n"
        message += f"<b>Location:</b> {observation.mgrs}\n"
        message += f"<b>Threat Level:</b> {observation.threat_level}\n\n"
        
        message += f"<b>Observation:</b> {observation.formatted_data.get('what', 'Unknown')}\n"
        
        if observation.formatted_data.get('amount'):
            message += f"<b>Quantity:</b> {observation.formatted_data['amount']}\n"
        
        message += f"<b>Confidence:</b> {observation.formatted_data.get('confidence', 50)}%\n"
        message += f"<b>Processing:</b> {observation.processing_method.replace('_', ' ').title()}\n\n"
        
        if observation.original_message and observation.original_message != observation.formatted_data.get('what', ''):
            message += f"<b>Original Report:</b> {observation.original_message[:200]}{'...' if len(observation.original_message) > 200 else ''}\n\n"
        
        if observation_id:
            message += f"<b>Database ID:</b> {observation_id}\n\n"
        
        message += "<b>Action Required:</b> Review observation and determine if FRAGO is needed."
        
        return message
    
    def _create_frago_request_keyboard(self, observer_user_id: int, 
                                     chat_id: int, observation_time: str) -> InlineKeyboardMarkup:
        """Create inline keyboard for FRAGO request"""
        # Create unique callback data
        callback_data = f"frago_req_{observer_user_id}_{chat_id}_{observation_time}"
        
        keyboard = [
            [
                InlineKeyboardButton("📋 Generate FRAGO", callback_data=callback_data),
                InlineKeyboardButton("❌ No Action", callback_data=f"no_action_{callback_data}")
            ],
            [
                InlineKeyboardButton("📊 Get Details", callback_data=f"details_{callback_data}")
            ]
        ]
        
        return InlineKeyboardMarkup(keyboard)
    
    async def handle_frago_request(self, update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle FRAGO generation request from leader"""
        query = update.callback_query
        await query.answer()
        
        try:
            callback_data = query.data
            
            if callback_data.startswith("frago_req_"):
                # Parse callback data
                parts = callback_data.split("_", 2)
                if len(parts) >= 3:
                    observer_user_id = int(parts[2].split("_")[0])
                    chat_id = int(parts[2].split("_")[1])
                    observation_time = "_".join(parts[2].split("_")[2:])
                    
                    await self._generate_and_send_frago(
                        query.from_user.id, 
                        observer_user_id, 
                        chat_id, 
                        observation_time,
                        query.message.chat_id
                    )
            
            elif callback_data.startswith("no_action_"):
                await query.edit_message_text(
                    text=query.message.text + "\n\n✅ **Status:** No action taken by leader",
                    parse_mode='Markdown'
                )
            
            elif callback_data.startswith("details_"):
                await self._send_detailed_observation_info(query)
                
        except Exception as e:
            self.logger.error(f"Error handling FRAGO request: {e}")
            await query.edit_message_text("❌ Error processing request. Please try again.")
    
    async def _generate_and_send_frago(self, leader_user_id: int, observer_user_id: int,
                                     chat_id: int, observation_time: str, 
                                     notification_chat_id: int) -> None:
        """Generate and send FRAGO to the leader"""
        try:
            # Get observation data (this would typically query the database)
            observation_data = await self._get_observation_data(
                observer_user_id, chat_id, observation_time
            )
            
            if not observation_data:
                await self.bot.send_message(
                    chat_id=notification_chat_id,
                    text="❌ Could not retrieve observation data for FRAGO generation."
                )
                return
            
            # Generate FRAGO using DefHack military functions
            frago_results = await self.defhack_bridge.process_telegram_observation(observation_data)
            
            if 'frago_order' in frago_results:
                frago_message = f"📋 **FRAGMENTARY ORDER (FRAGO)**\n\n{frago_results['frago_order']}"
                
                # Send FRAGO to leader
                await self.bot.send_message(
                    chat_id=notification_chat_id,
                    text=frago_message,
                    parse_mode='Markdown'
                )
                
                # Update original notification
                await self.bot.edit_message_text(
                    chat_id=notification_chat_id,
                    message_id=notification_chat_id,  # This would need to be stored
                    text=f"✅ **FRAGO Generated and Sent**\n\nGenerated at: {datetime.now(timezone.utc).strftime('%H:%M %d-%m-%Y')}",
                    parse_mode='Markdown'
                )
                
                self.logger.info(f"Generated and sent FRAGO to leader {leader_user_id}")
            else:
                await self.bot.send_message(
                    chat_id=notification_chat_id,
                    text="❌ FRAGO generation failed. Please try again or create manually."
                )
                
        except Exception as e:
            self.logger.error(f"FRAGO generation failed: {e}")
            await self.bot.send_message(
                chat_id=notification_chat_id,
                text="❌ FRAGO generation encountered an error. Please try again."
            )
    
    async def _get_observation_data(self, observer_user_id: int, chat_id: int, 
                                  observation_time: str) -> Optional[Dict]:
        """Retrieve observation data for FRAGO generation"""
        # This would typically query the DefHack database
        # For now, return a placeholder structure
        return {
            'what': 'Recent tactical observation',
            'mgrs': 'UNKNOWN',
            'confidence': 70,
            'observer_signature': f'User_{observer_user_id}',
            'time': datetime.now(timezone.utc),
            'unit': 'Unknown Unit'
        }
    
    async def _send_detailed_observation_info(self, query) -> None:
        """Send detailed observation information"""
        detail_message = (
            "📊 **Detailed Observation Information**\n\n"
            "For more detailed analysis and historical context:\n"
            "• Use /intrep for intelligence reports\n"
            "• Contact S2 for threat analysis\n"
            "• Review similar observations in DefHack database\n\n"
            "**Available Commands:**\n"
            "/intrep - 24-hour intelligence summary\n"
            "/status - Current threat status\n"
            "/help - Available commands"
        )
        
        await query.edit_message_text(
            text=detail_message,
            parse_mode='Markdown'
        )
    
    async def send_intelligence_alert(self, threat_level: str, message: str, 
                                    target_roles: List[str] = None) -> None:
        """Send intelligence alerts to specified user roles"""
        if target_roles is None:
            target_roles = ['platoon_leader', 'company_commander', 'higher_echelon']
        
        try:
            # Get users by roles
            target_users = []
            for role_name in target_roles:
                role = getattr(self.user_manager.UserRole, role_name.upper(), None)
                if role:
                    target_users.extend(self.user_manager.get_users_by_role(role))
            
            # Remove duplicates
            unique_users = {user.user_id: user for user in target_users}.values()
            
            # Format alert message
            alert_emoji = "🚨" if threat_level in ['HIGH', 'CRITICAL'] else "⚠️"
            alert_message = f"{alert_emoji} **INTELLIGENCE ALERT - {threat_level}**\n\n{message}"
            
            # Send to all target users
            for user in unique_users:
                try:
                    await self.bot.send_message(
                        chat_id=user.user_id,
                        text=alert_message,
                        parse_mode='Markdown'
                    )
                except Exception as e:
                    self.logger.error(f"Failed to send alert to user {user.user_id}: {e}")
            
            self.logger.info(f"Sent {threat_level} intelligence alert to {len(unique_users)} users")
            
        except Exception as e:
            self.logger.error(f"Failed to send intelligence alert: {e}")

# Global instance for easy access
leader_notification_system = None

def initialize_leader_notifications(bot_application, logger):
    """Initialize the global leader notification system"""
    global leader_notification_system
    leader_notification_system = LeaderNotificationSystem(bot_application, logger)
    return leader_notification_system