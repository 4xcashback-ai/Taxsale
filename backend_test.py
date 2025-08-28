#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Tests Halifax tax sale scraper functionality and related endpoints
"""

import requests
import json
import sys
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://propfinder-24.preview.emergentagent.com/api"

def test_api_connection():
    """Test basic API connectivity"""
    print("🔗 Testing API Connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=30)
        if response.status_code == 200:
            print("✅ API connection successful")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False

def test_municipalities_endpoint():
    """Test municipalities endpoint and check Halifax exists"""
    print("\n🏛️ Testing Municipalities Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        if response.status_code == 200:
            municipalities = response.json()
            print(f"✅ Municipalities endpoint working - Found {len(municipalities)} municipalities")
            
            # Check if Halifax exists
            halifax_found = False
            halifax_data = None
            for muni in municipalities:
                if "Halifax" in muni.get("name", ""):
                    halifax_found = True
                    halifax_data = muni
                    print(f"   📍 Halifax found: {muni['name']}")
                    print(f"   📊 Scrape status: {muni.get('scrape_status', 'unknown')}")
                    print(f"   🕒 Last scraped: {muni.get('last_scraped', 'never')}")
                    break
            
            if not halifax_found:
                print("⚠️ Halifax Regional Municipality not found in database")
                return False, None
            
            return True, halifax_data
        else:
            print(f"❌ Municipalities endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Municipalities endpoint error: {e}")
        return False, None

def test_halifax_scraper():
    """Test Halifax scraper endpoint"""
    print("\n🔍 Testing Halifax Scraper Endpoint...")
    try:
        print("   Triggering Halifax scrape...")
        response = requests.post(f"{BACKEND_URL}/scrape/halifax", timeout=120)
        
        if response.status_code == 200:
            result = response.json()
            print("✅ Halifax scraper executed successfully")
            print(f"   📊 Status: {result.get('status', 'unknown')}")
            print(f"   🏠 Properties scraped: {result.get('properties_scraped', 0)}")
            return True, result
        else:
            print(f"❌ Halifax scraper failed with status {response.status_code}")
            try:
                error_detail = response.json()
                print(f"   Error details: {error_detail}")
            except:
                print(f"   Raw response: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ Halifax scraper error: {e}")
        return False, None

def test_tax_sales_endpoint():
    """Test tax sales endpoint and verify Halifax data"""
    print("\n🏠 Testing Tax Sales Endpoint...")
    try:
        # Test general tax sales endpoint
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            print(f"✅ Tax sales endpoint working - Found {len(properties)} properties")
            
            # Look for Halifax properties
            halifax_properties = [p for p in properties if "Halifax" in p.get("municipality_name", "")]
            print(f"   🏛️ Halifax properties: {len(halifax_properties)}")
            
            if halifax_properties:
                # Check the sample property we expect
                sample_property = None
                for prop in halifax_properties:
                    if prop.get("assessment_number") == "02102943":
                        sample_property = prop
                        break
                
                if sample_property:
                    print("✅ Expected Halifax property found:")
                    print(f"   📋 Assessment Number: {sample_property.get('assessment_number')}")
                    print(f"   👤 Owner: {sample_property.get('owner_name')}")
                    print(f"   🏠 Address: {sample_property.get('property_address')}")
                    print(f"   🏷️ PID: {sample_property.get('pid_number')}")
                    print(f"   💰 Opening Bid: ${sample_property.get('opening_bid')}")
                    print(f"   📅 Sale Date: {sample_property.get('sale_date')}")
                    print(f"   🔄 Redeemable: {sample_property.get('redeemable')}")
                    print(f"   💼 HST: {sample_property.get('hst_applicable')}")
                    
                    # Verify required fields are present
                    required_fields = ['assessment_number', 'owner_name', 'pid_number', 'opening_bid']
                    missing_fields = [field for field in required_fields if not sample_property.get(field)]
                    
                    if missing_fields:
                        print(f"⚠️ Missing required fields: {missing_fields}")
                        return False, halifax_properties
                    else:
                        print("✅ All required fields present")
                        return True, halifax_properties
                else:
                    print("⚠️ Expected sample property (assessment #02102943) not found")
                    if halifax_properties:
                        print("   Available Halifax properties:")
                        for prop in halifax_properties[:3]:  # Show first 3
                            print(f"   - Assessment: {prop.get('assessment_number', 'N/A')}, Owner: {prop.get('owner_name', 'N/A')}")
                    return False, halifax_properties
            else:
                print("⚠️ No Halifax properties found in database")
                return False, []
        else:
            print(f"❌ Tax sales endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Tax sales endpoint error: {e}")
        return False, None

def test_property_descriptions_bug():
    """Test for the specific property description bug reported by user"""
    print("\n🔍 Testing Property Description Bug (Assessment #00079006)...")
    try:
        # Get all Halifax properties to analyze descriptions
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            print(f"✅ Retrieved {len(properties)} Halifax properties for description analysis")
            
            # Look specifically for assessment #00079006
            target_property = None
            for prop in properties:
                if prop.get("assessment_number") == "00079006":
                    target_property = prop
                    break
            
            # Analyze property descriptions
            good_descriptions = []
            bad_descriptions = []
            placeholder_pattern = r"Property at assessment #\d{8}"
            
            for prop in properties:
                assessment = prop.get("assessment_number", "N/A")
                address = prop.get("property_address", "")
                description = prop.get("property_description", "")
                
                # Check if description is a placeholder
                if "Property at assessment #" in address or "Property at assessment #" in description:
                    bad_descriptions.append({
                        "assessment": assessment,
                        "address": address,
                        "description": description,
                        "owner": prop.get("owner_name", "N/A")
                    })
                else:
                    # Check if it has meaningful address/description content
                    if (len(address) > 20 and any(word in address.lower() for word in 
                        ["rd", "st", "ave", "drive", "road", "street", "avenue", "lane", "court", "place", "way"])):
                        good_descriptions.append({
                            "assessment": assessment,
                            "address": address,
                            "description": description,
                            "owner": prop.get("owner_name", "N/A")
                        })
            
            print(f"\n📊 Description Analysis Results:")
            print(f"   ✅ Properties with good descriptions: {len(good_descriptions)}")
            print(f"   ❌ Properties with placeholder descriptions: {len(bad_descriptions)}")
            
            # Show examples of good descriptions
            if good_descriptions:
                print(f"\n✅ Examples of GOOD property descriptions:")
                for i, prop in enumerate(good_descriptions[:3]):
                    print(f"   {i+1}. Assessment #{prop['assessment']}")
                    print(f"      Address: {prop['address']}")
                    print(f"      Owner: {prop['owner']}")
            
            # Show examples of bad descriptions
            if bad_descriptions:
                print(f"\n❌ Examples of BAD property descriptions (placeholders):")
                for i, prop in enumerate(bad_descriptions[:5]):
                    print(f"   {i+1}. Assessment #{prop['assessment']}")
                    print(f"      Address: {prop['address']}")
                    print(f"      Description: {prop['description']}")
                    print(f"      Owner: {prop['owner']}")
            
            # Check specifically for assessment #00079006
            if target_property:
                print(f"\n🎯 SPECIFIC TARGET PROPERTY (Assessment #00079006):")
                print(f"   Address: {target_property.get('property_address', 'N/A')}")
                print(f"   Description: {target_property.get('property_description', 'N/A')}")
                print(f"   Owner: {target_property.get('owner_name', 'N/A')}")
                
                # Check if this property has the bug
                address = target_property.get('property_address', '')
                if "Property at assessment #00079006" in address:
                    print(f"   ❌ BUG CONFIRMED: Property #00079006 has placeholder description")
                    return False, {"target_found": True, "has_bug": True, "bad_count": len(bad_descriptions), "good_count": len(good_descriptions)}
                else:
                    print(f"   ✅ Property #00079006 has proper description")
                    return True, {"target_found": True, "has_bug": False, "bad_count": len(bad_descriptions), "good_count": len(good_descriptions)}
            else:
                print(f"\n⚠️ Target property (Assessment #00079006) not found in current data")
                
            # Overall assessment
            total_properties = len(properties)
            if total_properties > 0:
                bad_percentage = (len(bad_descriptions) / total_properties) * 100
                print(f"\n📈 Overall Description Quality:")
                print(f"   Total properties: {total_properties}")
                print(f"   Bad descriptions: {len(bad_descriptions)} ({bad_percentage:.1f}%)")
                print(f"   Good descriptions: {len(good_descriptions)} ({100-bad_percentage:.1f}%)")
                
                # Consider it a failure if more than 10% have bad descriptions
                if bad_percentage > 10:
                    print(f"   ❌ DESCRIPTION BUG DETECTED: {bad_percentage:.1f}% of properties have placeholder descriptions")
                    return False, {"target_found": False, "has_bug": True, "bad_count": len(bad_descriptions), "good_count": len(good_descriptions)}
                else:
                    print(f"   ✅ Description quality acceptable: Only {bad_percentage:.1f}% have placeholders")
                    return True, {"target_found": False, "has_bug": False, "bad_count": len(bad_descriptions), "good_count": len(good_descriptions)}
            else:
                print(f"   ⚠️ No properties found to analyze")
                return False, {"target_found": False, "has_bug": True, "bad_count": 0, "good_count": 0}
                
        else:
            print(f"❌ Failed to retrieve Halifax properties: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Property description test error: {e}")
        return False, None

def test_stats_endpoint():
    """Test statistics endpoint"""
    print("\n📊 Testing Statistics Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/stats", timeout=30)
        if response.status_code == 200:
            stats = response.json()
            print("✅ Statistics endpoint working")
            print(f"   🏛️ Total municipalities: {stats.get('total_municipalities', 0)}")
            print(f"   🏠 Total properties: {stats.get('total_properties', 0)}")
            print(f"   📅 Scraped today: {stats.get('scraped_today', 0)}")
            print(f"   🕒 Last scrape: {stats.get('last_scrape', 'never')}")
            
            # Verify we have reasonable numbers
            if stats.get('total_municipalities', 0) > 0 and stats.get('total_properties', 0) > 0:
                print("✅ Statistics show expected data")
                return True, stats
            else:
                print("⚠️ Statistics show no data - may indicate scraping issues")
                return False, stats
        else:
            print(f"❌ Statistics endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Statistics endpoint error: {e}")
        return False, None

def test_map_data_endpoint():
    """Test map data endpoint for Halifax properties"""
    print("\n🗺️ Testing Map Data Endpoint...")
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales/map-data", timeout=30)
        if response.status_code == 200:
            map_data = response.json()
            print(f"✅ Map data endpoint working - Found {len(map_data)} properties with coordinates")
            
            # Check for Halifax properties with coordinates
            halifax_map_data = [p for p in map_data if "Halifax" in p.get("municipality", "")]
            print(f"   🏛️ Halifax properties with coordinates: {len(halifax_map_data)}")
            
            if halifax_map_data:
                sample_map_prop = halifax_map_data[0]
                print(f"   📍 Sample coordinates: ({sample_map_prop.get('latitude')}, {sample_map_prop.get('longitude')})")
                print("✅ Map data includes Halifax properties")
                return True, halifax_map_data
            else:
                print("⚠️ No Halifax properties found in map data")
                return False, []
        else:
            print(f"❌ Map data endpoint failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Map data endpoint error: {e}")
        return False, None

def initialize_municipalities_if_needed():
    """Initialize municipalities if database is empty"""
    print("\n🔧 Checking if municipalities need initialization...")
    try:
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        if response.status_code == 200:
            municipalities = response.json()
            if len(municipalities) == 0:
                print("   Database empty, initializing municipalities...")
                init_response = requests.post(f"{BACKEND_URL}/init-municipalities", timeout=30)
                if init_response.status_code == 200:
                    result = init_response.json()
                    print(f"✅ {result.get('message', 'Municipalities initialized')}")
                    return True
                else:
                    print(f"❌ Failed to initialize municipalities: {init_response.status_code}")
                    return False
            else:
                print(f"   Municipalities already exist ({len(municipalities)} found)")
                return True
        else:
            print(f"❌ Could not check municipalities: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Error checking municipalities: {e}")
        return False

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 Starting Comprehensive Halifax Tax Sale Scraper Tests")
    print("=" * 60)
    
    test_results = {
        "api_connection": False,
        "municipalities": False,
        "halifax_scraper": False,
        "tax_sales": False,
        "property_descriptions": False,
        "stats": False,
        "map_data": False
    }
    
    # Test 1: API Connection
    test_results["api_connection"] = test_api_connection()
    if not test_results["api_connection"]:
        print("\n❌ CRITICAL: API connection failed. Cannot proceed with other tests.")
        return test_results
    
    # Initialize municipalities if needed
    initialize_municipalities_if_needed()
    
    # Test 2: Municipalities endpoint
    municipalities_success, halifax_data = test_municipalities_endpoint()
    test_results["municipalities"] = municipalities_success
    
    # Test 3: Halifax scraper
    scraper_success, scraper_result = test_halifax_scraper()
    test_results["halifax_scraper"] = scraper_success
    
    # Test 4: Tax sales endpoint
    tax_sales_success, halifax_properties = test_tax_sales_endpoint()
    test_results["tax_sales"] = tax_sales_success
    
    # Test 5: Property descriptions bug test (CRITICAL for this review)
    descriptions_success, description_data = test_property_descriptions_bug()
    test_results["property_descriptions"] = descriptions_success
    
    # Test 6: Statistics endpoint
    stats_success, stats_data = test_stats_endpoint()
    test_results["stats"] = stats_success
    
    # Test 7: Map data endpoint
    map_success, map_data = test_map_data_endpoint()
    test_results["map_data"] = map_success
    
    # Summary
    print("\n" + "=" * 60)
    print("📋 TEST SUMMARY")
    print("=" * 60)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    # Special focus on property descriptions bug
    if not test_results["property_descriptions"]:
        print("\n🚨 CRITICAL BUG CONFIRMED: Property descriptions are not being extracted properly!")
        print("   This matches the user's report about assessment #00079006 showing placeholder text.")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Halifax scraper is working correctly!")
    elif passed_tests >= 5:  # Core functionality working
        print("⚠️ MOSTLY WORKING - Core functionality operational with minor issues")
    else:
        print("❌ MAJOR ISSUES - Halifax scraper has significant problems")
    
    return test_results

if __name__ == "__main__":
    print(f"Testing backend at: {BACKEND_URL}")
    print(f"Test started at: {datetime.now()}")
    
    results = run_comprehensive_test()
    
    # Exit with appropriate code
    passed_tests = sum(results.values())
    total_tests = len(results)
    
    if passed_tests == total_tests:
        sys.exit(0)  # All tests passed
    elif passed_tests >= 4:  # Core functionality working
        sys.exit(1)  # Minor issues
    else:
        sys.exit(2)  # Major issues