#!/usr/bin/env python3

"""Debug script to test the relationship API directly"""

import requests
import json

# Test the relationship API
base_url = "http://localhost:8000"

# First create test characters
alice_data = {
    "name": "Alice",
    "entity_type": "character",
    "description": "Test character"
}

bob_data = {
    "name": "Bob", 
    "entity_type": "character",
    "description": "Test character"
}

print("Creating test characters...")
alice_response = requests.post(f"{base_url}/api/v1/entities/", json=alice_data)
bob_response = requests.post(f"{base_url}/api/v1/entities/", json=bob_data)

print(f"Alice creation status: {alice_response.status_code}")
print(f"Bob creation status: {bob_response.status_code}")

if alice_response.status_code == 200 and bob_response.status_code == 200:
    alice = alice_response.json()["data"]["entity"]
    bob = bob_response.json()["data"]["entity"]
    
    print(f"Alice ID: {alice['id']}")
    print(f"Bob ID: {bob['id']}")
    
    # Try creating a relationship
    relationship_data = {
        "source_id": alice["id"],
        "target_id": bob["id"],
        "relation_type": "friends",
        "starts_at": 100,
        "meta": {"test": True}
    }
    
    print("\nCreating relationship...")
    print(f"Relationship data: {json.dumps(relationship_data, indent=2)}")
    
    rel_response = requests.post(f"{base_url}/api/v1/relationships/", json=relationship_data)
    print(f"Relationship creation status: {rel_response.status_code}")
    print(f"Response: {rel_response.text}")
    
else:
    print("Failed to create characters")
    print(f"Alice response: {alice_response.text}")
    print(f"Bob response: {bob_response.text}")