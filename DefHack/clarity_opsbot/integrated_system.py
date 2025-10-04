"""
Complete DefHack Telegram Bot Integration System
Integrates all components into a working military intelligence Telegram bot
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)

from .enhanced_processor import EnhancedMessageProcessor
from .leader_notifications import LeaderNotificationSystem
from .user_roles import user_manager, UserRole

# Configure logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

class DefHackIntegratedSystem:
    """Main system integrating all DefHack components"""
    
    def __init__(self, token: str):
        self.token = token
        self.app = None
        self.logger = logging.getLogger(__name__)
        self.message_processor = EnhancedMessageProcessor(self.logger)
        self.leader_notifications = None  # Will be initialized after app is created
        
        # Message clustering for combining multiple messages
        self.message_clusters: Dict[str, Dict] = {}
        self.cluster_timeouts: Dict[str, asyncio.Task] = {}
        
        # Bot initialization flag
        self.initialized = False
        
        self.logger.info("🚀 DefHack Integrated System initialized")
    
    async def initialize(self):
        """Initialize the bot application and all components"""
        if self.initialized:
            return
            
        try:
            # Build the application
            self.app = ApplicationBuilder().token(self.token).build()
            
            # Initialize leader notifications system
            self.leader_notifications = LeaderNotificationSystem(self.app, self.logger)
            
            # Setup handlers
            self._setup_handlers()
            
            # Initialize OpenAI client if available
            await self._initialize_openai()
            
            self.initialized = True
            self.logger.info("✅ DefHack system fully initialized")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize DefHack system: {e}")
            raise
    
    async def _process_clustered_messages(self, cluster_key: str):
        """Process a cluster of messages after timeout"""
        if cluster_key not in self.message_clusters:
            return
            
        cluster = self.message_clusters[cluster_key]
        
        try:
            self.logger.info(f"⏱️ Message cluster timeout for {cluster_key}, processing {len(cluster['messages'])} messages")
            
            # Combine all messages in the cluster
            combined_message = " | ".join(cluster['messages'])
            chat_id = int(cluster_key.split('_')[0])
            user_id = int(cluster_key.split('_')[1])
            
            self.logger.info(f"📝 Combined message: {combined_message}")
            
            try:
                # Process the combined message with enhanced processor
                # Create a mock message object with combined text
                class MockMessage:
                    def __init__(self, text, location=None):
                        self.text = text
                        self.location = location
                        self.date = cluster['timestamp']
                        self.photo = []
                
                # Add location if available
                mock_location = None
                if cluster['has_location'] and cluster['location']:
                    class MockLocation:
                        def __init__(self, mgrs_coords):
                            self.mgrs_coords = mgrs_coords
                            # Extract lat/lon from MGRS if possible, otherwise use defaults
                            self.latitude = 60.1681  # Helsinki area default
                            self.longitude = 24.9219
                    mock_location = MockLocation(cluster['location'])
                
                mock_message = MockMessage(combined_message, mock_location)
                
                # Process with enhanced processor
                observation = await self.message_processor.process_message(
                    mock_message, user_id, chat_id, cluster['chat_title'], cluster['username']
                )
                
                if observation:
                    # Update location if we have it from the cluster
                    if cluster['has_location'] and cluster['location']:
                        observation.mgrs = cluster['location']
                    
                    # Get message type from LLM classification (already done in enhanced_processor)
                    message_type = getattr(observation, 'message_type', 'TACTICAL').lower()
                    self.logger.info(f"🤖 LLM classified message as: {message_type.upper()} - '{combined_message[:100]}...'")
                    
                    # Handle BANTER messages by ignoring them completely
                    if message_type == "banter":
                        self.logger.info(f"� BANTER message ignored: '{combined_message[:50]}...'")
                        return  # Exit early for banter
                    
                    elif message_type == "logistics":
                        # Prefix logistics messages with LOGISTICS keyword (only if not already prefixed by LLM)
                        if not observation.formatted_data.get('what', '').startswith('LOGISTICS:'):
                            observation.formatted_data['what'] = f"LOGISTICS: {observation.formatted_data.get('what', 'Unknown logistics requirement')}"
                        self.logger.info(f"📦 Logistics observation: {observation.formatted_data['what']}")
                        
                        # Send to Platoon 2IC via leader notification system
                        if self.leader_notifications:
                            await self.leader_notifications.process_new_observation(observation, chat_id)
                            self.logger.info(f"✅ Logistics observation sent to Platoon 2IC")
                        else:
                            self.logger.warning(f"⚠️ Leader notification system not available, logistics observation not processed")
                        
                    elif message_type == "support":
                        # Prefix support messages with SUPPORT keyword (only if not already prefixed by LLM)
                        if not observation.formatted_data.get('what', '').startswith('SUPPORT:'):
                            observation.formatted_data['what'] = f"SUPPORT: {observation.formatted_data.get('what', 'Unknown support requirement')}"
                        self.logger.info(f"🔧 Support observation: {observation.formatted_data['what']}")
                        
                        # Send to Platoon 2IC via leader notification system
                        if self.leader_notifications:
                            await self.leader_notifications.process_new_observation(observation, chat_id)
                            self.logger.info(f"✅ Support observation sent to Platoon 2IC")
                        else:
                            self.logger.warning(f"⚠️ Leader notification system not available, support observation not processed")
                        
                    else:
                        # Tactical observation - normal processing with leader notifications
                        self.logger.info(f"⚡ Tactical observation: threat_level={observation.threat_level}, messages={len(cluster['messages'])}")
                        
                        # Send to leader notification system
                        if self.leader_notifications:
                            await self.leader_notifications.process_new_observation(observation, chat_id)
                            self.logger.info(f"✅ Leader notifications sent for tactical observation")
                        else:
                            self.logger.warning(f"⚠️ Leader notification system not available, tactical observation not processed")
                else:
                    self.logger.warning(f"❌ No observation created from clustered messages")
                    
            except Exception as e:
                self.logger.error(f"❌ Error processing clustered messages: {e}")
                
        finally:
            # Clean up cluster data
            if cluster_key in self.message_clusters:
                del self.message_clusters[cluster_key]
            if cluster_key in self.cluster_timeouts:
                del self.cluster_timeouts[cluster_key]
    
    async def _initialize_openai(self):
        """Initialize OpenAI client for enhanced processing"""
        try:
            try:
                import openai
            except ImportError:
                openai = None
                
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and openai:
                client = openai.AsyncOpenAI(api_key=api_key)
                self.message_processor.openai_client = client
                self.logger.info("✅ OpenAI client initialized and set in message processor")
            else:
                self.logger.warning("⚠️ OpenAI API key not found or openai module not available")
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
    
    def _setup_handlers(self):
        """Setup all message and command handlers"""
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("register", self._handle_register))
        self.app.add_handler(CommandHandler("help", self._handle_help))
        
        # Message handlers
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self._handle_message))
        self.app.add_handler(MessageHandler(filters.LOCATION, self._handle_location))
        self.app.add_handler(MessageHandler(filters.PHOTO, self._handle_photo))
        
        # Callback query handler for button interactions
        self.app.add_handler(CallbackQueryHandler(self._handle_callback_query))
        
        self.logger.info("✅ All handlers setup complete")
    
    async def _handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle text messages with enhanced processing and clustering"""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            username = update.effective_user.username or "Unknown"
            message_text = update.message.text
            
            # Check if user is providing a custom unit name during registration
            if context.user_data.get('awaiting_unit'):
                unit = message_text.strip()
                role = context.user_data.get('selected_role', UserRole.SOLDIER)
                role_display = context.user_data.get('selected_role_display', 'Soldier')
                
                # Complete registration with custom unit
                user_manager.register_user(user_id, username, username, unit, role)
                
                # Clear user context
                context.user_data.clear()
                
                await update.message.reply_text(
                    f"🎉 Registration Complete!\n\n"
                    f"👤 Role: {role_display}\n"
                    f"📍 Unit: {unit}\n\n"
                    f"You can now send observations and they will be routed to the appropriate leaders!"
                )
                return
            
            # Get user info
            user = user_manager.get_user(user_id)
            if not user:
                await update.message.reply_text(
                    "Please register first using /register command"
                )
                return
            
            # Only process group messages (filter out direct messages)
            if update.effective_chat.type == 'private':
                self.logger.info(f"🚫 Ignoring direct message from {username}: '{message_text}'")
                return
            
            self.logger.info(f"📥 Message from {username} ({user.role}) in {update.effective_chat.title}: {message_text}")
            
            # Note: Message relevance filtering is now handled by LLM classification
            # The LLM will classify messages as BANTER and we'll ignore those
            
            # Create cluster key for this user in this chat
            cluster_key = f"{chat_id}_{user_id}"
            current_time = datetime.now(timezone.utc)
            
            # Initialize or update cluster
            if cluster_key not in self.message_clusters:
                self.message_clusters[cluster_key] = {
                    'messages': [],
                    'timestamp': current_time,
                    'chat_id': chat_id,
                    'user_id': user_id,
                    'username': username,
                    'chat_title': update.effective_chat.title or "Unknown Chat",
                    'has_location': False,
                    'location': None
                }
                self.logger.info(f"🆕 New message cluster created for {cluster_key}")
            
            # Add message to cluster
            self.message_clusters[cluster_key]['messages'].append(message_text)
            self.logger.info(f"📦 Added message to cluster {cluster_key}: {len(self.message_clusters[cluster_key]['messages'])} total messages")
            
            # Cancel existing timeout for this cluster
            if cluster_key in self.cluster_timeouts:
                self.cluster_timeouts[cluster_key].cancel()
            
            # Set new 10-second timeout for location waiting
            timeout_task = asyncio.create_task(
                self._wait_and_process_cluster(cluster_key, 10.0)
            )
            self.cluster_timeouts[cluster_key] = timeout_task
            
            self.logger.info(f"⏰ Set 10s timeout for cluster {cluster_key} (waiting for potential location)")
            
        except Exception as e:
            self.logger.error(f"❌ Error handling message: {e}")
            await update.message.reply_text("Error processing message")
    
    async def _wait_and_process_cluster(self, cluster_key: str, delay: float):
        """Wait for the specified delay then process the message cluster"""
        try:
            await asyncio.sleep(delay)
            await self._process_clustered_messages(cluster_key)
        except asyncio.CancelledError:
            # Task was cancelled, which is normal when new messages arrive
            pass
        except Exception as e:
            self.logger.error(f"❌ Error in cluster timeout: {e}")
    
    # Note: Message relevance filtering is now handled by LLM classification in enhanced_processor.py
    # The LLM intelligently detects banter, logistics, support, and tactical messages
    
    # Note: Message classification is now handled by LLM in enhanced_processor.py
    # This provides more intelligent classification including banter detection
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user = user_manager.get_user(user_id)
        
        if user:
            welcome_text = f"Welcome back, {user.name}! You are registered as {user.role}."
        else:
            welcome_text = "Welcome to DefHack Intelligence System! Please register using /register command."
        
        await update.message.reply_text(welcome_text)
    
    async def _handle_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /register command"""
        keyboard = [
            [InlineKeyboardButton("🎖️ Platoon Leader", callback_data="register_platoon_leader")],
            [InlineKeyboardButton("⚡ Platoon 2IC", callback_data="register_platoon_2ic")],
            [InlineKeyboardButton("👥 Squad Leader", callback_data="register_squad_leader")],
            [InlineKeyboardButton("🔍 Observer", callback_data="register_observer")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        await update.message.reply_text(
            "Please select your role:",
            reply_markup=reply_markup
        )
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /help command"""
        help_text = """
🎯 **DefHack Intelligence System**

**Commands:**
/start - Start the bot
/register - Register your role
/help - Show this help

**Message Types:**
• **Tactical observations** - Enemy activity, threats, movements
• **Logistics reports** - Supply status, equipment needs
• **Support requests** - Maintenance, medical, facilities

**How it works:**
1. Send observation messages in group chats
2. Include location data when possible
3. System will classify and route appropriately
4. **TACTICAL** observations → Platoon Leader
5. **LOGISTICS/SUPPORT** observations → Platoon 2IC
6. **BANTER** messages → Ignored completely

**Roles:**
• **Observer** - Send observations and reports
• **Squad Leader** - Receive tactical updates  
• **Platoon Leader** - Receive tactical intelligence alerts
• **Platoon 2IC** - Receive logistics and support requests
        """
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle callback queries from inline keyboards"""
        query = update.callback_query
        await query.answer()
        
        user_id = update.effective_user.id
        username = update.effective_user.username or f"User_{user_id}"
        
        if query.data.startswith("register_"):
            role_data = query.data.replace("register_", "")
            
            # Handle special case for Platoon 2IC
            if role_data == "platoon_2ic":
                role_display = "Platoon 2IC"
                role_value = UserRole.PLATOON_2IC
            elif role_data == "platoon_leader":
                role_display = "Platoon Leader"
                role_value = UserRole.PLATOON_LEADER
            elif role_data == "company_commander":
                role_display = "Company Commander"
                role_value = UserRole.COMPANY_COMMANDER
            else:
                role_display = "Soldier"
                role_value = UserRole.SOLDIER
            
            # Store the role selection in user context and ask for unit
            context.user_data['selected_role'] = role_value
            context.user_data['selected_role_display'] = role_display
            
            # Create unit selection keyboard
            unit_keyboard = [
                [InlineKeyboardButton("Alpha Company", callback_data="unit_alpha_company")],
                [InlineKeyboardButton("Bravo Company", callback_data="unit_bravo_company")],
                [InlineKeyboardButton("Charlie Company", callback_data="unit_charlie_company")],
                [InlineKeyboardButton("Delta Company", callback_data="unit_delta_company")],
                [InlineKeyboardButton("HQ Company", callback_data="unit_hq_company")],
                [InlineKeyboardButton("Other Unit", callback_data="unit_other")]
            ]
            reply_markup = InlineKeyboardMarkup(unit_keyboard)
            
            await query.edit_message_text(
                f"✅ Role selected: {role_display}\n\n"
                f"📍 Please select your unit:",
                reply_markup=reply_markup
            )
            
        elif query.data.startswith("unit_"):
            # Handle unit selection
            unit_data = query.data.replace("unit_", "")
            
            if unit_data == "other":
                await query.edit_message_text(
                    "📝 Please send me your unit name as a regular message."
                )
                context.user_data['awaiting_unit'] = True
                return
            
            # Map unit codes to display names
            unit_map = {
                "alpha_company": "Alpha Company",
                "bravo_company": "Bravo Company", 
                "charlie_company": "Charlie Company",
                "delta_company": "Delta Company",
                "hq_company": "HQ Company"
            }
            
            unit = unit_map.get(unit_data, "Unknown Unit")
            
            # Complete registration
            role = context.user_data.get('selected_role', UserRole.SOLDIER)
            role_display = context.user_data.get('selected_role_display', 'Soldier')
            
            user_manager.register_user(user_id, username, username, unit, role)
            
            # Clear user context
            context.user_data.clear()
            
            await query.edit_message_text(
                f"🎉 Registration Complete!\n\n"
                f"👤 Role: {role_display}\n"
                f"📍 Unit: {unit}\n\n"
                f"You can now send observations and they will be routed to the appropriate leaders!"
            )
            
        elif query.data.startswith("obs_"):
            # Handle observation-related callbacks (More Info, FRAGO buttons)
            if self.leader_notifications:
                await self.leader_notifications.handle_callback_query(update, context)
    
    async def _handle_location(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle location messages"""
        try:
            user_id = update.effective_user.id
            chat_id = update.effective_chat.id
            cluster_key = f"{chat_id}_{user_id}"
            
            location = update.message.location
            
            # Convert to MGRS if possible
            mgrs_coords = None
            try:
                import mgrs
                m = mgrs.MGRS()
                mgrs_coords = m.toMGRS(location.latitude, location.longitude)
                self.logger.info(f"📍 Location converted to MGRS: {mgrs_coords}")
            except ImportError:
                self.logger.warning("MGRS library not available, using lat/lon")
                mgrs_coords = f"{location.latitude:.6f},{location.longitude:.6f}"
            except Exception as e:
                self.logger.error(f"MGRS conversion failed: {e}")
                mgrs_coords = f"{location.latitude:.6f},{location.longitude:.6f}"
            
            # Check if we have a pending message cluster for this user
            if cluster_key in self.message_clusters:
                self.message_clusters[cluster_key]['has_location'] = True
                self.message_clusters[cluster_key]['location'] = mgrs_coords
                self.logger.info(f"📍 Added location to existing cluster {cluster_key}: {mgrs_coords}")
                
                # Location received, process immediately
                if cluster_key in self.cluster_timeouts:
                    self.cluster_timeouts[cluster_key].cancel()
                
                await self._process_clustered_messages(cluster_key)
            else:
                self.logger.info(f"📍 Location received but no pending message cluster for {cluster_key}")
                
        except Exception as e:
            self.logger.error(f"❌ Error handling location: {e}")
    
    async def _handle_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle photo messages"""
        try:
            user_id = update.effective_user.id
            user = user_manager.get_user(user_id)
            
            if not user:
                await update.message.reply_text(
                    "Please register first using /register command"
                )
                return
            
            self.logger.info(f"📸 Photo received from {user.name} ({user.role})")
            
            # For now, just acknowledge photo receipt
            await update.message.reply_text(
                "📸 Photo received and will be processed for intelligence analysis"
            )
            
        except Exception as e:
            self.logger.error(f"❌ Error handling photo: {e}")
    
    async def start_bot(self):
        """Start the bot"""
        if not self.initialized:
            await self.initialize()
        
        self.logger.info("🚀 Starting DefHack Telegram bot...")
        await self.app.run_polling(allowed_updates=Update.ALL_TYPES)
    
    async def stop_bot(self):
        """Stop the bot gracefully"""
        if self.app:
            self.logger.info("🛑 Stopping DefHack bot...")
            await self.app.stop()


# Create global instance for import
defhack_system = None

def get_system(token: str = None) -> DefHackIntegratedSystem:
    """Get or create the global DefHack system instance"""
    global defhack_system
    if defhack_system is None and token:
        defhack_system = DefHackIntegratedSystem(token)
    return defhack_system