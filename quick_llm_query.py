#!/usr/bin/env python3
"""
Quick LLM Intelligence Queries
Simple script to make specific intelligence queries
"""
import sys
import requests

def quick_query(question):
    """Make a quick intelligence query"""
    print(f"🔍 Query: {question}")
    print("=" * 60)
    
    try:
        response = requests.post(
            "http://localhost:8080/orders/draft",
            params={"query": question, "k": 6}
        )
        
        if response.status_code == 200:
            result = response.json()
            analysis = result.get('body', result.get('text', 'No analysis generated'))
            print(analysis)
        else:
            print(f"❌ API Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Use command line argument
        question = " ".join(sys.argv[1:])
        quick_query(question)
    else:
        # Interactive mode
        print("🤖 DefHack Quick LLM Queries")
        print("Type your intelligence questions (or 'quit' to exit)")
        print("=" * 60)
        
        while True:
            question = input("\n📋 Intelligence Query: ").strip()
            
            if question.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break
            elif question:
                print()
                quick_query(question)
            else:
                print("Please enter a question or 'quit' to exit.")