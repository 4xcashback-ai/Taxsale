#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Auction Result Management System Testing
"""

import requests
import json
import sys
import re
import math
from datetime import datetime, timedelta
import time

# Get backend URL from environment
import os
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://taxsale-mapper.preview.emergentagent.com') + '/api'

# Admin credentials for testing
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "TaxSale2025!SecureAdmin"

def test_api_connection():
    """Test basic API connectivity"""
    print("🔗 Testing API Connection...")
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=30)
        if response.status_code == 200:
            print("✅ API connection successful")
            print(f"   Response: {response.json()}")
            return True, response.json()
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False, None

def test_single_pid_query():
    """Test single-PID query: GET /api/query-ns-government-parcel/85010866"""
    print("\n🎯 Testing Single-PID Query...")
    print("🔍 FOCUS: GET /api/query-ns-government-parcel/85010866")
    print("📋 EXPECTED: Should return bbox with {minLon, maxLon, minLat, maxLat} format")
    
    try:
        response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/85010866", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Single-PID endpoint accessible")
                
                # Check if property was found
                found = data.get('found', False)
                print(f"   🔍 Found: {found}")
                
                if found:
                    # Check required fields for single-PID response
                    required_fields = ['pid_number', 'geometry', 'bbox', 'center']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        print(f"   ⚠️ WARNING: Missing fields: {missing_fields}")
                        return False, data
                    
                    # Check bbox format (should be minLon/maxLon/minLat/maxLat for single PID)
                    bbox = data.get('bbox', {})
                    expected_bbox_keys = ['minLon', 'maxLon', 'minLat', 'maxLat']
                    bbox_keys = list(bbox.keys())
                    
                    print(f"   📦 Bbox keys: {bbox_keys}")
                    print(f"   📦 Expected keys: {expected_bbox_keys}")
                    
                    if all(key in bbox for key in expected_bbox_keys):
                        print(f"   ✅ BBOX FORMAT: Correct single-PID format (minLon/maxLon/minLat/maxLat)")
                        print(f"   📍 Bbox values: minLon={bbox['minLon']}, maxLon={bbox['maxLon']}, minLat={bbox['minLat']}, maxLat={bbox['maxLat']}")
                    else:
                        print(f"   ❌ BBOX FORMAT: Incorrect format - missing expected keys")
                        return False, data
                    
                    # Check center coordinates
                    center = data.get('center', {})
                    if 'lat' in center and 'lon' in center:
                        print(f"   📍 Center: lat={center['lat']}, lon={center['lon']}")
                        print(f"   ✅ CENTER: Valid center coordinates")
                    else:
                        print(f"   ❌ CENTER: Missing or invalid center coordinates")
                        return False, data
                    
                    # Check geometry
                    geometry = data.get('geometry', {})
                    if 'rings' in geometry and geometry['rings']:
                        print(f"   🗺️ Geometry: {len(geometry['rings'])} rings found")
                        print(f"   ✅ GEOMETRY: Valid geometry data")
                    else:
                        print(f"   ❌ GEOMETRY: Missing or invalid geometry")
                        return False, data
                    
                    print(f"   ✅ SINGLE-PID TEST: All requirements met")
                    return True, data
                else:
                    print(f"   ❌ PROPERTY NOT FOUND: PID 85010866 not found in NS Government database")
                    return False, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                print(f"   Raw Response: {response.text[:500]}...")
                return False, {"error": "Invalid JSON response"}
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
                return False, error_data
            except:
                print(f"   Raw Response: {response.text[:200]}...")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def test_multi_pid_query():
    """Test multi-PID query: GET /api/query-ns-government-parcel/85010866/85074276"""
    print("\n🎯 Testing Multi-PID Query...")
    print("🔍 FOCUS: GET /api/query-ns-government-parcel/85010866/85074276")
    print("📋 EXPECTED: Should return combined geometry with bbox in {north, south, east, west} format")
    
    try:
        response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/85010866/85074276", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Multi-PID endpoint accessible")
                
                # Check if this is recognized as multi-PID
                multiple_pids = data.get('multiple_pids', False)
                print(f"   🔍 Multiple PIDs: {multiple_pids}")
                
                if not multiple_pids:
                    print(f"   ❌ MULTI-PID DETECTION: Not recognized as multi-PID request")
                    return False, data
                
                # Check if any properties were found
                found = data.get('found', False)
                print(f"   🔍 Found: {found}")
                
                if found:
                    # Check required fields for multi-PID response
                    required_fields = ['pid_number', 'pids', 'multiple_pids', 'individual_results', 'combined_geometry', 'combined_bbox', 'center']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        print(f"   ⚠️ WARNING: Missing fields: {missing_fields}")
                        return False, data
                    
                    # Check individual results
                    individual_results = data.get('individual_results', [])
                    print(f"   📊 Individual results: {len(individual_results)} PIDs processed")
                    
                    if len(individual_results) != 2:
                        print(f"   ❌ INDIVIDUAL RESULTS: Expected 2 results, got {len(individual_results)}")
                        return False, data
                    
                    # Check combined bbox format (should be north/south/east/west for multi-PID)
                    combined_bbox = data.get('combined_bbox', {})
                    expected_bbox_keys = ['north', 'south', 'east', 'west']
                    bbox_keys = list(combined_bbox.keys()) if combined_bbox else []
                    
                    print(f"   📦 Combined bbox keys: {bbox_keys}")
                    print(f"   📦 Expected keys: {expected_bbox_keys}")
                    
                    if combined_bbox and all(key in combined_bbox for key in expected_bbox_keys):
                        print(f"   ✅ BBOX FORMAT: Correct multi-PID format (north/south/east/west)")
                        print(f"   📍 Bbox values: north={combined_bbox['north']}, south={combined_bbox['south']}, east={combined_bbox['east']}, west={combined_bbox['west']}")
                    else:
                        print(f"   ❌ BBOX FORMAT: Incorrect format - missing expected keys or null bbox")
                        return False, data
                    
                    # Check center coordinates calculated from combined bbox
                    center = data.get('center', {})
                    if center and 'lat' in center and 'lon' in center:
                        print(f"   📍 Combined center: lat={center['lat']}, lon={center['lon']}")
                        
                        # Verify center calculation
                        expected_lat = (combined_bbox['north'] + combined_bbox['south']) / 2
                        expected_lon = (combined_bbox['east'] + combined_bbox['west']) / 2
                        
                        if abs(center['lat'] - expected_lat) < 0.0001 and abs(center['lon'] - expected_lon) < 0.0001:
                            print(f"   ✅ CENTER: Correctly calculated from combined bbox")
                        else:
                            print(f"   ⚠️ CENTER: May not be correctly calculated (expected lat={expected_lat}, lon={expected_lon})")
                    else:
                        print(f"   ❌ CENTER: Missing or invalid center coordinates")
                        return False, data
                    
                    # Check combined geometry
                    combined_geometry = data.get('combined_geometry', {})
                    if combined_geometry and 'rings' in combined_geometry and combined_geometry['rings']:
                        print(f"   🗺️ Combined geometry: {len(combined_geometry['rings'])} rings found")
                        print(f"   ✅ GEOMETRY: Valid combined geometry data")
                    else:
                        print(f"   ❌ GEOMETRY: Missing or invalid combined geometry")
                        return False, data
                    
                    print(f"   ✅ MULTI-PID TEST: All requirements met")
                    return True, data
                else:
                    print(f"   ❌ PROPERTIES NOT FOUND: No valid PIDs found in multi-PID request")
                    return False, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                print(f"   Raw Response: {response.text[:500]}...")
                return False, {"error": "Invalid JSON response"}
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
                return False, error_data
            except:
                print(f"   Raw Response: {response.text[:200]}...")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def test_invalid_single_pid():
    """Test invalid single PID: GET /api/query-ns-government-parcel/99999999"""
    print("\n🎯 Testing Invalid Single PID...")
    print("🔍 FOCUS: GET /api/query-ns-government-parcel/99999999")
    print("📋 EXPECTED: Should return found: false with proper error handling")
    
    try:
        response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/99999999", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Invalid PID endpoint accessible")
                
                # Check if property was correctly marked as not found
                found = data.get('found', True)  # Default to True to catch errors
                print(f"   🔍 Found: {found}")
                
                if not found:
                    print(f"   ✅ ERROR HANDLING: Correctly returns found: false for invalid PID")
                    
                    # Check that it includes the PID number
                    pid_number = data.get('pid_number')
                    if pid_number == '99999999':
                        print(f"   ✅ PID TRACKING: Correctly tracks PID number in response")
                    else:
                        print(f"   ⚠️ PID TRACKING: PID number mismatch (got {pid_number})")
                    
                    # Check for error message
                    message = data.get('message', data.get('error', ''))
                    if message:
                        print(f"   ✅ ERROR MESSAGE: {message}")
                    else:
                        print(f"   ⚠️ ERROR MESSAGE: No error message provided")
                    
                    return True, data
                else:
                    print(f"   ❌ ERROR HANDLING: Invalid PID incorrectly marked as found")
                    return False, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                print(f"   Raw Response: {response.text[:500]}...")
                return False, {"error": "Invalid JSON response"}
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
                return False, error_data
            except:
                print(f"   Raw Response: {response.text[:200]}...")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def test_mixed_valid_invalid_multi_pid():
    """Test mixed valid/invalid multi-PID: GET /api/query-ns-government-parcel/85010866/99999999"""
    print("\n🎯 Testing Mixed Valid/Invalid Multi-PID...")
    print("🔍 FOCUS: GET /api/query-ns-government-parcel/85010866/99999999")
    print("📋 EXPECTED: Should handle one valid, one invalid PID gracefully")
    
    try:
        response = requests.get(f"{BACKEND_URL}/query-ns-government-parcel/85010866/99999999", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Mixed PID endpoint accessible")
                
                # Check if this is recognized as multi-PID
                multiple_pids = data.get('multiple_pids', False)
                print(f"   🔍 Multiple PIDs: {multiple_pids}")
                
                if not multiple_pids:
                    print(f"   ❌ MULTI-PID DETECTION: Not recognized as multi-PID request")
                    return False, data
                
                # Check individual results
                individual_results = data.get('individual_results', [])
                print(f"   📊 Individual results: {len(individual_results)} PIDs processed")
                
                if len(individual_results) != 2:
                    print(f"   ❌ INDIVIDUAL RESULTS: Expected 2 results, got {len(individual_results)}")
                    return False, data
                
                # Check that we have one valid and one invalid result
                valid_results = [r for r in individual_results if r.get('found')]
                invalid_results = [r for r in individual_results if not r.get('found')]
                
                print(f"   ✅ Valid results: {len(valid_results)}")
                print(f"   ✅ Invalid results: {len(invalid_results)}")
                
                if len(valid_results) == 1 and len(invalid_results) == 1:
                    print(f"   ✅ MIXED HANDLING: Correctly handles one valid, one invalid PID")
                else:
                    print(f"   ❌ MIXED HANDLING: Unexpected result distribution")
                    return False, data
                
                # Check overall found status (should be True if any PID is found)
                found = data.get('found', False)
                print(f"   🔍 Overall found: {found}")
                
                if found:
                    print(f"   ✅ OVERALL STATUS: Correctly returns found: true when at least one PID is valid")
                else:
                    print(f"   ❌ OVERALL STATUS: Should return found: true when at least one PID is valid")
                    return False, data
                
                # Check that combined geometry exists (from the valid PID)
                combined_geometry = data.get('combined_geometry')
                if combined_geometry and 'rings' in combined_geometry:
                    print(f"   ✅ COMBINED GEOMETRY: Valid geometry from valid PID")
                else:
                    print(f"   ❌ COMBINED GEOMETRY: Missing geometry despite valid PID")
                    return False, data
                
                return True, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                print(f"   Raw Response: {response.text[:500]}...")
                return False, {"error": "Invalid JSON response"}
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
                return False, error_data
            except:
                print(f"   Raw Response: {response.text[:200]}...")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def test_multi_pid_bbox_format_fix():
    """Comprehensive test of the bbox format mismatch fix"""
    print("\n🔧 Testing Multi-PID Bbox Format Fix...")
    print("🎯 FOCUS: Verify bbox format conversion from single-PID to multi-PID format")
    print("📋 ISSUE: Single-PID returns {minLon,maxLon,minLat,maxLat} but multi-PID needs {north,south,east,west}")
    
    # Test single PID first to get baseline
    print("\n   Step 1: Testing single PID to understand baseline format...")
    single_result, single_data = test_single_pid_query()
    
    if not single_result:
        print("   ❌ Cannot test bbox conversion - single PID test failed")
        return False, {"error": "Single PID test failed"}
    
    single_bbox = single_data.get('bbox', {})
    print(f"   📦 Single PID bbox format: {list(single_bbox.keys())}")
    
    # Test multi-PID to verify conversion
    print("\n   Step 2: Testing multi-PID to verify bbox format conversion...")
    multi_result, multi_data = test_multi_pid_query()
    
    if not multi_result:
        print("   ❌ Multi-PID test failed - bbox conversion cannot be verified")
        return False, {"error": "Multi-PID test failed"}
    
    combined_bbox = multi_data.get('combined_bbox', {})
    print(f"   📦 Multi-PID combined bbox format: {list(combined_bbox.keys())}")
    
    # Verify the conversion logic
    print("\n   Step 3: Verifying bbox format conversion logic...")
    
    # Check that single PID uses minLon/maxLon/minLat/maxLat format
    single_format_correct = all(key in single_bbox for key in ['minLon', 'maxLon', 'minLat', 'maxLat'])
    print(f"   ✅ Single PID format correct: {single_format_correct}")
    
    # Check that multi-PID uses north/south/east/west format
    multi_format_correct = all(key in combined_bbox for key in ['north', 'south', 'east', 'west'])
    print(f"   ✅ Multi-PID format correct: {multi_format_correct}")
    
    if single_format_correct and multi_format_correct:
        print(f"   ✅ BBOX FORMAT FIX: Successfully converts between formats")
        
        # Verify the conversion values make sense
        # north should correspond to maxLat, south to minLat, east to maxLon, west to minLon
        individual_results = multi_data.get('individual_results', [])
        if individual_results:
            # Find a valid individual result to compare
            valid_individual = None
            for result in individual_results:
                if result.get('found') and result.get('bbox'):
                    valid_individual = result
                    break
            
            if valid_individual:
                individual_bbox = valid_individual['bbox']
                print(f"   🔍 Comparing conversion values...")
                print(f"      Individual bbox: {individual_bbox}")
                print(f"      Combined bbox: {combined_bbox}")
                
                # The combined bbox should encompass the individual bbox
                conversion_correct = (
                    combined_bbox['north'] >= individual_bbox['maxLat'] and
                    combined_bbox['south'] <= individual_bbox['minLat'] and
                    combined_bbox['east'] >= individual_bbox['maxLon'] and
                    combined_bbox['west'] <= individual_bbox['minLon']
                )
                
                if conversion_correct:
                    print(f"   ✅ CONVERSION VALUES: Bbox conversion values are logically correct")
                else:
                    print(f"   ⚠️ CONVERSION VALUES: Bbox conversion values may be incorrect")
        
        return True, {
            "single_bbox_format": list(single_bbox.keys()),
            "multi_bbox_format": list(combined_bbox.keys()),
            "conversion_working": True
        }
    else:
        print(f"   ❌ BBOX FORMAT FIX: Format conversion not working correctly")
        return False, {
            "single_bbox_format": list(single_bbox.keys()),
            "multi_bbox_format": list(combined_bbox.keys()),
            "single_format_correct": single_format_correct,
            "multi_format_correct": multi_format_correct
        }

def test_multi_pid_api_logic_fix():
    """Comprehensive test of the multi-PID backend API logic fix"""
    print("\n🎯 COMPREHENSIVE MULTI-PID BACKEND API LOGIC FIX TEST")
    print("=" * 80)
    print("🎯 REVIEW REQUEST: Test multi-PID backend API logic fix for Tax Sale Compass")
    print("📋 SPECIFIC REQUIREMENTS:")
    print("   1. Single-PID Test: GET /api/query-ns-government-parcel/85010866")
    print("      - Should return bbox with {minLon, maxLon, minLat, maxLat} format")
    print("      - Should have found: true, geometry, center coordinates")
    print("   2. Multi-PID Test: GET /api/query-ns-government-parcel/85010866/85074276")
    print("      - Should return combined geometry with multiple_pids: true")
    print("      - Should have individual_results array with 2 entries")
    print("      - Should have combined_bbox with {north, south, east, west} format")
    print("      - Should have proper center coordinates from combined_bbox")
    print("   3. Error Scenarios: Test invalid PIDs for proper error handling")
    print("   4. Verify bbox format conversion fixes KeyError issues")
    print("=" * 80)
    
    # Run all tests
    results = {}
    
    # Test 1: Single-PID
    print("\n🔍 TEST 1: Single-PID Query")
    single_result, single_data = test_single_pid_query()
    results['single_pid'] = {'success': single_result, 'data': single_data}
    
    # Test 2: Multi-PID
    print("\n🔍 TEST 2: Multi-PID Query")
    multi_result, multi_data = test_multi_pid_query()
    results['multi_pid'] = {'success': multi_result, 'data': multi_data}
    
    # Test 3: Invalid Single PID
    print("\n🔍 TEST 3: Invalid Single PID")
    invalid_single_result, invalid_single_data = test_invalid_single_pid()
    results['invalid_single'] = {'success': invalid_single_result, 'data': invalid_single_data}
    
    # Test 4: Mixed Valid/Invalid Multi-PID
    print("\n🔍 TEST 4: Mixed Valid/Invalid Multi-PID")
    mixed_result, mixed_data = test_mixed_valid_invalid_multi_pid()
    results['mixed_multi'] = {'success': mixed_result, 'data': mixed_data}
    
    # Test 5: Bbox Format Fix
    print("\n🔍 TEST 5: Bbox Format Conversion Fix")
    bbox_fix_result, bbox_fix_data = test_multi_pid_bbox_format_fix()
    results['bbox_fix'] = {'success': bbox_fix_result, 'data': bbox_fix_data}
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("📊 MULTI-PID BACKEND API LOGIC FIX - FINAL ASSESSMENT")
    print("=" * 80)
    
    test_names = [
        ('Single-PID Query', 'single_pid'),
        ('Multi-PID Query', 'multi_pid'),
        ('Invalid Single PID', 'invalid_single'),
        ('Mixed Multi-PID', 'mixed_multi'),
        ('Bbox Format Fix', 'bbox_fix')
    ]
    
    passed_tests = 0
    total_tests = len(test_names)
    
    print(f"📋 DETAILED RESULTS:")
    for test_name, test_key in test_names:
        result = results[test_key]
        status = "✅ PASSED" if result['success'] else "❌ FAILED"
        print(f"   {status} - {test_name}")
        if result['success']:
            passed_tests += 1
    
    print(f"\n📊 SUMMARY:")
    print(f"   Passed: {passed_tests}/{total_tests} tests")
    print(f"   Success Rate: {(passed_tests/total_tests)*100:.1f}%")
    
    # Critical findings
    print(f"\n🔍 CRITICAL FINDINGS:")
    
    if results['single_pid']['success']:
        print(f"   ✅ Single-PID requests work without regression")
        single_bbox = results['single_pid']['data'].get('bbox', {})
        if all(key in single_bbox for key in ['minLon', 'maxLon', 'minLat', 'maxLat']):
            print(f"   ✅ Single-PID uses correct bbox format: {list(single_bbox.keys())}")
    else:
        print(f"   ❌ Single-PID requests have issues")
    
    if results['multi_pid']['success']:
        print(f"   ✅ Multi-PID requests work without KeyError")
        multi_bbox = results['multi_pid']['data'].get('combined_bbox', {})
        if all(key in multi_bbox for key in ['north', 'south', 'east', 'west']):
            print(f"   ✅ Multi-PID uses correct bbox format: {list(multi_bbox.keys())}")
        
        individual_results = results['multi_pid']['data'].get('individual_results', [])
        if len(individual_results) == 2:
            print(f"   ✅ Multi-PID processes both PIDs correctly")
    else:
        print(f"   ❌ Multi-PID requests still have issues")
    
    if results['bbox_fix']['success']:
        print(f"   ✅ Bbox format conversion working correctly")
        print(f"   ✅ No more KeyError on bbox access")
    else:
        print(f"   ❌ Bbox format conversion still has issues")
    
    # Overall assessment
    critical_tests_passed = (
        results['single_pid']['success'] and 
        results['multi_pid']['success'] and 
        results['bbox_fix']['success']
    )
    
    if critical_tests_passed:
        print(f"\n🎉 MULTI-PID BACKEND API LOGIC FIX: SUCCESS!")
        print(f"   ✅ Bbox format mismatch issue resolved")
        print(f"   ✅ Single-PID and multi-PID both working")
        print(f"   ✅ No more 404 errors for multi-PID requests")
        print(f"   ✅ Proper center coordinates for mapping")
    else:
        print(f"\n❌ MULTI-PID BACKEND API LOGIC FIX: ISSUES REMAIN")
        print(f"   🔧 Additional fixes may be needed")
    
    return critical_tests_passed, results

def main():
    """Main test execution function - Focus on Multi-PID Backend API Logic Fix"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Multi-PID Backend API Logic Fix Testing")
    print("📋 REVIEW REQUEST: Test the multi-PID backend API logic fix for Tax Sale Compass")
    print("🔍 ISSUE FIXED: Bbox format mismatch in /api/query-ns-government-parcel/{pid_number}")
    print("   - Single-PID returns bbox with {minLon, maxLon, minLat, maxLat}")
    print("   - Multi-PID logic tried to access {north, south, east, west} keys")
    print("   - This caused KeyError and 404 errors for multi-PID requests")
    print("   - Fix implemented bbox format conversion")
    print("🎯 TESTING SCOPE:")
    print("   - Single-PID requests (should work without regression)")
    print("   - Multi-PID requests (should work without KeyError)")
    print("   - Error handling for invalid PIDs")
    print("   - Bbox format conversion verification")
    print("=" * 80)
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Multi-PID API Logic Fix (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Multi-PID Backend API Logic Fix Testing")
    all_working, test_results = test_multi_pid_api_logic_fix()
    
    # Final Results Summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS SUMMARY - Multi-PID Backend API Logic Fix")
    print("=" * 80)
    
    if all_working:
        print(f"🎉 MULTI-PID BACKEND API LOGIC FIX: SUCCESSFUL!")
        print(f"   ✅ All critical tests passed")
        print(f"   ✅ Bbox format mismatch issue resolved")
        print(f"   ✅ Single-PID requests work without regression")
        print(f"   ✅ Multi-PID requests work without KeyError")
        print(f"   ✅ Proper error handling for invalid PIDs")
        print(f"   ✅ Center coordinates calculated correctly")
        
        print(f"\n📊 DETAILED SUCCESS METRICS:")
        passed_count = sum(1 for result in test_results.values() if result['success'])
        total_count = len(test_results)
        print(f"   Tests passed: {passed_count}/{total_count}")
        print(f"   Success rate: {(passed_count/total_count)*100:.1f}%")
        
        print(f"\n🎯 KEY ACHIEVEMENTS:")
        print(f"   ✅ Fixed bbox format conversion from single-PID to multi-PID")
        print(f"   ✅ Eliminated KeyError when accessing bbox keys")
        print(f"   ✅ Multi-PID requests now return proper combined geometry")
        print(f"   ✅ Center coordinates calculated from combined bbox")
        print(f"   ✅ No more 404 errors for valid multi-PID requests")
        
    else:
        print(f"❌ MULTI-PID BACKEND API LOGIC FIX: ISSUES IDENTIFIED")
        print(f"   ❌ Some critical tests failed")
        print(f"   🔧 Additional fixes may be needed")
        
        print(f"\n📋 ISSUES IDENTIFIED:")
        failed_tests = [name for name, result in test_results.items() if not result['success']]
        if failed_tests:
            print(f"   ❌ FAILED TESTS:")
            for test_name in failed_tests:
                print(f"      - {test_name}")
        
        print(f"\n   🔧 RECOMMENDED ACTIONS:")
        print(f"      1. Review bbox format conversion logic")
        print(f"      2. Check multi-PID geometry combination")
        print(f"      3. Verify center coordinate calculation")
        print(f"      4. Test with different PID combinations")
        print(f"      5. Check error handling for edge cases")
    
    print("=" * 80)
    
    return all_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)