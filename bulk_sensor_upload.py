#!/usr/bin/env python3
import requests
import json

def bulk_upload_sensor_data(json_file):
    """Upload multiple sensor observations from a JSON file"""
    
    url = "http://localhost:8080/ingest/sensor"
    headers = {
        "X-API-Key": "583C55345736D7218355BCB51AA47",
        "Content-Type": "application/json"
    }
    
    # Load data from JSON file
    with open(json_file, 'r') as f:
        sensor_data = json.load(f)
    
    print(f"Loading {len(sensor_data)} sensor observations from {json_file}")
    
    for i, observation in enumerate(sensor_data, 1):
        print(f"📡 Uploading observation {i}: {observation['what']}")
        
        response = requests.post(url, headers=headers, json=observation)
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Success - Report ID: {result.get('report_id')}")
        else:
            print(f"   ❌ Failed: {response.status_code} - {response.text}")

if __name__ == "__main__":
    bulk_upload_sensor_data("sensor_data.json")