#!/usr/bin/env python3
"""
DefHack Data Input Interface
Unified tool for adding both sensor observations and intelligence documents
"""
import requests
import json
import os
from datetime import datetime, timezone
from typing import List, Dict, Any

class DefHackClient:
    """Unified client for DefHack intelligence system"""
    
    def __init__(self, base_url: str = "http://localhost:8080", api_key: str = "583C55345736D7218355BCB51AA47"):
        self.base_url = base_url
        self.headers = {
            "X-API-Key": api_key,
            "Content-Type": "application/json"
        }
        
    def add_sensor_observation(self, observation: Dict[str, Any]) -> Dict[str, Any]:
        """Add a single sensor observation (tactical field data)"""
        url = f"{self.base_url}/ingest/sensor"
        
        print(f"📡 Adding sensor observation: {observation.get('what', 'Unknown')}")
        print(f"   Location: {observation.get('mgrs', 'N/A')}")
        print(f"   Observer: {observation.get('observer_signature', 'N/A')}")
        print(f"   Confidence: {observation.get('confidence', 0)}%")
        
        try:
            response = requests.post(url, headers=self.headers, json=observation)
            
            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ Success - Report ID: {result.get('report_id')}")
                return result
            else:
                print(f"   ❌ Failed: {response.status_code} - {response.text}")
                return {"error": response.text, "status": response.status_code}
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return {"error": str(e)}
    
    def add_multiple_observations(self, observations: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Add multiple sensor observations"""
        print(f"📡 Adding {len(observations)} sensor observations...")
        print("=" * 50)
        
        results = []
        for i, obs in enumerate(observations, 1):
            print(f"\n[{i}/{len(observations)}]")
            result = self.add_sensor_observation(obs)
            results.append(result)
            
        return results
    
    def upload_intelligence_document(self, file_path: str, title: str, **metadata) -> Dict[str, Any]:
        """Upload an intelligence document (PDF/TXT)"""
        if not os.path.exists(file_path):
            print(f"❌ File not found: {file_path}")
            return {"error": "File not found"}
            
        url = f"{self.base_url}/intel/upload"
        
        filename = os.path.basename(file_path)
        print(f"📄 Uploading intelligence document: {filename}")
        print(f"   Title: {title}")
        
        # Prepare metadata
        data = {"title": title}
        for key, value in metadata.items():
            if value is not None:
                data[key] = value
                print(f"   {key.title()}: {value}")
        
        try:
            with open(file_path, 'rb') as f:
                files = {'file': (filename, f, 'application/pdf' if filename.lower().endswith('.pdf') else 'text/plain')}
                
                # Use multipart form data for file upload
                headers = {"X-API-Key": self.headers["X-API-Key"]}  # Remove Content-Type for multipart
                response = requests.post(url, headers=headers, files=files, data=data)
                
                if response.status_code == 200:
                    result = response.json()
                    print(f"   ✅ Success - Doc ID: {result.get('doc_id')}, Chunks: {result.get('chunks')}")
                    return result
                else:
                    print(f"   ❌ Failed: {response.status_code} - {response.text}")
                    return {"error": response.text, "status": response.status_code}
                    
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return {"error": str(e)}
    
    def search(self, query: str, k: int = 5) -> List[Dict[str, Any]]:
        """Search the intelligence database"""
        url = f"{self.base_url}/search"
        params = {"q": query, "k": k}
        
        print(f"🔍 Searching for: '{query}'")
        
        try:
            response = requests.get(url, params=params)
            
            if response.status_code == 200:
                results = response.json()
                print(f"   ✅ Found {len(results)} results")
                return results
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                return []
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
            return []

def create_sample_observations() -> List[Dict[str, Any]]:
    """Create sample tactical sensor observations"""
    return [
        {
            "time": "2025-10-04T15:30:00+00:00",
            "mgrs": "35VLG8476572200",
            "what": "Infantry Squad",
            "amount": 8,
            "confidence": 92,
            "sensor_id": "OPTIC_001",
            "unit": "Alpha Company, 2nd Platoon",
            "observer_signature": "MikeAlpha"
        },
        {
            "time": "2025-10-04T15:45:00+00:00",
            "mgrs": "35VLG8477572180",
            "what": "BMP-2 IFV",
            "amount": 1,
            "confidence": 95,
            "sensor_id": "THERMAL_002",
            "unit": "Bravo Company, Scout Team",
            "observer_signature": "EchoSix"
        },
        {
            "time": "2025-10-04T16:10:00+00:00",
            "mgrs": "35VLG8478572150",
            "what": "Supply Truck",
            "amount": 3,
            "confidence": 88,
            "sensor_id": "DRONE_003",
            "unit": "Charlie Company, UAV Team",
            "observer_signature": "SkyWatcher"
        }
    ]

def demo_tactical_observations():
    """Demo: Add tactical sensor observations"""
    print("🎯 TACTICAL SENSOR OBSERVATIONS")
    print("=" * 60)
    
    client = DefHackClient()
    observations = create_sample_observations()
    
    results = client.add_multiple_observations(observations)
    
    print(f"\n📊 Summary:")
    successful = sum(1 for r in results if 'report_id' in r)
    print(f"   Successfully added: {successful}/{len(results)} observations")
    
    return results

def demo_intelligence_documents():
    """Demo: Upload intelligence documents"""
    print("\n📚 INTELLIGENCE DOCUMENTS")
    print("=" * 60)
    
    client = DefHackClient()
    
    # Check for existing documents
    documents_to_upload = [
        {
            "file": "Documents/2Fiore17.pdf",
            "title": "Russian Battalion Tactical Group Analysis - Fiore 2017",
            "version": "1.0",
            "lang": "en",
            "published_at": "2017-01-01",
            "origin": "US Army",
            "type": "Doctrinal Analysis"
        },
        {
            "file": "Documents/3Baez22.pdf", 
            "title": "BTG Tactical Employment Study - Baez 2022",
            "version": "1.0",
            "lang": "en", 
            "published_at": "2022-01-01",
            "origin": "Military Academy",
            "type": "Tactical Study"
        }
    ]
    
    results = []
    for doc in documents_to_upload:
        file_path = doc.pop("file")
        if os.path.exists(file_path):
            result = client.upload_intelligence_document(file_path, **doc)
            results.append(result)
        else:
            print(f"⚠️  Document not found: {file_path}")
            results.append({"error": "File not found"})
    
    print(f"\n📊 Summary:")
    successful = sum(1 for r in results if 'doc_id' in r)
    print(f"   Successfully uploaded: {successful}/{len(results)} documents")
    
    return results

def demo_search_capabilities():
    """Demo: Search across all data"""
    print("\n🔍 SEARCH CAPABILITIES")
    print("=" * 60)
    
    client = DefHackClient()
    
    search_queries = [
        "tactical",
        "BTG",
        "infantry", 
        "Russian",
        "analysis"
    ]
    
    for query in search_queries:
        results = client.search(query, k=2)
        if results:
            print(f"   Top result: Doc {results[0].get('doc_id')} - {results[0].get('text', '')[:80]}...")
        print()

def main():
    """Main demo function"""
    print("🚀 DefHack Unified Data Input Interface")
    print("=" * 80)
    print("This tool provides consistent interfaces for:")
    print("  📡 Tactical Sensor Observations (field reports)")
    print("  📚 Intelligence Documents (PDFs, doctrinal materials)")
    print("  🔍 Search & Analysis capabilities")
    print("=" * 80)
    
    # Demo tactical observations
    demo_tactical_observations()
    
    # Demo intelligence documents  
    demo_intelligence_documents()
    
    # Demo search
    demo_search_capabilities()
    
    print("\n🎉 DefHack system demonstration complete!")
    print("Use DefHackClient class for programmatic access to all functions.")

if __name__ == "__main__":
    main()