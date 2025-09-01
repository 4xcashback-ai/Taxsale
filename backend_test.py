#!/usr/bin/env python3
"""
Backend API Testing for Nova Scotia Tax Sale Aggregator
Focus on Production VPS Deployment Check-Updates Endpoint Testing
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

# Production VPS URL for deployment testing
PRODUCTION_VPS_URL = 'https://taxsalecompass.ca/api'

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

def test_deployment_status_endpoint():
    """Test GET /api/deployment/status endpoint"""
    print("\n📊 Testing Deployment Status Endpoint...")
    print("🎯 FOCUS: GET /api/deployment/status - should return current deployment status")
    
    try:
        response = requests.get(f"{BACKEND_URL}/deployment/status", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Deployment status endpoint accessible")
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Check response structure
                required_fields = ['status', 'message', 'last_check']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ⚠️ WARNING: Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ STRUCTURE: All required fields present")
                
                # Check if status shows "Error"
                status = data.get('status', '')
                if status.lower() == 'error':
                    print(f"   ❌ CRITICAL: Status shows 'Error' - this matches user report!")
                    print(f"   Error Message: {data.get('message', 'No message')}")
                    return False, data
                else:
                    print(f"   ✅ STATUS: {status} (not 'Error')")
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

def test_deployment_check_updates_endpoint():
    """Test POST /api/deployment/check-updates endpoint"""
    print("\n🔄 Testing Deployment Check Updates Endpoint...")
    print("🎯 FOCUS: POST /api/deployment/check-updates - should check for available updates")
    
    try:
        response = requests.post(f"{BACKEND_URL}/deployment/check-updates", timeout=60)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Check updates endpoint accessible")
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Check response structure
                required_fields = ['updates_available', 'message', 'checked_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ⚠️ WARNING: Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ STRUCTURE: All required fields present")
                
                # Check updates availability
                updates_available = data.get('updates_available', False)
                print(f"   📦 Updates Available: {updates_available}")
                
                # Check if this matches user report of "Updates Available: No"
                if not updates_available:
                    print(f"   ✅ MATCHES USER REPORT: No updates available")
                else:
                    print(f"   ⚠️ DIFFERS FROM USER REPORT: Updates are available")
                
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

def test_deployment_health_endpoint():
    """Test GET /api/deployment/health endpoint"""
    print("\n🏥 Testing Deployment Health Endpoint...")
    print("🎯 FOCUS: GET /api/deployment/health - should return system health")
    
    try:
        response = requests.get(f"{BACKEND_URL}/deployment/health", timeout=120)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Deployment health endpoint accessible")
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Check response structure
                required_fields = ['health_status', 'checked_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ⚠️ WARNING: Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ STRUCTURE: All required fields present")
                
                # Check health status
                health_status = data.get('health_status', '')
                print(f"   🏥 Health Status: {health_status}")
                
                # Analyze health status
                if health_status in ['excellent', 'good']:
                    print(f"   ✅ HEALTH: System health is {health_status}")
                    return True, data
                elif health_status in ['poor', 'unknown']:
                    print(f"   ⚠️ HEALTH: System health is {health_status} - may contribute to deployment errors")
                    return False, data
                else:
                    print(f"   ❌ HEALTH: Unknown health status '{health_status}'")
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

def test_deployment_verify_endpoint():
    """Test POST /api/deployment/verify endpoint"""
    print("\n✅ Testing Deployment Verify Endpoint...")
    print("🎯 FOCUS: POST /api/deployment/verify - verify it's still working after previous fix")
    
    try:
        response = requests.post(f"{BACKEND_URL}/deployment/verify", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Deployment verify endpoint accessible")
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Check response structure
                required_fields = ['deployment_valid', 'message', 'verified_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    print(f"   ⚠️ WARNING: Missing fields: {missing_fields}")
                else:
                    print(f"   ✅ STRUCTURE: All required fields present")
                
                # Check deployment validity
                deployment_valid = data.get('deployment_valid', False)
                message = data.get('message', '')
                
                print(f"   🔍 Deployment Valid: {deployment_valid}")
                print(f"   📝 Message: {message}")
                
                if deployment_valid:
                    print(f"   ✅ VERIFICATION: Deployment is valid")
                    return True, data
                else:
                    print(f"   ❌ VERIFICATION: Deployment verification failed")
                    # Check for specific error details
                    errors = data.get('errors', '')
                    if errors:
                        print(f"   🔍 Error Details: {errors}")
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

def analyze_deployment_error_source():
    """Analyze which endpoint is causing the deployment error status"""
    print("\n🔍 Analyzing Deployment Error Source...")
    print("🎯 FOCUS: Identify which endpoint is returning error status causing 'Status: Error'")
    
    # Test all deployment endpoints
    status_result, status_data = test_deployment_status_endpoint()
    updates_result, updates_data = test_deployment_check_updates_endpoint()
    health_result, health_data = test_deployment_health_endpoint()
    verify_result, verify_data = test_deployment_verify_endpoint()
    
    print(f"\n📊 DEPLOYMENT ENDPOINTS ANALYSIS:")
    print(f"   GET /api/deployment/status: {'✅ Working' if status_result else '❌ Error'}")
    print(f"   POST /api/deployment/check-updates: {'✅ Working' if updates_result else '❌ Error'}")
    print(f"   GET /api/deployment/health: {'✅ Working' if health_result else '❌ Error'}")
    print(f"   POST /api/deployment/verify: {'✅ Working' if verify_result else '❌ Error'}")
    
    # Identify error sources
    error_sources = []
    
    if not status_result:
        error_sources.append("deployment/status")
        print(f"\n❌ ERROR SOURCE IDENTIFIED: /api/deployment/status")
        if 'status' in status_data and status_data['status'] == 'error':
            print(f"   🔍 This endpoint returns status='error' - MATCHES USER REPORT!")
            print(f"   📝 Error Message: {status_data.get('message', 'No message')}")
    
    if not updates_result:
        error_sources.append("deployment/check-updates")
        print(f"\n❌ ERROR SOURCE IDENTIFIED: /api/deployment/check-updates")
    
    if not health_result:
        error_sources.append("deployment/health")
        print(f"\n❌ ERROR SOURCE IDENTIFIED: /api/deployment/health")
    
    if not verify_result:
        error_sources.append("deployment/verify")
        print(f"\n❌ ERROR SOURCE IDENTIFIED: /api/deployment/verify")
    
    # Check for "Last Deployment: Never" issue
    print(f"\n🕐 CHECKING 'Last Deployment: Never' ISSUE:")
    
    # Check if status endpoint provides deployment history
    if status_result and 'last_deployment' in status_data:
        last_deployment = status_data.get('last_deployment')
        if not last_deployment or last_deployment == 'never':
            print(f"   ❌ CONFIRMED: last_deployment is '{last_deployment}' - MATCHES USER REPORT!")
        else:
            print(f"   ✅ last_deployment: {last_deployment}")
    else:
        print(f"   ⚠️ No 'last_deployment' field found in status response")
    
    # Summary
    print(f"\n📋 ERROR SOURCE SUMMARY:")
    if error_sources:
        print(f"   ❌ Problematic endpoints: {', '.join(error_sources)}")
        print(f"   🔧 These endpoints need investigation/fixing")
    else:
        print(f"   ✅ All deployment endpoints are working")
        print(f"   🤔 Error may be in frontend interpretation or data format")
    
    return {
        'error_sources': error_sources,
        'status_result': status_result,
        'status_data': status_data,
        'updates_result': updates_result,
        'updates_data': updates_data,
        'health_result': health_result,
        'health_data': health_data,
        'verify_result': verify_result,
        'verify_data': verify_data
    }

def test_deployment_management_endpoints():
    """Comprehensive test of all deployment management endpoints"""
    print("\n🎯 COMPREHENSIVE DEPLOYMENT MANAGEMENT ENDPOINTS TEST")
    print("=" * 80)
    print("🎯 REVIEW REQUEST: Test all deployment management endpoints to identify error source")
    print("📋 SPECIFIC REQUIREMENTS:")
    print("   1. Test GET /api/deployment/status - should return current deployment status")
    print("   2. Test POST /api/deployment/check-updates - should check for available updates")
    print("   3. Test GET /api/deployment/health - should return system health")
    print("   4. Test POST /api/deployment/verify - verify it's still working after previous fix")
    print("   5. Identify why status shows 'Error' and 'Last Deployment: Never'")
    print("=" * 80)
    
    # Run comprehensive analysis
    analysis_results = analyze_deployment_error_source()
    
    # Final Assessment
    print("\n" + "=" * 80)
    print("📊 DEPLOYMENT MANAGEMENT ENDPOINTS - FINAL ASSESSMENT")
    print("=" * 80)
    
    error_sources = analysis_results['error_sources']
    all_working = len(error_sources) == 0
    
    print(f"✅ Working Endpoints: {4 - len(error_sources)}/4")
    print(f"❌ Error Endpoints: {len(error_sources)}/4")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    endpoints = [
        ('deployment/status', analysis_results['status_result']),
        ('deployment/check-updates', analysis_results['updates_result']),
        ('deployment/health', analysis_results['health_result']),
        ('deployment/verify', analysis_results['verify_result'])
    ]
    
    for endpoint, result in endpoints:
        status = "✅ WORKING" if result else "❌ ERROR"
        print(f"   {status} - /api/{endpoint}")
    
    # Root cause analysis
    print(f"\n🔍 ROOT CAUSE ANALYSIS:")
    
    if 'deployment/status' in error_sources:
        print(f"   ❌ CRITICAL: /api/deployment/status returns error - this causes 'Status: Error' in UI")
        status_data = analysis_results['status_data']
        if 'message' in status_data:
            print(f"      Error Message: {status_data['message']}")
    
    if not analysis_results['status_result']:
        print(f"   🔍 Status endpoint issue likely causes 'Last Deployment: Never' display")
    
    # User report matching
    print(f"\n📊 USER REPORT MATCHING:")
    print(f"   Status: Error - {'✅ CONFIRMED' if not analysis_results['status_result'] else '❌ NOT CONFIRMED'}")
    print(f"   Updates Available: No - {'✅ CONFIRMED' if analysis_results['updates_result'] and not analysis_results['updates_data'].get('updates_available', True) else '❌ NOT CONFIRMED'}")
    print(f"   Last Deployment: Never - {'✅ LIKELY' if not analysis_results['status_result'] else '❌ UNLIKELY'}")
    
    return all_working, analysis_results

def main():
    """Main test execution function - Focus on Deployment Management Endpoints"""
    print("🚀 Starting Backend API Testing for Nova Scotia Tax Sale Aggregator")
    print("=" * 80)
    print("🎯 FOCUS: Test deployment management endpoints to identify error source")
    print("📋 REVIEW REQUEST: Test all deployment management endpoints to identify why deployment status shows 'Error'")
    print("🔍 SPECIFIC TESTING REQUIREMENTS:")
    print("   1. Test GET /api/deployment/status - should return current deployment status")
    print("   2. Test POST /api/deployment/check-updates - should check for available updates")
    print("   3. Test GET /api/deployment/health - should return system health")
    print("   4. Test POST /api/deployment/verify - verify it's still working after previous fix")
    print("   5. Check what data each endpoint returns and identify why status shows 'Error'")
    print("   6. Verify the response formats match what the frontend expects")
    print("🎯 CONTEXT:")
    print("   - User reports deployment interface shows 'Status: Error', 'Updates Available: No', 'Last Deployment: Never'")
    print("   - We fixed the /api/deployment/verify timeout issue but other endpoints might have problems")
    print("   - Need to identify which endpoint is returning error status and why")
    print("=" * 80)
    
    # Test 1: Basic API connectivity
    api_connected, _ = test_api_connection()
    
    if not api_connected:
        print("\n❌ Cannot proceed without API connection")
        return False
    
    # Test 2: Deployment Management Endpoints (MAIN FOCUS)
    print("\n🎯 MAIN FOCUS: Deployment Management Endpoints Testing")
    all_working, analysis_data = test_deployment_management_endpoints()
    
    # Final Results Summary
    print("\n" + "=" * 80)
    print("📊 FINAL TEST RESULTS SUMMARY - Deployment Management Endpoints")
    print("=" * 80)
    
    if all_working:
        print(f"🎉 DEPLOYMENT MANAGEMENT ENDPOINTS: ALL WORKING!")
        print(f"   ✅ All 4 deployment endpoints are functional")
        print(f"   ✅ GET /api/deployment/status working properly")
        print(f"   ✅ POST /api/deployment/check-updates working properly")
        print(f"   ✅ GET /api/deployment/health working properly")
        print(f"   ✅ POST /api/deployment/verify working properly")
        print(f"   🤔 Error may be in frontend interpretation or data format")
        
        # Show detailed success data
        error_sources = analysis_data.get('error_sources', [])
        
        print(f"\n📊 DETAILED SUCCESS METRICS:")
        print(f"   Working endpoints: {4 - len(error_sources)}/4")
        print(f"   Error endpoints: {len(error_sources)}/4")
        
        # Show response data for analysis
        print(f"\n📋 RESPONSE DATA ANALYSIS:")
        if analysis_data.get('status_result'):
            status_data = analysis_data.get('status_data', {})
            print(f"   Status Response: {json.dumps(status_data, indent=2)}")
        
        if analysis_data.get('updates_result'):
            updates_data = analysis_data.get('updates_data', {})
            print(f"   Updates Response: {json.dumps(updates_data, indent=2)}")
        
    else:
        print(f"❌ DEPLOYMENT MANAGEMENT ENDPOINTS: ISSUES IDENTIFIED")
        print(f"   ❌ Some deployment endpoints have problems")
        print(f"   🔧 These endpoints need investigation/fixing")
        
        error_sources = analysis_data.get('error_sources', [])
        
        print(f"\n📋 ISSUES IDENTIFIED:")
        print(f"   Working endpoints: {4 - len(error_sources)}/4")
        print(f"   Error endpoints: {len(error_sources)}/4")
        
        # Show specific failures
        if error_sources:
            print(f"\n   ❌ PROBLEMATIC ENDPOINTS:")
            for endpoint in error_sources:
                print(f"      - /api/{endpoint}")
        
        print(f"\n   🔧 RECOMMENDED ACTIONS:")
        print(f"      1. Check deployment script files exist and are executable")
        print(f"      2. Verify system health check scripts are working")
        print(f"      3. Check deployment status script output format")
        print(f"      4. Ensure proper permissions for deployment scripts")
        print(f"      5. Test deployment endpoints manually for detailed error messages")
    
    print("=" * 80)
    
    return all_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)