#!/usr/bin/env python3
"""
DefHack Data Viewer - Simple interface to view system data
Uses the existing API endpoints where possible
"""
import requests
import json
from defhack_unified_input import DefHackClient

def view_search_results():
    """View searchable intelligence content"""
    print("🔍 SEARCHABLE INTELLIGENCE CONTENT")
    print("=" * 60)
    
    client = DefHackClient()
    
    # Test different search terms to see what's indexed
    search_terms = [
        ("all content", "the"),  # Generic search to see all content
        ("tactical", "tactical"),
        ("BTG", "BTG"),
        ("Russian", "Russian"),
        ("analysis", "analysis")
    ]
    
    for label, query in search_terms:
        print(f"\n📋 {label.upper()} (search: '{query}'):")
        results = client.search(query, k=3)
        
        if results:
            for i, result in enumerate(results, 1):
                doc_id = result.get('doc_id', 'N/A')
                page = result.get('page', 'N/A')
                chunk_idx = result.get('chunk_idx', 'N/A')
                text = result.get('text', '')
                
                # Truncate long text
                if len(text) > 150:
                    text = text[:150] + "..."
                    
                print(f"  [{i}] Doc {doc_id}, Page {page}, Chunk {chunk_idx}")
                print(f"      {text}")
        else:
            print(f"  No results found")

def view_api_endpoints():
    """Test API endpoints to see what data is available"""
    print("\n🌐 API ENDPOINT STATUS")
    print("=" * 60)
    
    base_url = "http://localhost:8080"
    
    # Test search endpoint
    try:
        response = requests.get(f"{base_url}/search", params={"q": "test", "k": 1})
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Search endpoint: Working ({len(results)} results for 'test')")
        else:
            print(f"⚠️  Search endpoint: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Search endpoint: Error - {e}")
    
    # Note: The sensor data is not exposed via API endpoints, only via database queries
    print("ℹ️  Sensor observations: Only available via database queries (see database_inspector.py)")

def view_system_summary():
    """Show a summary of the entire system"""
    print("\n📊 DEFHACK SYSTEM SUMMARY")  
    print("=" * 60)
    
    # Run the database inspector to get stats
    import subprocess
    import sys
    
    try:
        result = subprocess.run([
            sys.executable, "database_inspector.py"
        ], capture_output=True, text=True, timeout=30)
        
        if result.returncode == 0:
            # Extract just the statistics section
            lines = result.stdout.split('\n')
            in_stats = False
            for line in lines:
                if "DATABASE STATISTICS" in line:
                    in_stats = True
                elif in_stats and "📡" in line:
                    break
                elif in_stats:
                    print(line)
        else:
            print("❌ Could not get database statistics")
            print(f"Error: {result.stderr}")
            
    except Exception as e:
        print(f"❌ Error getting system summary: {e}")

def main():
    """Main viewer function"""
    print("👁️  DefHack Data Viewer")
    print("=" * 80)
    print("This tool shows you what data is currently in your DefHack system")
    print("=" * 80)
    
    # Show system summary
    view_system_summary()
    
    # Show API status  
    view_api_endpoints()
    
    # Show searchable content
    view_search_results()
    
    print(f"\n" + "=" * 80)
    print("📋 HOW TO VIEW COMPLETE DATA:")
    print("  📡 Sensor observations: python database_inspector.py")
    print("  📚 Document analysis: python defhack_cli.py search --query 'your_topic'")
    print("  🔍 Interactive search: Use DefHackClient.search() in Python")
    print("=" * 80)

if __name__ == "__main__":
    main()