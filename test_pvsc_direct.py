#!/usr/bin/env python3
"""
Direct PVSC Scraping Test - Test the scraping function directly
"""

import requests
import re
from bs4 import BeautifulSoup

def test_pvsc_scraping_direct():
    """Test PVSC scraping function directly"""
    print("🔍 Testing PVSC Scraping Function Directly...")
    print("🎯 Target: Assessment 00079006")
    print("=" * 60)
    
    try:
        assessment_number = "00079006"
        pvsc_url = f"https://webapi.pvsc.ca/Search/Property?ain={assessment_number}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"📡 Fetching: {pvsc_url}")
        response = requests.get(pvsc_url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"✅ HTTP {response.status_code} - Content length: {len(response.content)} bytes")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Google Maps link
        google_maps_link = None
        maps_links = soup.find_all('a', href=True)
        for link in maps_links:
            href = link['href']
            if 'maps.google.com' in href:
                google_maps_link = href
                break
        
        print(f"🗺️ Google Maps Link: {google_maps_link}")
        
        # Extract civic address
        civic_address = None
        address_elements = soup.find_all(['h1', 'div'], string=re.compile(r'[A-Z0-9\s]+[A-Z]{2,}'))
        for element in address_elements:
            text = element.get_text(strip=True)
            if len(text) > 10 and any(word in text.upper() for word in ['RD', 'ST', 'AVE', 'DRIVE', 'COURT', 'CRT']):
                civic_address = text
                break
        
        print(f"🏠 Civic Address: {civic_address}")
        
        # Extract property details from table-like structure
        property_details = {}
        
        # Get all text for regex matching
        assessment_text = soup.get_text()
        
        print(f"\n📊 Testing Regex Patterns:")
        
        # Current Property Assessment
        assessment_match = re.search(r'Current Property Assessment\s*\$?([\d,]+)', assessment_text)
        if assessment_match:
            property_details['current_assessment'] = float(assessment_match.group(1).replace(',', ''))
            print(f"✅ current_assessment: {property_details['current_assessment']}")
        
        # Taxable Assessed Value
        taxable_match = re.search(r'Current Taxable Assessed Value:\s*\$?([\d,]+)', assessment_text)
        if taxable_match:
            property_details['taxable_assessment'] = float(taxable_match.group(1).replace(',', ''))
            print(f"✅ taxable_assessment: {property_details['taxable_assessment']}")
        
        # Land Size
        land_size_match = re.search(r'Land Size\s*([\d,]+)\s*Sq\.\s*Ft\.', assessment_text)
        if land_size_match:
            property_details['land_size'] = land_size_match.group(1).replace(',', '') + ' Sq. Ft.'
            print(f"✅ land_size: {property_details['land_size']}")
        
        # Building Style
        style_match = re.search(r'Building Style\s*([^\n]+)', assessment_text)
        if style_match:
            property_details['building_style'] = style_match.group(1).strip()
            print(f"✅ building_style: {property_details['building_style']}")
        
        # Year Built
        year_match = re.search(r'Year Built\s*(\d{4})', assessment_text)
        if year_match:
            property_details['year_built'] = int(year_match.group(1))
            print(f"✅ year_built: {property_details['year_built']}")
        
        # Living Area
        area_match = re.search(r'Total Living Area\(Sq Ft\)\s*†?\s*(\d+)', assessment_text)
        if area_match:
            property_details['living_area'] = int(area_match.group(1))
            print(f"✅ living_area: {property_details['living_area']}")
        
        # Bedrooms
        bedroom_match = re.search(r'Bedrooms\s*(\d+)', assessment_text)
        if bedroom_match:
            property_details['bedrooms'] = int(bedroom_match.group(1))
            print(f"✅ bedrooms: {property_details['bedrooms']}")
        
        # Bathrooms
        bath_match = re.search(r'#of Baths[^0-9]*(\d+)', assessment_text)
        if bath_match:
            property_details['bathrooms'] = int(bath_match.group(1))
            print(f"✅ bathrooms: {property_details['bathrooms']}")
        
        print(f"\n🎯 NEW FIELDS TESTING:")
        
        # Quality of Construction
        quality_match = re.search(r'Quality of Construction\s*([^\n]+)', assessment_text)
        if quality_match:
            property_details['quality_of_construction'] = quality_match.group(1).strip()
            print(f"✅ quality_of_construction: '{property_details['quality_of_construction']}'")
        else:
            print(f"❌ quality_of_construction: NOT FOUND")
        
        # Under Construction
        under_construction_match = re.search(r'Under Construction\s*([YN])', assessment_text)
        if under_construction_match:
            property_details['under_construction'] = under_construction_match.group(1)
            print(f"✅ under_construction: '{property_details['under_construction']}'")
        else:
            print(f"❌ under_construction: NOT FOUND")
        
        # Living Units
        living_units_match = re.search(r'Living Units\s*(\d+)', assessment_text)
        if living_units_match:
            property_details['living_units'] = int(living_units_match.group(1))
            print(f"✅ living_units: {property_details['living_units']}")
        else:
            print(f"❌ living_units: NOT FOUND")
        
        # Finished Basement
        finished_basement_match = re.search(r'Finished Basement\s*([YN])', assessment_text)
        if finished_basement_match:
            property_details['finished_basement'] = finished_basement_match.group(1)
            print(f"✅ finished_basement: '{property_details['finished_basement']}'")
        else:
            print(f"❌ finished_basement: NOT FOUND")
        
        # Garage
        garage_match = re.search(r'Garage\s*([YN]|[^\n]+)', assessment_text)
        if garage_match:
            property_details['garage'] = garage_match.group(1).strip()
            print(f"✅ garage: '{property_details['garage']}'")
        else:
            print(f"❌ garage: NOT FOUND")
        
        # Summary
        new_fields = ['quality_of_construction', 'under_construction', 'living_units', 'finished_basement', 'garage']
        found_new_fields = [field for field in new_fields if field in property_details]
        
        print(f"\n📋 SUMMARY:")
        print(f"   Total fields extracted: {len(property_details)}")
        print(f"   New fields found: {len(found_new_fields)}/5")
        print(f"   New fields: {found_new_fields}")
        
        if len(found_new_fields) == 5:
            print(f"✅ ALL NEW FIELDS SUCCESSFULLY EXTRACTED")
            return True
        else:
            print(f"⚠️ PARTIAL SUCCESS - {len(found_new_fields)} out of 5 new fields found")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    success = test_pvsc_scraping_direct()
    if success:
        print(f"\n🎉 Direct PVSC scraping test PASSED")
    else:
        print(f"\n❌ Direct PVSC scraping test FAILED")