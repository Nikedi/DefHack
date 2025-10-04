#!/usr/bin/env python3
"""
DefHack Document Citation System Demo
Shows how document references and citations work
"""
import requests
import json

def test_citation_system():
    """Comprehensive test of the citation system"""
    
    print("🎯 DefHack Document Citation System Demo")
    print("=" * 80)
    
    # Test 1: Search for specific document content
    print("\n1. SEARCH RESULTS WITH CITATION DATA")
    print("-" * 50)
    
    search_response = requests.get(
        "http://localhost:8080/search", 
        params={"q": "BTG command control centralized", "k": 4}
    )
    
    if search_response.status_code == 200:
        results = search_response.json()
        print(f"Found {len(results)} document chunks:")
        
        for i, result in enumerate(results, 1):
            print(f"\n[{i}] DOCUMENT CHUNK:")
            print(f"    Document ID: {result['doc_id']}")
            print(f"    Page: {result['page']}")
            print(f"    Paragraph: {result['para']}")
            print(f"    Text Sample: {result['text'][:200]}...")
            
            # Generate proper citation
            citation = f"[D:{result['doc_id']} p{result['page']} ¶{result['para']}]"
            print(f"    CITATION: {citation}")
    
    # Test 2: Full analysis with citations
    print("\n\n2. LLM ANALYSIS WITH DOCUMENT CITATIONS")
    print("-" * 50)
    
    draft_response = requests.post(
        "http://localhost:8080/orders/draft",
        params={
            "query": "What does the Fiore document say about BTG command and control vulnerabilities? Include specific page references.",
            "k": 5
        }
    )
    
    if draft_response.status_code == 200:
        result = draft_response.json()
        analysis = result.get('body', result.get('text', 'No analysis'))
        print(analysis)
        
        # Check for separate citations field
        citations = result.get('citations', [])
        if citations:
            print(f"\nSeparate Citations: {citations}")
    
    # Test 3: Show document mapping
    print("\n\n3. DOCUMENT MAPPING")
    print("-" * 50)
    
    # Get document info from database
    try:
        import asyncio
        import asyncpg
        
        async def get_doc_info():
            conn = await asyncpg.connect("postgresql://postgres:postgres@localhost:5432/defhack")
            
            docs = await conn.fetch("""
            SELECT id, title, origin, published_at, type
            FROM intel_doc 
            ORDER BY id
            """)
            
            print("Available Documents:")
            for doc in docs:
                print(f"  [D:{doc['id']}] {doc['title']}")
                print(f"      Source: {doc['origin']} ({doc['published_at'].year if doc['published_at'] else 'Unknown'})")
                print(f"      Type: {doc['type']}")
            
            await conn.close()
        
        asyncio.run(get_doc_info())
        
    except Exception as e:
        print(f"Could not fetch document info: {e}")
    
    print("\n\n4. CITATION FORMAT EXPLANATION")
    print("-" * 50)
    print("Citation Format: [D:<doc_id> p<page> ¶<para>]")
    print("Examples:")
    print("  [D:5 p1 ¶4] = Document 5, Page 1, Paragraph 4")
    print("  [D:6 p3 ¶2] = Document 6, Page 3, Paragraph 2")
    print("  [D:7 lines 45–67] = Document 7, Lines 45 to 67 (for text files)")
    print("  [R:uuid] = Sensor Report with UUID reference")

if __name__ == "__main__":
    test_citation_system()