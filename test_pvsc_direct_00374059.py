#!/usr/bin/env python3
"""
Direct PVSC Website Test for Assessment 00374059 (Working Property)
Test to compare with 00554596 and see the difference
"""

import requests
import re
from bs4 import BeautifulSoup

def test_pvsc_direct_00374059():
    """Test PVSC website directly for assessment 00374059"""
    print("🔍 Testing PVSC Website Directly for Assessment 00374059 (Working Property)")
    print("=" * 70)
    
    assessment_number = "00374059"
    pvsc_url = f"https://webapi.pvsc.ca/Search/Property?ain={assessment_number}"
    
    try:
        print(f"📡 Fetching PVSC data from: {pvsc_url}")
        
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(pvsc_url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            print(f"✅ PVSC response received (status: {response.status_code})")
            print(f"📊 Response length: {len(response.text)} characters")
            
            # Parse the HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            text_content = soup.get_text()
            
            print(f"\n🔍 SEARCHING FOR LAND SIZE PATTERNS:")
            
            # Search for land size pattern
            land_size_match = re.search(r'Land Size\s*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)', text_content)
            if land_size_match:
                size_value = land_size_match.group(1)
                size_unit = land_size_match.group(2)
                print(f"   ✅ Found land_size: {size_value} {size_unit}")
            else:
                print(f"   ❌ No land size pattern found")
            
            # Look for context around "Land Size"
            print(f"\n🔍 CONTEXT AROUND 'LAND SIZE':")
            land_size_contexts = re.findall(r'.{0,50}Land Size.{0,50}', text_content, re.IGNORECASE)
            for i, context in enumerate(land_size_contexts):
                print(f"   Context {i+1}: '{context.strip()}'")
            
            # Save raw content for comparison
            with open('/app/pvsc_00374059_raw.txt', 'w') as f:
                f.write(response.text)
            print(f"\n💾 Raw PVSC content saved to /app/pvsc_00374059_raw.txt")
            
            return True, {
                "status_code": response.status_code,
                "content_length": len(response.text),
                "land_size_found": land_size_match is not None,
                "land_size_value": f"{land_size_match.group(1)} {land_size_match.group(2)}" if land_size_match else None
            }
            
        else:
            print(f"❌ PVSC request failed with status: {response.status_code}")
            return False, {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error testing PVSC directly: {e}")
        return False, {"error": str(e)}

if __name__ == "__main__":
    success, result = test_pvsc_direct_00374059()
    print(f"\n🏁 Test completed: {'✅ SUCCESS' if success else '❌ FAILED'}")
    if result:
        print(f"📊 Result: {result}")