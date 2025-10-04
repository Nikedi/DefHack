#!/usr/bin/env python3
"""
Quick Test of Military LLM Functions
Fast testing with real DefHack sensor data
"""
import asyncio
import asyncpg
from datetime import datetime, timezone
from military_llm_functions import DefHackMilitaryLLM

async def test_with_real_data():
    """Test military LLM functions with actual sensor data from database"""
    
    print("🔍 Testing Military LLM Functions with Real Data")
    print("=" * 60)
    
    # Get latest observation from database
    try:
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
        
        latest_obs = await conn.fetchrow("""
        SELECT time, mgrs, what, amount, confidence, observer_signature, unit, sensor_id
        FROM sensor_reading 
        ORDER BY received_at DESC 
        LIMIT 1
        """)
        
        await conn.close()
        
        if not latest_obs:
            print("❌ No sensor observations found in database")
            return
        
        # Convert to dictionary for the functions
        observation = {
            'what': latest_obs['what'],
            'mgrs': latest_obs['mgrs'],
            'amount': latest_obs['amount'],
            'confidence': latest_obs['confidence'],
            'time': latest_obs['time'],
            'observer_signature': latest_obs['observer_signature'],
            'unit': latest_obs['unit'] or 'Unknown Unit'
        }
        
        print(f"📡 Using Observation: {observation['what']} at {observation['mgrs']}")
        print(f"    Confidence: {observation['confidence']}%, Observer: {observation['observer_signature']}")
        
        llm = DefHackMilitaryLLM()
        
        # Test 1: Generate Telegram Message
        print("\n1. 📱 TELEGRAM MESSAGE GENERATION")
        print("-" * 40)
        telegram_msg = llm.generate_telegram_message(observation)
        if telegram_msg:
            print(telegram_msg)
        else:
            print("❌ Telegram generation failed")
        
        # Test 2: Generate FRAGO Order (shorter version for speed)
        print("\n2. 📋 FRAGO ORDER GENERATION")
        print("-" * 40)
        
        # Create a simplified FRAGO query for faster response
        simple_frago_query = f"""
Generate a brief FRAGO for: {observation['what']} sighted at {observation['mgrs']} with {observation['confidence']}% confidence.

Include:
1. Situation summary
2. Mission statement 
3. Key execution tasks
4. Timeline for response

Keep response under 300 words for rapid dissemination.
"""
        
        frago_result = llm._make_llm_query(simple_frago_query, k=5)
        if frago_result:
            print(frago_result)
        else:
            print("❌ FRAGO generation failed")
        
    except Exception as e:
        print(f"❌ Database error: {e}")

async def test_intelligence_report():
    """Test the intelligence report generation"""
    
    print("\n3. 📊 24-HOUR INTELLIGENCE REPORT (Sample)")
    print("-" * 40)
    
    llm = DefHackMilitaryLLM()
    
    # Get a quick intelligence summary
    intel_query = """
Generate a brief intelligence summary based on recent sensor observations.

Include:
1. Executive Summary (2-3 sentences)
2. Key Observations (list format)
3. Threat Assessment
4. Recommendations

Keep under 400 words for quick briefing.
"""
    
    intel_result = llm._make_llm_query(intel_query, k=8)
    if intel_result:
        print(intel_result)
    else:
        print("❌ Intelligence report generation failed")

if __name__ == "__main__":
    print("🚀 Quick Military LLM Function Test")
    print("=" * 60)
    
    # Run the tests
    asyncio.run(test_with_real_data())
    asyncio.run(test_intelligence_report())
    
    print("\n✅ Testing Complete!")
    print("\nNext Steps:")
    print("1. Integrate with Telegram bot for automatic notifications")
    print("2. Add FRAGO generation triggers for high-confidence observations")
    print("3. Schedule automatic 24h intelligence reports")
    print("4. Customize prompts for specific threat types")