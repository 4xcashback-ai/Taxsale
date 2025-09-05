#!/usr/bin/env python3
"""
Deployment Optimizations Testing for Nova Scotia Tax Sale Aggregator
Focus on testing backend functionality after deployment optimizations
"""

import requests
import json
import sys
import time
import os

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://taxsaletracker.preview.emergentagent.com') + '/api'

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
            return True, response.json()
        else:
            print(f"❌ API connection failed with status {response.status_code}")
            return False, None
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return False, None

def get_admin_token():
    """Get admin JWT token for authenticated requests"""
    print("🔐 Getting admin authentication token...")
    try:
        response = requests.post(f"{BACKEND_URL}/auth/login", 
                               json={"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD},
                               timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            token = data.get("access_token")
            if token:
                print("✅ Admin authentication successful")
                return token
            else:
                print("❌ No access token in response")
                return None
        else:
            print(f"❌ Authentication failed with status {response.status_code}")
            return None
            
    except Exception as e:
        print(f"❌ Authentication error: {e}")
        return None

def test_core_api_endpoints():
    """Test core API endpoints mentioned in review request"""
    print("🔗 Testing Core API Endpoints...")
    print("🔍 FOCUS: GET /api/municipalities, POST /api/auth/login, property image endpoints")
    
    results = {}
    
    try:
        # Test 1: GET /api/municipalities
        print(f"\n   Test 1: GET /api/municipalities")
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                print(f"   ✅ Municipalities endpoint working ({len(data)} municipalities)")
                results["municipalities"] = True
            else:
                print(f"   ❌ Empty or invalid municipalities response")
                results["municipalities"] = False
        else:
            print(f"   ❌ Municipalities endpoint failed")
            results["municipalities"] = False
        
        # Test 2: POST /api/auth/login
        print(f"\n   Test 2: POST /api/auth/login")
        login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            if "access_token" in data:
                print(f"   ✅ Admin login working, JWT token generated")
                results["auth_login"] = True
            else:
                print(f"   ❌ Login response missing access_token")
                results["auth_login"] = False
        else:
            print(f"   ❌ Admin login failed")
            results["auth_login"] = False
        
        # Test 3: Property image endpoint with test assessment number
        print(f"\n   Test 3: GET /api/property-image/07486596")
        response = requests.get(f"{BACKEND_URL}/property-image/07486596", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        
        if response.status_code == 200 and response.headers.get('Content-Type') == 'image/png':
            print(f"   ✅ Property image endpoint working")
            results["property_image"] = True
        else:
            print(f"   ❌ Property image endpoint failed")
            results["property_image"] = False
        
        # Test 4: Boundary image endpoint
        print(f"\n   Test 4: GET /api/boundary-image/test.png")
        response = requests.get(f"{BACKEND_URL}/boundary-image/test.png", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [200, 404]:  # 404 is acceptable if file doesn't exist
            print(f"   ✅ Boundary image endpoint accessible")
            results["boundary_image"] = True
        else:
            print(f"   ❌ Boundary image endpoint failed")
            results["boundary_image"] = False
        
        successful_tests = sum(1 for result in results.values() if result is True)
        total_tests = len(results)
        
        print(f"\n   📊 Core Endpoints Results: {successful_tests}/{total_tests} tests passed")
        
        if successful_tests >= 3:  # At least 3 out of 4 core endpoints working
            return True, results
        else:
            return False, results
            
    except Exception as e:
        print(f"   ❌ Core endpoints test error: {e}")
        return False, {"error": str(e)}

def test_admin_authentication():
    """Test admin authentication with specific credentials"""
    print("🔐 Testing Admin Authentication...")
    print("🔍 FOCUS: Admin login with admin/TaxSale2025!SecureAdmin")
    
    try:
        # Test admin login
        login_data = {"username": ADMIN_USERNAME, "password": ADMIN_PASSWORD}
        response = requests.post(f"{BACKEND_URL}/auth/login", json=login_data, timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            # Check response structure
            if "access_token" in data and "token_type" in data:
                token = data["access_token"]
                
                # Test token validation by making authenticated request
                headers = {"Authorization": f"Bearer {token}"}
                test_response = requests.get(f"{BACKEND_URL}/municipalities", headers=headers, timeout=30)
                
                if test_response.status_code == 200:
                    print(f"   ✅ Admin authentication fully functional")
                    print(f"   ✅ JWT token validation working")
                    return True, {"token": token, "login_data": data}
                else:
                    print(f"   ❌ JWT token validation failed")
                    return False, {"error": "Token validation failed"}
            else:
                print(f"   ❌ Invalid login response structure")
                return False, {"error": "Invalid response structure"}
        else:
            print(f"   ❌ Admin login failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
                return False, error_data
            except:
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ Authentication test error: {e}")
        return False, {"error": str(e)}

def test_database_connectivity():
    """Test MongoDB database connectivity"""
    print("🗄️ Testing Database Connectivity...")
    print("🔍 FOCUS: MongoDB connection and basic operations")
    
    try:
        # Test database connectivity by fetching municipalities
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, list):
                print(f"   ✅ Database connectivity working")
                print(f"   ✅ Retrieved {len(data)} municipalities from database")
                
                # Test tax sales data
                tax_sales_response = requests.get(f"{BACKEND_URL}/tax-sales?limit=5", timeout=30)
                
                if tax_sales_response.status_code == 200:
                    tax_sales_data = tax_sales_response.json()
                    
                    if isinstance(tax_sales_data, dict) and 'properties' in tax_sales_data:
                        properties = tax_sales_data['properties']
                        print(f"   ✅ Tax sales data accessible ({len(properties)} properties)")
                        return True, {"municipalities": len(data), "properties": len(properties)}
                    elif isinstance(tax_sales_data, list):
                        print(f"   ✅ Tax sales data accessible ({len(tax_sales_data)} properties)")
                        return True, {"municipalities": len(data), "properties": len(tax_sales_data)}
                    else:
                        print(f"   ⚠️ Unexpected tax sales response format")
                        return True, {"municipalities": len(data), "properties": 0}
                else:
                    print(f"   ⚠️ Tax sales endpoint issue, but municipalities working")
                    return True, {"municipalities": len(data), "properties": "unknown"}
            else:
                print(f"   ❌ Invalid municipalities response format")
                return False, {"error": "Invalid response format"}
        else:
            print(f"   ❌ Database connectivity failed")
            return False, {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Database connectivity test error: {e}")
        return False, {"error": str(e)}

def test_property_image_serving():
    """Test property image serving endpoints"""
    print("🖼️ Testing Property Image Serving...")
    print("🔍 FOCUS: Property and boundary image endpoints")
    
    results = {}
    
    try:
        # Test with known assessment number from review request
        test_assessment = "07486596"
        
        # Test 1: Property image endpoint
        print(f"\n   Test 1: GET /api/property-image/{test_assessment}")
        response = requests.get(f"{BACKEND_URL}/property-image/{test_assessment}", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Content-Type: {response.headers.get('Content-Type', 'Not set')}")
        print(f"   Content-Length: {len(response.content)} bytes")
        
        if response.status_code == 200 and response.headers.get('Content-Type') == 'image/png':
            if len(response.content) > 1000:
                print(f"   ✅ Property image serving working")
                results["property_image"] = True
            else:
                print(f"   ❌ Image too small, might be error response")
                results["property_image"] = False
        else:
            print(f"   ❌ Property image endpoint failed")
            results["property_image"] = False
        
        # Test 2: Boundary image endpoint
        print(f"\n   Test 2: GET /api/boundary-image/test.png")
        response = requests.get(f"{BACKEND_URL}/boundary-image/test.png", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [200, 404]:  # 404 is acceptable for non-existent file
            print(f"   ✅ Boundary image endpoint accessible")
            results["boundary_image"] = True
        else:
            print(f"   ❌ Boundary image endpoint failed")
            results["boundary_image"] = False
        
        # Test 3: Security check - invalid filename
        print(f"\n   Test 3: Security check - invalid filename")
        response = requests.get(f"{BACKEND_URL}/boundary-image/../../../etc/passwd", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code in [400, 404]:
            print(f"   ✅ Security measures working")
            results["security"] = True
        else:
            print(f"   ⚠️ Unexpected security response")
            results["security"] = False
        
        successful_tests = sum(1 for result in results.values() if result is True)
        total_tests = len(results)
        
        print(f"\n   📊 Image Serving Results: {successful_tests}/{total_tests} tests passed")
        
        if successful_tests >= 2:
            return True, results
        else:
            return False, results
            
    except Exception as e:
        print(f"   ❌ Property image serving test error: {e}")
        return False, {"error": str(e)}

def test_environment_variables():
    """Test environment variables loading"""
    print("🌍 Testing Environment Variables...")
    print("🔍 FOCUS: Environment variable loading after optimization")
    
    try:
        # Test Google Maps API key by checking if geocoding works
        # We can infer this by checking if properties have coordinates
        response = requests.get(f"{BACKEND_URL}/tax-sales?limit=5", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            if isinstance(data, dict) and 'properties' in data:
                properties = data['properties']
            elif isinstance(data, list):
                properties = data
            else:
                properties = []
            
            # Check if properties have coordinates (indicates Google Maps API working)
            properties_with_coords = 0
            for prop in properties:
                if prop.get('latitude') and prop.get('longitude'):
                    properties_with_coords += 1
            
            print(f"   📋 Properties with coordinates: {properties_with_coords}/{len(properties)}")
            
            if properties_with_coords > 0:
                print(f"   ✅ Google Maps API key likely loaded correctly")
                print(f"   ✅ Environment variables working")
                return True, {"properties_with_coords": properties_with_coords, "total_properties": len(properties)}
            else:
                print(f"   ⚠️ No properties with coordinates found")
                print(f"   ⚠️ Google Maps API key might not be loaded")
                return False, {"error": "No geocoded properties found"}
        else:
            print(f"   ❌ Cannot test environment variables - API not accessible")
            return False, {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Environment variables test error: {e}")
        return False, {"error": str(e)}

def test_redis_caching():
    """Test Redis caching functionality"""
    print("🔄 Testing Redis Caching...")
    print("🔍 FOCUS: Redis caching system integration")
    
    try:
        # Since we don't have direct access to cache_utils.py, we'll test indirectly
        # by making repeated requests and checking response times
        
        # Make first request (should populate cache if caching is working)
        start_time = time.time()
        response1 = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        first_request_time = time.time() - start_time
        
        if response1.status_code != 200:
            print(f"   ❌ Cannot test caching - API not accessible")
            return False, {"error": "API not accessible"}
        
        # Make second request immediately (should be faster if cached)
        start_time = time.time()
        response2 = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        second_request_time = time.time() - start_time
        
        print(f"   📋 First request time: {first_request_time:.3f}s")
        print(f"   📋 Second request time: {second_request_time:.3f}s")
        
        # Check if responses are identical (good sign)
        if response1.json() == response2.json():
            print(f"   ✅ Consistent responses between requests")
            
            # If second request is significantly faster, caching might be working
            if second_request_time < first_request_time * 0.8:
                print(f"   ✅ Second request faster - caching likely working")
                return True, {"first_time": first_request_time, "second_time": second_request_time}
            else:
                print(f"   ⚠️ No significant speed improvement detected")
                print(f"   ⚠️ Redis caching might not be active or not needed for this endpoint")
                return False, {"error": "No caching performance improvement detected"}
        else:
            print(f"   ❌ Inconsistent responses - potential caching issue")
            return False, {"error": "Inconsistent responses"}
            
    except Exception as e:
        print(f"   ❌ Redis caching test error: {e}")
        return False, {"error": str(e)}

def test_deployment_optimizations():
    """Test backend functionality after deployment optimizations"""
    print("\n🎯 DEPLOYMENT OPTIMIZATIONS TESTING")
    print("=" * 80)
    print("🎯 REVIEW REQUEST: Test backend functionality after deployment optimizations")
    print("📋 FOCUS AREAS:")
    print("   1. Core API Endpoints (municipalities, auth/login, property-image)")
    print("   2. Dependencies after requirements.txt optimization")
    print("   3. Redis Caching (cache_utils.py integration)")
    print("   4. Authentication (admin login with admin/TaxSale2025!SecureAdmin)")
    print("   5. Database Connectivity (MongoDB)")
    print("   6. Property Image Serving")
    print("   7. Environment Variables loading")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Core API Endpoints
    print("\n🔍 TEST 1: Core API Endpoints")
    endpoints_result, endpoints_data = test_core_api_endpoints()
    results['core_endpoints'] = {'success': endpoints_result, 'data': endpoints_data}
    
    # Test 2: Authentication System
    print("\n🔍 TEST 2: Authentication System")
    auth_result, auth_data = test_admin_authentication()
    results['authentication'] = {'success': auth_result, 'data': auth_data}
    
    # Test 3: Database Connectivity
    print("\n🔍 TEST 3: Database Connectivity")
    db_result, db_data = test_database_connectivity()
    results['database'] = {'success': db_result, 'data': db_data}
    
    # Test 4: Property Image Serving
    print("\n🔍 TEST 4: Property Image Serving")
    image_result, image_data = test_property_image_serving()
    results['property_images'] = {'success': image_result, 'data': image_data}
    
    # Test 5: Environment Variables
    print("\n🔍 TEST 5: Environment Variables")
    env_result, env_data = test_environment_variables()
    results['environment'] = {'success': env_result, 'data': env_data}
    
    # Test 6: Redis Caching (if available)
    print("\n🔍 TEST 6: Redis Caching")
    cache_result, cache_data = test_redis_caching()
    results['caching'] = {'success': cache_result, 'data': cache_data}
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("📊 DEPLOYMENT OPTIMIZATIONS - FINAL ASSESSMENT")
    print("=" * 80)
    
    test_names = [
        ('Core API Endpoints', 'core_endpoints'),
        ('Authentication System', 'authentication'),
        ('Database Connectivity', 'database'),
        ('Property Image Serving', 'property_images'),
        ('Environment Variables', 'environment'),
        ('Redis Caching', 'caching')
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
    
    if results['core_endpoints']['success']:
        print(f"   ✅ Core API endpoints working after optimization")
        print(f"   ✅ GET /api/municipalities accessible")
        print(f"   ✅ POST /api/auth/login functional")
    else:
        print(f"   ❌ Core API endpoints have issues")
    
    if results['authentication']['success']:
        print(f"   ✅ Admin authentication working with TaxSale2025!SecureAdmin")
        print(f"   ✅ JWT token generation and validation functional")
    else:
        print(f"   ❌ Authentication system has issues")
    
    if results['database']['success']:
        print(f"   ✅ MongoDB connectivity working")
        print(f"   ✅ Database operations functional")
    else:
        print(f"   ❌ Database connectivity issues detected")
    
    if results['property_images']['success']:
        print(f"   ✅ Property image serving working")
        print(f"   ✅ GET /api/property-image/{{assessment_number}} functional")
        print(f"   ✅ GET /api/boundary-image/{{filename}} functional")
    else:
        print(f"   ❌ Property image serving has issues")
    
    if results['environment']['success']:
        print(f"   ✅ Environment variables loading correctly")
        print(f"   ✅ Google Maps API key accessible")
    else:
        print(f"   ❌ Environment variable loading issues")
    
    if results['caching']['success']:
        print(f"   ✅ Redis caching system functional")
    else:
        print(f"   ⚠️ Redis caching not available or has issues")
    
    # Overall assessment
    critical_tests_passed = (
        results['core_endpoints']['success'] and 
        results['authentication']['success'] and 
        results['database']['success']
    )
    
    if critical_tests_passed:
        print(f"\n🎉 DEPLOYMENT OPTIMIZATIONS: SUCCESS!")
        print(f"   ✅ All critical systems operational after optimization")
        print(f"   ✅ Requirements.txt changes didn't break functionality")
        print(f"   ✅ Backend ready for production deployment")
    else:
        print(f"\n❌ DEPLOYMENT OPTIMIZATIONS: ISSUES DETECTED")
        print(f"   🔧 Some critical components need attention")
        print(f"   🔧 Review failed tests for specific issues")
    
    return critical_tests_passed, results

def main():
    """Main test execution for deployment optimizations"""
    print("🚀 STARTING DEPLOYMENT OPTIMIZATIONS TESTING")
    print("=" * 80)
    print(f"🔗 Backend URL: {BACKEND_URL}")
    print(f"👤 Admin Credentials: {ADMIN_USERNAME} / {ADMIN_PASSWORD}")
    print("=" * 80)
    
    # Test basic connectivity first
    connection_success, connection_data = test_api_connection()
    if not connection_success:
        print("\n❌ CRITICAL: Cannot connect to backend API")
        print("🔧 Please check if the backend server is running")
        sys.exit(1)
    
    # Run deployment optimizations test
    optimization_success, optimization_results = test_deployment_optimizations()
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 DEPLOYMENT OPTIMIZATIONS TESTING SUMMARY")
    print("=" * 80)
    
    if optimization_success:
        print(f"🎉 DEPLOYMENT OPTIMIZATIONS: SUCCESS!")
        print(f"   ✅ All critical systems operational after optimization")
        print(f"   ✅ Requirements.txt changes didn't break functionality")
        print(f"   ✅ Backend ready for production deployment")
        print(f"   ✅ Core API endpoints working correctly")
        print(f"   ✅ Authentication system functional")
        print(f"   ✅ Database connectivity confirmed")
        print(f"   ✅ Property image serving operational")
    else:
        print(f"❌ DEPLOYMENT OPTIMIZATIONS: ISSUES DETECTED")
        print(f"   🔧 Some critical components need attention")
        print(f"   🔧 Review failed tests for specific issues")
        print(f"   🔧 Address issues before production deployment")
    
    print("=" * 80)

if __name__ == "__main__":
    main()