#!/usr/bin/env python3
"""
DefHack Quick Summary - Windows-compatible data overview
"""
import asyncio
import asyncpg
import requests

async def get_quick_stats():
    """Get quick database statistics"""
    try:
        conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
        
        # Count observations
        obs_count = await conn.fetchval("SELECT COUNT(*) FROM sensor_reading")
        
        # Count documents  
        doc_count = await conn.fetchval("SELECT COUNT(*) FROM intel_doc")
        
        # Count chunks
        chunk_count = await conn.fetchval("SELECT COUNT(*) FROM doc_chunk")
        
        # Get recent observations sample
        recent_obs = await conn.fetch("""
            SELECT what, mgrs, observer_signature, confidence 
            FROM sensor_reading 
            ORDER BY received_at DESC 
            LIMIT 3
        """)
        
        # Get documents sample
        docs = await conn.fetch("""
            SELECT title, source_type, created_at::date as upload_date
            FROM intel_doc 
            ORDER BY created_at DESC 
            LIMIT 3
        """)
        
        await conn.close()
        
        return {
            "observations": obs_count,
            "documents": doc_count, 
            "chunks": chunk_count,
            "recent_obs": [dict(r) for r in recent_obs],
            "recent_docs": [dict(r) for r in docs]
        }
        
    except Exception as e:
        print(f"Database error: {e}")
        return None

def test_search_api():
    """Test the search API"""
    try:
        response = requests.get("http://localhost:8080/search", params={"q": "tactical", "k": 2})
        if response.status_code == 200:
            return response.json()
        else:
            return None
    except Exception as e:
        print(f"API error: {e}")
        return None

async def main():
    print("=== DefHack System Status ===")
    print()
    
    # Get database stats
    stats = await get_quick_stats()
    if stats:
        print("DATABASE SUMMARY:")
        print(f"  Total Sensor Observations: {stats['observations']}")
        print(f"  Total Intelligence Documents: {stats['documents']}")
        print(f"  Total Document Chunks: {stats['chunks']}")
        print()
        
        print("RECENT OBSERVATIONS:")
        for i, obs in enumerate(stats['recent_obs'], 1):
            print(f"  {i}. {obs['what']} at {obs['mgrs']} ({obs['confidence']}% confidence) - {obs['observer_signature']}")
        print()
        
        print("RECENT DOCUMENTS:")
        for i, doc in enumerate(stats['recent_docs'], 1):
            print(f"  {i}. {doc['title']} ({doc['source_type']}) - uploaded {doc['upload_date']}")
        print()
    
    # Test search API
    search_results = test_search_api()
    if search_results:
        print("SEARCH API TEST (query: 'tactical'):")
        for i, result in enumerate(search_results[:2], 1):
            doc_id = result.get('doc_id', 'N/A')
            page = result.get('page', 'N/A')
            text = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')
            print(f"  {i}. Doc {doc_id}, Page {page}: {text}")
        print()
    
    print("=== HOW TO VIEW COMPLETE DATA ===")
    print("For detailed sensor observations:")
    print("  python database_inspector.py")
    print()
    print("For searching intelligence documents:")
    print("  python defhack_cli.py search --query 'your search terms'")
    print()
    print("For adding new data:")
    print("  python defhack_cli.py obs --what 'Target' --mgrs 'Location' --observer 'Name'")
    print("  python defhack_cli.py doc --file 'document.pdf' --title 'Title'")

if __name__ == "__main__":
    asyncio.run(main())