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
from .services.speech import SpeechTranscriber

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
        self.speech_transcriber = SpeechTranscriber(self.logger)  # Initialize speech transcriber
        
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
            
            # Start polling for unsent API observations
            self._start_observation_polling()
            
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
                        
                        # Store observation (notifications will be sent via API polling)
                        if self.leader_notifications:
                            await self.leader_notifications.process_new_observation(observation, chat_id, send_notifications=False)
                            self.logger.info(f"✅ Logistics observation stored, notifications will be sent via API polling")
                        else:
                            self.logger.warning(f"⚠️ Leader notification system not available, logistics observation not processed")
                        
                    elif message_type == "support":
                        # Prefix support messages with SUPPORT keyword (only if not already prefixed by LLM)
                        if not observation.formatted_data.get('what', '').startswith('SUPPORT:'):
                            observation.formatted_data['what'] = f"SUPPORT: {observation.formatted_data.get('what', 'Unknown support requirement')}"
                        self.logger.info(f"🔧 Support observation: {observation.formatted_data['what']}")
                        
                        # Store observation (notifications will be sent via API polling)
                        if self.leader_notifications:
                            await self.leader_notifications.process_new_observation(observation, chat_id, send_notifications=False)
                            self.logger.info(f"✅ Support observation stored, notifications will be sent via API polling")
                        else:
                            self.logger.warning(f"⚠️ Leader notification system not available, support observation not processed")
                        
                    else:
                        # Tactical observation - normal processing with leader notifications
                        self.logger.info(f"⚡ Tactical observation: threat_level={observation.threat_level}, messages={len(cluster['messages'])}")
                        
                        # Store observation (notifications will be sent via API polling)
                        if self.leader_notifications:
                            await self.leader_notifications.process_new_observation(observation, chat_id, send_notifications=False)
                            self.logger.info(f"✅ Tactical observation stored, notifications will be sent via API polling")
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
    
    def _start_observation_polling(self):
        """Start periodic polling for unsent API observations"""
        try:
            from telegram.ext import JobQueue
            
            # Get the job queue from the application
            job_queue = self.app.job_queue
            
            # Schedule the polling job to run every 10 seconds
            job_queue.run_repeating(
                self._poll_unsent_observations,
                interval=10,  # Poll every 10 seconds
                first=5,      # Start after 5 seconds
                name="observation_polling"
            )
            
            self.logger.info("✅ Started polling for unsent API observations (every 10s)")
            
        except Exception as e:
            self.logger.error(f"Failed to start observation polling: {e}")
    
    async def _poll_unsent_observations(self, context):
        """Poll database for observations with sensor_id='UNSENT' and send notifications"""
        try:
            # Use direct database connection for bot (running outside Docker)
            import asyncpg
            
            # Connect directly to localhost database
            db_url = "postgresql://postgres:postgres@localhost:5432/defhack"
            conn = await asyncpg.connect(db_url)
            
            try:
                # Query for unsent observations
                query = """
                    SELECT time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature, received_at
                    FROM sensor_reading 
                    WHERE sensor_id = 'UNSENT'
                    ORDER BY received_at ASC
                    LIMIT 10
                """
                
                unsent_observations = await conn.fetch(query)
                
                if not unsent_observations:
                    self.logger.debug("📡 No unsent API observations found")
                    return  # No unsent observations
                
                self.logger.info(f"📡 Found {len(unsent_observations)} unsent API observations")
                # Debug: log the first observation to see what we're getting
                if unsent_observations:
                    first_obs = unsent_observations[0]
                    self.logger.debug(f"🔍 First unsent observation: sensor_id={first_obs['sensor_id']}, time={first_obs['time']}, what={first_obs['what'][:50]}...")
                
                # Process each unsent observation
                for obs in unsent_observations:
                    try:
                        await self._process_unsent_observation(conn, obs)
                    except Exception as e:
                        self.logger.error(f"Failed to process unsent observation: {e}")
                        continue
            finally:
                await conn.close()
                
        except Exception as e:
            self.logger.error(f"Error in observation polling: {e}")
    
    async def _process_unsent_observation(self, conn, observation):
        """Process a single unsent observation and send leader notifications"""
        try:
            from .enhanced_processor import ProcessedObservation
            
            # Convert database row to ProcessedObservation format (asyncpg Record access)
            # Convert Decimal to int/float for JSON serialization
            amount_value = None
            if observation['amount'] is not None:
                amount_value = int(observation['amount']) if observation['amount'] == int(observation['amount']) else float(observation['amount'])
            
            api_observation = ProcessedObservation(
                original_message=f"API Sensor: {observation['what']}",
                formatted_data={
                    'what': observation['what'],
                    'confidence': observation['confidence'],
                    'amount': amount_value,
                    'sensor_id': observation['sensor_id']
                },
                confidence_score=float(observation['confidence']) if observation['confidence'] else 50.0,
                processing_method="api_direct",
                user_id=0,  # API observations don't have user_id
                username=observation['observer_signature'] or "API_Observer",
                unit=observation['unit'] or "External API",
                mgrs=observation['mgrs'],  # Keep as None if NULL in database
                timestamp=observation['time'] or observation['received_at'],
                requires_leader_notification=True,
                message_type=self._determine_message_type(observation['what']),
                threat_level=self._determine_threat_level(observation)
            )
            
            # Send notifications to appropriate leaders
            await self.leader_notifications.process_new_observation(
                observation=api_observation,
                chat_id=0  # API observations don't have chat_id
            )
            
            # Mark observation as sent by updating sensor_id to 'SENT'
            # Use multiple fields to ensure we update the exact row
            if observation['mgrs'] is None:
                update_query = """
                    UPDATE sensor_reading 
                    SET sensor_id = 'SENT'
                    WHERE time = $1 AND observer_signature = $2 AND what = $3
                    AND sensor_id = 'UNSENT'
                    AND mgrs IS NULL
                """
                result = await conn.execute(update_query, 
                    observation['time'], 
                    observation['observer_signature'],
                    observation['what']
                )
            else:
                update_query = """
                    UPDATE sensor_reading 
                    SET sensor_id = 'SENT'
                    WHERE time = $1 AND observer_signature = $2 AND what = $3
                    AND sensor_id = 'UNSENT'
                    AND mgrs = $4
                """
                result = await conn.execute(update_query, 
                    observation['time'], 
                    observation['observer_signature'],
                    observation['what'],
                    observation['mgrs']
                )
            
            # Check if the update was successful
            if result == "UPDATE 0":
                self.logger.warning(f"⚠️ Failed to mark observation as sent - no matching rows updated")
            else:
                self.logger.debug(f"✅ Updated {result} rows to SENT status")
            
            self.logger.info(f"✅ Processed and marked as sent: {observation['what'][:50]}...")
            
        except Exception as e:
            self.logger.error(f"Failed to process unsent observation: {e}")
            raise
    
    def _determine_message_type(self, what: str) -> str:
        """Determine message type for API observations"""
        what_upper = what.upper()
        
        if any(keyword in what_upper for keyword in ['LOGISTICS', 'SUPPLY', 'FUEL', 'AMMO', 'FOOD']):
            return 'LOGISTICS'
        elif any(keyword in what_upper for keyword in ['SUPPORT', 'MAINTENANCE', 'REPAIR', 'MEDICAL']):
            return 'SUPPORT'
        else:
            return 'TACTICAL'
    
    def _determine_threat_level(self, observation) -> str:
        """Determine threat level for API observations based on content and confidence"""
        what = observation['what'].upper()
        confidence = observation['confidence'] or 50
        
        # High threat indicators
        critical_keywords = ['TANK', 'ARMOR', 'ARTILLERY', 'MISSILE', 'URGENT', 'CRITICAL', 'ATTACK', 'ASSAULT']
        high_keywords = ['PATROL', 'VEHICLE', 'SQUAD', 'MOVEMENT', 'AIRCRAFT', 'FIGHTER', 'BMP', 'BTR']
        
        if any(keyword in what for keyword in critical_keywords) and confidence >= 80:
            return 'CRITICAL'
        elif any(keyword in what for keyword in critical_keywords) and confidence >= 60:
            return 'HIGH'
        elif any(keyword in what for keyword in high_keywords) and confidence >= 70:
            return 'HIGH'
        elif confidence >= 80:
            return 'MEDIUM'
        else:
            return 'LOW'
    
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
        self.app.add_handler(MessageHandler(filters.VOICE, self._handle_voice))
        
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
            
            # Convert to MGRS using the utility function
            try:
                from .utils import to_mgrs
                mgrs_coords = to_mgrs(location.latitude, location.longitude)
                if mgrs_coords == "UNKNOWN":
                    # Fallback to lat/lon if conversion fails
                    mgrs_coords = f"{location.latitude:.6f},{location.longitude:.6f}"
                    self.logger.warning("MGRS conversion returned UNKNOWN, using lat/lon")
                else:
                    self.logger.info(f"📍 Location converted to MGRS: {mgrs_coords}")
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
    
    async def _handle_voice(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle voice messages with transcription"""
        try:
            msg = update.effective_message
            if not msg or not msg.voice or msg.from_user is None or msg.from_user.is_bot:
                return
            
            user_id = update.effective_user.id
            user = user_manager.get_user(user_id)
            
            if not user:
                await update.message.reply_text(
                    "Please register first using /register command"
                )
                return
            
            # Check if speech transcriber is available
            if not self.speech_transcriber.available:
                self.logger.warning("Voice message ignored; transcription disabled.")
                await msg.reply_text(
                    "🎤 Voice transcription isn't configured; please send the observation as text.",
                    reply_to_message_id=msg.message_id,
                )
                return
            
            self.logger.info(f"🎤 Voice message received from {user.full_name} ({user.role})")
            
            try:
                # Get the voice file from Telegram
                voice_file = await context.bot.get_file(msg.voice.file_id)
            except Exception:
                self.logger.exception("Failed to fetch voice file metadata from Telegram.")
                await msg.reply_text("❌ Failed to download voice message. Please try again.")
                return
            
            # Download voice file to memory
            import io
            buffer = io.BytesIO()
            try:
                await voice_file.download_to_memory(out=buffer)
            except Exception:
                self.logger.exception("Failed to download voice note for transcription.")
                try:
                    await msg.reply_text("❌ Failed to download voice message. Please try again.")
                except Exception as reply_error:
                    self.logger.error(f"❌ Failed to send download error reply: {reply_error}")
                return
            
            # Transcribe the voice message
            mime_type = msg.voice.mime_type or "audio/ogg"
            try:
                transcript = await self.speech_transcriber.transcribe(
                    buffer.getvalue(),
                    filename=f"voice_{msg.voice.file_unique_id}.ogg",
                    mime_type=mime_type,
                )
            except Exception as transcription_error:
                self.logger.error(f"❌ Transcription failed: {transcription_error}")
                try:
                    await msg.reply_text(
                        "🎤 Voice transcription service unavailable. Please try again later or send text.",
                        reply_to_message_id=msg.message_id,
                    )
                except Exception as reply_error:
                    self.logger.error(f"❌ Failed to send transcription service error reply: {reply_error}")
                return
            
            if not transcript:
                try:
                    await msg.reply_text(
                        "🎤 Couldn't transcribe that voice message. Please try again or send text.",
                        reply_to_message_id=msg.message_id,
                    )
                except Exception as reply_error:
                    self.logger.error(f"❌ Failed to send transcription error reply: {reply_error}")
                return
            
            # Send transcribed text back
            try:
                await msg.reply_text(
                    f"🎤 Transcribed voice note:\n{transcript}",
                    reply_to_message_id=msg.message_id,
                )
            except Exception as reply_error:
                self.logger.error(f"❌ Failed to send transcription reply: {reply_error}")
                # Continue processing even if we can't send the reply
            
            # Process the transcribed text as a normal message
            # Create a simulated text message to process the transcript
            await self._process_transcribed_message(update, context, transcript)
            
        except Exception as e:
            self.logger.error(f"❌ Error handling voice message: {e}")
            try:
                await update.message.reply_text("❌ Error processing voice message. Please try again.")
            except Exception as reply_error:
                self.logger.error(f"❌ Failed to send error reply: {reply_error}")
    
    async def _process_transcribed_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, transcript: str):
        """Process transcribed voice message text through normal message handling with location waiting"""
        try:
            # Get the message components we need
            message = update.effective_message
            user = update.effective_user
            chat = update.effective_chat
            
            # Process the transcript through the message processor
            cluster_key = f"{chat.id}_{user.id}"
            current_time = datetime.now(timezone.utc)
            
            # Add to message cluster using same logic as normal text messages
            if cluster_key in self.message_clusters:
                # Add to existing cluster
                self.message_clusters[cluster_key]["messages"].append(transcript)
                self.logger.info(f"📦 Added voice transcript to existing cluster {cluster_key}")
            else:
                # Create new cluster for transcribed message
                self.message_clusters[cluster_key] = {
                    "messages": [transcript],
                    "timestamp": current_time,
                    "chat_id": chat.id,
                    "user_id": user.id,
                    "username": user.username or user.full_name,
                    "chat_title": chat.title or "Unknown Chat",
                    "has_location": False,
                    "location": None
                }
                self.logger.info(f"🆕 New voice transcript cluster created for {cluster_key}")
            
            # Cancel existing timeout for this cluster (same as normal messages)
            if cluster_key in self.cluster_timeouts:
                self.cluster_timeouts[cluster_key].cancel()
            
            # Set new 10-second timeout for location waiting (same as normal messages)
            timeout_task = asyncio.create_task(
                self._wait_and_process_cluster(cluster_key, 10.0)
            )
            self.cluster_timeouts[cluster_key] = timeout_task
            
            self.logger.info(f"⏰ Set 10s timeout for voice transcript cluster {cluster_key} (waiting for potential location)")
                
        except Exception as e:
            self.logger.error(f"❌ Error processing transcribed message: {e}")
    
    def start_bot(self):
        """Start the bot"""
        if not self.initialized:
            # Run initialization synchronously
            import asyncio
            asyncio.run(self.initialize())
        
        self.logger.info("🚀 Starting DefHack Telegram bot...")
        # Use the synchronous run_polling method that manages its own event loop
        self.app.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)
    
    async def stop_bot(self):
        """Stop the bot gracefully"""
        if self.app:
            self.logger.info("🛑 Stopping DefHack bot...")
            await self.app.stop()
    
    def run(self):
        """Synchronous method to run the bot (wrapper around start_bot)"""
        try:
            # Check if we're already in an event loop
            try:
                loop = asyncio.get_running_loop()
                # If we're in an event loop, we need to use different approach
                self.logger.warning("Already in event loop, using create_task approach")
                import asyncio
                task = loop.create_task(self.start_bot())
                # This won't work well in Jupyter/existing loop, so let's use a different approach
                return task
            except RuntimeError:
                # No event loop running, safe to use asyncio.run
                asyncio.run(self.start_bot())
        except KeyboardInterrupt:
            self.logger.info("👋 Bot stopped by user")
        except Exception as e:
            self.logger.error(f"❌ Error running bot: {e}")
            raise


# Create global instance for import
defhack_system = None

def get_system(token: str = None) -> DefHackIntegratedSystem:
    """Get or create the global DefHack system instance"""
    global defhack_system
    if defhack_system is None and token:
        defhack_system = DefHackIntegratedSystem(token)
    return defhack_system

def create_defhack_telegram_system() -> DefHackIntegratedSystem:
    """Create DefHack Telegram system with token from environment"""
    import os
    
    # Get Telegram bot token from environment
    token = os.getenv('TELEGRAM_BOT_TOKEN')
    if not token:
        raise ValueError("TELEGRAM_BOT_TOKEN environment variable is required")
    
    # Create and return the system
    return DefHackIntegratedSystem(token)

def main():
    """Main entry point for running the bot"""
    try:
        system = create_defhack_telegram_system()
        system.start_bot()
    except KeyboardInterrupt:
        print("\n👋 DefHack Telegram Bot shutting down...")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()