"""Enhanced handlers for group chat interactions with DefHack military LLM integration."""

from __future__ import annotations

import logging
from datetime import timezone
from typing import Any, Dict, List

from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters

from ..services.gemini import GeminiAnalyzer
from ..utils import format_log, get_observer_signature, get_unit, to_mgrs, utc_iso
from ..defhack_bridge import DefHackTelegramBridge, extract_observation_from_message

def create_enhanced_group_handlers(analyzer: GeminiAnalyzer, logger: logging.Logger) -> List[MessageHandler]:
    """
    Create enhanced group handlers that integrate DefHack military LLM functions
    with the existing Telegram bot functionality
    """
    
    # Initialize DefHack bridge for military LLM integration
    try:
        defhack_bridge = DefHackTelegramBridge()
        logger.info("✅ DefHack military LLM bridge initialized")
    except Exception as e:
        logger.error(f"❌ Failed to initialize DefHack bridge: {e}")
        defhack_bridge = None

    async def on_enhanced_group_text(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Enhanced text message handler with DefHack military analysis"""
        msg = update.effective_message
        if not msg or not msg.text or msg.from_user is None or msg.from_user.is_bot:
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return

        record: Dict[str, str] = {
            "time": utc_iso(),
            "user": msg.from_user.full_name,
            "text": msg.text.replace("\n", " ").strip(),
        }
        logger.info(format_log(record))
        
        unit = get_unit(chat)
        observer = get_observer_signature(msg.from_user)
        
        # Original Gemini analysis (keep for backward compatibility)
        await analyzer.queue_for_analysis(
            chat.id,
            {
                "time": msg.date.astimezone(timezone.utc).isoformat(),
                "unit": unit,
                "observer_signature": observer,
                "mgrs": "UNKNOWN",
                "content": record["text"],
            },
        )
        
        # Enhanced DefHack military analysis
        if defhack_bridge and _is_tactical_message(msg.text):
            try:
                logger.info("🎯 Processing tactical message with DefHack military LLM...")
                
                # Extract observation data from message
                observation_data = extract_observation_from_message(msg)
                observation_data['unit'] = unit
                
                # Process with DefHack military functions
                results = await defhack_bridge.process_telegram_observation(observation_data)
                
                # Send automatic responses if significant
                if results['stored'] and 'enemy' in msg.text.lower():
                    # Send tactical alert
                    alert_msg = f"🚨 **TACTICAL ALERT**\n{results['telegram_message']}"
                    await msg.reply_text(alert_msg)
                    
                    # Offer FRAGO generation
                    if 'FRAGO' in results['frago_order']:
                        frago_msg = f"📋 **FRAGO AVAILABLE**\nReply with /frago to generate fragmentary order"
                        await msg.reply_text(frago_msg)
                
                logger.info("✅ DefHack military analysis completed")
                
            except Exception as e:
                logger.error(f"❌ DefHack analysis failed: {e}")

    async def on_enhanced_group_location(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Enhanced location handler with DefHack military positioning analysis"""
        msg = update.effective_message
        if not msg or not msg.location or msg.from_user is None or msg.from_user.is_bot:
            return
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return

        loc = msg.location
        mgrs_str = to_mgrs(loc.latitude, loc.longitude)
        meta_parts = []
        if getattr(loc, "horizontal_accuracy", None):
            meta_parts.append(f"acc={int(loc.horizontal_accuracy)}m")
        if getattr(loc, "live_period", None):
            meta_parts.append(f"live={loc.live_period}s")
        if getattr(loc, "heading", None):
            meta_parts.append(f"heading={loc.heading}")
        if getattr(loc, "proximity_alert_radius", None):
            meta_parts.append(f"alert_radius={loc.proximity_alert_radius}m")
        meta = (" " + " ".join(meta_parts)) if meta_parts else ""
        
        logger.info(
            "[%s] user='%s' location=(%.6f,%.6f) mgrs=%s%s",
            utc_iso(),
            msg.from_user.full_name,
            loc.latitude,
            loc.longitude,
            mgrs_str,
            meta,
        )
        
        unit = get_unit(chat)
        observer = get_observer_signature(msg.from_user)
        
        # Original Gemini analysis
        await analyzer.queue_for_analysis(
            chat.id,
            {
                "time": msg.date.astimezone(timezone.utc).isoformat(),
                "unit": unit,
                "observer_signature": observer,
                "mgrs": mgrs_str,
                "content": "Location update",
            },
        )
        
        # Enhanced DefHack location analysis
        if defhack_bridge:
            try:
                logger.info("📍 Processing location update with DefHack military analysis...")
                
                # Create location-based observation
                location_observation = {
                    'target': 'Position update',
                    'location': mgrs_str,
                    'confidence': 95 if loc.horizontal_accuracy and loc.horizontal_accuracy < 10 else 70,
                    'observer': observer,
                    'time': msg.date.astimezone(timezone.utc),
                    'unit': unit,
                    'coordinates': f"{loc.latitude}, {loc.longitude}",
                    'accuracy': getattr(loc, "horizontal_accuracy", None)
                }
                
                # Process location with DefHack
                results = await defhack_bridge.process_telegram_observation(location_observation)
                
                if results['stored']:
                    # Send location confirmation
                    loc_msg = f"📍 **POSITION LOGGED**\nMGRS: {mgrs_str}\nAccuracy: {meta}"
                    await msg.reply_text(loc_msg)
                
                logger.info("✅ DefHack location analysis completed")
                
            except Exception as e:
                logger.error(f"❌ DefHack location analysis failed: {e}")

    async def on_frago_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /frago command to generate fragmentary orders"""
        msg = update.effective_message
        if not msg or msg.from_user is None or msg.from_user.is_bot:
            return
        
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return
        
        if defhack_bridge:
            try:
                logger.info("📋 Generating FRAGO on user request...")
                
                # Get recent messages for context
                if hasattr(context, 'bot_data') and 'recent_observations' in context.bot_data:
                    recent_obs = context.bot_data['recent_observations'][-1]  # Get latest
                else:
                    # Create generic observation from command context
                    recent_obs = {
                        'target': 'User requested FRAGO',
                        'location': 'Unknown',
                        'confidence': 50,
                        'observer': get_observer_signature(msg.from_user),
                        'time': msg.date.astimezone(timezone.utc),
                    }
                
                # Generate FRAGO
                results = await defhack_bridge.process_telegram_observation(recent_obs)
                
                # Send FRAGO order
                frago_message = f"📋 **FRAGMENTARY ORDER (FRAGO)**\n\n{results['frago_order']}"
                await msg.reply_text(frago_message)
                
                logger.info("✅ FRAGO generated and sent")
                
            except Exception as e:
                logger.error(f"❌ FRAGO generation failed: {e}")
                await msg.reply_text("❌ Failed to generate FRAGO. Please try again.")
        else:
            await msg.reply_text("❌ FRAGO generation not available. DefHack bridge not initialized.")

    async def on_intrep_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        """Handle /intrep command to generate intelligence reports"""
        msg = update.effective_message
        if not msg or msg.from_user is None or msg.from_user.is_bot:
            return
        
        chat = update.effective_chat
        if chat.type not in ("group", "supergroup"):
            return
        
        if defhack_bridge:
            try:
                logger.info("📊 Generating intelligence report on user request...")
                
                # Generate 24-hour intelligence summary
                report = await defhack_bridge.generate_daily_intelligence_report()
                
                # Send intelligence report
                intrep_message = f"📊 **24-HOUR INTELLIGENCE REPORT**\n\n{report}"
                await msg.reply_text(intrep_message)
                
                logger.info("✅ Intelligence report generated and sent")
                
            except Exception as e:
                logger.error(f"❌ Intelligence report generation failed: {e}")
                await msg.reply_text("❌ Failed to generate intelligence report. Please try again.")
        else:
            await msg.reply_text("❌ Intelligence report not available. DefHack bridge not initialized.")

    def _is_tactical_message(text: str) -> bool:
        """Determine if a message contains tactical information worth processing"""
        tactical_keywords = [
            'enemy', 'hostile', 'contact', 'target', 'vehicle', 'personnel',
            'movement', 'position', 'location', 'threat', 'activity',
            'observation', 'spotted', 'sighting', 'patrol', 'convoy'
        ]
        
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in tactical_keywords)

    return [
        MessageHandler(
            filters.ChatType.GROUPS & filters.TEXT & ~filters.COMMAND,
            on_enhanced_group_text,
        ),
        MessageHandler(
            filters.ChatType.GROUPS & filters.LOCATION,
            on_enhanced_group_location,
        ),
        MessageHandler(
            filters.ChatType.GROUPS & filters.COMMAND & filters.Regex(r'^/frago'),
            on_frago_command,
        ),
        MessageHandler(
            filters.ChatType.GROUPS & filters.COMMAND & filters.Regex(r'^/intrep'),
            on_intrep_command,
        ),
    ]