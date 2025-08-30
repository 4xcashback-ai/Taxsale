#!/usr/bin/env python3
"""
Test Async PVSC Scraping - Test the async scraping function
"""

import asyncio
import requests
import re
from bs4 import BeautifulSoup

async def scrape_pvsc_details_test(assessment_number: str):
    """
    Test version of the PVSC scraping function
    """
    print(f"🔍 Testing async PVSC scraping for {assessment_number}")
    try:
        pvsc_url = f"https://webapi.pvsc.ca/Search/Property?ain={assessment_number}"
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"📡 Fetching: {pvsc_url}")
        response = requests.get(pvsc_url, headers=headers, timeout=30)
        response.raise_for_status()
        print(f"✅ HTTP {response.status_code}")
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract Google Maps link
        google_maps_link = None
        maps_links = soup.find_all('a', href=True)
        for link in maps_links:
            href = link['href']
            if 'maps.google.com' in href:
                google_maps_link = href
                break
        
        # Extract civic address
        civic_address = None
        address_elements = soup.find_all(['h1', 'div'], string=re.compile(r'[A-Z0-9\s]+[A-Z]{2,}'))
        for element in address_elements:
            text = element.get_text(strip=True)
            if len(text) > 10 and any(word in text.upper() for word in ['RD', 'ST', 'AVE', 'DRIVE', 'COURT', 'CRT']):
                civic_address = text
                break
        
        # Extract property details from table-like structure
        property_details = {}
        
        # Look for assessment value
        assessment_text = soup.get_text()
        
        # Current Property Assessment
        assessment_match = re.search(r'Current Property Assessment\s*\$?([\d,]+)', assessment_text)
        if assessment_match:
            property_details['current_assessment'] = float(assessment_match.group(1).replace(',', ''))
        
        # Taxable Assessed Value
        taxable_match = re.search(r'Current Taxable Assessed Value:\s*\$?([\d,]+)', assessment_text)
        if taxable_match:
            property_details['taxable_assessment'] = float(taxable_match.group(1).replace(',', ''))
        
        # Land Size
        land_size_match = re.search(r'Land Size\s*([\d,]+)\s*Sq\.\s*Ft\.', assessment_text)
        if land_size_match:
            property_details['land_size'] = land_size_match.group(1).replace(',', '') + ' Sq. Ft.'
        
        # Building Style
        style_match = re.search(r'Building Style\s*([^\n]+)', assessment_text)
        if style_match:
            property_details['building_style'] = style_match.group(1).strip()
        
        # Year Built
        year_match = re.search(r'Year Built\s*(\d{4})', assessment_text)
        if year_match:
            property_details['year_built'] = int(year_match.group(1))
        
        # Living Area
        area_match = re.search(r'Total Living Area\(Sq Ft\)\s*†?\s*(\d+)', assessment_text)
        if area_match:
            property_details['living_area'] = int(area_match.group(1))
        
        # Bedrooms
        bedroom_match = re.search(r'Bedrooms\s*(\d+)', assessment_text)
        if bedroom_match:
            property_details['bedrooms'] = int(bedroom_match.group(1))
        
        # Bathrooms
        bath_match = re.search(r'#of Baths[^0-9]*(\d+)', assessment_text)
        if bath_match:
            property_details['bathrooms'] = int(bath_match.group(1))
        
        print(f"\n🎯 Testing NEW FIELDS:")
        
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
        
        # Extract coordinates from Google Maps link if available
        latitude, longitude = None, None
        if google_maps_link:
            # Try to extract address from Google Maps link and geocode it
            try:
                import urllib.parse
                if '?q=' in google_maps_link:
                    address_query = google_maps_link.split('?q=')[1]
                    decoded_address = urllib.parse.unquote(address_query)
                    
                    # Use a simple geocoding approach with the address
                    # For now, we'll store the Google Maps link and address
                    property_details['google_maps_link'] = google_maps_link
                    property_details['geocoded_address'] = decoded_address
            except:
                property_details['google_maps_link'] = google_maps_link
        
        result = {
            'civic_address': civic_address,
            'google_maps_link': google_maps_link,
            'property_details': property_details,
            'pvsc_url': pvsc_url
        }
        
        print(f"\n📊 RESULT:")
        print(f"   Total property_details fields: {len(property_details)}")
        
        # Check new fields
        new_fields = ['quality_of_construction', 'under_construction', 'living_units', 'finished_basement', 'garage']
        found_new_fields = [field for field in new_fields if field in property_details]
        print(f"   New fields found: {len(found_new_fields)}/5")
        
        return result
        
    except Exception as e:
        print(f"❌ Error scraping PVSC data for {assessment_number}: {e}")
        return None

async def main():
    """Test the async scraping function"""
    print("🚀 Testing Async PVSC Scraping Function")
    print("=" * 60)
    
    result = await scrape_pvsc_details_test("00079006")
    
    if result:
        property_details = result.get('property_details', {})
        new_fields = ['quality_of_construction', 'under_construction', 'living_units', 'finished_basement', 'garage']
        found_new_fields = [field for field in new_fields if field in property_details]
        
        if len(found_new_fields) == 5:
            print(f"\n🎉 Async PVSC scraping test PASSED")
            return True
        else:
            print(f"\n❌ Async PVSC scraping test FAILED - {len(found_new_fields)}/5 fields found")
            return False
    else:
        print(f"\n❌ Async PVSC scraping test FAILED - No result returned")
        return False

if __name__ == "__main__":
    asyncio.run(main())