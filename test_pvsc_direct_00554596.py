#!/usr/bin/env python3
"""
Direct PVSC Website Test for Assessment 00554596
Test to check what land size data is actually available on PVSC website
"""

import requests
import re
from bs4 import BeautifulSoup

def test_pvsc_direct_00554596():
    """Test PVSC website directly for assessment 00554596"""
    print("🔍 Testing PVSC Website Directly for Assessment 00554596")
    print("=" * 60)
    
    assessment_number = "00554596"
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
            
            # Search for various land size patterns
            patterns = [
                r'Land Size\s*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)',  # Current regex
                r'Land Size[:\s]*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)',  # With colon
                r'Land Size[:\s]*([^\n\r]+)',  # Any text after Land Size
                r'Land[:\s]+Size[:\s]*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)',  # Variations
                r'Size[:\s]*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)',  # Just Size
                r'Lot Size[:\s]*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)',  # Lot Size
                r'Area[:\s]*([\d,\.]+)\s*(Sq\.\s*Ft\.|Acres)',  # Area
                r'Acreage[:\s]*([\d,\.]+)',  # Acreage
                r'(\d+\.?\d*)\s*Acres',  # Any number followed by Acres
                r'(\d+\.?\d*)\s*Sq\.\s*Ft\.',  # Any number followed by Sq. Ft.
            ]
            
            found_matches = []
            
            for i, pattern in enumerate(patterns):
                matches = re.findall(pattern, text_content, re.IGNORECASE)
                if matches:
                    print(f"   Pattern {i+1}: {pattern}")
                    print(f"   Matches: {matches}")
                    found_matches.extend(matches)
            
            if not found_matches:
                print(f"   ❌ No land size patterns found")
            
            # Search for the specific ".00 Acres" that we're seeing
            print(f"\n🔍 SEARCHING FOR '.00 ACRES' PATTERN:")
            zero_acres_matches = re.findall(r'\.00\s*Acres', text_content, re.IGNORECASE)
            if zero_acres_matches:
                print(f"   ✅ Found '.00 Acres' pattern: {zero_acres_matches}")
            else:
                print(f"   ❌ No '.00 Acres' pattern found")
            
            # Look for context around "Land Size"
            print(f"\n🔍 CONTEXT AROUND 'LAND SIZE':")
            land_size_contexts = re.findall(r'.{0,50}Land Size.{0,50}', text_content, re.IGNORECASE)
            for i, context in enumerate(land_size_contexts):
                print(f"   Context {i+1}: '{context.strip()}'")
            
            # Check if there are multiple land size entries
            print(f"\n🔍 ALL OCCURRENCES OF 'LAND' OR 'SIZE' OR 'ACRES':")
            land_occurrences = re.findall(r'.{0,30}(?:land|size|acres|sq\.?\s*ft\.?).{0,30}', text_content, re.IGNORECASE)
            for i, occurrence in enumerate(land_occurrences[:10]):  # Show first 10
                print(f"   {i+1}: '{occurrence.strip()}'")
            
            # Look for any numeric values that might be land size
            print(f"\n🔍 NUMERIC VALUES THAT MIGHT BE LAND SIZE:")
            numeric_patterns = re.findall(r'(\d+\.?\d*)\s*(acres?|sq\.?\s*ft\.?)', text_content, re.IGNORECASE)
            for i, (value, unit) in enumerate(numeric_patterns):
                if float(value) > 0:  # Only show non-zero values
                    print(f"   {i+1}: {value} {unit}")
            
            # Check if there's property information that might contain land size
            print(f"\n🔍 PROPERTY INFORMATION SECTIONS:")
            property_sections = re.findall(r'property.{0,100}', text_content, re.IGNORECASE)
            for i, section in enumerate(property_sections[:5]):  # Show first 5
                print(f"   {i+1}: '{section.strip()}'")
            
            # Save raw content for manual inspection
            with open('/app/pvsc_00554596_raw.txt', 'w') as f:
                f.write(response.text)
            print(f"\n💾 Raw PVSC content saved to /app/pvsc_00554596_raw.txt")
            
            return True, {
                "status_code": response.status_code,
                "content_length": len(response.text),
                "land_size_matches": found_matches,
                "zero_acres_found": len(zero_acres_matches) > 0,
                "contexts": land_size_contexts
            }
            
        else:
            print(f"❌ PVSC request failed with status: {response.status_code}")
            return False, {"error": f"HTTP {response.status_code}"}
            
    except Exception as e:
        print(f"❌ Error testing PVSC directly: {e}")
        return False, {"error": str(e)}

if __name__ == "__main__":
    success, result = test_pvsc_direct_00554596()
    print(f"\n🏁 Test completed: {'✅ SUCCESS' if success else '❌ FAILED'}")
    if result:
        print(f"📊 Result: {result}")