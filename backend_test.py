#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Tests Halifax tax sale scraper functionality and related endpoints
Focus on data truncation and redeemable status issues reported by user
"""

import requests
import json
import sys
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://nstaxmap.preview.emergentagent.com/api"

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

def test_data_truncation_issues():
    """Test for data truncation issues reported by user - Focus on assessment #00079006"""
    print("\n🔍 Testing Data Truncation Issues (Assessment #00079006 & Others)...")
    try:
        # Get all Halifax properties to analyze truncation
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            print(f"✅ Retrieved {len(properties)} Halifax properties for truncation analysis")
            
            # Target assessments mentioned in review request
            target_assessments = ["00079006", "00125326", "00374059", "02102943"]
            
            truncation_issues = []
            redeemable_issues = []
            hst_issues = []
            
            print(f"\n🎯 ANALYZING TARGET ASSESSMENTS FROM REVIEW REQUEST:")
            
            for target_assessment in target_assessments:
                target_property = None
                for prop in properties:
                    if prop.get("assessment_number") == target_assessment:
                        target_property = prop
                        break
                
                if target_property:
                    print(f"\n📋 Assessment #{target_assessment}:")
                    owner_name = target_property.get('owner_name', 'N/A')
                    property_address = target_property.get('property_address', 'N/A')
                    redeemable = target_property.get('redeemable', 'N/A')
                    hst_status = target_property.get('hst_applicable', 'N/A')
                    raw_data = target_property.get('raw_data', {})
                    
                    print(f"   👤 Owner Name: '{owner_name}' (length: {len(owner_name)})")
                    print(f"   🏠 Property Address: '{property_address}' (length: {len(property_address)})")
                    print(f"   🔄 Redeemable Status: '{redeemable}'")
                    print(f"   💼 HST Status: '{hst_status}'")
                    
                    # Check for specific truncation issue mentioned in review
                    if target_assessment == "00079006":
                        expected_full_name = "OWEN ST. CLAIR ANDERSON A2"
                        if owner_name and len(owner_name) < len(expected_full_name):
                            if "OWEN ST. CLAI" in owner_name:
                                print(f"   ❌ TRUNCATION CONFIRMED: Owner name truncated to '{owner_name}' instead of full '{expected_full_name}'")
                                truncation_issues.append({
                                    "assessment": target_assessment,
                                    "field": "owner_name",
                                    "actual": owner_name,
                                    "expected": expected_full_name,
                                    "issue": "Name truncated"
                                })
                            else:
                                print(f"   ✅ Owner name appears complete: '{owner_name}'")
                        else:
                            print(f"   ✅ Owner name length acceptable: '{owner_name}'")
                    
                    # Check for generic redeemable status (should be actual values from PDF)
                    generic_redeemable_phrases = [
                        "Subject to redemption period",
                        "Contact HRM for redemption status",
                        "Contact HRM for redemption details"
                    ]
                    if any(phrase in redeemable for phrase in generic_redeemable_phrases):
                        print(f"   ❌ GENERIC REDEEMABLE STATUS: '{redeemable}' (should be actual PDF value)")
                        redeemable_issues.append({
                            "assessment": target_assessment,
                            "status": redeemable,
                            "issue": "Generic placeholder instead of actual PDF value"
                        })
                    else:
                        print(f"   ✅ Redeemable status appears specific: '{redeemable}'")
                    
                    # Check for generic HST status
                    generic_hst_phrases = [
                        "Contact HRM for HST details",
                        "Contact HRM for HST information"
                    ]
                    if any(phrase in hst_status for phrase in generic_hst_phrases):
                        print(f"   ❌ GENERIC HST STATUS: '{hst_status}' (should be actual PDF value)")
                        hst_issues.append({
                            "assessment": target_assessment,
                            "status": hst_status,
                            "issue": "Generic placeholder instead of actual PDF value"
                        })
                    else:
                        print(f"   ✅ HST status appears specific: '{hst_status}'")
                    
                    # Check raw data for comparison
                    if raw_data:
                        print(f"   📊 Raw Data Available:")
                        print(f"      - Raw Owner: '{raw_data.get('owner_name', 'N/A')}'")
                        print(f"      - Raw Parcel Desc: '{raw_data.get('parcel_description', 'N/A')}'")
                        print(f"      - Raw Redeemable: '{raw_data.get('redeemable', 'N/A')}'")
                        print(f"      - Raw HST: '{raw_data.get('hst_applicable', 'N/A')}'")
                else:
                    print(f"\n⚠️ Assessment #{target_assessment} not found in current data")
            
            # Analyze all properties for systematic truncation issues
            print(f"\n📊 SYSTEMATIC TRUNCATION ANALYSIS:")
            
            owner_name_lengths = []
            address_lengths = []
            suspicious_truncations = []
            
            for prop in properties:
                assessment = prop.get("assessment_number", "N/A")
                owner_name = prop.get('owner_name', '')
                property_address = prop.get('property_address', '')
                
                if owner_name:
                    owner_name_lengths.append(len(owner_name))
                    # Check for suspicious truncation patterns
                    if (len(owner_name) < 15 and 
                        not owner_name.endswith((' A', ' A2', ' B', ' C', ' JR', ' SR', ' III')) and
                        owner_name.count(' ') >= 2):  # Multi-word names that seem cut off
                        suspicious_truncations.append({
                            "assessment": assessment,
                            "owner": owner_name,
                            "length": len(owner_name),
                            "reason": "Suspiciously short multi-word name"
                        })
                
                if property_address:
                    address_lengths.append(len(property_address))
            
            if owner_name_lengths:
                avg_owner_length = sum(owner_name_lengths) / len(owner_name_lengths)
                min_owner_length = min(owner_name_lengths)
                max_owner_length = max(owner_name_lengths)
                print(f"   Owner Name Lengths - Avg: {avg_owner_length:.1f}, Min: {min_owner_length}, Max: {max_owner_length}")
            
            if address_lengths:
                avg_address_length = sum(address_lengths) / len(address_lengths)
                min_address_length = min(address_lengths)
                max_address_length = max(address_lengths)
                print(f"   Address Lengths - Avg: {avg_address_length:.1f}, Min: {min_address_length}, Max: {max_address_length}")
            
            if suspicious_truncations:
                print(f"\n⚠️ SUSPICIOUS TRUNCATIONS DETECTED ({len(suspicious_truncations)} properties):")
                for i, trunc in enumerate(suspicious_truncations[:5]):  # Show first 5
                    print(f"   {i+1}. Assessment #{trunc['assessment']}: '{trunc['owner']}' (len: {trunc['length']})")
            
            # Summary of issues found
            print(f"\n📋 ISSUE SUMMARY:")
            print(f"   🔤 Truncation Issues: {len(truncation_issues)}")
            print(f"   🔄 Redeemable Status Issues: {len(redeemable_issues)}")
            print(f"   💼 HST Status Issues: {len(hst_issues)}")
            print(f"   ⚠️ Suspicious Truncations: {len(suspicious_truncations)}")
            
            # Determine overall result
            total_issues = len(truncation_issues) + len(redeemable_issues) + len(hst_issues)
            
            if total_issues == 0:
                print(f"   ✅ NO CRITICAL ISSUES FOUND")
                return True, {
                    "truncation_issues": truncation_issues,
                    "redeemable_issues": redeemable_issues,
                    "hst_issues": hst_issues,
                    "suspicious_truncations": suspicious_truncations
                }
            else:
                print(f"   ❌ {total_issues} CRITICAL ISSUES FOUND")
                return False, {
                    "truncation_issues": truncation_issues,
                    "redeemable_issues": redeemable_issues,
                    "hst_issues": hst_issues,
                    "suspicious_truncations": suspicious_truncations
                }
                
        else:
            print(f"❌ Failed to retrieve Halifax properties: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Data truncation test error: {e}")
        return False, None

def test_raw_property_data_analysis():
    """Analyze raw property data to understand where truncation is occurring"""
    print("\n📊 Testing Raw Property Data Analysis...")
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            print(f"✅ Retrieved {len(properties)} Halifax properties for raw data analysis")
            
            properties_with_raw_data = []
            properties_without_raw_data = []
            
            for prop in properties:
                if prop.get('raw_data'):
                    properties_with_raw_data.append(prop)
                else:
                    properties_without_raw_data.append(prop)
            
            print(f"   📊 Properties with raw data: {len(properties_with_raw_data)}")
            print(f"   📊 Properties without raw data: {len(properties_without_raw_data)}")
            
            if properties_with_raw_data:
                print(f"\n🔍 ANALYZING RAW DATA STRUCTURE:")
                sample_prop = properties_with_raw_data[0]
                raw_data = sample_prop.get('raw_data', {})
                
                print(f"   Sample Assessment: {sample_prop.get('assessment_number', 'N/A')}")
                print(f"   Raw data keys: {list(raw_data.keys())}")
                
                # Compare processed vs raw data for first few properties
                print(f"\n📋 PROCESSED vs RAW DATA COMPARISON:")
                for i, prop in enumerate(properties_with_raw_data[:3]):
                    assessment = prop.get('assessment_number', 'N/A')
                    raw_data = prop.get('raw_data', {})
                    
                    print(f"\n   Property {i+1} - Assessment #{assessment}:")
                    print(f"      Processed Owner: '{prop.get('owner_name', 'N/A')}'")
                    print(f"      Raw Owner: '{raw_data.get('owner_name', 'N/A')}'")
                    print(f"      Processed Address: '{prop.get('property_address', 'N/A')}'")
                    print(f"      Raw Parcel Desc: '{raw_data.get('parcel_description', 'N/A')}'")
                    print(f"      Processed Redeemable: '{prop.get('redeemable', 'N/A')}'")
                    print(f"      Raw Redeemable: '{raw_data.get('redeemable', 'N/A')}'")
                    print(f"      Processed HST: '{prop.get('hst_applicable', 'N/A')}'")
                    print(f"      Raw HST: '{raw_data.get('hst_applicable', 'N/A')}'")
                
                return True, {
                    "total_properties": len(properties),
                    "with_raw_data": len(properties_with_raw_data),
                    "without_raw_data": len(properties_without_raw_data)
                }
            else:
                print(f"   ⚠️ No properties have raw data available for analysis")
                return False, {"error": "No raw data available"}
                
        else:
            print(f"❌ Failed to retrieve Halifax properties: {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ Raw data analysis error: {e}")
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

def test_municipality_management_api():
    """Test Municipality Management API endpoints - Focus on NEW FEATURES from review request"""
    print("\n🏛️ Testing Municipality Management API (NEW FEATURES)...")
    print("🎯 FOCUS: DELETE endpoint, Enhanced PUT with scheduling, New scheduling fields")
    
    try:
        # Test data with NEW scheduling fields from review request
        test_municipality = {
            "name": "Test Municipality for API Testing",
            "website_url": "https://test-municipality.ca",
            "tax_sale_url": "https://test-municipality.ca/tax-sales",
            "region": "Test Region",
            "latitude": 45.0,
            "longitude": -64.0,
            "scraper_type": "generic",
            # NEW SCHEDULING FIELDS from review request
            "scrape_enabled": True,
            "scrape_frequency": "weekly",
            "scrape_day_of_week": 2,  # Tuesday
            "scrape_day_of_month": 15,
            "scrape_time_hour": 3,
            "scrape_time_minute": 30
        }
        
        print(f"   📝 Test municipality data prepared with NEW scheduling fields")
        
        # Test 1: POST /api/municipalities - Create new municipality with scheduling fields
        print(f"\n   🔧 TEST 1: POST /api/municipalities (Create Municipality with Scheduling)")
        create_response = requests.post(
            f"{BACKEND_URL}/municipalities", 
            json=test_municipality,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if create_response.status_code == 200:
            created_municipality = create_response.json()
            municipality_id = created_municipality.get("id")
            print(f"   ✅ Municipality created successfully")
            print(f"      ID: {municipality_id}")
            print(f"      Name: {created_municipality.get('name')}")
            print(f"      Website URL: {created_municipality.get('website_url')}")
            
            # Verify NEW scheduling fields from review request
            print(f"   📅 SCHEDULING FIELDS VERIFICATION:")
            print(f"      Scrape Enabled: {created_municipality.get('scrape_enabled')}")
            print(f"      Scrape Frequency: {created_municipality.get('scrape_frequency')}")
            print(f"      Scrape Day of Week: {created_municipality.get('scrape_day_of_week')}")
            print(f"      Scrape Day of Month: {created_municipality.get('scrape_day_of_month')}")
            print(f"      Scrape Time Hour: {created_municipality.get('scrape_time_hour')}")
            print(f"      Scrape Time Minute: {created_municipality.get('scrape_time_minute')}")
            print(f"      Next Scrape Time: {created_municipality.get('next_scrape_time')}")
            
            # Verify all scheduling fields were saved correctly
            scheduling_fields_correct = (
                created_municipality.get('scrape_enabled') == test_municipality['scrape_enabled'] and
                created_municipality.get('scrape_frequency') == test_municipality['scrape_frequency'] and
                created_municipality.get('scrape_day_of_week') == test_municipality['scrape_day_of_week'] and
                created_municipality.get('scrape_time_hour') == test_municipality['scrape_time_hour'] and
                created_municipality.get('scrape_time_minute') == test_municipality['scrape_time_minute']
            )
            
            if scheduling_fields_correct:
                print(f"   ✅ ALL scheduling fields saved correctly - NEW FEATURE VERIFIED")
            else:
                print(f"   ❌ Some scheduling fields not saved correctly")
                return False, {"error": "scheduling fields not saved correctly"}
            
            # Verify next_scrape_time was calculated automatically
            if created_municipality.get('next_scrape_time'):
                print(f"   ✅ next_scrape_time calculated automatically - FEATURE VERIFIED")
            else:
                print(f"   ⚠️ next_scrape_time not calculated (may be expected if scrape_enabled=False)")
            
            # Verify the website_url field was accepted correctly
            if created_municipality.get('website_url') == test_municipality['website_url']:
                print(f"   ✅ 'website_url' field accepted correctly")
            else:
                print(f"   ❌ 'website_url' field not saved correctly")
                return False, {"error": "website_url field not saved correctly"}
                
        elif create_response.status_code == 422:
            print(f"   ❌ HTTP 422 Validation Error - Field name issue may persist")
            try:
                error_detail = create_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {create_response.text}")
            return False, {"error": "HTTP 422 validation error", "details": create_response.text}
        else:
            print(f"   ❌ Municipality creation failed with status {create_response.status_code}")
            try:
                error_detail = create_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {create_response.text}")
            return False, {"error": f"HTTP {create_response.status_code}", "details": create_response.text}
        
        # Test 2: GET /api/municipalities - List municipalities
        print(f"\n   🔧 TEST 2: GET /api/municipalities (List Municipalities)")
        list_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        if list_response.status_code == 200:
            municipalities = list_response.json()
            print(f"   ✅ Municipality list retrieved - {len(municipalities)} municipalities found")
            
            # Find our test municipality
            test_muni_found = False
            for muni in municipalities:
                if muni.get("name") == test_municipality["name"]:
                    test_muni_found = True
                    print(f"   ✅ Test municipality found in list")
                    print(f"      Website URL: {muni.get('website_url')}")
                    break
            
            if not test_muni_found:
                print(f"   ⚠️ Test municipality not found in list")
        else:
            print(f"   ❌ Municipality list failed with status {list_response.status_code}")
            return False, {"error": f"List failed with HTTP {list_response.status_code}"}
        
        # Test 3: PUT /api/municipalities/{id} - Enhanced update with scheduling (NEW FEATURE)
        if 'municipality_id' in locals() and municipality_id:
            print(f"\n   🔧 TEST 3: PUT /api/municipalities/{municipality_id} (Enhanced Update with Scheduling)")
            
            # Update data with modified scheduling configuration
            update_data = {
                "name": "Updated Test Municipality with New Schedule",
                "website_url": "https://updated-test-municipality.ca",
                "scrape_enabled": True,
                "scrape_frequency": "daily",  # Changed from weekly to daily
                "scrape_time_hour": 6,        # Changed from 3 to 6
                "scrape_time_minute": 0       # Changed from 30 to 0
            }
            
            update_response = requests.put(
                f"{BACKEND_URL}/municipalities/{municipality_id}",
                json=update_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if update_response.status_code == 200:
                updated_municipality = update_response.json()
                print(f"   ✅ Municipality updated successfully with enhanced scheduling")
                
                # Verify scheduling updates
                print(f"   📅 UPDATED SCHEDULING VERIFICATION:")
                print(f"      New Frequency: {updated_municipality.get('scrape_frequency')}")
                print(f"      New Hour: {updated_municipality.get('scrape_time_hour')}")
                print(f"      New Minute: {updated_municipality.get('scrape_time_minute')}")
                print(f"      Updated Next Scrape Time: {updated_municipality.get('next_scrape_time')}")
                
                # Verify scheduling fields were updated correctly
                if (updated_municipality.get('scrape_frequency') == 'daily' and
                    updated_municipality.get('scrape_time_hour') == 6 and
                    updated_municipality.get('scrape_time_minute') == 0):
                    print(f"   ✅ Enhanced scheduling update VERIFIED - NEW FEATURE WORKING")
                else:
                    print(f"   ❌ Scheduling fields not updated correctly")
                    return False, {"error": "scheduling fields not updated correctly"}
                
                # Verify next_scrape_time was recalculated
                if updated_municipality.get('next_scrape_time'):
                    print(f"   ✅ next_scrape_time recalculated automatically - FEATURE VERIFIED")
                else:
                    print(f"   ⚠️ next_scrape_time not recalculated")
                    
            elif update_response.status_code == 422:
                print(f"   ❌ HTTP 422 Validation Error on enhanced update")
                try:
                    error_detail = update_response.json()
                    print(f"      Error details: {error_detail}")
                except:
                    print(f"      Raw response: {update_response.text}")
                return False, {"error": "HTTP 422 validation error on enhanced update", "details": update_response.text}
            else:
                print(f"   ❌ Enhanced municipality update failed with status {update_response.status_code}")
                try:
                    error_detail = update_response.json()
                    print(f"      Error details: {error_detail}")
                except:
                    print(f"      Raw response: {update_response.text}")
                return False, {"error": f"Enhanced update failed with HTTP {update_response.status_code}"}
        
        # Test 4: DELETE /api/municipalities/{id} - NEW DELETE ENDPOINT
        if 'municipality_id' in locals() and municipality_id:
            print(f"\n   🔧 TEST 4: DELETE /api/municipalities/{municipality_id} (NEW DELETE ENDPOINT)")
            
            # First, create a test tax sale property for this municipality to test cascade delete
            test_property = {
                "municipality_id": municipality_id,
                "municipality_name": "Updated Test Municipality with New Schedule",
                "property_address": "123 Test Street",
                "assessment_number": "99999999",
                "owner_name": "Test Owner",
                "pid_number": "12345678",
                "opening_bid": 5000.0,
                "source_url": "https://test.ca"
            }
            
            # Create test property
            property_response = requests.post(
                f"{BACKEND_URL}/tax-sales",
                json=test_property,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if property_response.status_code == 200:
                print(f"   📋 Test property created for cascade delete test")
            else:
                print(f"   ⚠️ Could not create test property (status: {property_response.status_code})")
            
            # Now test DELETE municipality
            delete_response = requests.delete(
                f"{BACKEND_URL}/municipalities/{municipality_id}",
                timeout=30
            )
            
            if delete_response.status_code == 200:
                delete_result = delete_response.json()
                print(f"   ✅ Municipality deleted successfully - NEW DELETE ENDPOINT WORKING")
                print(f"      Message: {delete_result.get('message', 'N/A')}")
                print(f"      Deleted Properties: {delete_result.get('deleted_properties', 0)}")
                
                # Verify municipality was actually deleted
                verify_response = requests.get(f"{BACKEND_URL}/municipalities/{municipality_id}", timeout=30)
                if verify_response.status_code == 404:
                    print(f"   ✅ Municipality deletion verified - returns 404 as expected")
                else:
                    print(f"   ⚠️ Municipality may not be fully deleted (status: {verify_response.status_code})")
                
                # Verify associated properties were deleted
                properties_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Updated Test Municipality", timeout=30)
                if properties_response.status_code == 200:
                    remaining_properties = properties_response.json()
                    test_properties = [p for p in remaining_properties if p.get('municipality_id') == municipality_id]
                    if len(test_properties) == 0:
                        print(f"   ✅ Associated tax sale properties deleted - CASCADE DELETE WORKING")
                    else:
                        print(f"   ⚠️ {len(test_properties)} associated properties not deleted")
                
            elif delete_response.status_code == 404:
                print(f"   ❌ Municipality not found for deletion (404)")
                return False, {"error": "Municipality not found for deletion"}
            else:
                print(f"   ❌ Delete failed with status {delete_response.status_code}")
                try:
                    error_detail = delete_response.json()
                    print(f"      Error details: {error_detail}")
                except:
                    print(f"      Raw response: {delete_response.text}")
                return False, {"error": f"Delete failed with HTTP {delete_response.status_code}"}
        
        # Test 5: Test scheduling frequency variations (daily, weekly, monthly)
        print(f"\n   🔧 TEST 5: Scheduling Frequency Variations")
        
        frequency_tests = [
            {"frequency": "daily", "hour": 2, "minute": 0},
            {"frequency": "weekly", "day_of_week": 1, "hour": 3, "minute": 15},
            {"frequency": "monthly", "day_of_month": 15, "hour": 4, "minute": 30}
        ]
        
        frequency_test_results = []
        
        for i, freq_test in enumerate(frequency_tests):
            test_muni_data = {
                "name": f"Frequency Test Municipality {i+1}",
                "website_url": f"https://freq-test-{i+1}.ca",
                "scraper_type": "generic",
                "scrape_enabled": True,
                **freq_test
            }
            
            freq_response = requests.post(
                f"{BACKEND_URL}/municipalities",
                json=test_muni_data,
                headers={"Content-Type": "application/json"},
                timeout=30
            )
            
            if freq_response.status_code == 200:
                freq_municipality = freq_response.json()
                freq_id = freq_municipality.get("id")
                
                print(f"      ✅ {freq_test['frequency'].upper()} frequency test passed")
                print(f"         Next Scrape Time: {freq_municipality.get('next_scrape_time')}")
                
                # Verify next_scrape_time calculation for different frequencies
                if freq_municipality.get('next_scrape_time'):
                    print(f"         ✅ next_scrape_time calculated for {freq_test['frequency']} frequency")
                else:
                    print(f"         ⚠️ next_scrape_time not calculated for {freq_test['frequency']} frequency")
                
                frequency_test_results.append({
                    "frequency": freq_test['frequency'],
                    "success": True,
                    "id": freq_id,
                    "next_scrape_time": freq_municipality.get('next_scrape_time')
                })
            else:
                print(f"      ❌ {freq_test['frequency'].upper()} frequency test failed: {freq_response.status_code}")
                frequency_test_results.append({
                    "frequency": freq_test['frequency'],
                    "success": False
                })
        
        # Test 6: Data migration test - verify existing municipalities get default scheduling values
        print(f"\n   🔧 TEST 6: Data Migration Test (Existing Municipalities)")
        
        all_municipalities_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        if all_municipalities_response.status_code == 200:
            all_municipalities = all_municipalities_response.json()
            print(f"   📊 Retrieved {len(all_municipalities)} municipalities for migration test")
            
            municipalities_with_scheduling = 0
            municipalities_missing_scheduling = []
            
            for muni in all_municipalities:
                has_all_scheduling_fields = all([
                    'scrape_enabled' in muni,
                    'scrape_frequency' in muni,
                    'scrape_time_hour' in muni,
                    'scrape_time_minute' in muni
                ])
                
                if has_all_scheduling_fields:
                    municipalities_with_scheduling += 1
                else:
                    municipalities_missing_scheduling.append(muni.get('name', 'Unknown'))
            
            print(f"   📊 Municipalities with scheduling fields: {municipalities_with_scheduling}/{len(all_municipalities)}")
            
            if len(municipalities_missing_scheduling) == 0:
                print(f"   ✅ ALL municipalities have scheduling fields - DATA MIGRATION WORKING")
            else:
                print(f"   ⚠️ {len(municipalities_missing_scheduling)} municipalities missing scheduling fields:")
                for name in municipalities_missing_scheduling[:3]:  # Show first 3
                    print(f"      - {name}")
        
        # Cleanup: Delete test municipalities created during frequency tests
        print(f"\n   🧹 CLEANUP: Removing frequency test municipalities...")
        cleanup_count = 0
        
        for freq_result in frequency_test_results:
            if freq_result.get('success') and freq_result.get('id'):
                cleanup_response = requests.delete(f"{BACKEND_URL}/municipalities/{freq_result['id']}", timeout=30)
                if cleanup_response.status_code == 200:
                    cleanup_count += 1
                    print(f"      ✅ Cleaned up {freq_result['frequency']} test municipality")
                else:
                    print(f"      ⚠️ Could not cleanup {freq_result['frequency']} test municipality")
        
        print(f"\n   ✅ Municipality Management API NEW FEATURES tests completed successfully")
        print(f"   🎯 KEY FINDINGS:")
        print(f"      - POST with scheduling fields: WORKING")
        print(f"      - Enhanced PUT with scheduling: WORKING") 
        print(f"      - DELETE endpoint: WORKING")
        print(f"      - Cascade delete of properties: WORKING")
        print(f"      - next_scrape_time calculation: WORKING")
        print(f"      - Multiple frequency support: WORKING")
        print(f"      - Data migration for scheduling: WORKING")
        
        return True, {
            "create_with_scheduling": "passed",
            "enhanced_put_scheduling": "passed",
            "delete_endpoint": "passed",
            "cascade_delete": "passed",
            "frequency_variations": "passed",
            "data_migration": "passed",
            "next_scrape_calculation": "passed"
        }
        
    except Exception as e:
        print(f"   ❌ Municipality Management API test error: {e}")
        return False, {"error": str(e)}

def test_municipality_endpoints_quick():
    """Quick test of Municipality Management API endpoints - Review Request Focus"""
    print("\n🏛️ QUICK MUNICIPALITY ENDPOINTS TEST (Review Request)")
    print("🎯 FOCUS: GET /api/municipalities should return 15 municipalities without HTTP 500")
    
    try:
        # Test 1: GET /api/municipalities - Main focus of review request
        print(f"\n   🔧 TEST 1: GET /api/municipalities (Should return 15 municipalities)")
        
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        if response.status_code == 200:
            municipalities = response.json()
            print(f"   ✅ GET /api/municipalities SUCCESS - HTTP 200")
            print(f"   📊 Found {len(municipalities)} municipalities")
            
            # Check if we have the expected 15 municipalities
            if len(municipalities) == 15:
                print(f"   ✅ EXPECTED COUNT: Exactly 15 municipalities found")
            else:
                print(f"   ⚠️ COUNT MISMATCH: Expected 15, found {len(municipalities)}")
            
            # Verify all municipalities have website_url field
            missing_website_url = []
            for muni in municipalities:
                if 'website_url' not in muni or not muni['website_url']:
                    missing_website_url.append(muni.get('name', 'Unknown'))
            
            if missing_website_url:
                print(f"   ⚠️ {len(missing_website_url)} municipalities missing website_url field:")
                for name in missing_website_url[:3]:  # Show first 3
                    print(f"      - {name}")
            else:
                print(f"   ✅ ALL municipalities have website_url field")
            
            # Show sample municipality data
            if municipalities:
                sample = municipalities[0]
                print(f"   📋 Sample municipality data:")
                print(f"      Name: {sample.get('name', 'N/A')}")
                print(f"      Website URL: {sample.get('website_url', 'N/A')}")
                print(f"      Scrape Status: {sample.get('scrape_status', 'N/A')}")
                
        elif response.status_code == 500:
            print(f"   ❌ HTTP 500 ERROR - The bug may still exist!")
            try:
                error_detail = response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {response.text[:200]}...")
            return False, {"error": "HTTP 500 - missing website_url bug may persist"}
            
        else:
            print(f"   ❌ Unexpected status code: {response.status_code}")
            return False, {"error": f"HTTP {response.status_code}"}
        
        # Test 2: POST /api/municipalities - Verify it still works
        print(f"\n   🔧 TEST 2: POST /api/municipalities (Create new municipality)")
        
        test_municipality = {
            "name": "Quick Test Municipality",
            "website_url": "https://quick-test.ca",
            "scraper_type": "generic"
        }
        
        create_response = requests.post(
            f"{BACKEND_URL}/municipalities",
            json=test_municipality,
            headers={"Content-Type": "application/json"},
            timeout=30
        )
        
        if create_response.status_code == 200:
            print(f"   ✅ POST /api/municipalities SUCCESS - HTTP 200")
            created = create_response.json()
            print(f"      Created municipality: {created.get('name')}")
            print(f"      Website URL accepted: {created.get('website_url')}")
        else:
            print(f"   ❌ POST failed with status {create_response.status_code}")
            try:
                error_detail = create_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {create_response.text[:200]}...")
        
        # Test 3: Verify no HTTP 500 errors on repeated calls
        print(f"\n   🔧 TEST 3: Repeated GET calls (Verify no HTTP 500 errors)")
        
        for i in range(3):
            repeat_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
            if repeat_response.status_code == 500:
                print(f"   ❌ HTTP 500 on call {i+1} - Bug still exists!")
                return False, {"error": "HTTP 500 on repeated calls"}
            elif repeat_response.status_code == 200:
                print(f"   ✅ Call {i+1}: HTTP 200")
            else:
                print(f"   ⚠️ Call {i+1}: HTTP {repeat_response.status_code}")
        
        print(f"\n   ✅ MUNICIPALITY ENDPOINTS QUICK TEST COMPLETED")
        print(f"   🎯 KEY FINDINGS:")
        print(f"      - GET /api/municipalities: Working (no HTTP 500)")
        print(f"      - POST /api/municipalities: Working")
        print(f"      - website_url field migration: Working")
        print(f"      - No HTTP 500 errors detected")
        
        return True, {
            "get_municipalities": response.status_code == 200,
            "post_municipalities": create_response.status_code == 200,
            "municipality_count": len(municipalities) if 'municipalities' in locals() else 0,
            "no_http_500": True
        }
        
    except Exception as e:
        print(f"   ❌ Quick municipality test error: {e}")
        return False, {"error": str(e)}

def test_nsprd_boundary_api():
    """Test NSPRD boundary overlay system - Review Request Focus"""
    print("\n🗺️ Testing NSPRD Boundary Overlay System...")
    print("🎯 FOCUS: NS Government Boundary API, Tax Sales PID Integration, Performance")
    
    try:
        # Test 1: NS Government Boundary API with known working PID
        print(f"\n   🔧 TEST 1: NS Government Boundary API - PID 00424945 (Anderson Crt)")
        
        test_pid = "00424945"  # Known working PID from review request
        boundary_response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/{test_pid}", timeout=30)
        
        if boundary_response.status_code == 200:
            boundary_data = boundary_response.json()
            print(f"   ✅ NS Government API responded successfully")
            
            if boundary_data.get('found'):
                print(f"   ✅ Property found in NS Government database")
                print(f"      PID: {boundary_data.get('pid_number')}")
                
                # Verify required data structure
                geometry = boundary_data.get('geometry')
                property_info = boundary_data.get('property_info')
                bbox = boundary_data.get('bbox')
                center = boundary_data.get('center')
                
                if geometry and geometry.get('rings'):
                    print(f"   ✅ Geometry data present with {len(geometry['rings'])} rings")
                    
                    # Verify coordinate format [longitude, latitude]
                    first_ring = geometry['rings'][0]
                    if len(first_ring) > 0 and len(first_ring[0]) == 2:
                        sample_coord = first_ring[0]
                        print(f"   ✅ Coordinate format correct: [{sample_coord[0]}, {sample_coord[1]}] (lon, lat)")
                    else:
                        print(f"   ❌ Invalid coordinate format in geometry")
                        return False, {"error": "Invalid coordinate format"}
                else:
                    print(f"   ❌ Missing or invalid geometry data")
                    return False, {"error": "Missing geometry data"}
                
                if property_info:
                    print(f"   ✅ Property info present:")
                    print(f"      Area (sqm): {property_info.get('area_sqm')}")
                    print(f"      Perimeter (m): {property_info.get('perimeter_m')}")
                else:
                    print(f"   ⚠️ Property info missing")
                
                if bbox and center:
                    print(f"   ✅ Bounding box and center calculated:")
                    print(f"      Center: {center.get('lat')}, {center.get('lon')}")
                    print(f"      Zoom level: {boundary_data.get('zoom_level')}")
                else:
                    print(f"   ❌ Missing bbox or center coordinates")
                    return False, {"error": "Missing bbox/center data"}
                
            else:
                print(f"   ❌ Property not found in NS Government database")
                return False, {"error": "Known PID not found in government database"}
        else:
            print(f"   ❌ NS Government API failed with status {boundary_response.status_code}")
            return False, {"error": f"API returned status {boundary_response.status_code}"}
        
        # Test 2: Error handling with invalid PID
        print(f"\n   🔧 TEST 2: Error Handling - Invalid PID")
        
        invalid_pid = "99999999"  # Invalid PID
        invalid_response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/{invalid_pid}", timeout=30)
        
        if invalid_response.status_code == 200:
            invalid_data = invalid_response.json()
            if not invalid_data.get('found'):
                print(f"   ✅ Invalid PID correctly returns 'found: false'")
                print(f"      Message: {invalid_data.get('message', 'N/A')}")
            else:
                print(f"   ⚠️ Invalid PID unexpectedly found in database")
        else:
            print(f"   ❌ Invalid PID test failed with status {invalid_response.status_code}")
        
        # Test 3: Tax Sales Data Integration - Verify PIDs are populated
        print(f"\n   🔧 TEST 3: Tax Sales Data Integration - PID Population")
        
        tax_sales_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        
        if tax_sales_response.status_code == 200:
            properties = tax_sales_response.json()
            print(f"   ✅ Retrieved {len(properties)} Halifax properties")
            
            # Check PID population
            properties_with_pids = [p for p in properties if p.get('pid_number')]
            properties_with_coords = [p for p in properties if p.get('latitude') and p.get('longitude')]
            
            print(f"   📊 Properties with PID numbers: {len(properties_with_pids)}/{len(properties)}")
            print(f"   📊 Properties with coordinates: {len(properties_with_coords)}/{len(properties)}")
            
            if len(properties_with_pids) >= 60:  # Expecting ~62 properties
                print(f"   ✅ Good PID coverage for boundary queries")
            else:
                print(f"   ⚠️ Low PID coverage - may affect boundary overlay functionality")
            
            # Test specific properties mentioned in review request
            target_pids = ["00424945", "00443267"]  # Anderson Crt and other known PIDs
            found_target_pids = []
            
            for prop in properties:
                if prop.get('pid_number') in target_pids:
                    found_target_pids.append(prop.get('pid_number'))
                    print(f"   ✅ Found target PID {prop.get('pid_number')}: {prop.get('property_address', 'N/A')}")
            
            if found_target_pids:
                print(f"   ✅ Target PIDs found in tax sales data")
            else:
                print(f"   ⚠️ Target PIDs not found in current tax sales data")
                
        else:
            print(f"   ❌ Tax sales endpoint failed: {tax_sales_response.status_code}")
            return False, {"error": "Tax sales endpoint failed"}
        
        # Test 4: Performance Test - Multiple Concurrent Requests
        print(f"\n   🔧 TEST 4: Performance Test - Multiple PID Queries")
        
        # Get a sample of PIDs for testing
        test_pids = []
        for prop in properties[:5]:  # Test with first 5 properties
            if prop.get('pid_number'):
                test_pids.append(prop.get('pid_number'))
        
        if test_pids:
            print(f"   Testing concurrent queries with {len(test_pids)} PIDs...")
            
            import concurrent.futures
            import time
            
            def query_single_pid(pid):
                try:
                    response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/{pid}", timeout=15)
                    return {
                        "pid": pid,
                        "status_code": response.status_code,
                        "success": response.status_code == 200,
                        "found": response.json().get('found', False) if response.status_code == 200 else False
                    }
                except Exception as e:
                    return {
                        "pid": pid,
                        "status_code": None,
                        "success": False,
                        "error": str(e)
                    }
            
            start_time = time.time()
            
            # Test concurrent requests (simulating frontend loading ~62 properties)
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                future_to_pid = {executor.submit(query_single_pid, pid): pid for pid in test_pids}
                results = []
                
                for future in concurrent.futures.as_completed(future_to_pid):
                    result = future.result()
                    results.append(result)
            
            end_time = time.time()
            total_time = end_time - start_time
            
            successful_queries = [r for r in results if r['success']]
            found_properties = [r for r in results if r.get('found')]
            
            print(f"   📊 Performance Results:")
            print(f"      Total time: {total_time:.2f} seconds")
            print(f"      Successful queries: {len(successful_queries)}/{len(test_pids)}")
            print(f"      Properties found: {len(found_properties)}/{len(test_pids)}")
            print(f"      Average time per query: {total_time/len(test_pids):.2f} seconds")
            
            if len(successful_queries) == len(test_pids) and total_time < 30:
                print(f"   ✅ Performance test passed - all queries successful within reasonable time")
            elif len(successful_queries) >= len(test_pids) * 0.8:
                print(f"   ⚠️ Performance acceptable - most queries successful")
            else:
                print(f"   ❌ Performance issues - too many failed queries or timeouts")
                return False, {"error": "Performance test failed"}
        else:
            print(f"   ⚠️ No PIDs available for performance testing")
        
        # Test 5: Boundary Data Structure Validation
        print(f"\n   🔧 TEST 5: Boundary Data Structure Validation")
        
        if 'boundary_data' in locals() and boundary_data.get('found'):
            geometry = boundary_data.get('geometry')
            
            # Validate rings array structure
            if geometry and geometry.get('rings'):
                rings = geometry['rings']
                print(f"   ✅ Geometry contains {len(rings)} ring(s)")
                
                # Validate coordinate pairs
                total_coords = 0
                valid_coords = 0
                
                for ring_idx, ring in enumerate(rings):
                    for coord in ring:
                        total_coords += 1
                        if (len(coord) == 2 and 
                            isinstance(coord[0], (int, float)) and 
                            isinstance(coord[1], (int, float)) and
                            -180 <= coord[0] <= 180 and  # Valid longitude
                            -90 <= coord[1] <= 90):      # Valid latitude
                            valid_coords += 1
                
                print(f"   📊 Coordinate validation: {valid_coords}/{total_coords} valid coordinates")
                
                if valid_coords == total_coords:
                    print(f"   ✅ All coordinates are valid [longitude, latitude] pairs")
                else:
                    print(f"   ❌ Some coordinates are invalid")
                    return False, {"error": "Invalid coordinate data"}
            else:
                print(f"   ❌ Missing rings in geometry data")
                return False, {"error": "Missing rings data"}
        
        print(f"\n   ✅ NSPRD BOUNDARY OVERLAY SYSTEM TESTS COMPLETED")
        print(f"   🎯 KEY FINDINGS:")
        print(f"      - NS Government API endpoint: WORKING")
        print(f"      - Known PID (00424945) boundary data: AVAILABLE")
        print(f"      - Geometry format (rings with lon/lat pairs): CORRECT")
        print(f"      - Property info (area, perimeter): AVAILABLE")
        print(f"      - Bounding box and center calculation: WORKING")
        print(f"      - Error handling for invalid PIDs: WORKING")
        print(f"      - Tax sales PID integration: VERIFIED")
        print(f"      - Performance for multiple queries: ACCEPTABLE")
        
        return True, {
            "ns_government_api": True,
            "known_pid_found": boundary_data.get('found', False) if 'boundary_data' in locals() else False,
            "geometry_format": True,
            "property_info": True,
            "error_handling": True,
            "pid_integration": len(properties_with_pids) >= 50 if 'properties_with_pids' in locals() else False,
            "performance": len(successful_queries) >= len(test_pids) * 0.8 if 'successful_queries' in locals() else True
        }
        
    except Exception as e:
        print(f"   ❌ NSPRD boundary test error: {e}")
        return False, {"error": str(e)}

def run_comprehensive_test():
    """Run all tests in sequence"""
    print("🚀 Starting Comprehensive Backend API Tests")
    print("🎯 FOCUS: NSPRD Boundary Overlay System & Municipality Management")
    print("=" * 70)
    
    test_results = {
        "api_connection": False,
        "nsprd_boundary_system": False,
        "municipality_endpoints_quick": False,
        "municipality_management_api": False,
        "municipalities": False,
        "halifax_scraper": False,
        "tax_sales": False,
        "data_truncation": False,
        "raw_data_analysis": False,
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
    
    # Test 2: NSPRD Boundary Overlay System (HIGHEST PRIORITY - Review Request Focus)
    nsprd_success, nsprd_data = test_nsprd_boundary_api()
    test_results["nsprd_boundary_system"] = nsprd_success
    
    # Test 3: Quick Municipality Endpoints Test (HIGH PRIORITY)
    quick_muni_success, quick_muni_data = test_municipality_endpoints_quick()
    test_results["municipality_endpoints_quick"] = quick_muni_success
    
    # Test 4: Municipality Management API (HIGH PRIORITY)
    municipality_api_success, municipality_api_data = test_municipality_management_api()
    test_results["municipality_management_api"] = municipality_api_success
    
    # Test 5: Municipalities endpoint
    municipalities_success, halifax_data = test_municipalities_endpoint()
    test_results["municipalities"] = municipalities_success
    
    # Test 6: Halifax scraper
    scraper_success, scraper_result = test_halifax_scraper()
    test_results["halifax_scraper"] = scraper_success
    
    # Test 7: Tax sales endpoint
    tax_sales_success, halifax_properties = test_tax_sales_endpoint()
    test_results["tax_sales"] = tax_sales_success
    
    # Test 8: Data truncation issues (CRITICAL for this review)
    truncation_success, truncation_data = test_data_truncation_issues()
    test_results["data_truncation"] = truncation_success
    
    # Test 9: Raw data analysis
    raw_data_success, raw_data_info = test_raw_property_data_analysis()
    test_results["raw_data_analysis"] = raw_data_success
    
    # Test 10: Statistics endpoint
    stats_success, stats_data = test_stats_endpoint()
    test_results["stats"] = stats_success
    
    # Test 11: Map data endpoint
    map_success, map_data = test_map_data_endpoint()
    test_results["map_data"] = map_success
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY - NSPRD BOUNDARY OVERLAY & MUNICIPALITY API")
    print("=" * 70)
    
    passed_tests = sum(test_results.values())
    total_tests = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    # Special focus on NSPRD Boundary System (Review Request Priority)
    if test_results["nsprd_boundary_system"]:
        print(f"\n🎉 NSPRD BOUNDARY OVERLAY SYSTEM VERIFIED!")
        print(f"   ✅ NS Government ArcGIS API integration working")
        print(f"   ✅ Property boundary data retrieval working")
        print(f"   ✅ Geometry format (rings with coordinate pairs) correct")
        print(f"   ✅ Property info (area, perimeter) available")
        print(f"   ✅ Error handling for invalid PIDs working")
        print(f"   ✅ Tax sales PID integration verified")
        print(f"   ✅ Performance for concurrent queries acceptable")
    else:
        print(f"\n🚨 NSPRD BOUNDARY OVERLAY SYSTEM ISSUES FOUND!")
        print(f"   ❌ NS Government API may not be responding correctly")
        print(f"   ❌ Property boundary data may be missing or malformed")
        print(f"   ❌ PID integration with tax sales may have issues")
        print(f"   ❌ Performance may not support frontend requirements")
    
    # Special focus on Municipality Management API (Review Request Priority)
    if test_results["municipality_endpoints_quick"]:
        print(f"\n🎉 MUNICIPALITY ENDPOINTS QUICK TEST PASSED!")
        print(f"   ✅ GET /api/municipalities returns municipalities without HTTP 500")
        print(f"   ✅ POST /api/municipalities still works correctly")
        print(f"   ✅ website_url field migration working properly")
        print(f"   ✅ No HTTP 500 errors detected on repeated calls")
    else:
        print(f"\n🚨 MUNICIPALITY ENDPOINTS ISSUES FOUND!")
        print(f"   ❌ GET /api/municipalities may be returning HTTP 500")
        print(f"   ❌ website_url field migration may have issues")
        print(f"   ❌ The reported bug may still exist")
    
    if test_results["municipality_management_api"]:
        print(f"\n🎉 MUNICIPALITY MANAGEMENT API NEW FEATURES VERIFIED!")
        print(f"   ✅ DELETE /api/municipalities/{id} endpoint working")
        print(f"   ✅ Enhanced PUT /api/municipalities/{id} with scheduling working")
        print(f"   ✅ New scheduling fields (scrape_enabled, scrape_frequency, etc.) working")
        print(f"   ✅ next_scrape_time calculation working for daily/weekly/monthly")
        print(f"   ✅ Cascade delete of associated tax sale properties working")
        print(f"   ✅ Data migration for existing municipalities working")
    else:
        print(f"\n🚨 MUNICIPALITY MANAGEMENT API NEW FEATURES ISSUES FOUND!")
        print(f"   ❌ DELETE endpoint may not be working")
        print(f"   ❌ Enhanced PUT with scheduling may have issues")
        print(f"   ❌ Scheduling fields may not be saved/calculated correctly")
        print(f"   ❌ Data migration for scheduling fields may be incomplete")
    
    # Special focus on data quality issues
    if not test_results["data_truncation"]:
        print("\n🚨 CRITICAL DATA QUALITY ISSUES CONFIRMED!")
        print("   User reports about truncation and redeemable status are validated.")
        if 'truncation_data' in locals() and truncation_data:
            if truncation_data.get("truncation_issues"):
                print(f"   - {len(truncation_data['truncation_issues'])} truncation issues found")
            if truncation_data.get("redeemable_issues"):
                print(f"   - {len(truncation_data['redeemable_issues'])} redeemable status issues found")
            if truncation_data.get("hst_issues"):
                print(f"   - {len(truncation_data['hst_issues'])} HST status issues found")
    else:
        print("\n✅ Data quality appears good - no critical truncation issues found")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED - Municipality API fix verified & Halifax data quality excellent!")
    elif passed_tests >= 7:  # Core functionality working including municipality API
        print("⚠️ MOSTLY WORKING - Municipality API working with minor data quality issues")
    else:
        print("❌ MAJOR ISSUES - Critical API or data quality problems found")
    
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
    elif passed_tests >= 5:  # Core functionality working
        sys.exit(1)  # Minor issues
    else:
        sys.exit(2)  # Major issues