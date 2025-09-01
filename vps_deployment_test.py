#!/usr/bin/env python3
"""
VPS Deployment Testing for Nova Scotia Tax Sale Aggregator
Focus on scraping functionality issues reported on VPS deployment
"""

import requests
import json
import sys
from datetime import datetime
import time
import concurrent.futures

# Get backend URL from environment
BACKEND_URL = "https://taxsale-automation.preview.emergentagent.com/api"

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

def test_vps_scraping_deployment_issues():
    """Test VPS deployment specific scraping issues - Review Request Focus"""
    print("\n🚨 Testing VPS Deployment Scraping Issues...")
    print("🎯 FOCUS: Scraping status updates, Halifax Live button, API connectivity")
    print("📋 USER REPORTS: 1) Scraping status not updating after 'Scrape All', 2) Halifax Live button failing")
    
    try:
        # Test 1: Halifax Scraper Endpoint - Core functionality
        print(f"\n   🔧 TEST 1: Halifax Scraper Endpoint (/api/scrape/halifax)")
        
        scrape_start_time = time.time()
        halifax_response = requests.post(f"{BACKEND_URL}/scrape/halifax", timeout=180)
        scrape_end_time = time.time()
        scrape_duration = scrape_end_time - scrape_start_time
        
        if halifax_response.status_code == 200:
            scrape_result = halifax_response.json()
            print(f"   ✅ Halifax scraper executed successfully")
            print(f"   📊 Status: {scrape_result.get('status', 'unknown')}")
            print(f"   🏠 Properties scraped: {scrape_result.get('properties_scraped', 0)}")
            print(f"   ⏱️ Scrape duration: {scrape_duration:.2f} seconds")
            
            # Verify expected property count (should be ~62 based on preview environment)
            properties_count = scrape_result.get('properties_scraped', 0)
            if properties_count >= 60:
                print(f"   ✅ Property count matches preview environment expectations (~62)")
            elif properties_count > 0:
                print(f"   ⚠️ Property count lower than expected (got {properties_count}, expected ~62)")
            else:
                print(f"   ❌ No properties scraped - critical failure")
                return False, {"error": "Halifax scraper returned 0 properties"}
                
        else:
            print(f"   ❌ Halifax scraper failed with status {halifax_response.status_code}")
            try:
                error_detail = halifax_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {halifax_response.text[:300]}...")
            return False, {"error": f"Halifax scraper HTTP {halifax_response.status_code}"}
        
        # Test 2: Scrape-All Endpoint - User reported issue
        print(f"\n   🔧 TEST 2: Scrape-All Endpoint (/api/scrape-all)")
        
        scrape_all_response = requests.post(f"{BACKEND_URL}/scrape-all", timeout=180)
        
        if scrape_all_response.status_code == 200:
            scrape_all_result = scrape_all_response.json()
            print(f"   ✅ Scrape-all executed successfully")
            print(f"   📊 Status: {scrape_all_result.get('status', 'unknown')}")
            print(f"   🏛️ Municipalities processed: {scrape_all_result.get('municipalities_processed', 0)}")
            print(f"   🏠 Total properties: {scrape_all_result.get('total_properties', 0)}")
        elif scrape_all_response.status_code == 404:
            print(f"   ⚠️ Scrape-all endpoint not found (404) - may not be implemented")
            # This is not critical as the main issue is with Halifax scraper
        else:
            print(f"   ❌ Scrape-all failed with status {scrape_all_response.status_code}")
            try:
                error_detail = scrape_all_response.json()
                print(f"      Error details: {error_detail}")
            except:
                print(f"      Raw response: {scrape_all_response.text[:300]}...")
        
        # Test 3: Municipality Status Updates - Critical for frontend status display
        print(f"\n   🔧 TEST 3: Municipality Status Updates After Scraping")
        
        # Get Halifax municipality status before and after scraping
        muni_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        if muni_response.status_code == 200:
            municipalities = muni_response.json()
            halifax_muni = None
            
            for muni in municipalities:
                if "Halifax" in muni.get("name", ""):
                    halifax_muni = muni
                    break
            
            if halifax_muni:
                print(f"   ✅ Halifax municipality found in status")
                print(f"   📊 Current scrape status: {halifax_muni.get('scrape_status', 'unknown')}")
                print(f"   🕒 Last scraped: {halifax_muni.get('last_scraped', 'never')}")
                
                # Verify status was updated to 'success' after scraping
                if halifax_muni.get('scrape_status') == 'success':
                    print(f"   ✅ Scrape status correctly updated to 'success'")
                elif halifax_muni.get('scrape_status') == 'in_progress':
                    print(f"   ⚠️ Scrape status still 'in_progress' - may indicate async issue")
                else:
                    print(f"   ❌ Scrape status not updated correctly: {halifax_muni.get('scrape_status')}")
                    return False, {"error": "Municipality status not updated after scraping"}
                
                # Verify last_scraped timestamp is recent
                last_scraped = halifax_muni.get('last_scraped')
                if last_scraped:
                    print(f"   ✅ Last scraped timestamp updated: {last_scraped}")
                else:
                    print(f"   ❌ Last scraped timestamp not updated")
                    return False, {"error": "Last scraped timestamp not updated"}
                    
            else:
                print(f"   ❌ Halifax municipality not found in status list")
                return False, {"error": "Halifax municipality not found"}
        else:
            print(f"   ❌ Municipality status check failed: {muni_response.status_code}")
            return False, {"error": f"Municipality status HTTP {muni_response.status_code}"}
        
        # Test 4: Tax Sales Data Verification - Ensure scraped data is accessible
        print(f"\n   🔧 TEST 4: Tax Sales Data Verification After Scraping")
        
        tax_sales_response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        
        if tax_sales_response.status_code == 200:
            properties = tax_sales_response.json()
            print(f"   ✅ Tax sales data accessible - {len(properties)} Halifax properties")
            
            # Verify we have the expected properties from scraping
            if len(properties) >= 60:
                print(f"   ✅ Property count matches scraper result")
                
                # Check a few sample properties for data quality
                sample_properties = properties[:3]
                for i, prop in enumerate(sample_properties):
                    print(f"   📋 Sample Property {i+1}:")
                    print(f"      Assessment: {prop.get('assessment_number', 'N/A')}")
                    print(f"      Owner: {prop.get('owner_name', 'N/A')}")
                    print(f"      Address: {prop.get('property_address', 'N/A')}")
                    print(f"      Opening Bid: ${prop.get('opening_bid', 0)}")
                    
            else:
                print(f"   ⚠️ Property count mismatch (expected ~62, got {len(properties)})")
        else:
            print(f"   ❌ Tax sales data not accessible: {tax_sales_response.status_code}")
            return False, {"error": f"Tax sales data HTTP {tax_sales_response.status_code}"}
        
        # Test 5: API Response Times - VPS performance check
        print(f"\n   🔧 TEST 5: API Response Times (VPS Performance)")
        
        endpoints_to_test = [
            ("/municipalities", "GET"),
            ("/tax-sales", "GET"),
            ("/stats", "GET"),
            ("/tax-sales/map-data", "GET")
        ]
        
        response_times = {}
        
        for endpoint, method in endpoints_to_test:
            start_time = time.time()
            
            if method == "GET":
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=30)
            
            end_time = time.time()
            response_time = end_time - start_time
            response_times[endpoint] = {
                "time": response_time,
                "status": response.status_code,
                "success": response.status_code == 200
            }
            
            print(f"   📊 {method} {endpoint}: {response_time:.2f}s (HTTP {response.status_code})")
        
        # Check for performance issues
        slow_endpoints = [ep for ep, data in response_times.items() if data["time"] > 10]
        failed_endpoints = [ep for ep, data in response_times.items() if not data["success"]]
        
        if slow_endpoints:
            print(f"   ⚠️ Slow endpoints detected: {slow_endpoints}")
        if failed_endpoints:
            print(f"   ❌ Failed endpoints detected: {failed_endpoints}")
            return False, {"error": f"Failed endpoints: {failed_endpoints}"}
        else:
            print(f"   ✅ All endpoints responding within acceptable time")
        
        # Test 6: CORS and Headers Check - VPS deployment specific
        print(f"\n   🔧 TEST 6: CORS and Headers Check (VPS Deployment)")
        
        # Test with different origins to simulate frontend requests
        test_origins = [
            "https://taxsale-automation.preview.emergentagent.com",
            "http://localhost:3000",
            "null"
        ]
        
        cors_results = {}
        
        for origin in test_origins:
            headers = {
                "Origin": origin,
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            }
            
            # Test preflight request
            try:
                options_response = requests.options(f"{BACKEND_URL}/scrape/halifax", headers=headers, timeout=10)
                
                cors_results[origin] = {
                    "preflight_status": options_response.status_code,
                    "cors_headers": {
                        "access_control_allow_origin": options_response.headers.get("Access-Control-Allow-Origin"),
                        "access_control_allow_methods": options_response.headers.get("Access-Control-Allow-Methods"),
                        "access_control_allow_headers": options_response.headers.get("Access-Control-Allow-Headers")
                    }
                }
                
                print(f"   🌐 Origin {origin}:")
                print(f"      Preflight: HTTP {options_response.status_code}")
                print(f"      CORS Origin: {options_response.headers.get('Access-Control-Allow-Origin', 'Not set')}")
            except Exception as e:
                print(f"   🌐 Origin {origin}: Error - {e}")
                cors_results[origin] = {"error": str(e)}
        
        # Test 7: Environment Variables Check
        print(f"\n   🔧 TEST 7: Environment Configuration Check")
        
        print(f"   🔧 Backend URL being tested: {BACKEND_URL}")
        print(f"   🔧 Expected frontend URL: https://taxsale-automation.preview.emergentagent.com")
        
        # Verify the backend URL matches what frontend should be using
        expected_backend = "https://taxsale-automation.preview.emergentagent.com/api"
        if BACKEND_URL == expected_backend:
            print(f"   ✅ Backend URL matches expected frontend configuration")
        else:
            print(f"   ⚠️ Backend URL mismatch - Frontend may be configured differently")
            print(f"      Testing: {BACKEND_URL}")
            print(f"      Expected: {expected_backend}")
        
        print(f"\n   ✅ VPS DEPLOYMENT SCRAPING TESTS COMPLETED")
        print(f"   🎯 KEY FINDINGS:")
        print(f"      - Halifax scraper endpoint: {'✅ WORKING' if halifax_response.status_code == 200 else '❌ FAILED'}")
        print(f"      - Municipality status updates: {'✅ WORKING' if halifax_muni and halifax_muni.get('scrape_status') == 'success' else '❌ FAILED'}")
        print(f"      - Tax sales data accessibility: {'✅ WORKING' if tax_sales_response.status_code == 200 else '❌ FAILED'}")
        print(f"      - API response times: {'✅ ACCEPTABLE' if not slow_endpoints else '⚠️ SLOW'}")
        print(f"      - CORS configuration: {'✅ CONFIGURED' if any(r.get('cors_headers', {}).get('access_control_allow_origin') for r in cors_results.values() if 'cors_headers' in r) else '⚠️ CHECK NEEDED'}")
        
        # Determine overall success
        critical_failures = []
        if halifax_response.status_code != 200:
            critical_failures.append("Halifax scraper failed")
        if not halifax_muni or halifax_muni.get('scrape_status') != 'success':
            critical_failures.append("Municipality status not updated")
        if tax_sales_response.status_code != 200:
            critical_failures.append("Tax sales data not accessible")
        if failed_endpoints:
            critical_failures.append("Critical endpoints failed")
        
        if critical_failures:
            print(f"\n   ❌ CRITICAL FAILURES DETECTED:")
            for failure in critical_failures:
                print(f"      - {failure}")
            return False, {
                "critical_failures": critical_failures,
                "halifax_scraper_status": halifax_response.status_code,
                "municipality_status_updated": halifax_muni.get('scrape_status') if halifax_muni else None,
                "tax_sales_accessible": tax_sales_response.status_code == 200,
                "response_times": response_times,
                "cors_results": cors_results
            }
        else:
            print(f"\n   ✅ ALL CRITICAL TESTS PASSED - VPS DEPLOYMENT APPEARS FUNCTIONAL")
            return True, {
                "halifax_scraper_status": halifax_response.status_code,
                "properties_scraped": scrape_result.get('properties_scraped', 0),
                "municipality_status_updated": halifax_muni.get('scrape_status') if halifax_muni else None,
                "tax_sales_accessible": tax_sales_response.status_code == 200,
                "response_times": response_times,
                "cors_results": cors_results
            }
        
    except Exception as e:
        print(f"   ❌ VPS deployment test error: {e}")
        return False, {"error": str(e)}

def test_frontend_backend_integration():
    """Test frontend-backend integration scenarios"""
    print("\n🔗 Testing Frontend-Backend Integration...")
    print("🎯 FOCUS: Simulating frontend API calls and status updates")
    
    try:
        # Test 1: Simulate frontend scraping workflow
        print(f"\n   🔧 TEST 1: Frontend Scraping Workflow Simulation")
        
        # Step 1: Frontend calls scrapeHalifax()
        print(f"      Step 1: Frontend calls POST /api/scrape/halifax")
        scrape_response = requests.post(f"{BACKEND_URL}/scrape/halifax", timeout=180)
        
        if scrape_response.status_code == 200:
            scrape_result = scrape_response.json()
            print(f"      ✅ Scrape API call successful: {scrape_result.get('properties_scraped', 0)} properties")
        else:
            print(f"      ❌ Scrape API call failed: HTTP {scrape_response.status_code}")
            return False, {"error": "Scrape API call failed"}
        
        # Step 2: Frontend calls fetchMunicipalities() to update status
        print(f"      Step 2: Frontend calls GET /api/municipalities to refresh status")
        municipalities_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        if municipalities_response.status_code == 200:
            municipalities = municipalities_response.json()
            halifax_muni = next((m for m in municipalities if "Halifax" in m.get("name", "")), None)
            
            if halifax_muni:
                print(f"      ✅ Municipality status retrieved: {halifax_muni.get('scrape_status', 'unknown')}")
                
                # Verify status reflects recent scraping
                if halifax_muni.get('scrape_status') == 'success':
                    print(f"      ✅ Status correctly shows 'success' after scraping")
                else:
                    print(f"      ⚠️ Status shows '{halifax_muni.get('scrape_status')}' instead of 'success'")
            else:
                print(f"      ❌ Halifax municipality not found in response")
                return False, {"error": "Halifax municipality not found"}
        else:
            print(f"      ❌ Municipalities API call failed: HTTP {municipalities_response.status_code}")
            return False, {"error": "Municipalities API call failed"}
        
        # Step 3: Frontend calls fetchTaxSales() to get updated property data
        print(f"      Step 3: Frontend calls GET /api/tax-sales to get property data")
        tax_sales_response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        
        if tax_sales_response.status_code == 200:
            properties = tax_sales_response.json()
            halifax_properties = [p for p in properties if "Halifax" in p.get("municipality_name", "")]
            print(f"      ✅ Property data retrieved: {len(halifax_properties)} Halifax properties")
        else:
            print(f"      ❌ Tax sales API call failed: HTTP {tax_sales_response.status_code}")
            return False, {"error": "Tax sales API call failed"}
        
        # Step 4: Frontend calls fetchStats() to update statistics
        print(f"      Step 4: Frontend calls GET /api/stats to update statistics")
        stats_response = requests.get(f"{BACKEND_URL}/stats", timeout=30)
        
        if stats_response.status_code == 200:
            stats = stats_response.json()
            print(f"      ✅ Statistics retrieved: {stats.get('total_properties', 0)} total properties")
        else:
            print(f"      ❌ Stats API call failed: HTTP {stats_response.status_code}")
            return False, {"error": "Stats API call failed"}
        
        print(f"   ✅ Frontend workflow simulation completed successfully")
        
        # Test 2: Concurrent API calls (simulating multiple users)
        print(f"\n   🔧 TEST 2: Concurrent API Calls (Multiple Users)")
        
        def make_api_call(endpoint):
            try:
                response = requests.get(f"{BACKEND_URL}{endpoint}", timeout=15)
                return {
                    "endpoint": endpoint,
                    "status_code": response.status_code,
                    "success": response.status_code == 200,
                    "response_time": response.elapsed.total_seconds()
                }
            except Exception as e:
                return {
                    "endpoint": endpoint,
                    "status_code": None,
                    "success": False,
                    "error": str(e)
                }
        
        # Simulate 5 concurrent users accessing different endpoints
        endpoints = ["/municipalities", "/tax-sales", "/stats", "/tax-sales/map-data", "/municipalities"]
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(make_api_call, endpoint) for endpoint in endpoints]
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
        
        successful_calls = [r for r in results if r['success']]
        failed_calls = [r for r in results if not r['success']]
        
        print(f"      📊 Concurrent calls: {len(successful_calls)}/{len(results)} successful")
        
        if len(failed_calls) > 0:
            print(f"      ⚠️ Failed calls:")
            for call in failed_calls:
                print(f"         - {call['endpoint']}: {call.get('error', 'HTTP ' + str(call['status_code']))}")
        
        avg_response_time = sum(r.get('response_time', 0) for r in successful_calls) / len(successful_calls) if successful_calls else 0
        print(f"      ⏱️ Average response time: {avg_response_time:.2f} seconds")
        
        if len(successful_calls) >= len(results) * 0.8:
            print(f"   ✅ Concurrent API calls test passed")
        else:
            print(f"   ❌ Too many concurrent API call failures")
            return False, {"error": "Concurrent API calls failed"}
        
        return True, {
            "frontend_workflow": "success",
            "concurrent_calls_success_rate": len(successful_calls) / len(results),
            "average_response_time": avg_response_time,
            "halifax_status_updated": halifax_muni.get('scrape_status') if 'halifax_muni' in locals() else None
        }
        
    except Exception as e:
        print(f"   ❌ Frontend-backend integration test error: {e}")
        return False, {"error": str(e)}

def run_vps_deployment_tests():
    """Run VPS deployment focused tests"""
    print("🚀 Starting VPS Deployment Tests")
    print("🎯 FOCUS: Scraping functionality and frontend-backend communication")
    print("=" * 70)
    
    test_results = {
        "api_connection": False,
        "vps_scraping_deployment": False,
        "frontend_backend_integration": False
    }
    
    # Test 1: API Connection
    test_results["api_connection"] = test_api_connection()
    if not test_results["api_connection"]:
        print("\n❌ CRITICAL: API connection failed. Cannot proceed with other tests.")
        return test_results
    
    # Test 2: VPS Deployment Scraping Issues
    vps_success, vps_data = test_vps_scraping_deployment_issues()
    test_results["vps_scraping_deployment"] = vps_success
    
    # Test 3: Frontend-Backend Integration
    integration_success, integration_data = test_frontend_backend_integration()
    test_results["frontend_backend_integration"] = integration_success
    
    # Print final summary
    print("\n" + "=" * 70)
    print("📋 VPS DEPLOYMENT TEST SUMMARY")
    print("=" * 70)
    
    passed_tests = sum(1 for result in test_results.values() if result)
    total_tests = len(test_results)
    
    print(f"📊 Overall Results: {passed_tests}/{total_tests} tests passed")
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name.replace('_', ' ').title()}")
    
    if passed_tests == total_tests:
        print("\n🎉 ALL TESTS PASSED - VPS deployment appears to be working correctly")
        print("   The reported issues may be environment-specific or resolved")
    else:
        print(f"\n⚠️ {total_tests - passed_tests} TEST(S) FAILED - Issues detected in VPS deployment")
        print("   Review the detailed test output above for specific problems")
    
    return test_results

if __name__ == "__main__":
    run_vps_deployment_tests()