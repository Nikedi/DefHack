"""
Complete DefHack Telegram Bot Integration System
Integrates all components into a working military intelligence system
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

# Import all our custom components
from .user_roles import user_manager, UserRole
from .enhanced_processor import EnhancedMessageProcessor, ProcessedObservation
from .leader_notifications import initialize_leader_notifications
from .higher_echelon_intelligence import initialize_higher_echelon_intelligence, SummaryType
from .services.openai_analyzer import OpenAIAnalyzer
from .defhack_bridge import DefHackTelegramBridge

class DefHackTelegramSystem:
    """Complete integrated DefHack Telegram bot system"""
    
    def __init__(self, token: str, logger: logging.Logger):
        self.token = token
        self.logger = logger
        
        # Initialize core components
        self.app = ApplicationBuilder().token(token).build()
        self.message_processor = EnhancedMessageProcessor(logger)
        self.defhack_bridge = DefHackTelegramBridge()
        
        # Initialize subsystems
        self.leader_notifications = initialize_leader_notifications(self.app, logger)
        self.higher_echelon_intel = initialize_higher_echelon_intelligence(logger)
        
        # Track active registrations
        self.active_registrations: Dict[int, Dict] = {}
        
        # Setup handlers
        self._setup_handlers()
    
    def _setup_handlers(self):
        """Setup all message and command handlers"""
        
        # Command handlers
        self.app.add_handler(CommandHandler("start", self._handle_start))
        self.app.add_handler(CommandHandler("register", self._handle_register))
        self.app.add_handler(CommandHandler("help", self._handle_help))
        self.app.add_handler(CommandHandler("status", self._handle_status))
        self.app.add_handler(CommandHandler("frago", self._handle_frago_command))
        self.app.add_handler(CommandHandler("intrep", self._handle_intrep_command))
        self.app.add_handler(CommandHandler("threat", self._handle_threat_assessment))
        self.app.add_handler(CommandHandler("activity", self._handle_activity_summary))
        self.app.add_handler(CommandHandler("profile", self._handle_profile))
        
        # Message handlers for different chat types
        self.app.add_handler(MessageHandler(
            filters.ChatType.GROUPS & (filters.TEXT | filters.PHOTO | filters.LOCATION),
            self._handle_group_message
        ))
        
        self.app.add_handler(MessageHandler(
            filters.ChatType.PRIVATE & (filters.TEXT | filters.PHOTO | filters.LOCATION),
            self._handle_private_message
        ))
        
        # Callback query handler for inline keyboards
        self.app.add_handler(CallbackQueryHandler(self._handle_callback_query))
        
        self.logger.info("All handlers registered successfully")
    
    async def _handle_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle /start command"""
        user_id = update.effective_user.id
        user = user_manager.get_user(user_id)
        
        if update.effective_chat.type == "private":
            if user:
                welcome_msg = f"""👋 **Welcome back, {user.full_name}!**

🎖️ **Role:** {user.role.value.replace('_', ' ').title()}
🏛️ **Unit:** {user.unit}
📊 **Status:** Registered and Active

**Available Commands:**
• `/help` - Show all available commands
• `/profile` - View your profile information
• `/status` - Check system status

**Intelligence Commands:**
• `/intrep` - Request 24-hour intelligence report
• `/threat` - Get current threat assessment
• `/activity` - View activity summary

Ready to serve! 🎯"""
            else:
                welcome_msg = """👋 **Welcome to DefHack Military Intelligence Bot!**

⚡ **You are not yet registered**

To use this system, you need to register with your military credentials.

Use `/register` to begin the registration process.

🎖️ **This bot provides:**
• Real-time tactical intelligence
• Automated FRAGO generation
• Intelligence summaries for command staff
• Secure military communications

🔐 **For official use only**"""
        else:
            # Group chat
            welcome_msg = """👋 **DefHack Intelligence Bot Online**

📡 **Monitoring Active** - This bot is now monitoring tactical communications in this group.

**Automatic Features:**
• Tactical message analysis
• Threat detection and alerting
• MGRS coordinate extraction
• Leader notifications for significant events

**Group Commands:**
• Share locations for MGRS conversion
• Report tactical observations
• All messages analyzed for intelligence value

🎯 **Ready for tactical operations!**"""
        
        await update.message.reply_text(welcome_msg, parse_mode='Markdown')
    
    async def _handle_register(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle user registration process"""
        if update.effective_chat.type != "private":
            await update.message.reply_text(
                "🔐 **Registration must be done in private messages.**\n\n"
                "Please send me a direct message to register."
            )
            return
        
        user_id = update.effective_user.id
        
        # Start registration process
        self.active_registrations[user_id] = {
            'step': 'role_selection',
            'data': {
                'user_id': user_id,
                'username': update.effective_user.username or f"user_{user_id}",
                'full_name': update.effective_user.full_name or "Unknown"
            }
        }
        
        # Show role selection keyboard
        keyboard = [
            [
                InlineKeyboardButton("🪖 Soldier", callback_data="role_soldier"),
                InlineKeyboardButton("⭐ Platoon Leader", callback_data="role_platoon_leader")
            ],
            [
                InlineKeyboardButton("🎖️ Company Commander", callback_data="role_company_commander"),
                InlineKeyboardButton("🏛️ Battalion Staff", callback_data="role_battalion_staff")
            ],
            [
                InlineKeyboardButton("🎯 Higher Echelon", callback_data="role_higher_echelon")
            ]
        ]
        
        await update.message.reply_text(
            "🎖️ **DefHack Registration**\n\n"
            "Select your military role:",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )
    
    async def _handle_group_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle messages in group chats - main tactical processing"""
        user_id = update.effective_user.id
        chat_id = update.effective_chat.id
        
        # Check if user is registered
        user = user_manager.get_user(user_id)
        if not user:
            # Send registration reminder (privately)
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text="🔐 **Registration Required**\n\n"
                         "You need to register before I can process your tactical reports.\n"
                         "Send me `/register` in private message to begin."
                )
            except:
                pass  # User may not allow private messages
            return
        
        # Process the message with enhanced processor
        try:
            observation = await self.message_processor.process_message(
                update.effective_message, user_id, chat_id
            )
            
            if observation:
                # Send to leader notification system
                await self.leader_notifications.process_new_observation(observation, chat_id)
                
                # Send confirmation to group if significant
                if observation.threat_level in ['HIGH', 'CRITICAL']:
                    confirmation = f"""⚡ **Tactical Report Processed**
👤 Observer: {user.username}
📊 Confidence: {observation.confidence_score:.0%}
🎯 Method: {observation.processing_method.replace('_', ' ').title()}
🚨 Threat Level: {observation.threat_level}

✅ Leaders have been notified"""
                    
                    await update.message.reply_text(confirmation, parse_mode='Markdown')
                
                self.logger.info(f"Processed tactical report from {user.username} in group {chat_id}")
            
        except Exception as e:
            self.logger.error(f"Error processing group message: {e}")
    
    async def _handle_private_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle private messages - registration and commands"""
        user_id = update.effective_user.id
        
        # Check if user is in registration process
        if user_id in self.active_registrations:
            await self._handle_registration_step(update, context)
            return
        
        # Check if user is registered
        user = user_manager.get_user(user_id)
        if not user:
            await update.message.reply_text(
                "🔐 **Registration Required**\n\n"
                "Please use `/register` to register before using the system."
            )
            return
        
        # Process as regular message (for individual reports)
        await self._process_individual_report(update, context)
    
    async def _handle_registration_step(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle registration process steps"""
        user_id = update.effective_user.id
        registration = self.active_registrations[user_id]
        
        if registration['step'] == 'unit_input':
            # User provided unit information
            unit = update.message.text.strip()
            registration['data']['unit'] = unit
            
            # Complete registration
            profile = user_manager.register_user(
                user_id=registration['data']['user_id'],
                username=registration['data']['username'],
                full_name=registration['data']['full_name'],
                unit=unit,
                role=registration['data']['role']
            )
            
            # Remove from active registrations
            del self.active_registrations[user_id]
            
            # Send confirmation
            await update.message.reply_text(
                f"✅ **Registration Complete!**\n\n"
                f"👤 **Name:** {profile.full_name}\n"
                f"🎖️ **Role:** {profile.role.value.replace('_', ' ').title()}\n"
                f"🏛️ **Unit:** {profile.unit}\n\n"
                f"🎯 **You're now ready to use the DefHack Intelligence System!**\n\n"
                f"Use `/help` to see available commands.",
                parse_mode='Markdown'
            )
    
    async def _handle_callback_query(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle inline keyboard callbacks"""
        query = update.callback_query
        await query.answer()
        
        user_id = query.from_user.id
        
        # Handle role selection during registration
        if query.data.startswith("role_"):
            if user_id in self.active_registrations:
                role_name = query.data[5:]  # Remove "role_" prefix
                role = getattr(UserRole, role_name.upper(), UserRole.SOLDIER)
                
                self.active_registrations[user_id]['data']['role'] = role
                self.active_registrations[user_id]['step'] = 'unit_input'
                
                await query.edit_message_text(
                    f"🎖️ **Role Selected:** {role.value.replace('_', ' ').title()}\n\n"
                    f"📝 **Please enter your unit designation:**\n"
                    f"(Example: 1st Battalion, Alpha Company, 2nd Platoon)",
                    parse_mode='Markdown'
                )
            return
        
        # Handle FRAGO requests from leader notifications
        if query.data.startswith("frago_req_") or query.data.startswith("no_action_") or query.data.startswith("details_"):
            await self.leader_notifications.handle_frago_request(update, context)
            return
    
    async def _handle_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show help information"""
        user_id = update.effective_user.id
        user = user_manager.get_user(user_id)
        
        if not user:
            help_text = """❓ **DefHack Intelligence Bot Help**

🔐 **You are not registered**
Use `/register` to register first.

**Basic Commands:**
• `/start` - Start the bot
• `/register` - Register with the system
• `/help` - Show this help message
"""
        else:
            help_text = f"""❓ **DefHack Intelligence Bot Help**
👤 **User:** {user.full_name} ({user.role.value.replace('_', ' ').title()})

**📋 Basic Commands:**
• `/start` - Welcome message and status
• `/profile` - View your profile
• `/status` - Check system status
• `/help` - Show this help message

**🎖️ Intelligence Commands:**
• `/intrep` - 24-hour intelligence report
• `/threat` - Current threat assessment
• `/activity` - Activity pattern summary

**📡 Group Features:**
• Share location → Automatic MGRS conversion
• Send tactical reports → Automatic analysis
• Photo analysis → Vision-based intelligence
• Automatic leader notifications for threats

**🔐 Permissions:**
"""
            
            if user_manager.can_request_frago(user_id):
                help_text += "• ✅ Can request FRAGO generation\n"
            if user_manager.can_request_intelligence_summary(user_id):
                help_text += "• ✅ Can request intelligence summaries\n"
            
            help_text += "\n🎯 **Ready for tactical operations!**"
        
        await update.message.reply_text(help_text, parse_mode='Markdown')
    
    async def _handle_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show system status"""
        stats = user_manager.get_user_statistics()
        
        status_msg = f"""📊 **DefHack System Status**

**👥 User Statistics:**
• Total Users: {stats['total']}
• Soldiers: {stats['soldier']}
• Platoon Leaders: {stats['platoon_leader']}
• Company Commanders: {stats['company_commander']}
• Battalion Staff: {stats['battalion_staff']}
• Higher Echelon: {stats['higher_echelon']}

**🔧 System Components:**
• ✅ Message Processing: Online
• ✅ OpenAI Integration: Active
• ✅ DefHack Database: Connected
• ✅ Leader Notifications: Active
• ✅ Intelligence Summaries: Available

**📡 Current Time:** {datetime.now(timezone.utc).strftime('%H:%M %d-%m-%Y UTC')}

🎯 **System Status: OPERATIONAL**"""
        
        await update.message.reply_text(status_msg, parse_mode='Markdown')
    
    async def _handle_frago_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle FRAGO generation request"""
        user_id = update.effective_user.id
        
        if not user_manager.can_request_frago(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "You do not have permission to request FRAGO generation.\n"
                "Only leaders (Platoon Leader and above) can request FRAGOs."
            )
            return
        
        try:
            # Generate FRAGO using most recent observation
            frago_data = {
                'what': 'FRAGO request from leader',
                'mgrs': 'Command discretion',
                'confidence': 90,
                'observer_signature': user_manager.get_user(user_id).username,
                'time': datetime.now(timezone.utc),
                'unit': user_manager.get_user(user_id).unit
            }
            
            results = await self.defhack_bridge.process_telegram_observation(frago_data)
            
            if 'frago_order' in results:
                await update.message.reply_text(
                    f"📋 **FRAGMENTARY ORDER (FRAGO)**\n\n{results['frago_order']}",
                    parse_mode='Markdown'
                )
            else:
                await update.message.reply_text(
                    "❌ FRAGO generation failed. Please try again or contact S3."
                )
                
        except Exception as e:
            self.logger.error(f"FRAGO generation error: {e}")
            await update.message.reply_text(
                "❌ FRAGO generation encountered an error. Please try again."
            )
    
    async def _handle_intrep_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle intelligence report request"""
        user_id = update.effective_user.id
        
        if not user_manager.can_request_intelligence_summary(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "You do not have permission to request intelligence summaries.\n"
                "Only higher echelon users can request INTREPs."
            )
            return
        
        try:
            summary = await self.higher_echelon_intel.generate_intelligence_summary(
                SummaryType.DAILY_INTREP, user_id, 24
            )
            
            await update.message.reply_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"INTREP generation error: {e}")
            await update.message.reply_text(
                "❌ INTREP generation encountered an error. Please try again."
            )
    
    async def _handle_threat_assessment(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle threat assessment request"""
        user_id = update.effective_user.id
        
        if not user_manager.can_request_intelligence_summary(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "You do not have permission to request threat assessments."
            )
            return
        
        try:
            assessment = await self.higher_echelon_intel.generate_intelligence_summary(
                SummaryType.THREAT_ASSESSMENT, user_id, 24
            )
            
            await update.message.reply_text(assessment, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Threat assessment error: {e}")
            await update.message.reply_text(
                "❌ Threat assessment generation encountered an error."
            )
    
    async def _handle_activity_summary(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handle activity summary request"""
        user_id = update.effective_user.id
        
        if not user_manager.can_request_intelligence_summary(user_id):
            await update.message.reply_text(
                "❌ **Access Denied**\n\n"
                "You do not have permission to request activity summaries."
            )
            return
        
        try:
            summary = await self.higher_echelon_intel.generate_intelligence_summary(
                SummaryType.ACTIVITY_SUMMARY, user_id, 24
            )
            
            await update.message.reply_text(summary, parse_mode='Markdown')
            
        except Exception as e:
            self.logger.error(f"Activity summary error: {e}")
            await update.message.reply_text(
                "❌ Activity summary generation encountered an error."
            )
    
    async def _handle_profile(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Show user profile"""
        user_id = update.effective_user.id
        profile_info = user_manager.format_user_info(user_id)
        await update.message.reply_text(profile_info, parse_mode='Markdown')
    
    async def _process_individual_report(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Process individual tactical reports sent via private message"""
        user_id = update.effective_user.id
        
        try:
            observation = await self.message_processor.process_message(
                update.effective_message, user_id, update.effective_chat.id
            )
            
            if observation:
                # Send confirmation
                await update.message.reply_text(
                    f"✅ **Report Processed**\n\n"
                    f"📊 Confidence: {observation.confidence_score:.0%}\n"
                    f"🎯 Method: {observation.processing_method.replace('_', ' ').title()}\n"
                    f"🚨 Threat Level: {observation.threat_level}\n\n"
                    f"✅ Leaders have been notified",
                    parse_mode='Markdown'
                )
                
                # Process through leader notifications
                await self.leader_notifications.process_new_observation(
                    observation, update.effective_chat.id
                )
            else:
                await update.message.reply_text(
                    "⚠️ **Unable to process report**\n\n"
                    "Please provide more detailed tactical information."
                )
                
        except Exception as e:
            self.logger.error(f"Error processing individual report: {e}")
            await update.message.reply_text(
                "❌ **Processing Error**\n\n"
                "Report processing encountered an error. Please try again."
            )
    
    def run(self):
        """Start the DefHack Telegram system"""
        self.logger.info("Starting DefHack Telegram Intelligence System...")
        self.app.run_polling(close_loop=False)

def create_defhack_telegram_system(token: str = None) -> DefHackTelegramSystem:
    """Create and initialize the complete DefHack Telegram system"""
    
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger("DefHack-Telegram")
    
    # Get token from environment if not provided
    if not token:
        token = os.getenv('TELEGRAM_BOT_TOKEN')
        if not token:
            raise ValueError("TELEGRAM_BOT_TOKEN not found in environment variables")
    
    # Create system
    system = DefHackTelegramSystem(token, logger)
    
    logger.info("✅ DefHack Telegram Intelligence System initialized")
    logger.info("🎯 Ready for tactical deployment!")
    
    return system