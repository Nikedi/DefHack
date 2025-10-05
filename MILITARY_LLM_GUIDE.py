#!/usr/bin/env python3
"""
DefHack Military LLM Integration Guide
Complete setup guide for military LLM query functions
"""

print("""
🎯 DefHack Military LLM Functions - Complete Integration Guide
================================================================

✅ COMPLETED: All military LLM query functions are now ready for production use!

📁 FILES CREATED:
----------------
1. military_llm_functions.py      - Core LLM functions (FRAGO, Telegram, Intel reports)
2. military_prompt_templates.py   - Professional military prompt templates  
3. military_operations_integration.py - Production-ready integration module
4. test_military_llm.py          - Testing utilities

🚀 CORE CAPABILITIES:
--------------------
1. ✅ FRAGO ORDER GENERATION
   - Automatic FRAGO generation for new observations
   - Proper military format (5-paragraph order structure)
   - Threat-specific response procedures
   - Timeline and coordination instructions

2. ✅ TELEGRAM MESSAGE GENERATION  
   - Concise tactical notifications (< 200 chars)
   - Priority-based formatting with emojis
   - Military time format and abbreviations
   - Immediate situational awareness

3. ✅ 24-HOUR INTELLIGENCE REPORTS
   - Comprehensive intelligence summaries
   - Pattern analysis and threat assessment
   - Document-supported doctrinal analysis
   - Professional briefing format

🔧 INTEGRATION EXAMPLES:
-----------------------

# Example 1: Process New Observation for Telegram Bot
from military_operations_integration import auto_process_observation
import asyncio

async def handle_new_observation():
    results = await auto_process_observation()
    telegram_msg = results['telegram']
    frago_order = results['frago']
    
    # Send to Telegram bot
    # send_telegram_message(telegram_msg)
    
    # Distribute FRAGO if high confidence
    if 'FRAGO' in frago_order:
        # distribute_frago(frago_order)
        pass

# Example 2: Generate Daily Intelligence Brief
async def daily_briefing():
    from military_operations_integration import daily_intel_brief
    
    intel_report = await daily_intel_brief()
    # Send to command staff
    # email_intel_report(intel_report)

# Example 3: Custom FRAGO for Specific Threat
from military_llm_functions import DefHackMilitaryLLM

def generate_armor_frago(observation):
    llm = DefHackMilitaryLLM() 
    frago = llm.generate_frago_order(observation)
    return frago

📱 TELEGRAM BOT INTEGRATION:
---------------------------
In your Telegram bot branch, use:

```python
from military_operations_integration import DefHackMilitaryOperations

async def on_new_observation(observation_data):
    ops = DefHackMilitaryOperations()
    results = await ops.process_new_observation(observation_data)
    
    # Send Telegram message
    telegram_message = results['telegram']
    await bot.send_message(chat_id=COMMAND_CHAT, text=telegram_message)
    
    # Generate FRAGO if needed (high confidence observations)
    if results['frago'].startswith('FRAGO'):
        await bot.send_message(chat_id=TACTICAL_CHAT, text=results['frago'])
```

⚙️ PROMPT CUSTOMIZATION:
-----------------------
All prompts are in military_prompt_templates.py for easy customization:

- FRAGO templates by threat type (armor, infantry, aviation)
- Priority-based Telegram formatting  
- Intelligence report sections and format
- Threat analysis specializations

🎯 READY FOR DEPLOYMENT:
-----------------------
1. ✅ FRAGO generation working with real sensor data
2. ✅ Telegram messages formatted for mobile notifications
3. ✅ Intelligence reports integrate with uploaded military documents  
4. ✅ Document citations working ([D:5 p1 ¶4] format)
5. ✅ Error handling and timeout protection
6. ✅ Professional military format compliance

🔗 NEXT INTEGRATION STEPS:
-------------------------
1. Connect to your Telegram bot branch:
   - Import military_operations_integration module
   - Add auto_process_observation() to new observation handler
   - Schedule daily_intel_brief() for automated reports

2. Add database triggers (optional):
   - Automatic FRAGO generation for high-confidence observations
   - Real-time Telegram notifications

3. Customize prompts for your specific operational needs:
   - Modify templates in military_prompt_templates.py
   - Add new threat-specific FRAGO formats
   - Adjust intelligence report sections

📋 EXAMPLE OUTPUTS:
------------------
TELEGRAM: "🚨 0600Z: Recon Team (x4) at 35VLG8479572100 - 93% - Delta7"

FRAGO: "FRAGO 001 - RECON TEAM RESPONSE
1. SITUATION: Reconnaissance Team observed at 35VLG8479572100...
2. MISSION: Deploy rapid response team to assess...
3. EXECUTION: Immediate actions (0-30 min), Follow-up (30min-2hr)..."

INTEL REPORT: "EXECUTIVE SUMMARY: 7 observations in last 24h including 
3x T-72 tanks at 35VLG8475672108. Pattern analysis indicates BTG 
reconnaissance phase per Fiore doctrine [D:5 p1 ¶4]..."

🎉 ALL MILITARY LLM FUNCTIONS ARE PRODUCTION READY!
""")

if __name__ == "__main__":
    print("\n🚀 Ready to integrate with your Telegram bot branch!")
    print("Import military_operations_integration and start using the functions.")