#!/usr/bin/env python3
"""
Working Citation System Test - Simplified
"""
import requests
import json

def working_citation_test():
    """Test with known working queries"""
    
    print("✅ DefHack Working Citation System")
    print("=" * 60)
    
    # Test with queries we know work
    working_queries = [
        "BTG vulnerabilities",
        "Russian battalion tactical",
        "Fiore"
    ]
    
    for query in working_queries:
        print(f"\n🔍 Testing: '{query}'")
        print("-" * 40)
        
        # Search first
        search_response = requests.get(
            "http://localhost:8080/search",
            params={"q": query, "k": 2}
        )
        
        if search_response.status_code == 200:
            results = search_response.json()
            print(f"📚 Found {len(results)} documents:")
            
            for i, result in enumerate(results, 1):
                citation = f"[D:{result['doc_id']} p{result['page']} ¶{result['para']}]"
                print(f"  {i}. {citation}")
                print(f"     Text: {result['text'][:100]}...")
            
            # Now test LLM with same query
            if results:  # Only test LLM if we found documents
                print(f"\n🤖 LLM Analysis:")
                draft_response = requests.post(
                    "http://localhost:8080/orders/draft",
                    params={"query": f"Summarize key points about {query}", "k": 3}
                )
                
                if draft_response.status_code == 200:
                    analysis = draft_response.json().get('body', 'No analysis')
                    print(analysis[:400] + "..." if len(analysis) > 400 else analysis)
        else:
            print(f"❌ Search failed: {search_response.status_code}")
        
        print()

    # Document mapping
    print("\n📋 DOCUMENT SUMMARY")
    print("-" * 40)
    try:
        import asyncio
        import asyncpg
        
        async def get_docs():
            conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
            docs = await conn.fetch("SELECT id, title, origin FROM intel_doc ORDER BY id")
            
            for doc in docs:
                print(f"[D:{doc['id']}] {doc['title']}")
                print(f"        Source: {doc['origin']}")
            
            await conn.close()
        
        asyncio.run(get_docs())
    except Exception as e:
        print(f"Database error: {e}")

if __name__ == "__main__":
    working_citation_test()