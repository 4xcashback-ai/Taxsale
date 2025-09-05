#!/usr/bin/env python3
"""
Debug script to test JWT authentication for admin endpoints
"""
import requests
import json
import sys

# Configuration
BACKEND_URL = "http://localhost:8001"
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "TaxSale2025!SecureAdmin"

def test_admin_login():
    """Test admin login and get token"""
    print("Testing admin login...")
    
    login_data = {
        "username": ADMIN_USERNAME,
        "password": ADMIN_PASSWORD
    }
    
    try:
        response = requests.post(
            f"{BACKEND_URL}/api/auth/login",
            json=login_data,
            headers={"Content-Type": "application/json"}
        )
        
        print(f"Login response status: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            print(f"✅ Login successful! Token length: {len(token)}")
            return token
        else:
            print(f"❌ Login failed: {response.text}")
            return None
            
    except Exception as e:
        print(f"❌ Login error: {e}")
        return None

def test_deployment_endpoints(token):
    """Test deployment endpoints with token"""
    if not token:
        print("No token available for testing")
        return
        
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    endpoints = [
        ("GET", "/api/deployment/status"),
        ("POST", "/api/deployment/check-updates"),
        ("POST", "/api/deployment/verify")
    ]
    
    for method, endpoint in endpoints:
        print(f"\nTesting {method} {endpoint}...")
        try:
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", headers=headers)
            else:
                response = requests.post(f"{BACKEND_URL}{endpoint}", json={}, headers=headers)
                
            print(f"Response status: {response.status_code}")
            
            if response.status_code == 200:
                print(f"✅ Success: {endpoint}")
                print(f"Response: {response.json()}")
            else:
                print(f"❌ Failed: {endpoint}")
                print(f"Error: {response.text}")
                
        except Exception as e:
            print(f"❌ Error testing {endpoint}: {e}")

if __name__ == "__main__":
    print("=== JWT Authentication Debug Script ===")
    token = test_admin_login()
    test_deployment_endpoints(token)
    print("\n=== Debug Complete ===")