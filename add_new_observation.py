#!/usr/bin/env python3
import requests
import json
from datetime import datetime, timezone

def add_new_observation():
    """Add a new sensor observation example"""
    
    url = "http://localhost:8080/ingest/sensor"
    headers = {
        "X-API-Key": "583C55345736D7218355BCB51AA47",
        "Content-Type": "application/json"
    }
    
    # New observation example
    new_observation = {
        "time": "2025-10-04T14:23:15+00:00",
        "mgrs": "35VLG8475672108",
        "what": "T-72 Tank",
        "amount": 3,
        "confidence": 95,
        "sensor_id": "SENSOR_003",
        "unit": "Recon Team Alpha",
        "observer_signature": "SarahConnor"
    }
    
    print("Adding new sensor observation...")
    print("=" * 40)
    print(f"📡 New Observation Details:")
    print(f"   Time: {new_observation['time']}")
    print(f"   Location (MGRS): {new_observation['mgrs']}")
    print(f"   Target: {new_observation['what']}")
    print(f"   Count: {new_observation['amount']}")
    print(f"   Confidence: {new_observation['confidence']}%")
    print(f"   Sensor ID: {new_observation['sensor_id']}")
    print(f"   Unit: {new_observation['unit']}")
    print(f"   Observer: {new_observation['observer_signature']}")
    
    try:
        response = requests.post(url, headers=headers, json=new_observation)
        
        if response.status_code == 200:
            result = response.json()
            print(f"\n✅ SUCCESS!")
            print(f"   Report ID: {result.get('report_id')}")
            print(f"   Observation successfully added to DefHack system")
            
            # Show the JSON that was sent
            print(f"\n📋 JSON Payload Sent:")
            print(json.dumps(new_observation, indent=2))
            
        else:
            print(f"\n❌ FAILED!")
            print(f"   Status Code: {response.status_code}")
            print(f"   Error: {response.text}")
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network Error: {e}")

if __name__ == "__main__":
    add_new_observation()