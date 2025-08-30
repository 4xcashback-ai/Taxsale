#!/usr/bin/env python3
"""
Detailed Property Description Testing for Halifax Tax Sale Scraper
Focus on specific assessments mentioned in the review request
"""

import requests
import json
import re

BACKEND_URL = "https://nstaxmap-1.preview.emergentagent.com/api"

def test_specific_assessments():
    """Test specific assessment numbers mentioned in the review request"""
    target_assessments = ["00079006", "00125326", "00374059", "02102943"]
    
    print("🎯 Testing Specific Assessment Numbers from Review Request")
    print("=" * 60)
    
    try:
        # Get all Halifax properties
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to retrieve properties: {response.status_code}")
            return False
        
        properties = response.json()
        print(f"📊 Retrieved {len(properties)} Halifax properties")
        
        found_properties = {}
        
        # Find each target assessment
        for target in target_assessments:
            for prop in properties:
                if prop.get("assessment_number") == target:
                    found_properties[target] = prop
                    break
        
        print(f"\n🔍 Analysis of Target Assessments:")
        print("-" * 40)
        
        for assessment in target_assessments:
            print(f"\n📋 Assessment #{assessment}:")
            if assessment in found_properties:
                prop = found_properties[assessment]
                address = prop.get("property_address", "N/A")
                description = prop.get("property_description", "N/A")
                owner = prop.get("owner_name", "N/A")
                
                print(f"   ✅ FOUND")
                print(f"   📍 Address: {address}")
                print(f"   📝 Description: {description}")
                print(f"   👤 Owner: {owner}")
                
                # Analyze if this is a proper property description vs AAN + owner name
                is_placeholder = "Property at assessment #" in address
                is_aan_plus_owner = (assessment in address and owner.replace(",", "").replace(" ", "") in address.replace(",", "").replace(" ", ""))
                
                if is_placeholder:
                    print(f"   ❌ STATUS: Placeholder description (Property at assessment #)")
                elif is_aan_plus_owner and len(address) < 50:
                    print(f"   ⚠️  STATUS: Appears to be AAN + Owner name concatenation")
                else:
                    # Check if it contains actual address elements
                    address_indicators = ["rd", "st", "ave", "drive", "road", "street", "avenue", "lane", "court", "place", "way", "lot", "unit", "highway"]
                    has_address_elements = any(indicator in address.lower() for indicator in address_indicators)
                    
                    if has_address_elements:
                        print(f"   ✅ STATUS: Proper property description with address elements")
                    else:
                        print(f"   ⚠️  STATUS: May be AAN + Owner, lacks clear address elements")
                
            else:
                print(f"   ❌ NOT FOUND in current dataset")
        
        # Overall analysis
        print(f"\n📈 Overall Assessment:")
        total_found = len(found_properties)
        print(f"   Found {total_found}/{len(target_assessments)} target properties")
        
        if total_found > 0:
            # Check what percentage have proper descriptions
            proper_descriptions = 0
            for assessment, prop in found_properties.items():
                address = prop.get("property_address", "")
                if not "Property at assessment #" in address:
                    # Check for address elements
                    address_indicators = ["rd", "st", "ave", "drive", "road", "street", "avenue", "lane", "court", "place", "way", "lot", "unit", "highway"]
                    if any(indicator in address.lower() for indicator in address_indicators):
                        proper_descriptions += 1
            
            percentage = (proper_descriptions / total_found) * 100
            print(f"   {proper_descriptions}/{total_found} ({percentage:.1f}%) have proper property descriptions")
            
            return proper_descriptions == total_found
        else:
            print(f"   ❌ No target properties found - cannot assess description quality")
            return False
            
    except Exception as e:
        print(f"❌ Error testing specific assessments: {e}")
        return False

def analyze_all_property_descriptions():
    """Analyze all Halifax property descriptions to understand the pattern"""
    print(f"\n🔍 Comprehensive Property Description Analysis")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to retrieve properties: {response.status_code}")
            return False
        
        properties = response.json()
        print(f"📊 Analyzing {len(properties)} Halifax properties")
        
        # Categorize descriptions
        categories = {
            "placeholder": [],  # "Property at assessment #XXXXXXXX"
            "aan_plus_owner": [],  # Assessment number + owner name
            "proper_address": [],  # Contains actual address elements
            "other": []
        }
        
        address_indicators = ["rd", "st", "ave", "drive", "road", "street", "avenue", "lane", "court", "place", "way", "lot", "unit", "highway", "crescent", "circle", "close"]
        
        for prop in properties:
            assessment = prop.get("assessment_number", "")
            address = prop.get("property_address", "")
            owner = prop.get("owner_name", "")
            
            if "Property at assessment #" in address:
                categories["placeholder"].append(prop)
            elif any(indicator in address.lower() for indicator in address_indicators):
                categories["proper_address"].append(prop)
            elif assessment in address and len(address) < 100:
                # Likely AAN + owner concatenation
                categories["aan_plus_owner"].append(prop)
            else:
                categories["other"].append(prop)
        
        # Report results
        total = len(properties)
        print(f"\n📊 Description Categories:")
        print(f"   ✅ Proper addresses: {len(categories['proper_address'])} ({len(categories['proper_address'])/total*100:.1f}%)")
        print(f"   ⚠️  AAN + Owner: {len(categories['aan_plus_owner'])} ({len(categories['aan_plus_owner'])/total*100:.1f}%)")
        print(f"   ❌ Placeholders: {len(categories['placeholder'])} ({len(categories['placeholder'])/total*100:.1f}%)")
        print(f"   ❓ Other: {len(categories['other'])} ({len(categories['other'])/total*100:.1f}%)")
        
        # Show examples from each category
        if categories["proper_address"]:
            print(f"\n✅ Examples of PROPER ADDRESS descriptions:")
            for i, prop in enumerate(categories["proper_address"][:3]):
                print(f"   {i+1}. #{prop.get('assessment_number')}: {prop.get('property_address')}")
        
        if categories["aan_plus_owner"]:
            print(f"\n⚠️  Examples of AAN + OWNER descriptions:")
            for i, prop in enumerate(categories["aan_plus_owner"][:3]):
                print(f"   {i+1}. #{prop.get('assessment_number')}: {prop.get('property_address')}")
        
        if categories["placeholder"]:
            print(f"\n❌ Examples of PLACEHOLDER descriptions:")
            for i, prop in enumerate(categories["placeholder"][:3]):
                print(f"   {i+1}. #{prop.get('assessment_number')}: {prop.get('property_address')}")
        
        # Determine if the bug is resolved
        placeholder_percentage = len(categories["placeholder"]) / total * 100
        proper_percentage = len(categories["proper_address"]) / total * 100
        
        print(f"\n🎯 Bug Assessment:")
        if placeholder_percentage > 5:
            print(f"   ❌ SIGNIFICANT BUG: {placeholder_percentage:.1f}% have placeholder descriptions")
            return False
        elif proper_percentage < 70:
            print(f"   ⚠️  PARTIAL BUG: Only {proper_percentage:.1f}% have proper address descriptions")
            print(f"   Most descriptions appear to be AAN + Owner name concatenations")
            return False
        else:
            print(f"   ✅ BUG RESOLVED: {proper_percentage:.1f}% have proper descriptions, {placeholder_percentage:.1f}% placeholders")
            return True
            
    except Exception as e:
        print(f"❌ Error analyzing descriptions: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Detailed Property Description Analysis for Halifax Tax Sale Scraper")
    print("Focus: User-reported bug about property descriptions vs AAN + owner name")
    print("=" * 80)
    
    # Test specific assessments mentioned in review
    specific_test_passed = test_specific_assessments()
    
    # Analyze all property descriptions
    overall_test_passed = analyze_all_property_descriptions()
    
    print(f"\n" + "=" * 80)
    print("📋 FINAL ASSESSMENT")
    print("=" * 80)
    
    if specific_test_passed and overall_test_passed:
        print("✅ PROPERTY DESCRIPTION BUG RESOLVED")
        print("   All target assessments have proper property descriptions")
        print("   Overall description quality is acceptable")
    elif specific_test_passed:
        print("⚠️  PARTIAL RESOLUTION")
        print("   Target assessments have proper descriptions")
        print("   But overall description quality needs improvement")
    else:
        print("❌ PROPERTY DESCRIPTION BUG STILL EXISTS")
        print("   Properties are showing AAN + owner name instead of actual property descriptions")
        print("   This matches the user's reported issue")