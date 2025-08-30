#!/usr/bin/env python3
"""
Enhanced PVSC Scraping Test - Review Request Focus
Tests the new PVSC fields: quality_of_construction, under_construction, living_units, finished_basement, garage
"""

import requests
import json

BACKEND_URL = "https://taxsalecompass.ca/api"

def test_enhanced_pvsc_fields():
    """Test Enhanced PVSC Scraping with New Fields"""
    print("🏠 Testing Enhanced PVSC Scraping with New Fields...")
    print("🎯 FOCUS: GET /api/property/00079006/enhanced")
    print("📋 EXPECTED: quality_of_construction: 'Low', under_construction: 'N', living_units: 1, finished_basement: 'N', garage: 'N'")
    print("=" * 80)
    
    try:
        # Test the enhanced property endpoint
        response = requests.get(f"{BACKEND_URL}/property/00079006/enhanced", timeout=60)
        
        if response.status_code == 200:
            property_data = response.json()
            print("✅ Enhanced property endpoint accessible")
            
            # Get property_details object
            property_details = property_data.get('property_details', {})
            
            if property_details:
                print(f"✅ property_details object found with {len(property_details)} fields")
                
                # Test each new field
                new_fields_status = {}
                
                # Quality of Construction
                quality = property_details.get('quality_of_construction')
                if quality:
                    print(f"✅ quality_of_construction: '{quality}'")
                    if quality.lower() == "low":
                        print(f"   ✅ Expected value 'Low' found")
                        new_fields_status['quality_of_construction'] = True
                    else:
                        print(f"   ⚠️ Value '{quality}' differs from expected 'Low'")
                        new_fields_status['quality_of_construction'] = False
                else:
                    print(f"❌ quality_of_construction: NOT FOUND")
                    new_fields_status['quality_of_construction'] = False
                
                # Under Construction
                under_construction = property_details.get('under_construction')
                if under_construction:
                    print(f"✅ under_construction: '{under_construction}'")
                    if under_construction == "N":
                        print(f"   ✅ Expected value 'N' found")
                        new_fields_status['under_construction'] = True
                    else:
                        print(f"   ⚠️ Value '{under_construction}' differs from expected 'N'")
                        new_fields_status['under_construction'] = False
                else:
                    print(f"❌ under_construction: NOT FOUND")
                    new_fields_status['under_construction'] = False
                
                # Living Units
                living_units = property_details.get('living_units')
                if living_units is not None:
                    print(f"✅ living_units: {living_units}")
                    if living_units == 1:
                        print(f"   ✅ Expected value 1 found")
                        new_fields_status['living_units'] = True
                    else:
                        print(f"   ⚠️ Value {living_units} differs from expected 1")
                        new_fields_status['living_units'] = False
                else:
                    print(f"❌ living_units: NOT FOUND")
                    new_fields_status['living_units'] = False
                
                # Finished Basement
                finished_basement = property_details.get('finished_basement')
                if finished_basement:
                    print(f"✅ finished_basement: '{finished_basement}'")
                    if finished_basement == "N":
                        print(f"   ✅ Expected value 'N' found")
                        new_fields_status['finished_basement'] = True
                    else:
                        print(f"   ⚠️ Value '{finished_basement}' differs from expected 'N'")
                        new_fields_status['finished_basement'] = False
                else:
                    print(f"❌ finished_basement: NOT FOUND")
                    new_fields_status['finished_basement'] = False
                
                # Garage
                garage = property_details.get('garage')
                if garage:
                    print(f"✅ garage: '{garage}'")
                    if garage == "N":
                        print(f"   ✅ Expected value 'N' found")
                        new_fields_status['garage'] = True
                    else:
                        print(f"   ⚠️ Value '{garage}' differs from expected 'N'")
                        new_fields_status['garage'] = False
                else:
                    print(f"❌ garage: NOT FOUND")
                    new_fields_status['garage'] = False
                
                # Show complete property_details for debugging
                print(f"\n📊 COMPLETE property_details object:")
                for key, value in property_details.items():
                    print(f"   {key}: {value}")
                
                # Summary
                found_count = sum(new_fields_status.values())
                total_count = len(new_fields_status)
                
                print(f"\n📋 NEW FIELDS SUMMARY:")
                print(f"   Found: {found_count}/{total_count} new fields")
                print(f"   Success Rate: {(found_count/total_count)*100:.1f}%")
                
                if found_count == total_count:
                    print(f"✅ ALL NEW FIELDS CAPTURED - ENHANCEMENT SUCCESSFUL")
                    return True
                elif found_count > 0:
                    print(f"⚠️ PARTIAL SUCCESS - {found_count} out of {total_count} fields captured")
                    return False
                else:
                    print(f"❌ ENHANCEMENT FAILED - No new fields captured")
                    return False
                    
            else:
                print(f"❌ property_details object missing")
                return False
        else:
            print(f"❌ Enhanced property endpoint failed: HTTP {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Test error: {e}")
        return False

if __name__ == "__main__":
    success = test_enhanced_pvsc_fields()
    if success:
        print(f"\n🎉 Enhanced PVSC scraping test PASSED")
    else:
        print(f"\n❌ Enhanced PVSC scraping test FAILED")