#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Deployment Management Endpoints Testing
"""

import requests
import json
import sys
import re
import math
from datetime import datetime
import time

# Get backend URL from environment
import os
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://taxsale-automation.preview.emergentagent.com') + '/api'

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

def test_victoria_county_properties():
    """Test Victoria County properties exist with correct assessment numbers"""
    print("\n🏛️ Testing Victoria County Properties...")
    print("🎯 FOCUS: Verify Victoria County properties with assessment numbers 00254118, 00453706, 09541209")
    
    target_assessments = ["00254118", "00453706", "09541209"]
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        if response.status_code == 200:
            properties = response.json()
            print(f"✅ Tax sales endpoint working - Found {len(properties)} total properties")
            
            # Filter Victoria County properties
            victoria_properties = [p for p in properties if "Victoria County" in p.get("municipality_name", "")]
            print(f"   🏛️ Victoria County properties: {len(victoria_properties)}")
            
            # Check for target assessment numbers
            found_assessments = []
            property_data = {}
            
            for prop in victoria_properties:
                assessment = prop.get('assessment_number', '')
                if assessment in target_assessments:
                    found_assessments.append(assessment)
                    property_data[assessment] = prop
                    print(f"   ✅ Found target property: {assessment}")
                    print(f"      Owner: {prop.get('owner_name', 'N/A')}")
                    print(f"      Address: {prop.get('property_address', 'N/A')}")
                    print(f"      Opening Bid: ${prop.get('opening_bid', 0)}")
                    print(f"      Boundary Screenshot: {prop.get('boundary_screenshot', 'N/A')}")
            
            missing_assessments = [a for a in target_assessments if a not in found_assessments]
            
            if missing_assessments:
                print(f"   ❌ Missing target assessments: {missing_assessments}")
                return False, property_data
            else:
                print(f"   ✅ All target assessments found: {found_assessments}")
                return True, property_data
                
        else:
            print(f"❌ Tax sales endpoint failed with status {response.status_code}")
            return False, {}
    except Exception as e:
        print(f"❌ Victoria County properties test error: {e}")
        return False, {}

def test_boundary_screenshot_field_format():
    """Test that boundary_screenshot field stores filenames instead of full URLs"""
    print("\n📸 Testing Boundary Screenshot Field Format...")
    print("🎯 FOCUS: Verify boundary_screenshot stores filenames (e.g., 'boundary_00254118.png') not full URLs")
    
    target_assessments = ["00254118", "00453706", "09541209"]
    
    try:
        # Get Victoria County properties
        properties_found, property_data = test_victoria_county_properties()
        
        if not properties_found:
            print("❌ Cannot test boundary_screenshot format - Victoria County properties not found")
            return False, {}
        
        results = {}
        all_correct_format = True
        
        for assessment in target_assessments:
            if assessment in property_data:
                prop = property_data[assessment]
                boundary_screenshot = prop.get('boundary_screenshot', '')
                
                print(f"\n   📋 Assessment {assessment}:")
                print(f"      Boundary Screenshot: '{boundary_screenshot}'")
                
                # Check if it's a filename (not a full URL)
                is_filename = False
                is_full_url = False
                
                if boundary_screenshot:
                    # Check if it's a full URL (contains http/https)
                    if boundary_screenshot.startswith(('http://', 'https://')):
                        is_full_url = True
                        print(f"      ❌ ISSUE: Contains full URL (should be filename only)")
                        all_correct_format = False
                    # Check if it's a filename format (ends with .png and doesn't contain URL)
                    elif boundary_screenshot.endswith('.png') and not '/' in boundary_screenshot:
                        is_filename = True
                        print(f"      ✅ CORRECT: Filename format detected")
                        # Check if it matches expected pattern
                        expected_filename = f"boundary_{assessment}.png"
                        if boundary_screenshot == expected_filename:
                            print(f"      ✅ PERFECT: Matches expected pattern '{expected_filename}'")
                        else:
                            print(f"      ⚠️ DIFFERENT: Expected '{expected_filename}', got '{boundary_screenshot}'")
                    else:
                        print(f"      ❌ UNKNOWN: Format not recognized")
                        all_correct_format = False
                else:
                    print(f"      ❌ MISSING: No boundary_screenshot value")
                    all_correct_format = False
                
                results[assessment] = {
                    'boundary_screenshot': boundary_screenshot,
                    'is_filename': is_filename,
                    'is_full_url': is_full_url,
                    'correct_format': is_filename and not is_full_url
                }
        
        print(f"\n   📊 BOUNDARY SCREENSHOT FORMAT SUMMARY:")
        correct_count = sum(1 for r in results.values() if r['correct_format'])
        print(f"      Correct format: {correct_count}/{len(results)}")
        print(f"      All correct: {'✅ YES' if all_correct_format else '❌ NO'}")
        
        return all_correct_format, results
        
    except Exception as e:
        print(f"❌ Boundary screenshot format test error: {e}")
        return False, {}

def test_boundary_image_endpoints():
    """Test /api/boundary-image/{filename} endpoints work properly"""
    print("\n🖼️ Testing Boundary Image Endpoints...")
    print("🎯 FOCUS: Test /api/boundary-image/{filename} endpoints for Victoria County properties")
    
    target_assessments = ["00254118", "00453706", "09541209"]
    
    try:
        # Get boundary screenshot data
        format_correct, boundary_data = test_boundary_screenshot_field_format()
        
        if not boundary_data:
            print("❌ Cannot test boundary image endpoints - no boundary screenshot data")
            return False, {}
        
        results = {}
        all_endpoints_working = True
        
        for assessment in target_assessments:
            if assessment in boundary_data:
                boundary_info = boundary_data[assessment]
                filename = boundary_info['boundary_screenshot']
                
                print(f"\n   📋 Testing Assessment {assessment}:")
                print(f"      Filename: '{filename}'")
                
                if filename and filename.endswith('.png'):
                    # Test the boundary-image endpoint
                    boundary_url = f"{BACKEND_URL}/boundary-image/{filename}"
                    print(f"      Testing: {boundary_url}")
                    
                    try:
                        response = requests.get(boundary_url, timeout=30)
                        
                        print(f"      Status Code: {response.status_code}")
                        
                        if response.status_code == 200:
                            # Check content type
                            content_type = response.headers.get('content-type', '')
                            content_length = len(response.content)
                            
                            print(f"      ✅ SUCCESS: Image accessible")
                            print(f"      Content-Type: {content_type}")
                            print(f"      Content-Length: {content_length} bytes")
                            
                            # Verify it's actually an image
                            if 'image' in content_type and content_length > 1000:
                                print(f"      ✅ VALID: Proper image response")
                                results[assessment] = {
                                    'endpoint_working': True,
                                    'status_code': response.status_code,
                                    'content_type': content_type,
                                    'content_length': content_length,
                                    'filename': filename
                                }
                            else:
                                print(f"      ⚠️ WARNING: Response may not be valid image")
                                results[assessment] = {
                                    'endpoint_working': False,
                                    'status_code': response.status_code,
                                    'content_type': content_type,
                                    'content_length': content_length,
                                    'filename': filename,
                                    'issue': 'Invalid image response'
                                }
                                all_endpoints_working = False
                        elif response.status_code == 404:
                            print(f"      ❌ NOT FOUND: Image file does not exist")
                            results[assessment] = {
                                'endpoint_working': False,
                                'status_code': 404,
                                'filename': filename,
                                'issue': 'Image file not found'
                            }
                            all_endpoints_working = False
                        else:
                            print(f"      ❌ ERROR: HTTP {response.status_code}")
                            results[assessment] = {
                                'endpoint_working': False,
                                'status_code': response.status_code,
                                'filename': filename,
                                'issue': f'HTTP error {response.status_code}'
                            }
                            all_endpoints_working = False
                            
                    except Exception as e:
                        print(f"      ❌ REQUEST ERROR: {e}")
                        results[assessment] = {
                            'endpoint_working': False,
                            'filename': filename,
                            'issue': f'Request error: {e}'
                        }
                        all_endpoints_working = False
                else:
                    print(f"      ❌ INVALID FILENAME: '{filename}' is not a valid PNG filename")
                    results[assessment] = {
                        'endpoint_working': False,
                        'filename': filename,
                        'issue': 'Invalid filename format'
                    }
                    all_endpoints_working = False
        
        print(f"\n   📊 BOUNDARY IMAGE ENDPOINTS SUMMARY:")
        working_count = sum(1 for r in results.values() if r.get('endpoint_working', False))
        print(f"      Working endpoints: {working_count}/{len(results)}")
        print(f"      All working: {'✅ YES' if all_endpoints_working else '❌ NO'}")
        
        return all_endpoints_working, results
        
    except Exception as e:
        print(f"❌ Boundary image endpoints test error: {e}")
        return False, {}

def test_property_image_endpoints():
    """Test /api/property-image/{assessment_number} endpoints work properly"""
    print("\n🏠 Testing Property Image Endpoints...")
    print("🎯 FOCUS: Test /api/property-image/{assessment_number} endpoints for Victoria County properties")
    
    target_assessments = ["00254118", "00453706", "09541209"]
    
    try:
        results = {}
        all_endpoints_working = True
        
        for assessment in target_assessments:
            print(f"\n   📋 Testing Assessment {assessment}:")
            
            # Test the property-image endpoint
            property_url = f"{BACKEND_URL}/property-image/{assessment}"
            print(f"      Testing: {property_url}")
            
            try:
                response = requests.get(property_url, timeout=30)
                
                print(f"      Status Code: {response.status_code}")
                
                if response.status_code == 200:
                    # Check content type
                    content_type = response.headers.get('content-type', '')
                    content_length = len(response.content)
                    
                    print(f"      ✅ SUCCESS: Property image accessible")
                    print(f"      Content-Type: {content_type}")
                    print(f"      Content-Length: {content_length} bytes")
                    
                    # Verify it's actually an image
                    if 'image' in content_type and content_length > 1000:
                        print(f"      ✅ VALID: Proper image response")
                        results[assessment] = {
                            'endpoint_working': True,
                            'status_code': response.status_code,
                            'content_type': content_type,
                            'content_length': content_length
                        }
                    else:
                        print(f"      ⚠️ WARNING: Response may not be valid image")
                        results[assessment] = {
                            'endpoint_working': False,
                            'status_code': response.status_code,
                            'content_type': content_type,
                            'content_length': content_length,
                            'issue': 'Invalid image response'
                        }
                        all_endpoints_working = False
                elif response.status_code == 404:
                    print(f"      ❌ NOT FOUND: Property not found or no image available")
                    results[assessment] = {
                        'endpoint_working': False,
                        'status_code': 404,
                        'issue': 'Property or image not found'
                    }
                    all_endpoints_working = False
                else:
                    print(f"      ❌ ERROR: HTTP {response.status_code}")
                    results[assessment] = {
                        'endpoint_working': False,
                        'status_code': response.status_code,
                        'issue': f'HTTP error {response.status_code}'
                    }
                    all_endpoints_working = False
                    
            except Exception as e:
                print(f"      ❌ REQUEST ERROR: {e}")
                results[assessment] = {
                    'endpoint_working': False,
                    'issue': f'Request error: {e}'
                }
                all_endpoints_working = False
        
        print(f"\n   📊 PROPERTY IMAGE ENDPOINTS SUMMARY:")
        working_count = sum(1 for r in results.values() if r.get('endpoint_working', False))
        print(f"      Working endpoints: {working_count}/{len(results)}")
        print(f"      All working: {'✅ YES' if all_endpoints_working else '❌ NO'}")
        
        return all_endpoints_working, results
        
    except Exception as e:
        print(f"❌ Property image endpoints test error: {e}")
        return False, {}

def test_url_construction_correctness():
    """Test that URL construction is correct for frontend usage"""
    print("\n🔗 Testing URL Construction Correctness...")
    print("🎯 FOCUS: Verify frontend can construct correct URLs without 404 errors")
    
    target_assessments = ["00254118", "00453706", "09541209"]
    
    try:
        # Get boundary screenshot data
        format_correct, boundary_data = test_boundary_screenshot_field_format()
        
        if not boundary_data:
            print("❌ Cannot test URL construction - no boundary screenshot data")
            return False, {}
        
        results = {}
        all_constructions_correct = True
        
        # Get the backend URL that frontend would use
        frontend_backend_url = os.environ.get('REACT_APP_BACKEND_URL', 'https://taxsale-automation.preview.emergentagent.com')
        
        print(f"   🌐 Frontend Backend URL: {frontend_backend_url}")
        
        for assessment in target_assessments:
            if assessment in boundary_data:
                boundary_info = boundary_data[assessment]
                filename = boundary_info['boundary_screenshot']
                
                print(f"\n   📋 Testing Assessment {assessment}:")
                print(f"      Boundary Screenshot Field: '{filename}'")
                
                if filename:
                    # Simulate frontend URL construction
                    # Frontend should construct: ${BACKEND_URL}/api/boundary-image/${property.boundary_screenshot}
                    constructed_url = f"{frontend_backend_url}/api/boundary-image/{filename}"
                    print(f"      Constructed URL: {constructed_url}")
                    
                    # Test if this constructed URL works
                    try:
                        response = requests.get(constructed_url, timeout=30)
                        
                        print(f"      Status Code: {response.status_code}")
                        
                        if response.status_code == 200:
                            content_type = response.headers.get('content-type', '')
                            content_length = len(response.content)
                            
                            print(f"      ✅ SUCCESS: Frontend URL construction works")
                            print(f"      Content-Type: {content_type}")
                            print(f"      Content-Length: {content_length} bytes")
                            
                            results[assessment] = {
                                'url_construction_correct': True,
                                'constructed_url': constructed_url,
                                'status_code': response.status_code,
                                'content_type': content_type,
                                'content_length': content_length
                            }
                        else:
                            print(f"      ❌ FAILED: Frontend URL construction results in HTTP {response.status_code}")
                            results[assessment] = {
                                'url_construction_correct': False,
                                'constructed_url': constructed_url,
                                'status_code': response.status_code,
                                'issue': f'HTTP {response.status_code} error'
                            }
                            all_constructions_correct = False
                            
                    except Exception as e:
                        print(f"      ❌ REQUEST ERROR: {e}")
                        results[assessment] = {
                            'url_construction_correct': False,
                            'constructed_url': constructed_url,
                            'issue': f'Request error: {e}'
                        }
                        all_constructions_correct = False
                else:
                    print(f"      ❌ NO FILENAME: Cannot construct URL")
                    results[assessment] = {
                        'url_construction_correct': False,
                        'issue': 'No boundary_screenshot filename'
                    }
                    all_constructions_correct = False
        
        print(f"\n   📊 URL CONSTRUCTION SUMMARY:")
        correct_count = sum(1 for r in results.values() if r.get('url_construction_correct', False))
        print(f"      Correct constructions: {correct_count}/{len(results)}")
        print(f"      All correct: {'✅ YES' if all_constructions_correct else '❌ NO'}")
        
        return all_constructions_correct, results
        
    except Exception as e:
        print(f"❌ URL construction test error: {e}")
        return False, {}

def test_victoria_county_image_routing_fix():
    """Comprehensive test of Victoria County property image routing fix"""
    print("\n🎯 COMPREHENSIVE VICTORIA COUNTY IMAGE ROUTING FIX TEST")
    print("=" * 80)
    print("🎯 REVIEW REQUEST: Test property image routing fix for Victoria County properties")
    print("📋 SPECIFIC REQUIREMENTS:")
    print("   1. Test Victoria County properties with assessment numbers 00254118, 00453706, 09541209")
    print("   2. Verify boundary_screenshot field stores filenames (e.g., 'boundary_00254118.png') not full URLs")
    print("   3. Test that /api/boundary-image/{filename} endpoints work properly")
    print("   4. Check that frontend can access property images without 404 errors")
    print("   5. Verify URL construction is correct in property data")
    print("=" * 80)
    
    test_results = {}
    
    # Test 1: Victoria County Properties Exist
    print("\n🔍 TEST 1: Victoria County Properties Existence")
    properties_exist, property_data = test_victoria_county_properties()
    test_results['properties_exist'] = properties_exist
    
    # Test 2: Boundary Screenshot Field Format
    print("\n🔍 TEST 2: Boundary Screenshot Field Format")
    format_correct, boundary_data = test_boundary_screenshot_field_format()
    test_results['field_format_correct'] = format_correct
    
    # Test 3: Boundary Image Endpoints
    print("\n🔍 TEST 3: Boundary Image Endpoints")
    boundary_endpoints_working, boundary_results = test_boundary_image_endpoints()
    test_results['boundary_endpoints_working'] = boundary_endpoints_working
    
    # Test 4: Property Image Endpoints
    print("\n🔍 TEST 4: Property Image Endpoints")
    property_endpoints_working, property_results = test_property_image_endpoints()
    test_results['property_endpoints_working'] = property_endpoints_working
    
    # Test 5: URL Construction Correctness
    print("\n🔍 TEST 5: URL Construction Correctness")
    url_construction_correct, url_results = test_url_construction_correctness()
    test_results['url_construction_correct'] = url_construction_correct
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("📊 VICTORIA COUNTY IMAGE ROUTING FIX - FINAL ASSESSMENT")
    print("=" * 80)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"✅ Tests Passed: {passed_tests}/{total_tests}")
    print(f"❌ Tests Failed: {total_tests - passed_tests}/{total_tests}")
    
    print(f"\n📋 DETAILED RESULTS:")
    test_descriptions = {
        'properties_exist': 'Victoria County Properties Exist',
        'field_format_correct': 'Boundary Screenshot Field Format Correct',
        'boundary_endpoints_working': 'Boundary Image Endpoints Working',
        'property_endpoints_working': 'Property Image Endpoints Working',
        'url_construction_correct': 'URL Construction Correct'
    }
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        description = test_descriptions.get(test_name, test_name)
        print(f"   {status} - {description}")
    
    # Specific Review Request Assessment
    print(f"\n🎯 REVIEW REQUEST REQUIREMENTS ASSESSMENT:")
    
    # Requirement 1: Test specific assessment numbers
    req1_met = properties_exist
    print(f"   1. {'✅' if req1_met else '❌'} Victoria County properties (00254118, 00453706, 09541209) - {'Found' if req1_met else 'Missing'}")
    
    # Requirement 2: Boundary screenshot field format
    req2_met = format_correct
    print(f"   2. {'✅' if req2_met else '❌'} Boundary screenshot stores filenames not URLs - {'Correct' if req2_met else 'Incorrect'}")
    
    # Requirement 3: Boundary image endpoints work
    req3_met = boundary_endpoints_working
    print(f"   3. {'✅' if req3_met else '❌'} /api/boundary-image/{{filename}} endpoints work - {'Working' if req3_met else 'Failed'}")
    
    # Requirement 4: Frontend can access without 404s
    req4_met = url_construction_correct
    print(f"   4. {'✅' if req4_met else '❌'} Frontend can access images without 404 errors - {'Success' if req4_met else 'Failed'}")
    
    # Requirement 5: URL construction correct
    req5_met = property_endpoints_working and url_construction_correct
    print(f"   5. {'✅' if req5_met else '❌'} URL construction correct in property data - {'Correct' if req5_met else 'Incorrect'}")
    
    requirements_met = sum([req1_met, req2_met, req3_met, req4_met, req5_met])
    all_requirements_met = requirements_met == 5
    
    print(f"\n📊 REQUIREMENTS SUMMARY:")
    print(f"   Requirements met: {requirements_met}/5")
    print(f"   All requirements met: {'✅ YES' if all_requirements_met else '❌ NO'}")
    
    # Overall Assessment
    if all_requirements_met:
        print(f"\n🎉 VICTORIA COUNTY IMAGE ROUTING FIX: SUCCESSFUL!")
        print(f"   ✅ All Victoria County properties found with correct assessment numbers")
        print(f"   ✅ Boundary screenshot field stores filenames instead of full URLs")
        print(f"   ✅ /api/boundary-image/{{filename}} endpoints working properly")
        print(f"   ✅ Frontend can access property images without 404 errors")
        print(f"   ✅ URL construction is correct in property data")
        print(f"   🚀 Image routing fix is production-ready!")
    else:
        print(f"\n❌ VICTORIA COUNTY IMAGE ROUTING FIX: ISSUES IDENTIFIED")
        print(f"   ❌ {5 - requirements_met} out of 5 requirements not met")
        print(f"   🔧 Image routing fix needs additional work")
        
        # Detailed issue analysis
        if not req1_met:
            print(f"      ❌ Victoria County properties missing or incomplete")
        if not req2_met:
            print(f"      ❌ Boundary screenshot field still contains full URLs instead of filenames")
        if not req3_met:
            print(f"      ❌ /api/boundary-image/{{filename}} endpoints not working properly")
        if not req4_met:
            print(f"      ❌ Frontend URL construction still results in 404 errors")
        if not req5_met:
            print(f"      ❌ URL construction or property image endpoints have issues")
    
    success_rate = (passed_tests / total_tests) * 100
    print(f"\n📊 Overall Success Rate: {success_rate:.1f}%")
    
    return all_requirements_met, {
        'test_results': test_results,
        'requirements_met': requirements_met,
        'property_data': property_data if properties_exist else {},
        'boundary_data': boundary_data if format_correct else {},
        'boundary_results': boundary_results if boundary_endpoints_working else {},
        'property_results': property_results if property_endpoints_working else {},
        'url_results': url_results if url_construction_correct else {}
    }

def main():
    """Main test execution function - Focus on Victoria County Image Routing Fix"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Test Victoria County property image routing fix")
    print("📋 REVIEW REQUEST: Test property image routing fix for Victoria County properties")
    print("🔍 SPECIFIC TESTING REQUIREMENTS:")
    print("   1. Test Victoria County properties with assessment numbers 00254118, 00453706, 09541209")
    print("   2. Verify boundary_screenshot field stores filenames (e.g., 'boundary_00254118.png') not full URLs")
    print("   3. Test that /api/boundary-image/{filename} endpoints work properly")
    print("   4. Check that frontend can access property images without 404 errors")
    print("   5. Verify URL construction is correct in property data")
    print("🎯 CONTEXT:")
    print("   - Previously boundary_screenshot was storing full URLs causing 404 errors")
    print("   - Fixed by changing boundary_screenshot to store filenames only")
    print("   - Frontend constructs: ${BACKEND_URL}/api/boundary-image/${property.boundary_screenshot}")
    print("=" * 80)
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Victoria County Image Routing Fix (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Victoria County Image Routing Fix Testing")
    fix_successful, fix_data = test_victoria_county_image_routing_fix()
    
    # Final Results Summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS SUMMARY - Victoria County Image Routing Fix")
    print("=" * 80)
    
    if fix_successful:
        print(f"🎉 VICTORIA COUNTY IMAGE ROUTING FIX: SUCCESSFUL!")
        print(f"   ✅ All 5 review request requirements met")
        print(f"   ✅ Victoria County properties found with correct assessment numbers")
        print(f"   ✅ Boundary screenshot field stores filenames instead of full URLs")
        print(f"   ✅ /api/boundary-image/{{filename}} endpoints working properly")
        print(f"   ✅ Frontend can access property images without 404 errors")
        print(f"   ✅ URL construction is correct in property data")
        print(f"   🚀 Image routing fix is production-ready!")
        
        # Show detailed success data
        test_results = fix_data.get('test_results', {})
        requirements_met = fix_data.get('requirements_met', 0)
        
        print(f"\n📊 DETAILED SUCCESS METRICS:")
        print(f"   Requirements met: {requirements_met}/5")
        print(f"   Test success rate: {(sum(test_results.values()) / len(test_results) * 100):.1f}%")
        
        # Show property data
        property_data = fix_data.get('property_data', {})
        if property_data:
            print(f"\n📋 VERIFIED PROPERTIES:")
            for assessment, prop in property_data.items():
                print(f"   ✅ {assessment}: {prop.get('owner_name', 'N/A')} - {prop.get('boundary_screenshot', 'N/A')}")
        
    else:
        print(f"❌ VICTORIA COUNTY IMAGE ROUTING FIX: ISSUES IDENTIFIED")
        print(f"   ❌ Review request requirements not fully met")
        print(f"   🔧 Image routing fix needs additional work")
        
        test_results = fix_data.get('test_results', {})
        requirements_met = fix_data.get('requirements_met', 0)
        
        print(f"\n📋 ISSUES IDENTIFIED:")
        print(f"   Requirements met: {requirements_met}/5")
        print(f"   Requirements failed: {5 - requirements_met}/5")
        
        # Show specific failures
        test_descriptions = {
            'properties_exist': 'Victoria County Properties Missing',
            'field_format_correct': 'Boundary Screenshot Field Format Incorrect',
            'boundary_endpoints_working': 'Boundary Image Endpoints Not Working',
            'property_endpoints_working': 'Property Image Endpoints Not Working',
            'url_construction_correct': 'URL Construction Incorrect'
        }
        
        failed_tests = [name for name, result in test_results.items() if not result]
        if failed_tests:
            print(f"\n   ❌ FAILED TESTS:")
            for test_name in failed_tests:
                description = test_descriptions.get(test_name, test_name)
                print(f"      - {description}")
        
        print(f"\n   🔧 RECOMMENDED ACTIONS:")
        print(f"      1. Verify Victoria County properties exist in database")
        print(f"      2. Check boundary_screenshot field format (should be filenames, not URLs)")
        print(f"      3. Ensure /api/boundary-image/{{filename}} endpoints are accessible")
        print(f"      4. Test frontend URL construction manually")
        print(f"      5. Verify property image endpoints work for all assessment numbers")
    
    print("=" * 80)
    
    return fix_successful

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)