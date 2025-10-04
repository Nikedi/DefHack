"""
Enhanced Message Processing System for DefHack Telegram Bot
Handles unformatted text, vision model input, and structured data processing
"""

import asyncio
import base64
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union
from dataclasses import dataclass
import io

from .services.openai_analyzer import OpenAIAnalyzer
from .user_roles import user_manager, UserRole
from .defhack_bridge import DefHackTelegramBridge

try:
    import openai
    from PIL import Image
except ImportError:
    openai = None
    Image = None

@dataclass
class ProcessedObservation:
    """Structured observation data after processing"""
    original_message: str
    formatted_data: Dict[str, Any]
    confidence_score: float
    processing_method: str  # "text_llm", "vision_model", "manual_format"
    user_id: int
    username: str
    unit: str
    mgrs: str
    timestamp: datetime
    requires_leader_notification: bool = True
    threat_level: str = "UNKNOWN"

class EnhancedMessageProcessor:
    """Enhanced message processor for tactical communications"""
    
    def __init__(self, logger: logging.Logger):
        self.logger = logger
        self.openai_client = self._init_openai_client()
        self.defhack_bridge = DefHackTelegramBridge()
        
    def _init_openai_client(self):
        """Initialize OpenAI client for vision and text processing"""
        try:
            import os
            api_key = os.getenv("OPENAI_API_KEY")
            if api_key and openai:
                return openai.AsyncOpenAI(api_key=api_key)
        except Exception as e:
            self.logger.error(f"Failed to initialize OpenAI client: {e}")
        return None
    
    async def process_message(self, message, user_id: int, chat_id: int) -> Optional[ProcessedObservation]:
        """
        Main processing function for incoming messages
        Handles text, photos, and location data
        """
        try:
            user_profile = user_manager.get_user(user_id)
            if not user_profile:
                self.logger.warning(f"Unknown user {user_id} - registration required")
                return None
            
            # Update user activity
            user_manager.update_user_activity(user_id)
            
            # Determine message type and process accordingly
            if message.photo and len(message.photo) > 0:
                return await self._process_photo_message(message, user_profile, chat_id)
            elif message.text:
                return await self._process_text_message(message, user_profile, chat_id)
            elif message.location:
                return await self._process_location_message(message, user_profile, chat_id)
            else:
                self.logger.info(f"Unsupported message type from user {user_id}")
                return None
                
        except Exception as e:
            self.logger.error(f"Error processing message from user {user_id}: {e}")
            return None
    
    async def _process_photo_message(self, message, user_profile, chat_id: int) -> Optional[ProcessedObservation]:
        """Process photo messages using vision model"""
        if not self.openai_client:
            self.logger.error("OpenAI client not available for vision processing")
            return None
        
        try:
            # Get the highest resolution photo
            photo = message.photo[-1]  # Last item is highest resolution
            
            # Download photo
            photo_file = await message.bot.get_file(photo.file_id)
            photo_bytes = await photo_file.download_as_bytearray()
            
            # Encode for OpenAI Vision API
            photo_b64 = base64.b64encode(photo_bytes).decode('utf-8')
            
            # Create vision analysis prompt
            vision_prompt = self._build_vision_analysis_prompt(user_profile)
            
            # Call OpenAI Vision API
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",  # Use vision-capable model
                messages=[
                    {
                        "role": "system",
                        "content": "You are a military intelligence analyst examining tactical photographs for threat assessment."
                    },
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": vision_prompt},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:image/jpeg;base64,{photo_b64}",
                                    "detail": "high"
                                }
                            }
                        ]
                    }
                ],
                max_tokens=500,
                temperature=0.1
            )
            
            analysis_text = response.choices[0].message.content
            
            # Extract structured data from analysis
            formatted_data = await self._extract_structured_data_from_text(
                analysis_text, user_profile, message
            )
            
            # Determine threat level from image analysis
            threat_level = self._assess_threat_level(analysis_text)
            
            observation = ProcessedObservation(
                original_message=f"[PHOTO] {message.caption or 'Photo without caption'}",
                formatted_data=formatted_data,
                confidence_score=0.8,  # Vision model typically high confidence
                processing_method="vision_model",
                user_id=user_profile.user_id,
                username=user_profile.username,
                unit=user_profile.unit,
                mgrs=self._extract_mgrs_from_message(message),
                timestamp=message.date.astimezone(timezone.utc),
                requires_leader_notification=True,
                threat_level=threat_level
            )
            
            self.logger.info(f"Processed photo from {user_profile.username} with vision model")
            return observation
            
        except Exception as e:
            self.logger.error(f"Vision processing failed: {e}")
            return None
    
    async def _process_text_message(self, message, user_profile, chat_id: int) -> Optional[ProcessedObservation]:
        """Process text messages - both formatted and unformatted"""
        text = message.text.strip()
        
        # Check if message is already formatted (contains structured data)
        if self._is_formatted_message(text):
            return await self._process_formatted_message(message, user_profile, chat_id)
        else:
            return await self._process_unformatted_message(message, user_profile, chat_id)
    
    async def _process_formatted_message(self, message, user_profile, chat_id: int) -> Optional[ProcessedObservation]:
        """Process already formatted tactical messages"""
        try:
            # Extract structured data directly
            formatted_data = self._parse_formatted_message(message.text)
            
            observation = ProcessedObservation(
                original_message=message.text,
                formatted_data=formatted_data,
                confidence_score=0.95,  # High confidence for pre-formatted
                processing_method="manual_format",
                user_id=user_profile.user_id,
                username=user_profile.username,
                unit=user_profile.unit,
                mgrs=formatted_data.get('mgrs', 'UNKNOWN'),
                timestamp=message.date.astimezone(timezone.utc),
                requires_leader_notification=True,
                threat_level=formatted_data.get('threat_level', 'UNKNOWN')
            )
            
            return observation
            
        except Exception as e:
            self.logger.error(f"Failed to process formatted message: {e}")
            return None
    
    async def _process_unformatted_message(self, message, user_profile, chat_id: int) -> Optional[ProcessedObservation]:
        """Process unformatted text using LLM"""
        if not self.openai_client:
            self.logger.error("OpenAI client not available for text processing")
            return None
        
        try:
            # Create text analysis prompt
            text_prompt = self._build_text_analysis_prompt(message.text, user_profile)
            
            # Call OpenAI for text analysis and formatting
            response = await self.openai_client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {
                        "role": "system",
                        "content": "You are a military intelligence analyst converting informal tactical reports into structured military observations."
                    },
                    {
                        "role": "user",
                        "content": text_prompt
                    }
                ],
                temperature=0.1,
                max_tokens=400
            )
            
            formatted_text = response.choices[0].message.content
            
            # Extract structured data from LLM response
            formatted_data = await self._extract_structured_data_from_text(
                formatted_text, user_profile, message
            )
            
            # Assess threat level
            threat_level = self._assess_threat_level(formatted_text)
            
            observation = ProcessedObservation(
                original_message=message.text,
                formatted_data=formatted_data,
                confidence_score=0.75,  # Medium confidence for LLM formatting
                processing_method="text_llm",
                user_id=user_profile.user_id,
                username=user_profile.username,
                unit=user_profile.unit,
                mgrs=self._extract_mgrs_from_message(message),
                timestamp=message.date.astimezone(timezone.utc),
                requires_leader_notification=True,
                threat_level=threat_level
            )
            
            self.logger.info(f"Processed unformatted text from {user_profile.username} with LLM")
            return observation
            
        except Exception as e:
            self.logger.error(f"Text LLM processing failed: {e}")
            return None
    
    async def _process_location_message(self, message, user_profile, chat_id: int) -> Optional[ProcessedObservation]:
        """Process location sharing messages"""
        try:
            from ..utils import to_mgrs
            
            location = message.location
            mgrs = to_mgrs(location.latitude, location.longitude)
            
            formatted_data = {
                'what': 'Position Update',
                'mgrs': mgrs,
                'confidence': 95 if location.horizontal_accuracy and location.horizontal_accuracy < 10 else 80,
                'amount': None,
                'coordinates': f"{location.latitude}, {location.longitude}",
                'accuracy': location.horizontal_accuracy,
                'observer_signature': user_profile.username,
                'unit': user_profile.unit,
                'time': message.date.astimezone(timezone.utc).isoformat()
            }
            
            observation = ProcessedObservation(
                original_message=f"Location: {mgrs}",
                formatted_data=formatted_data,
                confidence_score=0.9,
                processing_method="location_data",
                user_id=user_profile.user_id,
                username=user_profile.username,
                unit=user_profile.unit,
                mgrs=mgrs,
                timestamp=message.date.astimezone(timezone.utc),
                requires_leader_notification=False,  # Location updates don't require FRAGO
                threat_level="INFO"
            )
            
            return observation
            
        except Exception as e:
            self.logger.error(f"Location processing failed: {e}")
            return None
    
    def _build_vision_analysis_prompt(self, user_profile) -> str:
        """Build prompt for vision model analysis"""
        return f"""
Analyze this tactical photograph and provide a structured military intelligence assessment.

Observer: {user_profile.full_name} ({user_profile.rank or 'Unknown rank'})
Unit: {user_profile.unit}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Provide your analysis in this format:

WHAT: [Description of observed entities/activities]
WHERE: [Location details if visible - landmarks, terrain features]
WHEN: [Time indicators if visible]
AMOUNT: [Number of personnel, vehicles, equipment]
CONFIDENCE: [Your confidence level 1-100]
THREAT LEVEL: [LOW/MEDIUM/HIGH/CRITICAL]
TACTICAL SIGNIFICANCE: [Brief assessment of military importance]

Focus on:
- Enemy personnel, vehicles, equipment
- Defensive positions, fortifications
- Movement patterns and directions
- Weapons systems and capabilities
- Terrain advantages/disadvantages
- Any immediate threats or opportunities
"""
    
    def _build_text_analysis_prompt(self, text: str, user_profile) -> str:
        """Build prompt for text analysis and formatting"""
        return f"""
Convert this informal tactical report into structured military observation format:

Original Report: "{text}"

Observer: {user_profile.full_name} ({user_profile.rank or 'Unknown rank'})
Unit: {user_profile.unit}
Time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S UTC')}

Format your response as:

WHAT: [Clear description using military terminology]
WHERE: [MGRS coordinates if mentioned, or location description]
WHEN: [Time of observation]
AMOUNT: [Quantity of personnel/equipment if specified]
CONFIDENCE: [Confidence level 1-100 based on report clarity]
THREAT LEVEL: [LOW/MEDIUM/HIGH/CRITICAL based on content]
FORMATTED OBSERVATION: [Professional military observation statement]

Extract and standardize:
- Military unit designations (BTG, squad, platoon, etc.)
- Weapon systems using NATO designations
- Tactical movements and positions
- Threat assessments and recommendations
"""
    
    async def _extract_structured_data_from_text(self, text: str, user_profile, message) -> Dict[str, Any]:
        """Extract structured data from processed text"""
        # Parse the formatted text response into structured data
        lines = text.split('\n')
        data = {
            'what': 'Unknown',
            'mgrs': 'UNKNOWN',
            'confidence': 50,
            'amount': None,
            'observer_signature': user_profile.username,
            'unit': user_profile.unit,
            'time': message.date.astimezone(timezone.utc).isoformat(),
            'sensor_id': None
        }
        
        for line in lines:
            line = line.strip()
            if line.startswith('WHAT:'):
                data['what'] = line[5:].strip()
            elif line.startswith('WHERE:') and 'mgrs' not in data:
                location = line[6:].strip()
                # Try to extract MGRS from location description
                mgrs = self._extract_mgrs_from_text(location)
                if mgrs:
                    data['mgrs'] = mgrs
            elif line.startswith('AMOUNT:'):
                try:
                    amount_str = line[7:].strip()
                    if amount_str and amount_str.lower() != 'unknown':
                        data['amount'] = float(amount_str.split()[0])  # Get first number
                except:
                    pass
            elif line.startswith('CONFIDENCE:'):
                try:
                    conf_str = line[11:].strip()
                    data['confidence'] = int(conf_str.split()[0])  # Get first number
                except:
                    pass
        
        return data
    
    def _assess_threat_level(self, text: str) -> str:
        """Assess threat level from text content"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['critical', 'immediate', 'urgent', 'enemy attack']):
            return 'CRITICAL'
        elif any(word in text_lower for word in ['high', 'enemy', 'hostile', 'weapon', 'threat']):
            return 'HIGH'
        elif any(word in text_lower for word in ['medium', 'suspicious', 'possible', 'patrol']):
            return 'MEDIUM'
        elif any(word in text_lower for word in ['low', 'routine', 'normal', 'friendly']):
            return 'LOW'
        else:
            return 'UNKNOWN'
    
    def _is_formatted_message(self, text: str) -> bool:
        """Check if message is already in structured format"""
        structured_indicators = [
            'WHAT:', 'WHERE:', 'WHEN:', 'MGRS:', 'CONFIDENCE:', 'OBSERVER:'
        ]
        return any(indicator in text.upper() for indicator in structured_indicators)
    
    def _parse_formatted_message(self, text: str) -> Dict[str, Any]:
        """Parse already formatted message into structured data"""
        # Implementation for parsing pre-formatted messages
        # This would extract data from structured military format
        return {
            'what': 'Formatted observation',
            'mgrs': 'UNKNOWN',
            'confidence': 80,
            'amount': None
        }
    
    def _extract_mgrs_from_message(self, message) -> str:
        """Extract MGRS coordinates from message"""
        if hasattr(message, 'location') and message.location:
            try:
                from ..utils import to_mgrs
                return to_mgrs(message.location.latitude, message.location.longitude)
            except:
                pass
        return 'UNKNOWN'
    
    def _extract_mgrs_from_text(self, text: str) -> Optional[str]:
        """Extract MGRS coordinates from text"""
        import re
        # Pattern for MGRS coordinates (simplified)
        mgrs_pattern = r'\b\d{1,2}[A-Z]{1,3}\s?[A-Z]{2}\s?\d{4,10}\b'
        match = re.search(mgrs_pattern, text.upper())
        return match.group(0) if match else None