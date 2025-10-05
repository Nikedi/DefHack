#!/usr/bin/env python3
"""
Test API Leader Notifications
"""
import requests
import json
from datetime import datetime, timezone

# Test data matching the example observation format
test_observation = {
    "time": "2025-10-04T16:30:00+00:00",
    "mgrs": "35VLG8472571866",
    "what": "TACTICAL:fighter-jet",
    "amount": 5,
    "confidence": 50,
    "sensor_id": "uav-17",
    "unit": "2. PSTOS",
    "observer_signature": "ExternalDevice"
}

def test_api_observation():
    """Test sending observation via API"""
    url = "http://localhost:8080/ingest/sensor"
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": "583C55345736D7218355BCB51AA47"
    }
    
    try:
        response = requests.post(url, json=test_observation, headers=headers)
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            print("✅ API observation sent successfully!")
            print("✅ Leader notifications should have been triggered")
        else:
            print(f"❌ Failed with status {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error sending API observation: {e}")

if __name__ == "__main__":
    print("🧪 Testing API Leader Notifications")
    print("=" * 50)
    test_api_observation()