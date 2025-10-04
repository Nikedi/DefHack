#!/usr/bin/env python3
import requests

def test_auth():
    """Test different header formats"""
    url = "http://localhost:8080/search"
    
    # Test with different header formats
    headers_to_test = [
        {"X-API-Key": "change-me"},
        {"x-api-key": "change-me"},
        {"X-Api-Key": "change-me"},
    ]
    
    for headers in headers_to_test:
        print(f"Testing headers: {headers}")
        response = requests.get(url, params={"q": "test"}, headers=headers)
        print(f"Status: {response.status_code}")
        print()

def test_settings():
    """Test what settings value is being used"""
    url = "http://localhost:8080/intel/upload"
    
    # Try a simple POST to see what authentication error we get
    headers = {"X-API-Key": "wrong-key"}
    data = {"title": "test"}
    
    response = requests.post(url, headers=headers, data=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")

if __name__ == "__main__":
    print("Testing auth headers...")
    test_auth()
    
    print("Testing settings...")
    test_settings()