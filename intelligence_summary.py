#!/usr/bin/env python3
"""
DefHack Intelligence Summary Generator
Creates comprehensive intelligence reports using OpenAI API
"""
import asyncio
import asyncpg
import requests
import json
from datetime import datetime, timedelta, timezone
from defhack_unified_input import DefHackClient

class IntelligenceSummaryGenerator:
    """Generate AI-powered intelligence summaries"""
    
    def __init__(self, db_url: str = "postgresql://postgres:postgres@localhost:5432/defhack"):
        self.db_url = db_url
        self.api_base = "http://localhost:8080"
        self.client = DefHackClient()
        
    async def get_recent_observations(self, hours: int = 24):
        """Get sensor observations from the last N hours"""
        conn = await asyncpg.connect(self.db_url)
        
        cutoff_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = """
        SELECT time, mgrs, what, amount, confidence, sensor_id, unit, observer_signature, received_at
        FROM sensor_reading 
        WHERE received_at >= $1
        ORDER BY time DESC
        """
        
        rows = await conn.fetch(query, cutoff_time)
        
        observations = []
        for row in rows:
            obs = dict(row)
            obs['time'] = obs['time'].isoformat() if obs['time'] else None
            obs['received_at'] = obs['received_at'].isoformat() if obs['received_at'] else None
            observations.append(obs)
            
        await conn.close()
        return observations
    
    def search_relevant_intelligence(self, query_terms: list, k: int = 10):
        """Search intelligence documents for relevant context"""
        all_results = []
        
        for term in query_terms:
            results = self.client.search(term, k=k//len(query_terms) + 1)
            all_results.extend(results)
        
        # Deduplicate by doc_id + chunk_idx
        seen = set()
        unique_results = []
        for result in all_results:
            key = (result.get('doc_id'), result.get('chunk_idx'))
            if key not in seen:
                seen.add(key)
                unique_results.append(result)
        
        return unique_results[:k]
    
    def format_observations_for_llm(self, observations):
        """Format sensor observations for LLM context"""
        if not observations:
            return "No recent sensor observations."
            
        formatted = ["RECENT SENSOR OBSERVATIONS:"]
        
        for i, obs in enumerate(observations, 1):
            time_str = obs['time'][:19] if obs['time'] else 'Unknown'
            amount_str = f" (qty: {obs['amount']})" if obs['amount'] else ""
            unit_str = f" - {obs['unit']}" if obs['unit'] else ""
            
            formatted.append(
                f"{i}. {time_str}: {obs['what']}{amount_str} at {obs['mgrs']} "
                f"({obs['confidence']}% confidence) - {obs['observer_signature']}{unit_str}"
            )
        
        return "\n".join(formatted)
    
    def format_documents_for_llm(self, doc_results):
        """Format document search results for LLM context"""
        if not doc_results:
            return "No relevant intelligence documents found."
            
        formatted = ["RELEVANT INTELLIGENCE DOCUMENTS:"]
        
        for i, result in enumerate(doc_results, 1):
            doc_id = result.get('doc_id', 'N/A')
            page = result.get('page', 'N/A')
            text = result.get('text', '')[:300] + "..." if len(result.get('text', '')) > 300 else result.get('text', '')
            
            citation = f"[D:{doc_id}"
            if page != 'N/A':
                citation += f" p{page}"
            citation += "]"
            
            formatted.append(f"{i}. {citation} {text}")
        
        return "\n".join(formatted)
    
    async def generate_24h_summary(self):
        """Generate a comprehensive 24-hour intelligence summary"""
        print("🔍 Generating 24-hour intelligence summary...")
        print("=" * 60)
        
        # Get recent observations
        print("📡 Gathering sensor observations...")
        observations = await self.get_recent_observations(24)
        print(f"   Found {len(observations)} observations in last 24 hours")
        
        # Search for relevant intelligence based on what we observed
        print("📚 Searching intelligence documents...")
        
        # Extract key terms from observations for intelligent document search
        search_terms = []
        for obs in observations:
            what = obs.get('what', '').lower()
            if 'tank' in what or 't-72' in what or 't-80' in what:
                search_terms.extend(['tank', 'armor', 'BTG'])
            elif 'infantry' in what or 'soldier' in what:
                search_terms.extend(['infantry', 'personnel', 'troops'])
            elif 'bmp' in what or 'ifv' in what:
                search_terms.extend(['infantry fighting vehicle', 'mechanized', 'BMP'])
            elif 'truck' in what or 'supply' in what:
                search_terms.extend(['logistics', 'supply', 'transport'])
            elif 'recon' in what:
                search_terms.extend(['reconnaissance', 'intelligence', 'surveillance'])
        
        # Add general search terms
        search_terms.extend(['tactical', 'operations', 'Russian', 'BTG'])
        
        # Remove duplicates and limit
        search_terms = list(set(search_terms))[:5]
        print(f"   Using search terms: {search_terms}")
        
        doc_results = self.search_relevant_intelligence(search_terms, k=8)
        print(f"   Found {len(doc_results)} relevant document chunks")
        
        # Format context for LLM
        obs_context = self.format_observations_for_llm(observations)
        doc_context = self.format_documents_for_llm(doc_results)
        
        # Build the prompt
        current_time = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        prompt = f"""
Generate a comprehensive 24-hour intelligence summary for {current_time}.

INSTRUCTIONS:
- Analyze recent sensor observations for tactical patterns
- Cross-reference with available intelligence documents
- Identify potential threats, movements, and tactical significance
- Provide military assessment with specific locations (use MGRS coordinates)
- Include confidence assessments and source citations
- Format as a professional military intelligence brief

CONTEXT:

{obs_context}

{doc_context}

Provide a structured intelligence summary with:
1. EXECUTIVE SUMMARY
2. TACTICAL SITUATION
3. ENEMY ACTIVITY ANALYSIS  
4. INTELLIGENCE GAPS
5. RECOMMENDATIONS
"""
        
        # Use the existing DefHack API endpoint
        print("🤖 Generating AI analysis...")
        
        try:
            response = requests.post(
                f"{self.api_base}/orders/draft",
                params={"query": prompt, "k": 10}
            )
            
            if response.status_code == 200:
                result = response.json()
                summary = result.get('text', 'No summary generated')
                citations = result.get('citations', [])
                
                print("✅ Intelligence summary generated!")
                print("=" * 60)
                print()
                print(summary)
                
                if citations:
                    print("\n" + "=" * 60)
                    print("CITATIONS:")
                    for i, citation in enumerate(citations, 1):
                        print(f"{i}. {citation}")
                
                return summary, citations
                
            else:
                print(f"❌ API Error: {response.status_code}")
                print(f"Response: {response.text}")
                return None, []
                
        except Exception as e:
            print(f"❌ Error generating summary: {e}")
            return None, []
    
    async def generate_custom_query(self, query: str, hours: int = 24):
        """Generate a custom intelligence analysis"""
        print(f"🔍 Generating custom intelligence analysis...")
        print(f"Query: {query}")
        print(f"Time window: {hours} hours")
        print("=" * 60)
        
        # Get recent observations
        observations = await self.get_recent_observations(hours)
        
        # Search documents based on query
        doc_results = self.client.search(query, k=10)
        
        # Format context  
        obs_context = self.format_observations_for_llm(observations)
        doc_context = self.format_documents_for_llm(doc_results)
        
        full_prompt = f"""
{query}

Use the following context to provide a comprehensive analysis:

{obs_context}

{doc_context}

Provide specific analysis with citations and confidence assessments.
"""
        
        try:
            response = requests.post(
                f"{self.api_base}/orders/draft",
                params={"query": full_prompt, "k": 15}
            )
            
            if response.status_code == 200:
                result = response.json()
                analysis = result.get('text', 'No analysis generated')
                citations = result.get('citations', [])
                
                print("✅ Analysis complete!")
                print("=" * 60)
                print()
                print(analysis)
                
                return analysis, citations
                
            else:
                print(f"❌ API Error: {response.status_code}")
                return None, []
                
        except Exception as e:
            print(f"❌ Error: {e}")
            return None, []

async def main():
    """Main function for intelligence summary generation"""
    generator = IntelligenceSummaryGenerator()
    
    print("🎯 DefHack Intelligence Summary Generator")
    print("=" * 80)
    
    # Generate 24-hour summary
    await generator.generate_24h_summary()

if __name__ == "__main__":
    asyncio.run(main())