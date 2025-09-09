#!/usr/bin/env python3
"""
Focused test for enhanced generate-boundary-thumbnail endpoint
Testing apartment property 07737947 with address-based geocoding fallback
"""

import requests
import json
import sys
import time
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class EnhancedBoundaryThumbnailTester:
    def __init__(self, base_url="http://localhost:8001"):
        self.base_url = base_url
        self.session = requests.Session()
        self.admin_token = None
        
    def authenticate_admin(self):
        """Authenticate as admin to access property details"""
        try:
            admin_creds = {
                "email": "admin",
                "password": "TaxSale2025!SecureAdmin"
            }
            
            response = self.session.post(
                f"{self.base_url}/api/auth/login",
                json=admin_creds,
                timeout=10
            )
            
            if response.status_code == 200:
                data = response.json()
                if data.get('access_token'):
                    self.admin_token = data['access_token']
                    self.session.headers.update({'Authorization': f'Bearer {self.admin_token}'})
                    print("✅ Admin authentication successful")
                    return True
            
            print("❌ Admin authentication failed")
            return False
                
        except Exception as e:
            print(f"❌ Admin authentication error: {e}")
            return False
    
    def test_enhanced_boundary_thumbnail_07737947(self):
        """Test enhanced generate-boundary-thumbnail endpoint for apartment property 07737947"""
        print("\n" + "="*80)
        print("TESTING ENHANCED GENERATE-BOUNDARY-THUMBNAIL FOR APARTMENT PROPERTY 07737947")
        print("="*80)
        
        assessment_number = "07737947"
        expected_address = "80 Spinnaker Dr Unit 209 Halifax"
        
        try:
            # Step 1: Get initial property state
            print(f"\n1. Getting initial property state for {assessment_number}...")
            property_response = self.session.get(f"{self.base_url}/api/property/{assessment_number}", timeout=10)
            
            if property_response.status_code == 200:
                initial_property = property_response.json()
                print(f"   ✅ Property found: {initial_property.get('civic_address', 'No address')}")
                print(f"   📍 Initial coordinates: lat={initial_property.get('latitude')}, lng={initial_property.get('longitude')}")
                print(f"   🏠 Property type: {initial_property.get('property_type', 'Unknown')}")
                print(f"   🆔 PID number: {initial_property.get('pid_number', 'None')}")
            else:
                print(f"   ❌ Could not fetch property: HTTP {property_response.status_code}")
                return False
            
            # Step 2: Test the enhanced generate-boundary-thumbnail endpoint
            print(f"\n2. Testing POST /api/generate-boundary-thumbnail/{assessment_number}...")
            response = self.session.post(f"{self.base_url}/api/generate-boundary-thumbnail/{assessment_number}", timeout=30)
            
            if response.status_code != 200:
                print(f"   ❌ Request failed: HTTP {response.status_code}")
                print(f"   Error: {response.text}")
                return False
            
            data = response.json()
            print(f"   ✅ Request successful")
            
            # Step 3: Verify method is "address_based"
            print(f"\n3. Verifying response method...")
            method = data.get('method')
            if method == 'address_based':
                print(f"   ✅ Method is 'address_based' as expected for apartment property")
            else:
                print(f"   ❌ Expected method 'address_based', got '{method}'")
                return False
            
            # Step 4: Verify coordinates are in Halifax area
            print(f"\n4. Verifying coordinates are in Halifax area...")
            center = data.get('center')
            if not center:
                print(f"   ❌ No center coordinates in response")
                return False
            
            lat = center.get('lat')
            lng = center.get('lon')
            
            if not lat or not lng:
                print(f"   ❌ Missing latitude or longitude in center: {center}")
                return False
            
            # Halifax area bounds: lat 44.0-45.5, lng -64.5 to -63.0
            if 44.0 <= lat <= 45.5 and -64.5 <= lng <= -63.0:
                print(f"   ✅ Valid Halifax coordinates: lat={lat}, lng={lng}")
            else:
                print(f"   ❌ Coordinates outside Halifax area: lat={lat}, lng={lng}")
                print(f"   Expected: lat 44.0-45.5, lng -64.5 to -63.0")
                return False
            
            # Step 5: Verify boundary_data is NULL
            print(f"\n5. Verifying boundary_data is NULL...")
            boundary_data = data.get('boundary_data')
            if boundary_data is None:
                print(f"   ✅ Boundary data is NULL as expected for apartment property")
            else:
                print(f"   ❌ Expected boundary_data to be NULL, got: {boundary_data}")
                return False
            
            # Step 6: Verify database was updated with coordinates
            print(f"\n6. Verifying database was updated...")
            updated_property_response = self.session.get(f"{self.base_url}/api/property/{assessment_number}", timeout=10)
            
            if updated_property_response.status_code != 200:
                print(f"   ❌ Could not fetch updated property: HTTP {updated_property_response.status_code}")
                return False
            
            updated_property = updated_property_response.json()
            db_lat = updated_property.get('latitude')
            db_lng = updated_property.get('longitude')
            
            if not db_lat or not db_lng:
                print(f"   ❌ Database coordinates missing: lat={db_lat}, lng={db_lng}")
                return False
            
            # Check if coordinates match (within small tolerance for floating point)
            if abs(float(db_lat) - lat) < 0.001 and abs(float(db_lng) - lng) < 0.001:
                print(f"   ✅ Database updated with coordinates: lat={db_lat}, lng={db_lng}")
            else:
                print(f"   ❌ Database coordinates don't match response:")
                print(f"      Response: lat={lat}, lng={lng}")
                print(f"      Database: lat={db_lat}, lng={db_lng}")
                return False
            
            # Step 7: Verify boundary_data is NULL in database
            print(f"\n7. Verifying boundary_data is NULL in database...")
            db_boundary_data = updated_property.get('boundary_data')
            if db_boundary_data is None:
                print(f"   ✅ Database boundary_data is NULL as expected")
            else:
                print(f"   ❌ Expected database boundary_data to be NULL, got: {db_boundary_data}")
                return False
            
            # Step 8: Verify the address used for geocoding
            print(f"\n8. Verifying address used for geocoding...")
            civic_address = updated_property.get('civic_address', '')
            if expected_address.lower() in civic_address.lower():
                print(f"   ✅ Address contains expected Halifax address: '{civic_address}'")
            else:
                print(f"   ⚠️  Address may have been cleaned: '{civic_address}'")
                print(f"   Expected to contain: '{expected_address}'")
            
            # Final summary
            print(f"\n" + "="*80)
            print("✅ ALL TESTS PASSED - ENHANCED BOUNDARY THUMBNAIL WORKING CORRECTLY")
            print("="*80)
            print(f"✅ PID-based boundary failed (expected for apartment)")
            print(f"✅ Fell back to Google Maps geocoding using address")
            print(f"✅ Successfully returned geocoded coordinates for Halifax area")
            print(f"✅ Updated database with coordinates: {db_lat}, {db_lng}")
            print(f"✅ Set boundary_data to NULL (correct for apartment)")
            print(f"✅ Response method: 'address_based'")
            print(f"✅ Coordinates in valid Halifax range")
            print("="*80)
            
            return True
            
        except Exception as e:
            print(f"\n❌ Test failed with exception: {e}")
            return False
    
    def run_test(self):
        """Run the focused test"""
        print("Enhanced Boundary Thumbnail Test for Property 07737947")
        print("Testing environment variable loading fix with python-dotenv")
        print(f"Backend URL: {self.base_url}")
        print(f"Started at: {datetime.now()}")
        
        # Authenticate first
        if not self.authenticate_admin():
            return False
        
        # Run the main test
        return self.test_enhanced_boundary_thumbnail_07737947()

def main():
    """Main test execution"""
    tester = EnhancedBoundaryThumbnailTester("http://localhost:8001")
    
    try:
        success = tester.run_test()
        if success:
            print(f"\n🎉 TEST COMPLETED SUCCESSFULLY")
            print("The enhanced generate-boundary-thumbnail endpoint is working correctly!")
            print("Environment variable loading issue has been fixed with python-dotenv.")
        else:
            print(f"\n❌ TEST FAILED")
            print("There are issues with the enhanced generate-boundary-thumbnail endpoint.")
        
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\nTesting interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error during testing: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()