#!/usr/bin/env python3
"""
DefHack LLM Query Tools
Various ways to interact with OpenAI API for intelligence analysis
"""
import requests
import asyncio
import asyncpg
from datetime import datetime, timezone, timedelta

class DefHackLLMQueries:
    """Collection of LLM query tools for DefHack"""
    
    def __init__(self):
        self.api_base = "http://localhost:8080"
    
    def simple_intelligence_query(self, query: str, k: int = 8):
        """Make a simple intelligence query using search + LLM"""
        print(f"🤖 Intelligence Query: {query}")
        print("=" * 60)
        
        try:
            response = requests.post(
                f"{self.api_base}/orders/draft",
                params={"query": query, "k": k}
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('body', result.get('text', 'No analysis generated'))
                print(analysis)
                return analysis
            else:
                print(f"❌ API Error: {response.status_code}")
                return None
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None
    
    async def threat_assessment_query(self, threat_type: str = "armor"):
        """Generate threat assessment based on recent observations"""
        # Get recent observations
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
        
        query = """
        SELECT time, mgrs, what, amount, confidence, observer_signature, unit
        FROM sensor_reading 
        WHERE received_at >= NOW() - INTERVAL '24 hours'
        ORDER BY confidence DESC, time DESC
        """
        
        rows = await conn.fetch(query)
        observations = [dict(row) for row in rows]
        await conn.close()
        
        # Filter observations by threat type if specified
        if threat_type.lower() == "armor":
            relevant_obs = [obs for obs in observations if any(term in obs['what'].lower() 
                          for term in ['tank', 't-72', 't-80', 'bmp', 'ifv', 'armor'])]
        elif threat_type.lower() == "infantry":
            relevant_obs = [obs for obs in observations if any(term in obs['what'].lower() 
                          for term in ['infantry', 'soldier', 'personnel', 'troops'])]
        else:
            relevant_obs = observations
        
        # Format for LLM
        obs_text = "\n".join([
            f"- {obs['time'].strftime('%H:%M UTC')}: {obs['what']} "
            f"({'x' + str(obs['amount']) if obs['amount'] else ''})"
            f" at {obs['mgrs']} ({obs['confidence']}% confidence) - {obs['observer_signature']}"
            for obs in relevant_obs
        ])
        
        threat_query = f"""
Conduct a tactical threat assessment focusing on {threat_type} threats based on recent sensor observations:

RECENT OBSERVATIONS:
{obs_text}

Provide analysis including:
1. THREAT IDENTIFICATION AND CLASSIFICATION
2. CAPABILITY ASSESSMENT  
3. PROBABLE COURSES OF ACTION
4. VULNERABILITY ANALYSIS
5. RECOMMENDED COUNTERMEASURES
6. PRIORITY TARGETS FOR ENGAGEMENT

Use doctrinal knowledge about Russian BTG tactics and equipment capabilities.
Reference specific observation details and confidence levels.
"""
        
        return self.simple_intelligence_query(threat_query, k=10)
    
    def doctrinal_analysis_query(self, topic: str):
        """Query focused on doctrinal analysis using uploaded documents"""
        query = f"""
Provide a comprehensive doctrinal analysis on: {topic}

Base your analysis on available intelligence documents and current best practices.
Include:
- Doctrinal background and context
- Tactical applications and implications  
- Historical examples or case studies
- Current threat considerations
- Recommended defensive/offensive approaches

Format as a military staff study with proper citations.
"""
        
        return self.simple_intelligence_query(query, k=12)
    
    def pattern_analysis_query(self, time_hours: int = 24):
        """Analyze patterns in recent observations"""
        query = f"""
Conduct pattern analysis on sensor observations from the last {time_hours} hours.

Analyze for:
1. TEMPORAL PATTERNS (timing, frequency, sequence)
2. SPATIAL PATTERNS (geographic clustering, movement patterns)  
3. FORCE COMPOSITION PATTERNS (unit types, capabilities)
4. TACTICAL PATTERNS (deployment methods, operational signatures)
5. ANOMALIES AND OUTLIERS
6. PREDICTIVE INDICATORS

Provide tactical intelligence assessment with confidence levels and recommendations for collection priorities.
"""
        
        return self.simple_intelligence_query(query, k=8)

def main():
    """Demo the LLM query tools"""
    llm = DefHackLLMQueries()
    
    print("🎯 DefHack LLM Query Tools Demo")
    print("=" * 80)
    
    # Demo 1: Simple intelligence query
    print("\n1. SIMPLE INTELLIGENCE QUERY")
    llm.simple_intelligence_query("What are the key vulnerabilities of Russian BTG formations?")
    
    print("\n" + "="*80)
    input("Press Enter to continue to threat assessment...")
    
    # Demo 2: Threat assessment  
    print("\n2. ARMOR THREAT ASSESSMENT")
    asyncio.run(llm.threat_assessment_query("armor"))
    
    print("\n" + "="*80)
    input("Press Enter to continue to doctrinal analysis...")
    
    # Demo 3: Doctrinal analysis
    print("\n3. DOCTRINAL ANALYSIS")
    llm.doctrinal_analysis_query("Russian Battalion Tactical Group combined arms operations")
    
    print("\n" + "="*80)
    input("Press Enter to continue to pattern analysis...")
    
    # Demo 4: Pattern analysis
    print("\n4. PATTERN ANALYSIS")
    llm.pattern_analysis_query(24)
    
    print("\n🎉 LLM Query Demo Complete!")

if __name__ == "__main__":
    main()