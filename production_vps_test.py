#!/usr/bin/env python3
"""
Production VPS Deployment Testing for Tax Sale Compass
Focus on testing the deployment check-updates endpoint on production VPS
"""

import requests
import json
import sys
import time
from datetime import datetime

# Production VPS URL for deployment testing
PRODUCTION_VPS_URL = 'https://taxsalecompass.ca/api'

def test_production_vps_check_updates():
    """Test POST https://taxsalecompass.ca/api/deployment/check-updates on production VPS"""
    print("\n🌐 Testing Production VPS Check Updates Endpoint...")
    print("🎯 FOCUS: POST https://taxsalecompass.ca/api/deployment/check-updates - production VPS deployment check")
    print("📋 REVIEW REQUEST: Test the deployment check-updates endpoint on the production VPS to troubleshoot why it's not detecting recent GitHub changes")
    
    try:
        # Test the production VPS endpoint
        response = requests.post(f"{PRODUCTION_VPS_URL}/deployment/check-updates", timeout=120)
        
        print(f"   Status Code: {response.status_code}")
        print(f"   Response Headers: {dict(response.headers)}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Production VPS check-updates endpoint accessible")
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Analyze the response for GitHub update detection issues
                updates_available = data.get('updates_available', False)
                message = data.get('message', '')
                output = data.get('output', '')
                
                print(f"\n   📊 PRODUCTION VPS ANALYSIS:")
                print(f"   Updates Available: {updates_available}")
                print(f"   Message: {message}")
                print(f"   Output: {output}")
                
                # Check if this matches the user report
                if not updates_available and "No updates available" in message:
                    print(f"   ✅ MATCHES USER REPORT: VPS shows 'No updates available' despite recent GitHub pushes")
                    print(f"   🔍 ISSUE CONFIRMED: VPS deployment system not detecting recent GitHub changes")
                    
                    # Analyze the output for clues about why updates aren't detected
                    if output:
                        print(f"   📝 Script Output Analysis:")
                        if "git fetch" in output:
                            print(f"      ✅ Git fetch command appears to be running")
                        else:
                            print(f"      ❌ No git fetch command detected in output")
                        
                        if "origin/main" in output:
                            print(f"      ✅ Remote branch origin/main referenced")
                        else:
                            print(f"      ❌ No remote branch reference found")
                        
                        if "commit" in output.lower():
                            print(f"      ✅ Commit information present in output")
                        else:
                            print(f"      ❌ No commit information in output")
                    else:
                        print(f"      ❌ CRITICAL: No script output - deployment script may not be running properly")
                
                return True, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                print(f"   Raw Response: {response.text[:1000]}...")
                return False, {"error": "Invalid JSON response", "raw_response": response.text[:500]}
        
        elif response.status_code == 404:
            print(f"   ❌ ENDPOINT NOT FOUND: Production VPS may not have deployment endpoints implemented")
            print(f"   🔍 This could explain why deployment system shows errors")
            return False, {"error": "Endpoint not found", "status_code": 404}
        
        elif response.status_code == 500:
            print(f"   ❌ SERVER ERROR: Production VPS deployment script may be failing")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
                return False, error_data
            except:
                print(f"   Raw Error Response: {response.text[:500]}...")
                return False, {"error": f"HTTP {response.status_code}", "raw_response": response.text[:500]}
        
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            try:
                error_data = response.json()
                print(f"   Error Details: {error_data}")
                return False, error_data
            except:
                print(f"   Raw Response: {response.text[:500]}...")
                return False, {"error": f"HTTP {response.status_code}", "raw_response": response.text[:500]}
                
    except requests.exceptions.Timeout:
        print(f"   ❌ TIMEOUT ERROR: Production VPS deployment check took too long (>120s)")
        print(f"   🔍 This suggests deployment script may be hanging or taking too long")
        return False, {"error": "Request timeout"}
    
    except requests.exceptions.ConnectionError as e:
        print(f"   ❌ CONNECTION ERROR: Cannot connect to production VPS")
        print(f"   Error: {e}")
        print(f"   🔍 VPS may be down or network issues")
        return False, {"error": f"Connection error: {str(e)}"}
    
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def test_production_vps_git_access():
    """Test if production VPS can access GitHub repository"""
    print("\n🔗 Testing Production VPS GitHub Repository Access...")
    print("🎯 FOCUS: Verify if the VPS can access the GitHub repository")
    
    try:
        # Try to get deployment status which might include git information
        response = requests.get(f"{PRODUCTION_VPS_URL}/deployment/status", timeout=30)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Production VPS deployment status accessible")
                print(f"   Response Data: {json.dumps(data, indent=2)}")
                
                # Look for git-related information
                status = data.get('status', '')
                message = data.get('message', '')
                
                print(f"\n   📊 GIT ACCESS ANALYSIS:")
                print(f"   Status: {status}")
                print(f"   Message: {message}")
                
                # Check if status indicates git issues
                if status == 'error':
                    print(f"   ❌ CRITICAL: Deployment status shows 'error' - may indicate git access issues")
                elif status == 'success':
                    print(f"   ✅ Deployment status shows 'success' - git access likely working")
                
                return True, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                return False, {"error": "Invalid JSON response"}
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def test_production_vps_deployment_paths():
    """Test if production VPS deployment script paths are correct"""
    print("\n📁 Testing Production VPS Deployment Script Paths...")
    print("🎯 FOCUS: Verify deployment script paths are correct for VPS environment")
    print("📋 CONTEXT: VPS should be checking /var/www/nstaxsales directory for git updates")
    
    try:
        # Test deployment health which might reveal path issues
        response = requests.get(f"{PRODUCTION_VPS_URL}/deployment/health", timeout=60)
        
        print(f"   Status Code: {response.status_code}")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"   ✅ SUCCESS: Production VPS deployment health accessible")
                
                health_status = data.get('health_status', '')
                output = data.get('output', '')
                errors = data.get('errors', '')
                
                print(f"\n   📊 DEPLOYMENT PATHS ANALYSIS:")
                print(f"   Health Status: {health_status}")
                
                # Analyze output for path-related information
                if output:
                    print(f"   📝 Health Check Output Analysis:")
                    if "/var/www/nstaxsales" in output:
                        print(f"      ✅ Correct VPS path /var/www/nstaxsales found in output")
                    elif "/app" in output:
                        print(f"      ⚠️ Development path /app found - may indicate path configuration issue")
                    else:
                        print(f"      ❓ No specific path information found in output")
                    
                    # Look for git-related path information
                    if "git" in output.lower():
                        print(f"      ✅ Git operations mentioned in health check")
                    else:
                        print(f"      ❌ No git operations mentioned in health check")
                
                if errors:
                    print(f"   ❌ ERRORS DETECTED:")
                    print(f"      {errors}")
                    
                    # Analyze errors for path issues
                    if "No such file or directory" in errors:
                        print(f"      🔍 CRITICAL: File/directory not found errors - likely path configuration issue")
                    if "/var/www/nstaxsales" in errors:
                        print(f"      🔍 VPS path mentioned in errors - script may be looking in wrong location")
                
                return True, data
                    
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON DECODE ERROR: {e}")
                return False, {"error": "Invalid JSON response"}
        else:
            print(f"   ❌ HTTP ERROR: {response.status_code}")
            return False, {"error": f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ REQUEST ERROR: {e}")
        return False, {"error": str(e)}

def analyze_production_vps_deployment_issues():
    """Comprehensive analysis of production VPS deployment issues"""
    print("\n🔍 Comprehensive Production VPS Deployment Issues Analysis...")
    print("🎯 FOCUS: Identify why VPS deployment system shows 'No updates available' despite recent GitHub changes")
    print("=" * 100)
    
    # Test all production VPS endpoints
    check_updates_result, check_updates_data = test_production_vps_check_updates()
    git_access_result, git_access_data = test_production_vps_git_access()
    paths_result, paths_data = test_production_vps_deployment_paths()
    
    print(f"\n📊 PRODUCTION VPS DEPLOYMENT ANALYSIS SUMMARY:")
    print(f"=" * 100)
    print(f"   POST /api/deployment/check-updates: {'✅ Working' if check_updates_result else '❌ Error'}")
    print(f"   GET /api/deployment/status (git info): {'✅ Working' if git_access_result else '❌ Error'}")
    print(f"   GET /api/deployment/health (paths): {'✅ Working' if paths_result else '❌ Error'}")
    
    # Identify specific issues
    issues_found = []
    
    print(f"\n🔍 ISSUE IDENTIFICATION:")
    
    # Check for update detection issues
    if check_updates_result:
        updates_data = check_updates_data
        if not updates_data.get('updates_available', True):
            issues_found.append("VPS not detecting GitHub updates")
            print(f"   ❌ ISSUE 1: VPS shows 'No updates available' despite recent GitHub pushes")
            
            output = updates_data.get('output', '')
            if not output:
                issues_found.append("Deployment script not producing output")
                print(f"   ❌ ISSUE 2: Deployment script not producing any output - script may not be running")
            else:
                print(f"   ✅ Deployment script is producing output")
    else:
        issues_found.append("Check-updates endpoint not accessible")
        print(f"   ❌ ISSUE 1: Cannot access check-updates endpoint on production VPS")
    
    # Check for git access issues
    if git_access_result:
        git_data = git_access_data
        if git_data.get('status') == 'error':
            issues_found.append("Deployment status shows error")
            print(f"   ❌ ISSUE 3: Deployment status shows 'error' - may indicate git access problems")
    else:
        issues_found.append("Cannot check git access status")
        print(f"   ❌ ISSUE 3: Cannot check deployment status for git access information")
    
    # Check for path configuration issues
    if paths_result:
        paths_data_obj = paths_data
        errors = paths_data_obj.get('errors', '')
        if errors and ("No such file or directory" in errors or "not found" in errors):
            issues_found.append("Path configuration issues")
            print(f"   ❌ ISSUE 4: Path configuration issues detected in deployment health check")
    
    # Summary and recommendations
    print(f"\n📋 ISSUES SUMMARY:")
    if issues_found:
        print(f"   ❌ {len(issues_found)} issues identified:")
        for i, issue in enumerate(issues_found, 1):
            print(f"      {i}. {issue}")
    else:
        print(f"   ✅ No obvious issues detected - problem may be more subtle")
    
    print(f"\n🔧 RECOMMENDED ACTIONS:")
    print(f"   1. Check if VPS deployment scripts are executable and have correct permissions")
    print(f"   2. Verify VPS can access GitHub repository (network connectivity, SSH keys)")
    print(f"   3. Confirm deployment script paths point to /var/www/nstaxsales not /app")
    print(f"   4. Test git fetch/pull operations manually on VPS")
    print(f"   5. Check VPS deployment script logs for detailed error messages")
    print(f"   6. Verify GitHub repository URL and branch configuration on VPS")
    
    return {
        'issues_found': issues_found,
        'check_updates_result': check_updates_result,
        'check_updates_data': check_updates_data,
        'git_access_result': git_access_result,
        'git_access_data': git_access_data,
        'paths_result': paths_result,
        'paths_data': paths_data
    }

def main():
    """Main test execution function - Focus on Production VPS Deployment Testing"""
    print("🚀 Starting Production VPS Deployment Testing for Tax Sale Compass")
    print("=" * 100)
    print("🎯 FOCUS: Test deployment check-updates endpoint on production VPS")
    print("📋 REVIEW REQUEST: Test the deployment check-updates endpoint on the production VPS to troubleshoot why it's not detecting recent GitHub changes")
    print("🔍 SPECIFIC TESTING REQUIREMENTS:")
    print("   1. Test POST https://taxsalecompass.ca/api/deployment/check-updates to see the actual response")
    print("   2. Check what error messages or output are returned")
    print("   3. Verify if the VPS can access the GitHub repository")
    print("   4. Test if git fetch/pull operations are working on the VPS")
    print("   5. Check if there are permission issues with git operations")
    print("   6. Verify the deployment script paths are correct for VPS environment")
    print("🎯 CONTEXT:")
    print("   - User pushed recent changes to GitHub (including 504 timeout fix and property image routing fix)")
    print("   - VPS deployment system shows 'No updates available' despite recent GitHub pushes")
    print("   - VPS should be checking /var/www/nstaxsales directory for git updates")
    print("   - Need to identify why git update checking isn't working on production VPS")
    print("=" * 100)
    
    # Run comprehensive production VPS analysis
    analysis_results = analyze_production_vps_deployment_issues()
    
    # Final Assessment
    print(f"\n" + "=" * 100)
    print("📊 PRODUCTION VPS DEPLOYMENT TESTING - FINAL ASSESSMENT")
    print("=" * 100)
    
    issues_found = analysis_results['issues_found']
    all_working = len(issues_found) == 0
    
    print(f"✅ Working Endpoints: {3 - len([i for i in issues_found if 'endpoint' in i])}/3")
    print(f"❌ Issues Identified: {len(issues_found)}")
    
    # Detailed results
    print(f"\n📋 DETAILED RESULTS:")
    endpoints = [
        ('deployment/check-updates', analysis_results['check_updates_result']),
        ('deployment/status (git info)', analysis_results['git_access_result']),
        ('deployment/health (paths)', analysis_results['paths_result'])
    ]
    
    for endpoint, result in endpoints:
        status = "✅ WORKING" if result else "❌ ERROR"
        print(f"   {status} - /api/{endpoint}")
    
    # Root cause analysis
    print(f"\n🔍 ROOT CAUSE ANALYSIS:")
    
    if analysis_results['check_updates_result']:
        check_data = analysis_results['check_updates_data']
        if not check_data.get('updates_available', True):
            print(f"   ❌ CRITICAL: VPS check-updates endpoint returns 'No updates available'")
            print(f"   🔍 This confirms the user report - VPS not detecting recent GitHub changes")
            
            output = check_data.get('output', '')
            if not output:
                print(f"   ❌ CRITICAL: No script output - deployment script may not be executing properly")
            else:
                print(f"   ✅ Script is producing output - issue may be in git operations")
    else:
        print(f"   ❌ CRITICAL: Cannot access check-updates endpoint on production VPS")
    
    # User report matching
    print(f"\n📊 USER REPORT MATCHING:")
    print(f"   VPS shows 'No updates available': {'✅ CONFIRMED' if analysis_results['check_updates_result'] and not analysis_results['check_updates_data'].get('updates_available', True) else '❌ NOT CONFIRMED'}")
    print(f"   Recent GitHub changes not detected: {'✅ CONFIRMED' if 'VPS not detecting GitHub updates' in issues_found else '❌ NOT CONFIRMED'}")
    
    # Final recommendations
    print(f"\n🔧 FINAL RECOMMENDATIONS:")
    if issues_found:
        print(f"   ❌ {len(issues_found)} issues need to be addressed:")
        for i, issue in enumerate(issues_found, 1):
            print(f"      {i}. {issue}")
        
        print(f"\n   🛠️ IMMEDIATE ACTIONS NEEDED:")
        print(f"      1. SSH into production VPS and manually test git operations in /var/www/nstaxsales")
        print(f"      2. Check deployment script permissions and execution")
        print(f"      3. Verify GitHub repository access and SSH keys")
        print(f"      4. Review deployment script logs for detailed error messages")
        print(f"      5. Test git fetch/pull operations manually to identify specific issues")
    else:
        print(f"   ✅ All endpoints working - issue may be more subtle")
        print(f"   🔍 Consider checking git configuration, branch settings, or timing issues")
    
    print("=" * 100)
    
    return all_working

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)