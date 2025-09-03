#!/usr/bin/env python3
"""
Deep Analysis of Parcel Description vs AAN + Owner Name Issue
Understanding the user's specific concern about property descriptions
"""

import requests
import json
import re

BACKEND_URL = "https://taxsale-hub.preview.emergentagent.com/api"

def analyze_user_concern():
    """
    Analyze the specific user concern:
    User says assessment #00079006 should show actual property description/address 
    from PDF "Parcel Description" field, not just AAN + owner name concatenated
    """
    print("🔍 Deep Analysis: User's Parcel Description Concern")
    print("=" * 70)
    print("User Report: Assessment #00079006 should show actual property description")
    print("from PDF 'Parcel Description' field, not AAN + owner name")
    print("-" * 70)
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to retrieve properties: {response.status_code}")
            return False
        
        properties = response.json()
        
        # Find assessment #00079006
        target_property = None
        for prop in properties:
            if prop.get("assessment_number") == "00079006":
                target_property = prop
                break
        
        if not target_property:
            print("❌ Assessment #00079006 not found in current dataset")
            return False
        
        print(f"\n📋 Current Data for Assessment #00079006:")
        print(f"   Assessment Number: {target_property.get('assessment_number')}")
        print(f"   Property Address: {target_property.get('property_address')}")
        print(f"   Property Description: {target_property.get('property_description')}")
        print(f"   Owner Name: {target_property.get('owner_name')}")
        print(f"   Raw Data: {target_property.get('raw_data', {})}")
        
        # Analyze the current address field
        current_address = target_property.get('property_address', '')
        assessment_num = target_property.get('assessment_number', '')
        owner_name = target_property.get('owner_name', '')
        
        print(f"\n🔍 Analysis of Current Address Field:")
        print(f"   Current Address: '{current_address}'")
        
        # Check if this is just AAN + Owner concatenation
        # The current address is: "00079006 OWEN ST. CLAIR ANDERSON 42"
        # Assessment: 00079006
        # Owner: OWEN ST. CLAIR ANDERSON A2
        
        # Parse the address to understand its components
        address_parts = current_address.split()
        print(f"   Address Parts: {address_parts}")
        
        # Check if it starts with assessment number
        starts_with_aan = current_address.startswith(assessment_num)
        print(f"   Starts with AAN ({assessment_num}): {starts_with_aan}")
        
        # Check if it contains owner name elements
        owner_parts = owner_name.replace(",", "").split()
        owner_in_address = any(part in current_address for part in owner_parts if len(part) > 2)
        print(f"   Contains owner name elements: {owner_in_address}")
        
        # What the user expects vs what we have
        print(f"\n🎯 User's Concern Analysis:")
        print(f"   What user expects: Actual property address/location from PDF 'Parcel Description'")
        print(f"   What we currently have: '{current_address}'")
        
        # This looks like: "00079006 OWEN ST. CLAIR ANDERSON 42"
        # Which could be interpreted as:
        # - Assessment number (00079006) + Street name (OWEN ST.) + Owner name parts + Number (42)
        # OR
        # - A property address that happens to include the assessment number
        
        # Let's check if this follows a pattern that suggests it's a real address
        has_street_indicators = any(indicator in current_address.lower() for indicator in 
                                 ['st.', 'st ', 'street', 'rd.', 'rd ', 'road', 'ave.', 'ave ', 'avenue', 'dr.', 'dr ', 'drive'])
        
        has_numbers = bool(re.search(r'\d+', current_address.replace(assessment_num, '')))
        
        print(f"   Has street indicators: {has_street_indicators}")
        print(f"   Has additional numbers: {has_numbers}")
        
        # The key question: Is "OWEN ST." a real street name or part of owner name?
        # Looking at owner: "OWEN ST. CLAIR ANDERSON A2"
        # Looking at address: "00079006 OWEN ST. CLAIR ANDERSON 42"
        
        # This suggests the address might be constructed as: AAN + Owner name + some modification
        
        print(f"\n🚨 CRITICAL FINDING:")
        if "OWEN ST." in owner_name and "OWEN ST." in current_address:
            print(f"   ❌ CONFIRMED BUG: 'OWEN ST.' appears in both owner name and address")
            print(f"   This suggests the address is constructed from AAN + owner name")
            print(f"   Real parcel description should be a property location, not owner name")
            return False
        else:
            print(f"   ✅ Address appears to be legitimate property description")
            return True
            
    except Exception as e:
        print(f"❌ Error in analysis: {e}")
        return False

def check_other_examples():
    """Check other properties to see the pattern"""
    print(f"\n🔍 Checking Other Properties for Pattern Recognition")
    print("=" * 60)
    
    try:
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        properties = response.json()
        
        print(f"📊 Analyzing patterns in {len(properties)} properties...")
        
        # Look for patterns where owner name appears in address
        suspicious_properties = []
        good_properties = []
        
        for prop in properties:
            assessment = prop.get('assessment_number', '')
            address = prop.get('property_address', '')
            owner = prop.get('owner_name', '')
            
            if not address or "Property at assessment #" in address:
                continue  # Skip placeholders
            
            # Check if significant parts of owner name appear in address
            owner_words = [word.strip(',') for word in owner.split() if len(word.strip(',')) > 3]
            address_words = address.split()
            
            owner_words_in_address = sum(1 for word in owner_words if word in address_words)
            
            if owner_words_in_address >= 2:  # If 2+ owner name words appear in address
                suspicious_properties.append({
                    'assessment': assessment,
                    'address': address,
                    'owner': owner,
                    'overlap_count': owner_words_in_address
                })
            else:
                good_properties.append({
                    'assessment': assessment,
                    'address': address,
                    'owner': owner
                })
        
        print(f"\n📊 Pattern Analysis Results:")
        print(f"   🚨 Suspicious (owner name in address): {len(suspicious_properties)}")
        print(f"   ✅ Good (clean addresses): {len(good_properties)}")
        
        if suspicious_properties:
            print(f"\n🚨 Examples of SUSPICIOUS properties (owner name in address):")
            for i, prop in enumerate(suspicious_properties[:5]):
                print(f"   {i+1}. Assessment #{prop['assessment']}")
                print(f"      Address: {prop['address']}")
                print(f"      Owner: {prop['owner']}")
                print(f"      Overlap words: {prop['overlap_count']}")
                print()
        
        if good_properties:
            print(f"\n✅ Examples of GOOD properties (clean addresses):")
            for i, prop in enumerate(good_properties[:3]):
                print(f"   {i+1}. Assessment #{prop['assessment']}")
                print(f"      Address: {prop['address']}")
                print(f"      Owner: {prop['owner']}")
                print()
        
        # Determine if there's a systematic issue
        total_analyzed = len(suspicious_properties) + len(good_properties)
        if total_analyzed > 0:
            suspicious_percentage = (len(suspicious_properties) / total_analyzed) * 100
            print(f"📈 Overall Assessment:")
            print(f"   {suspicious_percentage:.1f}% of properties have owner names in addresses")
            
            if suspicious_percentage > 20:
                print(f"   ❌ SYSTEMATIC BUG CONFIRMED: High percentage of owner names in addresses")
                return False
            else:
                print(f"   ✅ Acceptable level of owner name overlap")
                return True
        
        return len(suspicious_properties) == 0
        
    except Exception as e:
        print(f"❌ Error checking patterns: {e}")
        return False

if __name__ == "__main__":
    print("🔍 Parcel Description vs AAN + Owner Name Analysis")
    print("Investigating user's specific concern about property descriptions")
    print("=" * 80)
    
    # Analyze the specific user concern
    user_concern_resolved = analyze_user_concern()
    
    # Check patterns in other properties
    pattern_analysis_passed = check_other_examples()
    
    print(f"\n" + "=" * 80)
    print("📋 FINAL VERDICT")
    print("=" * 80)
    
    if user_concern_resolved and pattern_analysis_passed:
        print("✅ USER CONCERN RESOLVED")
        print("   Property descriptions appear to be legitimate addresses")
        print("   No systematic AAN + owner name concatenation detected")
    elif not user_concern_resolved:
        print("❌ USER CONCERN CONFIRMED")
        print("   Assessment #00079006 shows signs of AAN + owner name concatenation")
        print("   Property description should be actual location, not owner name elements")
    else:
        print("⚠️  MIXED RESULTS")
        print("   Target property may be OK, but systematic issues detected in other properties")
    
    print(f"\n💡 RECOMMENDATION:")
    if not (user_concern_resolved and pattern_analysis_passed):
        print("   The PDF parsing logic needs to extract actual 'Parcel Description' field")
        print("   from the PDF, which should contain property location/address information")
        print("   Current implementation appears to concatenate AAN + owner name in some cases")
    else:
        print("   Property descriptions appear to be working correctly")
        print("   User concern may be based on outdated data or misunderstanding")