#!/usr/bin/env python3
"""
DefHack Military LLM Functions
Specialized LLM query functions for military operations
"""
import requests
import asyncio
import asyncpg
from datetime import datetime, timezone, timedelta
from typing import Dict, List, Optional

class DefHackMilitaryLLM:
    """Military-specific LLM query functions for DefHack"""
    
    def __init__(self, api_base: str = "http://localhost:8080"):
        self.api_base = api_base
    
    def _make_llm_query(self, query: str, k: int = 8) -> Optional[str]:
        """Base function to make LLM queries"""
        try:
            response = requests.post(
                f"{self.api_base}/orders/draft",
                params={"query": query, "k": k}
            )
            
            if response.status_code == 200:
                result = response.json()
                return result.get('body', result.get('text', 'Analysis not available'))
            else:
                print(f"❌ LLM API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ LLM Query Error: {e}")
            return None
    
    def generate_frago_order(self, observation: Dict) -> Optional[str]:
        """
        Generate a FRAGO (Fragmentary Order) based on a new sensor observation
        
        Args:
            observation: Dictionary containing observation data (mgrs, what, amount, confidence, etc.)
        """
        # Extract key details
        target = observation.get('what', 'Unknown Target')
        location = observation.get('mgrs', 'Unknown Location')
        amount = observation.get('amount', 1)
        confidence = observation.get('confidence', 0)
        time_str = observation.get('time', datetime.now(timezone.utc)).strftime('%d%H%MZ %b %Y')
        observer = observation.get('observer_signature', 'Unknown')
        unit = observation.get('unit', 'Unknown Unit')
        
        # Determine threat level and response type
        threat_level = "HIGH" if confidence >= 90 else "MEDIUM" if confidence >= 80 else "LOW"
        
        frago_query = f"""
Generate a FRAGO (Fragmentary Order) in proper military format for the following observation:

OBSERVATION DETAILS:
- Time: {time_str}
- Target: {target} (Quantity: {amount})
- Location: {location} (MGRS)
- Confidence: {confidence}%
- Observer: {observer} ({unit})
- Threat Level: {threat_level}

FRAGO REQUIREMENTS:
1. Use proper military FRAGO format (OPORD reference, situation, mission, execution, admin/logistics, command/signal)
2. Include immediate response actions based on the threat type
3. Specify units to engage, surveillance requirements, and coordination measures
4. Reference specific MGRS coordinates for positioning and boundaries
5. Include timeline for immediate actions (next 2-4 hours)
6. Address force protection measures
7. Use tactical knowledge about {target} capabilities and vulnerabilities

Consider doctrinal responses to {target} sightings and provide actionable orders that can be executed immediately.

Format as a complete FRAGO with proper military structure and terminology.
"""
        
        return self._make_llm_query(frago_query, k=10)
    
    def generate_telegram_message(self, observation: Dict) -> Optional[str]:
        """
        Generate a concise Telegram message for new observations
        
        Args:
            observation: Dictionary containing observation data
        """
        target = observation.get('what', 'Unknown')
        location = observation.get('mgrs', 'Unknown')
        amount = observation.get('amount', 1)
        confidence = observation.get('confidence', 0)
        time_str = observation.get('time', datetime.now(timezone.utc)).strftime('%H%MZ')
        observer = observation.get('observer_signature', 'Observer')
        
        # Determine urgency emoji and priority
        if confidence >= 90:
            urgency = "🚨 HIGH PRIORITY"
        elif confidence >= 80:
            urgency = "⚠️ MEDIUM PRIORITY"
        else:
            urgency = "ℹ️ LOW PRIORITY"
        
        telegram_query = f"""
Generate a concise Telegram message for immediate tactical notification:

OBSERVATION:
- Time: {time_str}
- Target: {target} (x{amount})
- Location: {location}
- Confidence: {confidence}%
- Observer: {observer}

MESSAGE REQUIREMENTS:
1. Maximum 200 characters for mobile readability
2. Include relevant emojis for quick visual recognition
3. Use military time format and tactical abbreviations
4. Highlight key threat information and location
5. Include confidence level and priority assessment
6. Format for immediate situational awareness

Create a brief, professional tactical message suitable for command notification via Telegram.
Priority Level: {urgency}
"""
        
        return self._make_llm_query(telegram_query, k=5)
    
    async def generate_24h_intelligence_report(self, include_patterns: bool = True) -> Optional[str]:
        """
        Generate comprehensive 24-hour intelligence report
        
        Args:
            include_patterns: Whether to include pattern analysis
        """
        # Get observations from last 24 hours
        try:
            conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
            
            observations = await conn.fetch("""
            SELECT time, mgrs, what, amount, confidence, observer_signature, unit, sensor_id
            FROM sensor_reading 
            WHERE received_at >= NOW() - INTERVAL '24 hours'
            ORDER BY time DESC
            """)
            
            await conn.close()
            
            if not observations:
                return "No observations available for the last 24 hours."
            
            # Format observations for analysis
            obs_summary = []
            for obs in observations:
                time_str = obs['time'].strftime('%H%MZ')
                obs_summary.append(
                    f"- {time_str}: {obs['what']} "
                    f"(x{obs['amount'] if obs['amount'] else '?'}) "
                    f"at {obs['mgrs']} "
                    f"({obs['confidence']}% conf) "
                    f"- {obs['observer_signature']}"
                )
            
            observations_text = "\n".join(obs_summary)
            current_time = datetime.now(timezone.utc).strftime('%d%H%MZ %b %Y')
            
            intel_query = f"""
Generate a comprehensive 24-hour intelligence summary for {current_time}:

RECENT OBSERVATIONS ({len(observations)} total):
{observations_text}

INTELLIGENCE REQUIREMENTS:
1. EXECUTIVE SUMMARY - Key findings and immediate threats
2. TACTICAL SITUATION ANALYSIS - Enemy force composition and disposition
3. PATTERN ANALYSIS - Temporal, spatial, and tactical patterns in observations
4. THREAT ASSESSMENT - Capability analysis and probable courses of action
5. ENEMY ACTIVITY ASSESSMENT - Doctrinal analysis using BTG knowledge
6. INTELLIGENCE GAPS - Missing information and collection priorities
7. RECOMMENDATIONS - Immediate actions and future collection requirements

ANALYSIS GUIDELINES:
- Cross-reference observations with uploaded intelligence documents about Russian BTG tactics
- Use proper military intelligence format and terminology
- Reference specific MGRS coordinates and times
- Apply doctrinal knowledge about observed equipment capabilities
- Assess tactical significance of force positioning and movement patterns
- Include confidence assessments for all conclusions
- Cite relevant document sources when applying doctrinal knowledge

Provide professional military intelligence brief suitable for command briefing.
"""
            
            return self._make_llm_query(intel_query, k=12)
            
        except Exception as e:
            print(f"❌ Database error in intelligence report: {e}")
            return None
    
    def generate_threat_analysis(self, threat_type: str = "all") -> Optional[str]:
        """
        Generate focused threat analysis for specific threat types
        
        Args:
            threat_type: Type of threat to analyze ("armor", "infantry", "aviation", "all")
        """
        threat_query = f"""
Conduct tactical threat analysis focusing on {threat_type} threats based on recent sensor observations and intelligence documents.

ANALYSIS REQUIREMENTS:
1. THREAT IDENTIFICATION - Classify observed threats by type and capability
2. DOCTRINAL ANALYSIS - Apply enemy doctrine knowledge from available documents
3. CAPABILITY ASSESSMENT - Analyze equipment capabilities and limitations
4. VULNERABILITY ANALYSIS - Identify exploitable weaknesses
5. COUNTERMEASURE RECOMMENDATIONS - Specific tactical responses
6. PRIORITY TARGET IDENTIFICATION - High-value targets for engagement

Use available intelligence documents about Russian BTG tactics and equipment.
Reference specific observations and document citations.
Provide actionable intelligence for tactical planning.
"""
        
        return self._make_llm_query(threat_query, k=10)
    
    def generate_patrol_order(self, observation: Dict) -> Optional[str]:
        """
        Generate a patrol order based on an observation requiring investigation
        
        Args:
            observation: Dictionary containing observation data
        """
        target = observation.get('what', 'Unknown')
        location = observation.get('mgrs', 'Unknown')
        confidence = observation.get('confidence', 0)
        
        patrol_query = f"""
Generate a tactical patrol order to investigate and confirm the following observation:

OBSERVATION TO INVESTIGATE:
- Target: {target}
- Location: {location}
- Confidence: {confidence}%

PATROL ORDER REQUIREMENTS:
1. Proper military patrol order format (5-paragraph OPORD)
2. Reconnaissance objectives and priority intelligence requirements
3. Route planning and navigation waypoints
4. Rules of engagement and escalation procedures
5. Communication procedures and reporting timeline
6. Emergency procedures and extraction plans
7. Equipment and personnel requirements

Consider the threat level and surveillance requirements for {target} confirmation.
Include specific tactical procedures for safe approach and observation.
"""
        
        return self._make_llm_query(patrol_query, k=8)

# Convenience functions for easy use
def quick_frago(observation_dict: Dict) -> str:
    """Quick FRAGO generation"""
    llm = DefHackMilitaryLLM()
    result = llm.generate_frago_order(observation_dict)
    return result or "FRAGO generation failed"

def quick_telegram(observation_dict: Dict) -> str:
    """Quick Telegram message generation"""
    llm = DefHackMilitaryLLM()
    result = llm.generate_telegram_message(observation_dict)
    return result or "Telegram message generation failed"

async def quick_intel_report() -> str:
    """Quick 24h intelligence report"""
    llm = DefHackMilitaryLLM()
    result = await llm.generate_24h_intelligence_report()
    return result or "Intelligence report generation failed"

# Example usage
if __name__ == "__main__":
    # Example observation for testing
    test_observation = {
        'what': 'T-72 Tank',
        'mgrs': '35VLG8475672108',
        'amount': 3,
        'confidence': 95,
        'time': datetime.now(timezone.utc),
        'observer_signature': 'Alpha-6',
        'unit': 'Recon Team Alpha'
    }
    
    llm = DefHackMilitaryLLM()
    
    print("🎯 DefHack Military LLM Functions Demo")
    print("=" * 60)
    
    # Test FRAGO generation
    print("\n1. FRAGO ORDER GENERATION")
    print("-" * 40)
    frago = llm.generate_frago_order(test_observation)
    if frago:
        print(frago)
    
    input("\nPress Enter to continue to Telegram message...")
    
    # Test Telegram message
    print("\n2. TELEGRAM MESSAGE GENERATION")
    print("-" * 40)
    telegram = llm.generate_telegram_message(test_observation)
    if telegram:
        print(telegram)
    
    input("\nPress Enter to continue to Intelligence Report...")
    
    # Test Intelligence Report
    print("\n3. 24-HOUR INTELLIGENCE REPORT")
    print("-" * 40)
    intel_report = asyncio.run(llm.generate_24h_intelligence_report())
    if intel_report:
        print(intel_report[:500] + "..." if len(intel_report) > 500 else intel_report)
    
    print("\n🎉 Military LLM Functions Demo Complete!")