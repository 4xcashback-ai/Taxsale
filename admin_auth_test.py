#!/usr/bin/env python3
"""
Admin Authentication Testing for Tax Sale Compass
Focus on specific review request requirements:
1. Admin Login Testing: POST /api/users/login with admin@taxsalecompass.ca / admin123
2. JWT Token Validation: GET /api/users/me endpoint with valid JWT token  
3. Property Data Access: GET /api/tax-sales endpoint to verify properties are accessible
4. Municipality Data: GET /api/municipalities endpoint to verify dropdown data
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://nstax-boundary.preview.emergentagent.com') + '/api'

# Admin credentials from review request
ADMIN_EMAIL = "admin@taxsalecompass.ca"
ADMIN_PASSWORD = "admin123"

def test_admin_login():
    """Test admin login with specific credentials from review request"""
    print("🔐 Testing Admin Login...")
    print(f"🔍 FOCUS: POST {BACKEND_URL}/users/login")
    print(f"📋 CREDENTIALS: {ADMIN_EMAIL} / {ADMIN_PASSWORD}")
    print("📋 EXPECTED: Return JWT token on successful login")
    
    try:
        login_data = {
            "email": ADMIN_EMAIL,
            "password": ADMIN_PASSWORD
        }
        
        response = requests.post(f"{BACKEND_URL}/users/login", 
                               json=login_data,
                               timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Admin login successful")
            
            # Check response structure
            required_fields = ["access_token", "token_type", "user"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   ❌ Missing fields in response: {missing_fields}")
                return False, {"error": f"Missing fields: {missing_fields}"}
            
            # Check user data
            user_data = data["user"]
            print(f"   📋 User email: {user_data.get('email')}")
            print(f"   📋 Subscription tier: {user_data.get('subscription_tier')}")
            print(f"   📋 JWT token: {data.get('access_token')[:20]}...")
            
            if user_data.get("email") == ADMIN_EMAIL:
                print("   ✅ Admin credentials validated correctly")
                return True, {
                    "access_token": data.get("access_token"),
                    "user_data": user_data
                }
            else:
                print(f"   ❌ Email mismatch in response")
                return False, {"error": "Email mismatch"}
                
        else:
            print(f"   ❌ Admin login failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
                return False, error_data
            except:
                print(f"   Raw response: {response.text}")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ Admin login error: {e}")
        return False, {"error": str(e)}

def test_jwt_token_validation(access_token):
    """Test JWT token validation with GET /api/users/me"""
    print("\n🔒 Testing JWT Token Validation...")
    print(f"🔍 FOCUS: GET {BACKEND_URL}/users/me")
    print("📋 EXPECTED: Return user profile with valid JWT token")
    
    try:
        headers = {"Authorization": f"Bearer {access_token}"}
        
        response = requests.get(f"{BACKEND_URL}/users/me", 
                              headers=headers,
                              timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ JWT token validation successful")
            
            # Check profile data
            required_fields = ["id", "email", "subscription_tier", "is_verified", "created_at"]
            missing_fields = [field for field in required_fields if field not in data]
            
            if missing_fields:
                print(f"   ❌ Missing fields in profile: {missing_fields}")
                return False, {"error": f"Missing fields: {missing_fields}"}
            
            print(f"   📋 Profile email: {data.get('email')}")
            print(f"   📋 Profile subscription: {data.get('subscription_tier')}")
            print(f"   📋 Profile verified: {data.get('is_verified')}")
            print(f"   📋 Profile ID: {data.get('id')}")
            
            if data.get("email") == ADMIN_EMAIL:
                print("   ✅ JWT token validated - profile matches admin user")
                return True, data
            else:
                print(f"   ❌ Profile email mismatch")
                return False, {"error": "Profile mismatch"}
                
        else:
            print(f"   ❌ JWT validation failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
                return False, error_data
            except:
                print(f"   Raw response: {response.text}")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ JWT validation error: {e}")
        return False, {"error": str(e)}

def test_property_data_access():
    """Test GET /api/tax-sales endpoint to verify properties are accessible"""
    print("\n🏠 Testing Property Data Access...")
    print(f"🔍 FOCUS: GET {BACKEND_URL}/tax-sales")
    print("📋 EXPECTED: Return 65+ properties from live site")
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Property data access successful")
            
            # Handle different response formats
            if isinstance(data, dict):
                properties = data.get('properties', [])
                total_count = data.get('total', len(properties))
            else:
                properties = data
                total_count = len(properties)
            
            print(f"   📋 Total properties: {total_count}")
            print(f"   📋 Properties in response: {len(properties)}")
            
            if properties:
                # Check first few properties for structure
                sample_property = properties[0]
                required_fields = ["id", "municipality_name", "property_address", "assessment_number"]
                missing_fields = [field for field in required_fields if field not in sample_property]
                
                if missing_fields:
                    print(f"   ⚠️ Missing fields in property data: {missing_fields}")
                else:
                    print("   ✅ Property data structure looks good")
                
                # Show sample properties
                print(f"   📋 Sample properties:")
                for i, prop in enumerate(properties[:3]):
                    municipality = prop.get('municipality_name', 'Unknown')
                    address = prop.get('property_address', 'Unknown')
                    assessment = prop.get('assessment_number', 'Unknown')
                    print(f"      {i+1}. {municipality}: {address} (AAN: {assessment})")
                
                # Check if we have the expected 65+ properties
                if total_count >= 65:
                    print(f"   ✅ Property count meets expectation (65+ properties)")
                    return True, {"total_properties": total_count, "sample_properties": properties[:5]}
                else:
                    print(f"   ⚠️ Property count below expectation ({total_count} < 65)")
                    return True, {"total_properties": total_count, "sample_properties": properties[:5], "warning": "Low property count"}
            else:
                print(f"   ❌ No properties found in response")
                return False, {"error": "No properties found"}
                
        else:
            print(f"   ❌ Property access failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
                return False, error_data
            except:
                print(f"   Raw response: {response.text}")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ Property access error: {e}")
        return False, {"error": str(e)}

def test_municipality_data():
    """Test GET /api/municipalities endpoint to verify dropdown data"""
    print("\n🏛️ Testing Municipality Data...")
    print(f"🔍 FOCUS: GET {BACKEND_URL}/municipalities")
    print("📋 EXPECTED: Return municipality data for dropdown")
    
    try:
        response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Municipality data access successful")
            
            # Handle different response formats
            if isinstance(data, dict):
                municipalities = data.get('municipalities', [])
            else:
                municipalities = data
            
            print(f"   📋 Total municipalities: {len(municipalities)}")
            
            if municipalities:
                # Check municipality structure
                sample_municipality = municipalities[0]
                required_fields = ["id", "name"]
                missing_fields = [field for field in required_fields if field not in sample_municipality]
                
                if missing_fields:
                    print(f"   ⚠️ Missing fields in municipality data: {missing_fields}")
                else:
                    print("   ✅ Municipality data structure looks good")
                
                # Show sample municipalities
                print(f"   📋 Sample municipalities:")
                for i, muni in enumerate(municipalities[:5]):
                    name = muni.get('name', 'Unknown')
                    region = muni.get('region', 'Unknown')
                    scrape_status = muni.get('scrape_status', 'Unknown')
                    print(f"      {i+1}. {name} ({region}) - Status: {scrape_status}")
                
                return True, {"total_municipalities": len(municipalities), "sample_municipalities": municipalities[:5]}
            else:
                print(f"   ❌ No municipalities found in response")
                return False, {"error": "No municipalities found"}
                
        else:
            print(f"   ❌ Municipality access failed with status {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
                return False, error_data
            except:
                print(f"   Raw response: {response.text}")
                return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ Municipality access error: {e}")
        return False, {"error": str(e)}

def main():
    """Main test execution function - Focus on Review Request Requirements"""
    print("🚀 Starting Admin Authentication Testing for Tax Sale Compass")
    print("=" * 80)
    print("🎯 REVIEW REQUEST: Test the user authentication system")
    print("📋 SPECIFIC REQUIREMENTS:")
    print("   1. Admin Login Testing: POST /api/users/login with admin@taxsalecompass.ca / admin123")
    print("   2. JWT Token Validation: GET /api/users/me endpoint with valid JWT token")
    print("   3. Property Data Access: GET /api/tax-sales endpoint to verify properties are accessible")
    print("   4. Municipality Data: GET /api/municipalities endpoint to verify dropdown data")
    print("🔍 ISSUE: Admin user was created successfully but frontend login is not working")
    print("🎯 GOAL: Verify backend authentication flow is working properly")
    print("=" * 80)
    
    results = {}
    
    # Test 1: Admin Login
    print("\n🔍 TEST 1: Admin Login Testing")
    admin_login_result, admin_login_data = test_admin_login()
    results['admin_login'] = {'success': admin_login_result, 'data': admin_login_data}
    
    if not admin_login_result:
        print("\n❌ Cannot proceed with other tests without successful admin login")
        print("🔧 CRITICAL ISSUE: Admin login is failing - this explains frontend login issues")
        return False
    
    access_token = admin_login_data.get('access_token')
    
    # Test 2: JWT Token Validation
    print("\n🔍 TEST 2: JWT Token Validation")
    jwt_validation_result, jwt_validation_data = test_jwt_token_validation(access_token)
    results['jwt_validation'] = {'success': jwt_validation_result, 'data': jwt_validation_data}
    
    # Test 3: Property Data Access
    print("\n🔍 TEST 3: Property Data Access")
    property_access_result, property_access_data = test_property_data_access()
    results['property_access'] = {'success': property_access_result, 'data': property_access_data}
    
    # Test 4: Municipality Data
    print("\n🔍 TEST 4: Municipality Data")
    municipality_result, municipality_data = test_municipality_data()
    results['municipality_data'] = {'success': municipality_result, 'data': municipality_data}
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("📊 ADMIN AUTHENTICATION TESTING - FINAL ASSESSMENT")
    print("=" * 80)
    
    test_names = [
        ('Admin Login (admin@taxsalecompass.ca / admin123)', 'admin_login'),
        ('JWT Token Validation (/api/users/me)', 'jwt_validation'),
        ('Property Data Access (/api/tax-sales)', 'property_access'),
        ('Municipality Data (/api/municipalities)', 'municipality_data')
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
    
    if results['admin_login']['success']:
        print(f"   ✅ Admin login working: admin@taxsalecompass.ca / admin123 credentials accepted")
        print(f"   ✅ Backend returns JWT token on successful admin login")
        user_data = results['admin_login']['data'].get('user_data', {})
        print(f"   📋 Admin user email: {user_data.get('email')}")
        print(f"   📋 Admin subscription tier: {user_data.get('subscription_tier')}")
    else:
        print(f"   ❌ CRITICAL: Admin login failing - this explains frontend login issues")
        print(f"   🔧 Backend authentication flow has problems")
    
    if results['jwt_validation']['success']:
        print(f"   ✅ JWT token validation working correctly")
        print(f"   ✅ GET /api/users/me endpoint returns admin profile")
    else:
        print(f"   ❌ JWT token validation has issues")
    
    if results['property_access']['success']:
        property_count = results['property_access']['data'].get('total_properties', 0)
        print(f"   ✅ Property data accessible: {property_count} properties found")
        if property_count >= 65:
            print(f"   ✅ Property count meets expectation (65+ properties from live site)")
        else:
            print(f"   ⚠️ Property count below expectation ({property_count} < 65)")
    else:
        print(f"   ❌ Property data access has issues")
    
    if results['municipality_data']['success']:
        municipality_count = results['municipality_data']['data'].get('total_municipalities', 0)
        print(f"   ✅ Municipality data accessible: {municipality_count} municipalities found")
        print(f"   ✅ Dropdown data available for frontend")
    else:
        print(f"   ❌ Municipality data access has issues")
    
    # Overall assessment
    critical_tests_passed = (
        results['admin_login']['success'] and 
        results['jwt_validation']['success']
    )
    
    if critical_tests_passed:
        print(f"\n🎉 BACKEND AUTHENTICATION FLOW: WORKING!")
        print(f"   ✅ Admin login credentials (admin@taxsalecompass.ca / admin123) accepted")
        print(f"   ✅ JWT tokens generated and validated properly")
        print(f"   ✅ Backend authentication endpoints functioning correctly")
        print(f"   🔧 If frontend login still not working, issue is likely in frontend code")
    else:
        print(f"\n❌ BACKEND AUTHENTICATION FLOW: ISSUES IDENTIFIED")
        print(f"   ❌ Admin login or JWT validation failing")
        print(f"   🔧 Backend authentication needs fixes before frontend can work")
    
    return critical_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)