#!/usr/bin/env python3
"""
DefHack Military Operations Integration
Production-ready integration for Telegram and FRAGO automation
"""
import asyncio
import asyncpg
import requests
from datetime import datetime, timezone
from typing import Dict, Optional

class DefHackMilitaryOperations:
    """Production military operations integration"""
    
    def __init__(self, api_base: str = "http://localhost:8080"):
        self.api_base = api_base
        self.db_url = "postgresql://postgres:postgres@localhost:5432/defhack"
    
    def _query_llm(self, prompt: str, k: int = 6) -> Optional[str]:
        """Make LLM query with error handling"""
        try:
            response = requests.post(
                f"{self.api_base}/orders/draft",
                params={"query": prompt, "k": k},
                timeout=30  # 30 second timeout
            )
            
            if response.status_code == 200:
                return response.json().get('body', response.json().get('text'))
            else:
                print(f"❌ LLM API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ LLM Error: {e}")
            return None
    
    async def process_new_observation(self, observation: Dict) -> Dict[str, str]:
        """
        Process a new observation and generate both Telegram message and FRAGO
        
        Returns:
            Dict with 'telegram' and 'frago' keys containing generated content
        """
        
        target = observation.get('what', 'Unknown')
        location = observation.get('mgrs', 'Unknown')
        amount = observation.get('amount', 1)
        confidence = observation.get('confidence', 0)
        observer = observation.get('observer_signature', 'Observer')
        time_str = observation.get('time', datetime.now(timezone.utc)).strftime('%H%MZ')
        
        results = {}
        
        # Generate Telegram message
        telegram_prompt = f"""
Create a concise tactical Telegram message (max 150 characters):

OBSERVATION: {target} (x{amount}) at {location} - {confidence}% confidence - {observer} at {time_str}

Format: [PRIORITY] TIME: TARGET (QTY) at GRID - CONF% - OBSERVER

Use emojis: 🚨 (90%+), ⚠️ (80-89%), ℹ️ (<80%)
"""
        
        telegram_result = self._query_llm(telegram_prompt, k=3)
        results['telegram'] = telegram_result or f"🚨 {time_str}: {target} (x{amount}) at {location} - {confidence}% - {observer}"
        
        # Generate FRAGO only for high-confidence observations
        if confidence >= 85:
            frago_prompt = f"""
Generate a brief FRAGO for immediate response to: {target} (x{amount}) at {location} with {confidence}% confidence.

Format:
FRAGO [NUMBER] - [TARGET] RESPONSE
1. SITUATION: {target} observed at {location}
2. MISSION: [Unit] will [action] to [purpose]
3. EXECUTION: 
   - Immediate actions (0-30 min)
   - Follow-up actions (30 min - 2 hours)
4. TIMELINE: Specific milestones
5. COORDINATION: Communication and reporting

Keep under 250 words for rapid dissemination.
"""
            
            frago_result = self._query_llm(frago_prompt, k=5)
            results['frago'] = frago_result or f"FRAGO: Respond to {target} sighting at {location}"
        else:
            results['frago'] = f"INFORMATION: {target} sighted at {location} - Continue monitoring"
        
        return results
    
    async def generate_daily_intelligence_summary(self) -> Optional[str]:
        """Generate comprehensive daily intelligence summary"""
        
        try:
            # Get observations from last 24 hours
            conn = await asyncpg.connect(self.db_url)
            
            observations = await conn.fetch("""
            SELECT time, mgrs, what, amount, confidence, observer_signature, unit
            FROM sensor_reading 
            WHERE received_at >= NOW() - INTERVAL '24 hours'
            ORDER BY confidence DESC, time DESC
            """)
            
            await conn.close()
            
            if not observations:
                return "No observations in the last 24 hours."
            
            # Format observations for analysis
            obs_list = []
            for obs in observations:
                time_str = obs['time'].strftime('%H%MZ')
                obs_list.append(
                    f"- {time_str}: {obs['what']} "
                    f"(x{obs['amount'] if obs['amount'] else '?'}) "
                    f"at {obs['mgrs']} "
                    f"({obs['confidence']}%) - {obs['observer_signature']}"
                )
            
            intel_prompt = f"""
Generate a professional 24-hour intelligence summary:

OBSERVATIONS ({len(observations)} total):
{chr(10).join(obs_list)}

FORMAT:
1. EXECUTIVE SUMMARY (2-3 sentences)
2. KEY OBSERVATIONS (priority threats)
3. PATTERN ANALYSIS (geographic/temporal patterns)
4. THREAT ASSESSMENT (capabilities and intentions)
5. RECOMMENDATIONS (immediate actions and collection priorities)

Use proper military intelligence format. Reference specific observations and apply doctrinal knowledge from available documents about enemy tactics.

Keep under 500 words for briefing purposes.
"""
            
            return self._query_llm(intel_prompt, k=10)
            
        except Exception as e:
            print(f"❌ Intelligence summary error: {e}")
            return None
    
    async def get_latest_observation(self) -> Optional[Dict]:
        """Get the most recent observation from database"""
        try:
            conn = await asyncpg.connect(self.db_url)
            
            latest = await conn.fetchrow("""
            SELECT time, mgrs, what, amount, confidence, observer_signature, unit, sensor_id
            FROM sensor_reading 
            ORDER BY received_at DESC 
            LIMIT 1
            """)
            
            await conn.close()
            
            if latest:
                return {
                    'what': latest['what'],
                    'mgrs': latest['mgrs'],
                    'amount': latest['amount'],
                    'confidence': latest['confidence'],
                    'time': latest['time'],
                    'observer_signature': latest['observer_signature'],
                    'unit': latest['unit'] or 'Unknown Unit',
                    'sensor_id': latest['sensor_id']
                }
            
            return None
            
        except Exception as e:
            print(f"❌ Database error: {e}")
            return None

# Convenience functions for external integration
async def auto_process_observation(observation_id: Optional[int] = None) -> Dict[str, str]:
    """Automatically process latest or specific observation"""
    ops = DefHackMilitaryOperations()
    
    if observation_id:
        # Get specific observation by ID (implement if needed)
        observation = await ops.get_latest_observation()
    else:
        # Get latest observation
        observation = await ops.get_latest_observation()
    
    if observation:
        return await ops.process_new_observation(observation)
    else:
        return {'telegram': 'No observations available', 'frago': 'No orders required'}

async def daily_intel_brief() -> str:
    """Generate daily intelligence brief"""
    ops = DefHackMilitaryOperations()
    result = await ops.generate_daily_intelligence_summary()
    return result or "Intelligence summary not available"

# Example usage and testing
if __name__ == "__main__":
    async def demo():
        print("🎯 DefHack Military Operations Integration")
        print("=" * 60)
        
        ops = DefHackMilitaryOperations()
        
        # Test with latest observation
        print("\n1. PROCESSING LATEST OBSERVATION")
        print("-" * 40)
        
        observation = await ops.get_latest_observation()
        if observation:
            print(f"📡 Observation: {observation['what']} at {observation['mgrs']}")
            print(f"    Confidence: {observation['confidence']}%, Observer: {observation['observer_signature']}")
            
            results = await ops.process_new_observation(observation)
            
            print(f"\n📱 Telegram Message:")
            print(results['telegram'])
            
            print(f"\n📋 FRAGO/Order:")
            print(results['frago'][:200] + "..." if len(results['frago']) > 200 else results['frago'])
        
        print("\n2. DAILY INTELLIGENCE SUMMARY")
        print("-" * 40)
        
        intel_summary = await ops.generate_daily_intelligence_summary()
        if intel_summary:
            print(intel_summary[:300] + "..." if len(intel_summary) > 300 else intel_summary)
        
        print("\n✅ Integration Demo Complete!")
        print("\n🔗 Integration Points:")
        print("- Connect to Telegram bot API for automatic message sending")
        print("- Add database triggers for real-time observation processing") 
        print("- Schedule daily intelligence reports")
        print("- Implement FRAGO distribution to tactical units")
    
    asyncio.run(demo())