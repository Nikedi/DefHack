#!/usr/bin/env python3
"""
Test script for message classification logic
"""

import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def classify_message_type(message_text: str) -> str:
    """Classify message type for appropriate handling"""
    if not message_text:
        return "tactical"
        
    message_lower = message_text.lower()
    
    # Logistics keywords (supplies, fuel, ammo)
    logistics_keywords = [
        'food', 'ruoka', 'water', 'vesi', 'supplies', 'tarvike', 
        'fuel', 'polttoaine', 'ammunition', 'ampumatar', 'ammo',
        'mre', 'mres', 'rations', 'annokset', 'out of', 'low on'
    ]
    
    # Support keywords (maintenance, medical, facilities)
    support_keywords = [
        'toilet', 'wc', 'toiletpaper', 'vessapaperi', 'medicine', 'lääke', 'medical',
        'maintenance', 'huolto', 'repair', 'korjaus', 'spare', 'varaosa',
        'broken', 'rikki', 'fix', 'korjaa', 'help', 'apu'
    ]
    
    for keyword in logistics_keywords:
        if keyword in message_lower:
            logger.info(f"🔍 LOGISTICS keyword '{keyword}' found in '{message_text}'")
            return "logistics"
            
    for keyword in support_keywords:
        if keyword in message_lower:
            logger.info(f"🔍 SUPPORT keyword '{keyword}' found in '{message_text}'")
            return "support"
    
    logger.info(f"🔍 No logistics/support keywords found, classifying as TACTICAL: '{message_text}'")
    return "tactical"

def test_messages():
    """Test various message types"""
    test_cases = [
        "We're out of MREs",
        "50cal low on ammo", 
        "I want home",
        "Enemy contact at grid 123456",
        "Need toilet paper",
        "Radio is broken",
        "Spotted enemy movement north"
    ]
    
    logger.info("🧪 Testing message classification...")
    
    for message in test_cases:
        result = classify_message_type(message)
        logger.info(f"📝 '{message}' → {result}")
        
        # Show what should happen based on classification
        if result == "logistics":
            logger.info(f"   → Should be prefixed with 'LOGISTICS:' and stored in database only")
        elif result == "support":
            logger.info(f"   → Should be prefixed with 'SUPPORT:' and stored in database only")
        else:
            logger.info(f"   → Should be processed as tactical and sent to leaders")
        
        print("-" * 50)

if __name__ == "__main__":
    test_messages()