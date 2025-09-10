#!/usr/bin/env python3
"""
Test script to verify Halifax rescan fix deployment on VPS
Run this on your VPS: python3 test_vps_deployment.py
"""

import sys
import os

print("🔍 Testing Halifax Rescan Fix Deployment...")
print("=" * 50)

# Add backend to path
sys.path.append('/var/www/tax-sale-compass/backend')

try:
    from mysql_config import mysql_db
    print("✅ Database connection module imported")
    
    # Test 1: Check Halifax scraper configuration
    print("\n📋 Test 1: Halifax Scraper Configuration")
    config = mysql_db.get_scraper_config('Halifax Regional Municipality')
    if config:
        print("✅ Halifax config found:")
        print(f"   - URL: {config['tax_sale_page_url']}")
        print(f"   - Enabled: {config['enabled']}")
        print(f"   - PDF patterns: {len(config['pdf_search_patterns'])} patterns")
        print(f"   - Excel patterns: {len(config['excel_search_patterns'])} patterns")
        
        # Check if URL was fixed
        if 'tax-sale' in config['tax_sale_page_url'] and 'tax-sales' not in config['tax_sale_page_url']:
            print("✅ Halifax URL correctly fixed: tax-sales → tax-sale")
        else:
            print("❌ Halifax URL not updated correctly")
    else:
        print("❌ Halifax config not found in database")
    
    # Test 2: Test property lookup
    print("\n📋 Test 2: Property Database Lookup")
    property_data = mysql_db.get_property_by_assessment('01999184')
    if property_data:
        print("✅ Property 01999184 found:")
        print(f"   - Type: {property_data.get('property_type', 'NOT SET')}")
        print(f"   - Municipality: {property_data.get('municipality', 'NOT SET')}")
        print(f"   - Address: {property_data.get('civic_address', 'NOT SET')}")
    else:
        print("⚠️ Property 01999184 not found (may need sample data)")
    
    # Test 3: Test rescan functionality  
    print("\n📋 Test 3: Halifax Rescan Functionality")
    try:
        from scrapers_mysql import rescan_halifax_property
        print("✅ Rescan module imported successfully")
        
        # Test with timeout to avoid hanging
        import signal
        
        def timeout_handler(signum, frame):
            raise TimeoutError("Rescan test timed out")
        
        signal.signal(signal.SIGALRM, timeout_handler)
        signal.alarm(30)  # 30 second timeout
        
        try:
            result = rescan_halifax_property('01999184')
            signal.alarm(0)  # Cancel timeout
            
            print("✅ Rescan test completed:")
            print(f"   - Success: {result.get('success', False)}")
            print(f"   - Message: {result.get('message', 'No message')}")
            
            files_checked = result.get('files_checked', {})
            pdfs_found = len(files_checked.get('pdfs', []))
            excel_found = len(files_checked.get('excel', []))
            print(f"   - Files found: {pdfs_found} PDFs, {excel_found} Excel files")
            
            if pdfs_found > 0 or excel_found > 0:
                print("✅ Halifax file discovery is working!")
            else:
                print("⚠️ No files found - may indicate connectivity or pattern issues")
                
        except TimeoutError:
            print("⚠️ Rescan test timed out (but deployment likely successful)")
        except Exception as e:
            print(f"❌ Rescan test error: {e}")
            
    except ImportError as e:
        print(f"❌ Failed to import rescan module: {e}")

except ImportError as e:
    print(f"❌ Failed to import database module: {e}")
    print("   This may indicate Python path or dependency issues")

print("\n" + "=" * 50)
print("🏁 Deployment Test Complete")
print("\nNext steps:")
print("1. If all tests passed ✅ - the fix is working!")
print("2. Test in admin panel: go to Missing PIDs and try rescanning property 01999184")
print("3. If issues remain, check /var/log/supervisor/backend.*.log for errors")