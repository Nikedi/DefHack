#!/usr/bin/env python3
import requests
import os

def upload_document(file_path, title, description=None, version=None, lang="en", origin=None, adversary=None, published_at=None):
    """Upload a document to the DefHack intelligence system"""
    url = "http://localhost:8080/intel/upload"
    headers = {"X-API-Key": "583C55345736D7218355BCB51AA47"}
    
    filename = os.path.basename(file_path)
    
    with open(file_path, 'rb') as f:
        files = {'file': (filename, f, 'application/pdf')}
        data = {
            'title': title,
        }
        
        # Add optional fields
        if version:
            data['version'] = version
        if lang:
            data['lang'] = lang
        if origin:
            data['origin'] = origin
        if adversary:
            data['adversary'] = adversary
        if published_at:
            data['published_at'] = published_at
        
        print(f"Uploading {filename}...")
        response = requests.post(url, headers=headers, files=files, data=data)
        
        if response.status_code == 200:
            print(f"✅ Successfully uploaded {filename}")
            print(f"Response: {response.json()}")
        else:
            print(f"❌ Failed to upload {filename}")
            print(f"Status: {response.status_code}")
            print(f"Error: {response.text}")
        
        return response

if __name__ == "__main__":
    # Upload documents
    documents = [
        ("Documents/2Fiore17.pdf", "Intelligence Report - Fiore 2017", "2017-01-01"),
        ("Documents/3Baez22.pdf", "Intelligence Report - Baez 2022", "2022-01-01")
    ]
    
    for file_path, title, published_at in documents:
        if os.path.exists(file_path):
            upload_document(file_path, title, published_at=published_at, lang="en")
        else:
            print(f"❌ File not found: {file_path}")