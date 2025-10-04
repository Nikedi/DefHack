#!/usr/bin/env python3
import requests
import json

def test_comprehensive_search():
    """Test various search queries to verify document processing"""
    
    test_queries = [
        ("intelligence", "Should find general intelligence content"),
        ("BTG", "Should find Battle Group references"),
        ("2017", "Should find content from Fiore 2017 document"),
        ("2022", "Should find content from Baez 2022 document"),
        ("command", "Should find command and control references"),
        ("analysis", "Should find analytical content")
    ]
    
    print("Testing comprehensive search functionality...")
    print("=" * 60)
    
    all_results = []
    
    for query, description in test_queries:
        print(f"\n🔍 Query: '{query}' - {description}")
        
        response = requests.get("http://localhost:8080/search", params={"q": query, "k": 2})
        
        if response.status_code == 200:
            results = response.json()
            print(f"✅ Found {len(results)} results")
            
            for i, result in enumerate(results, 1):
                doc_id = result.get('doc_id', 'N/A')
                page = result.get('page', 'N/A')
                text = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')
                print(f"   {i}. Doc ID: {doc_id}, Page: {page}")
                print(f"      Text: {text}")
                
            all_results.extend(results)
        else:
            print(f"❌ Search failed: {response.status_code} - {response.text}")
    
    # Summary
    unique_docs = set(r.get('doc_id') for r in all_results if r.get('doc_id'))
    print(f"\n📊 Summary:")
    print(f"   Total search results: {len(all_results)}")
    print(f"   Unique documents found: {len(unique_docs)} - {list(unique_docs)}")
    
    return len(all_results) > 0

def test_database_verification():
    """Check that both documents are properly indexed"""
    print("\n" + "=" * 60)
    print("Database Verification Test")
    print("=" * 60)
    
    # Test specific content from each document
    specific_tests = [
        ("Fiore", "Should find author Fiore from 2017 document"),
        ("Baez", "Should find author Baez from 2022 document")
    ]
    
    doc_5_found = False
    doc_6_found = False
    
    for query, description in specific_tests:
        print(f"\n🔍 Testing: '{query}' - {description}")
        
        response = requests.get("http://localhost:8080/search", params={"q": query, "k": 5})
        
        if response.status_code == 200:
            results = response.json()
            if results:
                print(f"✅ Found {len(results)} results")
                for result in results:
                    doc_id = result.get('doc_id')
                    if doc_id == '5':
                        doc_5_found = True
                    elif doc_id == '6':
                        doc_6_found = True
                    print(f"   Doc ID: {doc_id}, Page: {result.get('page', 'N/A')}")
            else:
                print(f"⚠️  No results found")
        else:
            print(f"❌ Search failed: {response.status_code}")
    
    print(f"\n📋 Document Status:")
    print(f"   Document 5 (2Fiore17.pdf): {'✅ Found' if doc_5_found else '❌ Not found'}")
    print(f"   Document 6 (3Baez22.pdf): {'✅ Found' if doc_6_found else '❌ Not found'}")
    
    return doc_5_found and doc_6_found

if __name__ == "__main__":
    # Run comprehensive search test
    search_success = test_comprehensive_search()
    
    # Verify both documents are indexed
    docs_verified = test_database_verification()
    
    print(f"\n" + "=" * 60)
    print("FINAL RESULTS")
    print("=" * 60)
    print(f"Search functionality: {'✅ WORKING' if search_success else '❌ FAILED'}")
    print(f"Document indexing: {'✅ COMPLETE' if docs_verified else '❌ INCOMPLETE'}")
    
    if search_success and docs_verified:
        print(f"\n🎉 SUCCESS: DefHack intelligence system is fully operational!")
        print(f"   - Both PDF documents uploaded and processed")
        print(f"   - Document chunking and embedding working")
        print(f"   - Search functionality operational")
        print(f"   - Ready for intelligence analysis queries")
    else:
        print(f"\n⚠️  Some issues detected - see details above")