#!/usr/bin/env python3

import sys
import os

# Add the backend directory to the Python path
sys.path.append('/app/backend')

from mysql_config import mysql_db

def check_property(assessment_number):
    try:
        property_data = mysql_db.get_property_by_assessment(assessment_number)
        
        if property_data:
            print(f"Property found:")
            print(f"Assessment Number: {property_data['assessment_number']}")
            print(f"Property Type: {property_data.get('property_type', 'NOT SET')}")
            print(f"Civic Address: {property_data.get('civic_address', 'NOT SET')}")
            print(f"Owner Name: {property_data.get('owner_name', 'NOT SET')}")
            print(f"Municipality: {property_data.get('municipality', 'NOT SET')}")
            print(f"Status: {property_data.get('status', 'NOT SET')}")
            print(f"Latitude: {property_data.get('latitude', 'NOT SET')}")
            print(f"Longitude: {property_data.get('longitude', 'NOT SET')}")
            return property_data
        else:
            print(f"Property {assessment_number} not found in database.")
            return None
            
    except Exception as e:
        print(f"Error: {e}")
        return None

def update_property_type(assessment_number, new_type):
    try:
        result = mysql_db.update_property(assessment_number, {'property_type': new_type})
        if result:
            print(f"Successfully updated property {assessment_number} to type '{new_type}'")
        else:
            print(f"Failed to update property {assessment_number}")
        return result
    except Exception as e:
        print(f"Error updating property: {e}")
        return False

if __name__ == "__main__":
    assessment_number = "01999184"
    
    print("Checking current property status:")
    print("=" * 50)
    property_data = check_property(assessment_number)
    
    if property_data:
        current_type = property_data.get('property_type')
        print(f"\nCurrent property_type: {current_type}")
        
        if current_type != 'mobile_home_only':
            print(f"\n🚨 Property {assessment_number} is NOT classified as 'mobile_home_only'")
            print("This explains why the mobile home rescan logic is not being triggered!")
            
            response = input(f"\nDo you want to update property {assessment_number} to 'mobile_home_only'? (y/n): ")
            if response.lower() == 'y':
                if update_property_type(assessment_number, 'mobile_home_only'):
                    print("\n✅ Property type updated successfully!")
                    print("Now checking the updated property:")
                    print("=" * 50)
                    check_property(assessment_number)
                else:
                    print("\n❌ Failed to update property type")
        else:
            print(f"\n✅ Property {assessment_number} is already classified as 'mobile_home_only'")