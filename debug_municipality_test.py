#!/usr/bin/env python3
"""
Debug Municipality Management API - Focus on NEW scheduling features
"""

import requests
import json
from datetime import datetime

BACKEND_URL = "https://propmap-ns.preview.emergentagent.com/api"

def debug_municipality_scheduling():
    """Debug the scheduling fields in municipality management"""
    print("🔍 DEBUGGING MUNICIPALITY SCHEDULING FEATURES")
    print("=" * 60)
    
    # Test data with scheduling fields
    test_municipality = {
        "name": "Debug Test Municipality",
        "website_url": "https://debug-test.ca",
        "scraper_type": "generic",
        "scrape_enabled": True,
        "scrape_frequency": "weekly",
        "scrape_day_of_week": 2,
        "scrape_day_of_month": 15,
        "scrape_time_hour": 3,
        "scrape_time_minute": 30
    }
    
    print("📝 Test Data:")
    print(json.dumps(test_municipality, indent=2))
    
    # Test 1: POST municipality with scheduling
    print("\n🔧 TEST 1: POST /api/municipalities")
    try:
        response = requests.post(
            f"{BACKEND_URL}/municipalities",
            json=test_municipality,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            result = response.json()
            print("✅ SUCCESS - Response:")
            print(json.dumps(result, indent=2, default=str))
            
            municipality_id = result.get("id")
            
            # Test 2: GET the created municipality
            if municipality_id:
                print(f"\n🔧 TEST 2: GET /api/municipalities/{municipality_id}")
                get_response = requests.get(f"{BACKEND_URL}/municipalities/{municipality_id}", timeout=30)
                
                print(f"GET Status Code: {get_response.status_code}")
                if get_response.status_code == 200:
                    get_result = get_response.json()
                    print("✅ GET SUCCESS - Response:")
                    print(json.dumps(get_result, indent=2, default=str))
                else:
                    print(f"❌ GET FAILED: {get_response.text}")
                
                # Test 3: PUT update with scheduling changes
                print(f"\n🔧 TEST 3: PUT /api/municipalities/{municipality_id}")
                update_data = {
                    "scrape_frequency": "daily",
                    "scrape_time_hour": 6,
                    "scrape_time_minute": 0
                }
                
                put_response = requests.put(
                    f"{BACKEND_URL}/municipalities/{municipality_id}",
                    json=update_data,
                    headers={"Content-Type": "application/json"},
                    timeout=30
                )
                
                print(f"PUT Status Code: {put_response.status_code}")
                if put_response.status_code == 200:
                    put_result = put_response.json()
                    print("✅ PUT SUCCESS - Response:")
                    print(json.dumps(put_result, indent=2, default=str))
                else:
                    print(f"❌ PUT FAILED: {put_response.text}")
                
                # Test 4: DELETE municipality
                print(f"\n🔧 TEST 4: DELETE /api/municipalities/{municipality_id}")
                delete_response = requests.delete(f"{BACKEND_URL}/municipalities/{municipality_id}", timeout=30)
                
                print(f"DELETE Status Code: {delete_response.status_code}")
                if delete_response.status_code == 200:
                    delete_result = delete_response.json()
                    print("✅ DELETE SUCCESS - Response:")
                    print(json.dumps(delete_result, indent=2, default=str))
                else:
                    print(f"❌ DELETE FAILED: {delete_response.text}")
        else:
            print(f"❌ POST FAILED: {response.text}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

def test_existing_municipalities_scheduling():
    """Test if existing municipalities have scheduling fields"""
    print("\n🔍 TESTING EXISTING MUNICIPALITIES FOR SCHEDULING FIELDS")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        if response.status_code == 200:
            municipalities = response.json()
            print(f"📊 Found {len(municipalities)} municipalities")
            
            # Check first few municipalities for scheduling fields
            for i, muni in enumerate(municipalities[:3]):
                print(f"\n📋 Municipality {i+1}: {muni.get('name', 'Unknown')}")
                
                scheduling_fields = [
                    'scrape_enabled', 'scrape_frequency', 'scrape_day_of_week',
                    'scrape_day_of_month', 'scrape_time_hour', 'scrape_time_minute',
                    'next_scrape_time'
                ]
                
                for field in scheduling_fields:
                    value = muni.get(field, 'MISSING')
                    print(f"   {field}: {value}")
        else:
            print(f"❌ Failed to get municipalities: {response.status_code}")
            
    except Exception as e:
        print(f"❌ ERROR: {e}")

if __name__ == "__main__":
    debug_municipality_scheduling()
    test_existing_municipalities_scheduling()