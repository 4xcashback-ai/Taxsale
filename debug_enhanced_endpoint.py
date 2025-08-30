#!/usr/bin/env python3
"""
Debug Enhanced Endpoint - Test what the enhanced endpoint is actually doing
"""

import requests
import json

def test_enhanced_endpoint_debug():
    """Debug the enhanced endpoint to see what's happening"""
    print("🔍 Debugging Enhanced Endpoint...")
    print("🎯 Target: Assessment 00079006")
    print("=" * 60)
    
    try:
        # Test the enhanced endpoint
        url = "https://taxsalecompass.ca/api/property/00079006/enhanced"
        print(f"📡 Calling: {url}")
        
        response = requests.get(url, timeout=60)
        print(f"✅ HTTP {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if PVSC data was added
            print(f"\n📊 Response Analysis:")
            print(f"   Total fields: {len(data)}")
            
            # Check for PVSC-specific fields
            pvsc_fields = ['civic_address', 'google_maps_link', 'property_details', 'pvsc_url']
            found_pvsc_fields = [field for field in pvsc_fields if field in data]
            
            print(f"   PVSC fields found: {len(found_pvsc_fields)}/4")
            print(f"   PVSC fields: {found_pvsc_fields}")
            
            # Check property_details specifically
            property_details = data.get('property_details', {})
            if property_details:
                print(f"\n🏠 property_details object:")
                print(f"   Fields: {len(property_details)}")
                for key, value in property_details.items():
                    print(f"   {key}: {value}")
                
                # Check for new fields specifically
                new_fields = ['quality_of_construction', 'under_construction', 'living_units', 'finished_basement', 'garage']
                found_new_fields = [field for field in new_fields if field in property_details]
                
                print(f"\n🎯 New Fields Analysis:")
                print(f"   Found: {len(found_new_fields)}/5")
                print(f"   Missing: {[field for field in new_fields if field not in found_new_fields]}")
                
                if len(found_new_fields) == 5:
                    print(f"✅ ALL NEW FIELDS PRESENT")
                    return True
                else:
                    print(f"❌ NEW FIELDS MISSING")
                    return False
            else:
                print(f"❌ property_details object missing")
                return False
        else:
            print(f"❌ HTTP {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_endpoint_debug()
    if success:
        print(f"\n🎉 Enhanced endpoint has new fields")
    else:
        print(f"\n❌ Enhanced endpoint missing new fields")