#!/usr/bin/env python3
"""
Simple 24-hour Intelligence Summary using DefHack API
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone

async def get_recent_data():
    """Get recent observations and prepare summary"""
    # Connect to database
    conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
    
    # Get last 24 hours of observations
    cutoff_time = datetime.now(timezone.utc) - timedelta(hours=24)
    
    query = """
    SELECT time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature
    FROM sensor_reading 
    WHERE received_at >= $1
    ORDER BY time DESC
    """
    
    rows = await conn.fetch(query, cutoff_time)
    observations = [dict(row) for row in rows]
    
    await conn.close()
    
    return observations

def format_observations_summary(observations):
    """Format observations for the LLM query"""
    if not observations:
        return "No recent sensor observations in the last 24 hours."
    
    summary_lines = [
        f"SENSOR OBSERVATIONS (Last 24 Hours) - {len(observations)} total:",
        ""
    ]
    
    for i, obs in enumerate(observations, 1):
        time_str = obs['time'].strftime("%H:%M UTC") if obs['time'] else 'Unknown'
        amount_str = f" ({obs['amount']} units)" if obs['amount'] else ""
        unit_str = f" [{obs['unit']}]" if obs['unit'] else ""
        
        summary_lines.append(
            f"{i}. {time_str}: {obs['what']}{amount_str} at {obs['mgrs']} "
            f"({obs['confidence']}% confidence) - {obs['observer_signature']}{unit_str}"
        )
    
    return "\n".join(summary_lines)

async def generate_intelligence_summary():
    """Generate 24-hour intelligence summary"""
    print("🔍 24-Hour Intelligence Summary Generator")
    print("=" * 60)
    
    # Get recent observations
    print("📡 Gathering sensor data...")
    observations = await get_recent_data()
    print(f"   Found {len(observations)} observations in last 24 hours")
    
    # Format observations for LLM
    obs_summary = format_observations_summary(observations)
    
    # Create comprehensive intelligence query
    query = f"""Generate a comprehensive 24-hour intelligence summary based on the following data:

{obs_summary}

Please provide a structured military intelligence brief including:

1. EXECUTIVE SUMMARY
2. TACTICAL SITUATION ANALYSIS  
3. ENEMY ACTIVITY ASSESSMENT
4. PATTERN ANALYSIS
5. THREAT ASSESSMENT
6. INTELLIGENCE GAPS
7. RECOMMENDATIONS FOR FURTHER COLLECTION

Use proper military format and reference specific MGRS coordinates and observation details. Assess tactical significance of observed equipment and movements. Cross-reference with doctrinal knowledge about BTG operations and Russian tactical doctrine where relevant.

Current time: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}"""

    print("🤖 Generating AI analysis...")
    
    try:
        # Call the DefHack API
        response = requests.post(
            "http://localhost:8080/orders/draft",
            params={"query": query, "k": 10}
        )
        
        if response.status_code == 200:
            result = response.json()
            
            print("✅ Intelligence Summary Generated")
            print("=" * 80)
            print()
            
            # Display the summary
            summary_text = result.get('body', result.get('text', 'No summary generated'))
            print(summary_text)
            
            # Display citations if available
            citations = result.get('citations', [])
            if citations:
                print("\n" + "=" * 80)
                print("INTELLIGENCE SOURCES:")
                for i, citation in enumerate(citations, 1):
                    print(f"{i}. {citation}")
            
            print("\n" + "=" * 80)
            print("📊 Summary Statistics:")
            print(f"   Observations analyzed: {len(observations)}")
            print(f"   Time period: Last 24 hours")
            print(f"   Generated: {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}")
            
            return summary_text
            
        else:
            print(f"❌ API Error: {response.status_code}")
            print(f"Response: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Error generating summary: {e}")
        return None

async def main():
    await generate_intelligence_summary()

if __name__ == "__main__":
    asyncio.run(main())