#!/usr/bin/env python3
"""
DefHack Telegram Integration Bridge
Connects military LLM functions with the merged Telegram bot
"""

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Dict, Any, Optional, Tuple
import sys
import os

# Add the parent directory to Python path to import DefHack modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    # Import from the root directory
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from military_operations_integration import DefHackMilitaryOperations
    from defhack_unified_input import DefHackClient
except ImportError as e:
    print(f"⚠️  Import Error: {e}")
    print("📍 Make sure you're running from the DefHack root directory")
    print("💡 Try: python -m DefHack.clarity_opsbot.defhack_bridge")

# Import to_mgrs with fallback handling
try:
    from .utils import to_mgrs
except ImportError:
    try:
        from utils import to_mgrs
    except ImportError:
        print("⚠️  Warning: to_mgrs function not available, using placeholder")
        to_mgrs = None

class DefHackTelegramBridge:
    """
    Bridge class that connects DefHack military LLM functions 
    with the Telegram bot for automated tactical communications
    """
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.logger.info("🔗 Initializing DefHack Telegram Bridge...")
        
        try:
            # Initialize military operations handler
            self.military_ops = DefHackMilitaryOperations()
            self.logger.info("✅ Military operations integration loaded")
            
            # Initialize DefHack database client  
            self.client = DefHackClient()
            self.logger.info("✅ DefHack database client loaded")
            
        except Exception as e:
            self.logger.error(f"❌ Failed to initialize bridge: {e}")
            raise
    
    def _parse_lat_lon(self, location_str: str) -> Optional[Tuple[float, float]]:
        """
        Parse latitude/longitude coordinates from various string formats.
        
        Supports formats like:
        - "40.7128, -74.0060"  
        - "LAT: 40.7128, LON: -74.0060"
        - "40.7128,-74.0060"
        - etc.
        
        Returns tuple of (lat, lon) or None if parsing fails
        """
        if not location_str:
            return None
            
        try:
            # Remove common prefixes and clean up
            clean_str = location_str.replace('LAT:', '').replace('LON:', '').replace('lat:', '').replace('lon:', '').strip()
            
            # Look for coordinate patterns: two numbers separated by comma
            coord_pattern = r'(-?\d+\.?\d*)\s*,\s*(-?\d+\.?\d*)'
            match = re.search(coord_pattern, clean_str)
            
            if match:
                lat = float(match.group(1))
                lon = float(match.group(2))
                
                # Basic validation - lat should be -90 to 90, lon should be -180 to 180
                if -90 <= lat <= 90 and -180 <= lon <= 180:
                    return (lat, lon)
                    
        except (ValueError, AttributeError) as e:
            self.logger.debug(f"Failed to parse coordinates from '{location_str}': {e}")
            
        return None
    
    async def process_telegram_observation(self, telegram_data: Dict[str, Any]) -> Dict[str, str]:
        """
        Process a new observation from Telegram and generate military responses
        
        Args:
            telegram_data: Dictionary containing observation data from Telegram
                          Expected fields: target, location, confidence, observer, time
        
        Returns:
            Dictionary with telegram_message, frago_order, and status information
        """
        try:
            self.logger.info(f"📥 Processing Telegram observation: {telegram_data}")
            
            # Convert Telegram data to DefHack observation format
            observation = self._convert_telegram_to_observation(telegram_data)
            
            # Add observation to DefHack database
            self.logger.info("💾 Adding observation to DefHack database...")
            result = self.client.add_sensor_observation(observation)
            observation_id = result.get('report_id', 'unknown')
            self.logger.info(f"✅ Observation stored with ID: {observation_id}")
            
            # Generate military responses using DefHack LLM
            self.logger.info("🤖 Generating military analysis and responses...")
            # Convert ISO string back to datetime object for military ops processing
            observation_for_military = observation.copy()
            observation_for_military['time'] = datetime.fromisoformat(observation['time'])
            results = await self.military_ops.process_new_observation(observation_for_military)
            
            # Format response for Telegram
            response = {
                'telegram_message': results.get('telegram', 'Analysis completed'),
                'frago_order': results.get('frago', 'No FRAGO generated'),
                'stored': True,
                'observation_id': observation_id,
                'analysis_summary': results.get('analysis_summary', 'No summary available'),
                'threat_level': results.get('threat_level', 'Unknown')
            }
            
            self.logger.info("✅ Successfully processed Telegram observation")
            return response
            
        except Exception as e:
            self.logger.error(f"❌ Error processing Telegram observation: {e}")
            return {
                'telegram_message': f'❌ Error processing observation: {str(e)}',
                'frago_order': 'Error - FRAGO generation failed',
                'stored': False,
                'error': str(e)
            }
    
    def _convert_telegram_to_observation(self, telegram_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert Telegram message data to DefHack observation format
        
        Args:
            telegram_data: Raw data from Telegram message
            
        Returns:
            Formatted observation for DefHack database
        """
        # Extract and validate observation data
        what = telegram_data.get('target', telegram_data.get('what', 'Unknown target'))
        mgrs = telegram_data.get('location', telegram_data.get('mgrs', 'Unknown location'))
        confidence = int(telegram_data.get('confidence', 50))
        observer = telegram_data.get('observer', telegram_data.get('observer_signature', 'TelegramBot'))
        
        # Handle time field - convert to UTC datetime if needed
        time_field = telegram_data.get('time')
        if isinstance(time_field, str):
            # Try to parse string timestamp
            try:
                observation_time = datetime.fromisoformat(time_field.replace('Z', '+00:00'))
            except:
                observation_time = datetime.now(timezone.utc)
        elif isinstance(time_field, datetime):
            observation_time = time_field
        else:
            observation_time = datetime.now(timezone.utc)
        
        # Handle MGRS - preserve valid MGRS, convert lat/lon, or set None for unknown
        if mgrs in ['UNKNOWN', 'Unknown location', 'N/A', ''] or mgrs is None:
            # Keep as None for unknown locations - database should handle NULL values
            mgrs = None
            self.logger.debug(f"📍 MGRS set to None for unknown location")
        elif mgrs and (',' in mgrs or mgrs.startswith('LAT')):
            # Handle lat/lon coordinates - try to convert to MGRS
            self.logger.info(f"📍 Attempting to convert lat/lon coordinates to MGRS: {mgrs}")
            
            coords = self._parse_lat_lon(mgrs)
            if coords and to_mgrs:
                lat, lon = coords
                try:
                    converted_mgrs = to_mgrs(lat, lon)
                    if converted_mgrs and converted_mgrs != "UNKNOWN":
                        self.logger.info(f"✅ Successfully converted ({lat}, {lon}) to MGRS: {converted_mgrs}")
                        mgrs = converted_mgrs
                    else:
                        self.logger.warning(f"⚠️ MGRS conversion returned UNKNOWN for ({lat}, {lon})")
                        mgrs = None  # Keep as None for failed conversions
                except Exception as e:
                    self.logger.error(f"❌ MGRS conversion failed for ({lat}, {lon}): {e}")
                    mgrs = None  # Keep as None for failed conversions
            else:
                self.logger.warning(f"⚠️ Could not parse lat/lon coordinates or conversion not available: {mgrs}")
                mgrs = None  # Keep as None for unparseable coordinates
        elif mgrs and isinstance(mgrs, str) and len(mgrs) > 5:
            # Valid MGRS coordinate - preserve it
            self.logger.info(f"✅ Preserving valid MGRS coordinate: {mgrs}")
            # mgrs stays as is
        else:
            # Invalid or empty MGRS
            self.logger.warning(f"⚠️ Invalid MGRS format, setting to None: {mgrs}")
            mgrs = None
        
        # Extract unit from group name (first two words)
        unit_name = telegram_data.get('unit', 'Unknown Unit')
        if unit_name != 'Unknown Unit':
            unit_words = unit_name.split()[:2]  # First two words
            unit = ' '.join(unit_words) if unit_words else 'Unknown Unit'
        else:
            unit = 'Unknown Unit'
        
        observation = {
            'what': what,
            'mgrs': mgrs,  # None for unknown locations, actual MGRS string when available
            'confidence': confidence,
            'observer_signature': observer,  # Telegram username
            'time': observation_time.isoformat(),  # Convert datetime to ISO string
            'sensor_id': f'telegram_{observer}',  # Use string identifier for Telegram
            'unit': unit,  # First two words of group name
            'amount': telegram_data.get('amount', 1.0)  # Default to 1.0 if null
        }
        
        self.logger.debug(f"📝 Converted observation: {observation}")
        return observation
    
    async def generate_daily_intelligence_report(self) -> str:
        """
        Generate a 24-hour intelligence summary for Telegram distribution
        
        Returns:
            Formatted intelligence report string
        """
        try:
            self.logger.info("📊 Generating daily intelligence report...")
            
            # Use military operations to generate the report
            report = await self.military_ops.generate_daily_intelligence_summary()
            
            self.logger.info("✅ Daily intelligence report generated")
            return report
            
        except Exception as e:
            self.logger.error(f"❌ Error generating daily report: {e}")
            return f"❌ Error generating intelligence report: {str(e)}"
    
    async def analyze_telegram_conversation(self, messages: list) -> str:
        """
        Analyze a series of Telegram messages for tactical intelligence
        
        Args:
            messages: List of Telegram message objects or text strings
            
        Returns:
            Analysis summary as formatted string
        """
        try:
            self.logger.info(f"💬 Analyzing {len(messages)} Telegram messages...")
            
            # Extract text content from messages
            message_texts = []
            for msg in messages:
                if isinstance(msg, str):
                    message_texts.append(msg)
                elif hasattr(msg, 'text') and msg.text:
                    message_texts.append(msg.text)
                elif isinstance(msg, dict) and 'text' in msg:
                    message_texts.append(msg['text'])
            
            # Combine messages for analysis
            conversation_text = "\n".join(message_texts)
            
            # Use military LLM to analyze the conversation
            analysis = await self.military_ops.analyze_tactical_conversation(conversation_text)
            
            self.logger.info("✅ Telegram conversation analysis completed")
            return analysis
            
        except Exception as e:
            self.logger.error(f"❌ Error analyzing conversation: {e}")
            return f"❌ Error analyzing conversation: {str(e)}"

# Utility functions for Telegram bot integration
def extract_observation_from_message(message) -> Dict[str, Any]:
    """
    Extract observation data from a Telegram message
    
    Args:
        message: Telegram message object
        
    Returns:
        Dictionary with extracted observation data
    """
    observation_data = {}
    
    # Extract text content
    if hasattr(message, 'text') and message.text:
        text = message.text.lower()
        
        # Simple keyword extraction (can be enhanced with NLP)
        if 'enemy' in text or 'hostile' in text:
            observation_data['target'] = 'Enemy forces'
        elif 'vehicle' in text:
            observation_data['target'] = 'Vehicle'
        elif 'personnel' in text:
            observation_data['target'] = 'Personnel'
        else:
            observation_data['target'] = 'Unknown'
        
        # Look for confidence indicators
        if 'confirmed' in text or 'certain' in text:
            observation_data['confidence'] = 90
        elif 'likely' in text or 'probable' in text:
            observation_data['confidence'] = 70
        elif 'possible' in text or 'maybe' in text:
            observation_data['confidence'] = 40
        else:
            observation_data['confidence'] = 50
    
    # Extract location from message
    if hasattr(message, 'location') and message.location:
        lat, lng = message.location.latitude, message.location.longitude
        observation_data['location'] = f"Lat: {lat}, Lng: {lng}"
    
    # Extract user information
    if hasattr(message, 'from_user') and message.from_user:
        username = message.from_user.username or f"User{message.from_user.id}"
        observation_data['observer'] = username
    
    # Add timestamp
    if hasattr(message, 'date'):
        observation_data['time'] = message.date
    else:
        observation_data['time'] = datetime.now(timezone.utc)
    
    return observation_data

async def test_bridge():
    """Test function to verify the bridge integration"""
    print("🧪 Testing DefHack Telegram Bridge...")
    
    try:
        # Initialize bridge
        bridge = DefHackTelegramBridge()
        print("✅ Bridge initialized successfully")
        
        # Test observation processing
        test_observation = {
            'target': 'Enemy BTG',
            'location': '33S VN 12345 67890',
            'confidence': 80,
            'observer': 'TestUser',
            'time': datetime.now(timezone.utc)
        }
        
        print("📥 Processing test observation...")
        results = await bridge.process_telegram_observation(test_observation)
        
        print("📤 Results:")
        print(f"   Telegram Message: {results['telegram_message'][:100]}...")
        print(f"   FRAGO Generated: {'Yes' if 'FRAGO' in results['frago_order'] else 'No'}")
        print(f"   Stored in DB: {results['stored']}")
        
        print("✅ Bridge test completed successfully!")
        
    except Exception as e:
        print(f"❌ Bridge test failed: {e}")
        raise

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Run test
    asyncio.run(test_bridge())