#!/usr/bin/env python3
import requests
import json
from datetime import datetime

def add_sensor_data():
    """Add sensor observations through the DefHack API"""
    
    # API configuration
    url = "http://localhost:8080/ingest/sensor"
    headers = {
        "X-API-Key": "583C55345736D7218355BCB51AA47",
        "Content-Type": "application/json"
    }
    
    # Sensor data examples
    sensor_observations = [
        {
            "time": "2025-10-03T19:48:41+00:00",
            "mgrs": "35VLG8472571866",
            "what": "Soldier w/ Rifle",
            "amount": 7,
            "confidence": 90,
            "sensor_id": "SENSOR_001",  # Adding sensor_id as it's required
            "unit": "Platoon 1, Squad 2",
            "observer_signature": "JackJames"
        },
        {
            "time": "2025-10-03T20:37:21+00:00",
            "mgrs": "35VLG8474371854",
            "what": "MT-LB",
            "amount": 2,
            "confidence": 85,
            "sensor_id": "SENSOR_002",  # Adding sensor_id as it's required
            "unit": "Platoon 3, Squad 1",
            "observer_signature": "JimBean"
        }
    ]
    
    print("Adding sensor observations to DefHack system...")
    print("=" * 50)
    
    for i, observation in enumerate(sensor_observations, 1):
        print(f"\n📡 Submitting observation {i}:")
        print(f"   Time: {observation['time']}")
        print(f"   Location: {observation['mgrs']}")
        print(f"   What: {observation['what']} (Amount: {observation['amount']})")
        print(f"   Confidence: {observation['confidence']}%")
        print(f"   Observer: {observation['observer_signature']}")
        
        try:
            response = requests.post(url, headers=headers, json=observation)
            
            if response.status_code == 200:
                print(f"   ✅ Successfully added observation {i}")
                print(f"   Response: {response.json()}")
            else:
                print(f"   ❌ Failed to add observation {i}")
                print(f"   Status: {response.status_code}")
                print(f"   Error: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")
    
    print(f"\n🎯 Sensor data submission complete!")

def verify_sensor_data():
    """Verify sensor data was added by searching for it"""
    print("\n" + "=" * 50)
    print("Verifying sensor data was added...")
    print("=" * 50)
    
    # Search for the added sensor data
    search_terms = ["Soldier", "MT-LB", "JackJames", "JimBean"]
    
    for term in search_terms:
        print(f"\n🔍 Searching for: '{term}'")
        
        try:
            response = requests.get(
                "http://localhost:8080/search",
                params={"q": term, "k": 3}
            )
            
            if response.status_code == 200:
                results = response.json()
                if results:
                    print(f"   ✅ Found {len(results)} results")
                    for result in results:
                        doc_id = result.get('doc_id', 'N/A')
                        text = result.get('text', '')[:100] + "..." if len(result.get('text', '')) > 100 else result.get('text', '')
                        print(f"      Doc ID: {doc_id} - {text}")
                else:
                    print(f"   ⚠️  No results found")
            else:
                print(f"   ❌ Search failed: {response.status_code}")
                
        except requests.exceptions.RequestException as e:
            print(f"   ❌ Network error: {e}")

if __name__ == "__main__":
    # Add the sensor data
    add_sensor_data()
    
    # Verify it was added (note: sensor data goes to database, not search index)
    verify_sensor_data()