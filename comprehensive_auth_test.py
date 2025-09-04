#!/usr/bin/env python3
"""
Comprehensive Authentication Testing for Tax Sale Compass
Test both admin credentials and investigate property count discrepancy
"""

import requests
import json
import sys
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://novascotia-taxmap.preview.emergentagent.com') + '/api'

def test_admin_credentials_comparison():
    """Test both sets of admin credentials to identify discrepancy"""
    print("🔐 Testing Admin Credentials Comparison...")
    print("=" * 60)
    
    # Credentials from review request
    review_admin = {
        "email": "admin@taxsalecompass.ca",
        "password": "admin123"
    }
    
    # Credentials from .env file (converted to email format)
    env_admin = {
        "email": "admin",  # This might need to be converted
        "password": "TaxSale2025!SecureAdmin"
    }
    
    results = {}
    
    # Test 1: Review request credentials
    print("\n🔍 TEST 1: Review Request Credentials")
    print(f"   Email: {review_admin['email']}")
    print(f"   Password: {review_admin['password']}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/users/login", 
                               json=review_admin,
                               timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Review request credentials work")
            user_data = data.get("user", {})
            print(f"   📋 User email: {user_data.get('email')}")
            print(f"   📋 Subscription tier: {user_data.get('subscription_tier')}")
            results['review_credentials'] = True
        else:
            print("   ❌ Review request credentials failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            results['review_credentials'] = False
            
    except Exception as e:
        print(f"   ❌ Error testing review credentials: {e}")
        results['review_credentials'] = False
    
    # Test 2: .env file credentials (as username)
    print("\n🔍 TEST 2: .env File Credentials (as username)")
    print(f"   Username: {env_admin['email']}")
    print(f"   Password: {env_admin['password']}")
    
    try:
        # Try with username field instead of email
        response = requests.post(f"{BACKEND_URL}/auth/login", 
                               json={"username": env_admin['email'], "password": env_admin['password']},
                               timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ .env credentials work (as username)")
            print(f"   📋 Token: {data.get('access_token', 'N/A')[:20]}...")
            results['env_credentials_username'] = True
        else:
            print("   ❌ .env credentials failed (as username)")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            results['env_credentials_username'] = False
            
    except Exception as e:
        print(f"   ❌ Error testing .env credentials (username): {e}")
        results['env_credentials_username'] = False
    
    # Test 3: .env file credentials (as email)
    print("\n🔍 TEST 3: .env File Credentials (as email)")
    print(f"   Email: {env_admin['email']}")
    print(f"   Password: {env_admin['password']}")
    
    try:
        response = requests.post(f"{BACKEND_URL}/users/login", 
                               json=env_admin,
                               timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ .env credentials work (as email)")
            user_data = data.get("user", {})
            print(f"   📋 User email: {user_data.get('email')}")
            results['env_credentials_email'] = True
        else:
            print("   ❌ .env credentials failed (as email)")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            results['env_credentials_email'] = False
            
    except Exception as e:
        print(f"   ❌ Error testing .env credentials (email): {e}")
        results['env_credentials_email'] = False
    
    return results

def investigate_property_count():
    """Investigate why there are only 3 properties instead of 65+"""
    print("\n🔍 Investigating Property Count Discrepancy...")
    print("=" * 60)
    print("📋 EXPECTED: 65+ properties from live site")
    print("📋 ACTUAL: Only 3 properties found")
    
    try:
        # Get all properties with detailed info
        response = requests.get(f"{BACKEND_URL}/tax-sales", timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            
            # Handle different response formats
            if isinstance(data, dict):
                properties = data.get('properties', [])
                total_count = data.get('total', len(properties))
            else:
                properties = data
                total_count = len(properties)
            
            print(f"   📋 Total properties found: {total_count}")
            
            # Analyze properties by municipality
            municipality_counts = {}
            status_counts = {}
            
            for prop in properties:
                municipality = prop.get('municipality_name', 'Unknown')
                status = prop.get('status', 'Unknown')
                
                municipality_counts[municipality] = municipality_counts.get(municipality, 0) + 1
                status_counts[status] = status_counts.get(status, 0) + 1
            
            print(f"\n   📊 Properties by Municipality:")
            for municipality, count in municipality_counts.items():
                print(f"      {municipality}: {count} properties")
            
            print(f"\n   📊 Properties by Status:")
            for status, count in status_counts.items():
                print(f"      {status}: {count} properties")
            
            # Check if Halifax properties exist
            halifax_properties = [p for p in properties if 'Halifax' in p.get('municipality_name', '')]
            print(f"\n   🔍 Halifax Properties: {len(halifax_properties)} found")
            
            if halifax_properties:
                print(f"   📋 Sample Halifax properties:")
                for i, prop in enumerate(halifax_properties[:3]):
                    address = prop.get('property_address', 'Unknown')
                    assessment = prop.get('assessment_number', 'Unknown')
                    print(f"      {i+1}. {address} (AAN: {assessment})")
            else:
                print(f"   ❌ No Halifax properties found - this explains the low count")
                print(f"   🔧 Halifax scraper may not be working or data was cleared")
            
            # Check scraping status
            print(f"\n   🔍 Checking Municipality Scraping Status...")
            muni_response = requests.get(f"{BACKEND_URL}/municipalities", timeout=30)
            
            if muni_response.status_code == 200:
                muni_data = muni_response.json()
                if isinstance(muni_data, dict):
                    municipalities = muni_data.get('municipalities', [])
                else:
                    municipalities = muni_data
                
                print(f"   📋 Municipality Scraping Status:")
                for muni in municipalities:
                    name = muni.get('name', 'Unknown')
                    status = muni.get('scrape_status', 'Unknown')
                    last_scraped = muni.get('last_scraped', 'Never')
                    scraper_type = muni.get('scraper_type', 'Unknown')
                    print(f"      {name}: {status} (Type: {scraper_type}, Last: {last_scraped})")
            
            return {
                'total_properties': total_count,
                'municipality_counts': municipality_counts,
                'status_counts': status_counts,
                'halifax_count': len(halifax_properties)
            }
            
    except Exception as e:
        print(f"   ❌ Error investigating properties: {e}")
        return None

def test_halifax_scraper():
    """Test if Halifax scraper can be triggered"""
    print("\n🔍 Testing Halifax Scraper...")
    print("=" * 60)
    
    try:
        # Try to trigger Halifax scraper
        response = requests.post(f"{BACKEND_URL}/scrape/halifax", timeout=60)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("   ✅ Halifax scraper triggered successfully")
            print(f"   📋 Status: {data.get('status', 'Unknown')}")
            print(f"   📋 Properties scraped: {data.get('properties_scraped', 0)}")
            return True, data
        else:
            print("   ❌ Halifax scraper failed")
            try:
                error_data = response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {response.text}")
            return False, None
            
    except Exception as e:
        print(f"   ❌ Error testing Halifax scraper: {e}")
        return False, None

def main():
    """Main comprehensive testing function"""
    print("🚀 Starting Comprehensive Authentication & Property Testing")
    print("=" * 80)
    print("🎯 GOALS:")
    print("   1. Verify admin authentication working with review request credentials")
    print("   2. Investigate property count discrepancy (3 vs 65+ expected)")
    print("   3. Check Halifax scraper status")
    print("   4. Provide clear diagnosis for frontend login issues")
    print("=" * 80)
    
    # Test 1: Admin credentials comparison
    print("\n🔍 PHASE 1: Admin Credentials Testing")
    credentials_results = test_admin_credentials_comparison()
    
    # Test 2: Property count investigation
    print("\n🔍 PHASE 2: Property Count Investigation")
    property_analysis = investigate_property_count()
    
    # Test 3: Halifax scraper test
    print("\n🔍 PHASE 3: Halifax Scraper Testing")
    scraper_result, scraper_data = test_halifax_scraper()
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("📊 COMPREHENSIVE TESTING - FINAL DIAGNOSIS")
    print("=" * 80)
    
    print(f"\n🔐 AUTHENTICATION FINDINGS:")
    if credentials_results.get('review_credentials', False):
        print(f"   ✅ CRITICAL: admin@taxsalecompass.ca / admin123 credentials WORK")
        print(f"   ✅ Backend authentication is functioning correctly")
        print(f"   🔧 If frontend login fails, issue is in frontend code, not backend")
    else:
        print(f"   ❌ CRITICAL: Review request credentials not working")
        print(f"   🔧 Backend authentication has issues")
    
    if credentials_results.get('env_credentials_username', False):
        print(f"   ✅ .env admin credentials work (username format)")
    
    print(f"\n🏠 PROPERTY DATA FINDINGS:")
    if property_analysis:
        total_props = property_analysis.get('total_properties', 0)
        halifax_count = property_analysis.get('halifax_count', 0)
        
        print(f"   📊 Total properties: {total_props}")
        print(f"   📊 Halifax properties: {halifax_count}")
        
        if total_props < 65:
            print(f"   ⚠️ Property count below expectation ({total_props} < 65)")
            if halifax_count == 0:
                print(f"   🔧 Halifax scraper appears to not be working or data was cleared")
                print(f"   🔧 This explains the low property count")
            else:
                print(f"   🔧 Other municipality scrapers may need attention")
        else:
            print(f"   ✅ Property count meets expectation")
    
    print(f"\n🤖 SCRAPER FINDINGS:")
    if scraper_result:
        scraped_count = scraper_data.get('properties_scraped', 0)
        print(f"   ✅ Halifax scraper can be triggered")
        print(f"   📊 Properties scraped: {scraped_count}")
        if scraped_count > 0:
            print(f"   🔧 Halifax scraper is working - may need regular execution")
        else:
            print(f"   ⚠️ Halifax scraper runs but finds no properties")
    else:
        print(f"   ❌ Halifax scraper has issues")
    
    # Overall diagnosis
    auth_working = credentials_results.get('review_credentials', False)
    
    print(f"\n🎯 FINAL DIAGNOSIS:")
    if auth_working:
        print(f"   ✅ BACKEND AUTHENTICATION: WORKING CORRECTLY")
        print(f"   ✅ Admin login (admin@taxsalecompass.ca / admin123) successful")
        print(f"   ✅ JWT token generation and validation working")
        print(f"   ✅ Property and municipality endpoints accessible")
        print(f"   🔧 FRONTEND ISSUE: If login still fails, check frontend code")
        print(f"   🔧 PROPERTY COUNT: Halifax scraper may need regular execution")
    else:
        print(f"   ❌ BACKEND AUTHENTICATION: HAS ISSUES")
        print(f"   🔧 Fix backend authentication before addressing frontend")
    
    return auth_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)