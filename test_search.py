#!/usr/bin/env python3
import requests
import json

def search_documents(query, k=5):
    """Search the uploaded documents"""
    url = "http://localhost:8080/search"
    params = {"q": query, "k": k}
    
    print(f"🔍 Searching for: '{query}'")
    response = requests.get(url, params=params)
    
    if response.status_code == 200:
        results = response.json()
        print(f"✅ Found {len(results)} results:")
        
        for i, result in enumerate(results, 1):
            print(f"\n--- Result {i} ---")
            print(f"Document ID: {result.get('doc_id', 'N/A')}")
            print(f"Page: {result.get('page', 'N/A')}")
            print(f"Paragraph: {result.get('para', 'N/A')}")
            print(f"Chunk Index: {result.get('chunk_idx', 'N/A')}")
            if result.get('step_id'):
                print(f"Step ID: {result['step_id']}")
            if result.get('section'):
                print(f"Section: {result['section']}")
            
            text = result.get('text', '')
            # Truncate long text for display
            if len(text) > 200:
                text = text[:200] + "..."
            print(f"Text: {text}")
            
        return results
    else:
        print(f"❌ Search failed with status {response.status_code}")
        print(f"Error: {response.text}")
        return []

def check_database_content():
    """Check what's in the database"""
    # First, let's search for some general terms
    queries = [
        "intelligence",
        "analysis", 
        "report",
        "2017",
        "2022",
        "Fiore",
        "Baez"
    ]
    
    for query in queries:
        results = search_documents(query, k=3)
        if results:
            break  # Stop after first successful search
        print()

if __name__ == "__main__":
    print("Testing document search functionality...")
    print("=" * 50)
    
    check_database_content()