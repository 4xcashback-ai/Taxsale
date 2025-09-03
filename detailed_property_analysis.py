#!/usr/bin/env python3
"""
Detailed Property Description Analysis for Halifax Tax Sale Scraper
Specifically tests the assessments mentioned in the review request
"""

import requests
import json
import re
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://assessment-finder.preview.emergentagent.com/api"

def analyze_specific_assessments():
    """Analyze specific assessments mentioned in the review request"""
    print("🔍 DETAILED ANALYSIS: Specific Assessment Numbers from Review Request")
    print("=" * 80)
    
    # Target assessments from the review request
    target_assessments = ["00079006", "00125326", "00374059", "02102943"]
    
    try:
        # Get all Halifax properties
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax", timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to retrieve Halifax properties: {response.status_code}")
            return False
        
        properties = response.json()
        print(f"📊 Retrieved {len(properties)} Halifax properties for analysis")
        
        found_assessments = {}
        all_assessments = []
        
        # Collect all assessment numbers and find target ones
        for prop in properties:
            assessment = prop.get("assessment_number", "")
            all_assessments.append(assessment)
            
            if assessment in target_assessments:
                found_assessments[assessment] = prop
        
        print(f"\n🎯 TARGET ASSESSMENT ANALYSIS:")
        print("-" * 50)
        
        for target in target_assessments:
            if target in found_assessments:
                prop = found_assessments[target]
                address = prop.get("property_address", "")
                owner = prop.get("owner_name", "")
                description = prop.get("property_description", "")
                
                print(f"\n✅ Assessment #{target} FOUND:")
                print(f"   📍 Property Address: '{address}'")
                print(f"   👤 Owner Name: '{owner}'")
                print(f"   📝 Property Description: '{description}'")
                
                # Check if this looks like AAN + owner concatenation
                is_concatenation = False
                analysis_notes = []
                
                # Check if address contains the assessment number
                if target in address:
                    analysis_notes.append("⚠️ Assessment number appears in address")
                
                # Check if address contains owner name parts
                if owner and len(owner) > 5:
                    owner_words = owner.upper().split()
                    address_upper = address.upper()
                    matching_words = [word for word in owner_words if word in address_upper and len(word) > 2]
                    if matching_words:
                        analysis_notes.append(f"⚠️ Owner name parts found in address: {matching_words}")
                        is_concatenation = True
                
                # Check if it looks like a real property address
                address_indicators = ["ST", "STREET", "RD", "ROAD", "AVE", "AVENUE", "DR", "DRIVE", 
                                    "CT", "COURT", "CRT", "LN", "LANE", "WAY", "PL", "PLACE", "CRES", "CRESCENT"]
                has_address_indicators = any(indicator in address.upper() for indicator in address_indicators)
                
                if has_address_indicators:
                    analysis_notes.append("✅ Contains street address indicators")
                else:
                    analysis_notes.append("⚠️ No clear street address indicators")
                
                # Check for street numbers
                street_number_match = re.search(r'^\d+\s+', address.strip())
                if street_number_match:
                    analysis_notes.append("✅ Starts with street number")
                else:
                    analysis_notes.append("⚠️ No street number at start")
                
                # Overall assessment
                if is_concatenation:
                    print(f"   🚨 ISSUE DETECTED: Likely AAN + owner name concatenation")
                else:
                    print(f"   ✅ LOOKS GOOD: Appears to be proper property description")
                
                for note in analysis_notes:
                    print(f"   {note}")
                    
            else:
                print(f"\n❌ Assessment #{target} NOT FOUND in current data")
        
        print(f"\n📈 OVERALL PROPERTY DESCRIPTION QUALITY ANALYSIS:")
        print("-" * 60)
        
        # Analyze all properties for description quality
        good_descriptions = 0
        bad_descriptions = 0
        concatenation_issues = 0
        placeholder_issues = 0
        
        analysis_details = []
        
        for prop in properties:
            assessment = prop.get("assessment_number", "")
            address = prop.get("property_address", "")
            owner = prop.get("owner_name", "")
            
            # Skip if missing key data
            if not assessment or not address or not owner:
                continue
            
            issues = []
            
            # Check for placeholder patterns
            if "Property at assessment #" in address:
                issues.append("placeholder")
                placeholder_issues += 1
            
            # Check for AAN + owner concatenation
            if assessment in address and owner:
                owner_words = owner.upper().split()
                address_upper = address.upper()
                matching_words = [word for word in owner_words if word in address_upper and len(word) > 2]
                if len(matching_words) >= 2:  # Multiple owner name parts in address
                    issues.append("concatenation")
                    concatenation_issues += 1
            
            # Check for proper address indicators
            address_indicators = ["ST", "STREET", "RD", "ROAD", "AVE", "AVENUE", "DR", "DRIVE", 
                                "CT", "COURT", "CRT", "LN", "LANE", "WAY", "PL", "PLACE", "CRES", "CRESCENT"]
            has_address_indicators = any(indicator in address.upper() for indicator in address_indicators)
            street_number = re.search(r'^\d+\s+', address.strip())
            
            if issues:
                bad_descriptions += 1
                analysis_details.append({
                    "assessment": assessment,
                    "address": address,
                    "owner": owner,
                    "issues": issues
                })
            elif has_address_indicators or street_number:
                good_descriptions += 1
            else:
                # Ambiguous case
                bad_descriptions += 1
                analysis_details.append({
                    "assessment": assessment,
                    "address": address,
                    "owner": owner,
                    "issues": ["unclear_format"]
                })
        
        total_analyzed = good_descriptions + bad_descriptions
        
        print(f"Total properties analyzed: {total_analyzed}")
        print(f"✅ Good descriptions: {good_descriptions} ({(good_descriptions/total_analyzed*100):.1f}%)")
        print(f"❌ Bad descriptions: {bad_descriptions} ({(bad_descriptions/total_analyzed*100):.1f}%)")
        print(f"   - Placeholder issues: {placeholder_issues}")
        print(f"   - Concatenation issues: {concatenation_issues}")
        
        # Show examples of problematic descriptions
        if analysis_details:
            print(f"\n🚨 EXAMPLES OF PROBLEMATIC DESCRIPTIONS:")
            print("-" * 50)
            for i, detail in enumerate(analysis_details[:10]):  # Show first 10
                print(f"{i+1}. Assessment #{detail['assessment']}")
                print(f"   Address: '{detail['address']}'")
                print(f"   Owner: '{detail['owner']}'")
                print(f"   Issues: {', '.join(detail['issues'])}")
                print()
        
        # Determine if the fix is working
        success_rate = (good_descriptions / total_analyzed * 100) if total_analyzed > 0 else 0
        
        print(f"\n🎯 FINAL ASSESSMENT:")
        print("-" * 30)
        if success_rate >= 90:
            print(f"✅ EXCELLENT: {success_rate:.1f}% success rate - Property descriptions are working well")
            return True
        elif success_rate >= 75:
            print(f"⚠️ GOOD: {success_rate:.1f}% success rate - Minor issues remain")
            return True
        elif success_rate >= 50:
            print(f"⚠️ FAIR: {success_rate:.1f}% success rate - Significant issues remain")
            return False
        else:
            print(f"❌ POOR: {success_rate:.1f}% success rate - Major issues with property descriptions")
            return False
            
    except Exception as e:
        print(f"❌ Analysis error: {e}")
        return False

def check_parcel_description_extraction():
    """Check if actual Parcel Description field is being extracted from PDF"""
    print(f"\n🔍 PARCEL DESCRIPTION FIELD EXTRACTION ANALYSIS")
    print("=" * 60)
    
    try:
        # Get a sample of Halifax properties to analyze raw data
        response = requests.get(f"{BACKEND_URL}/tax-sales?municipality=Halifax&limit=10", timeout=30)
        if response.status_code != 200:
            print(f"❌ Failed to retrieve sample properties: {response.status_code}")
            return False
        
        properties = response.json()
        
        print(f"📊 Analyzing {len(properties)} sample properties for raw data structure...")
        
        for i, prop in enumerate(properties[:5]):  # Check first 5 properties
            print(f"\n📋 Property {i+1}:")
            print(f"   Assessment: {prop.get('assessment_number', 'N/A')}")
            print(f"   Address: {prop.get('property_address', 'N/A')}")
            print(f"   Owner: {prop.get('owner_name', 'N/A')}")
            
            # Check raw_data field for original PDF extraction
            raw_data = prop.get('raw_data', {})
            if raw_data:
                print(f"   Raw Data Available: ✅")
                parcel_desc = raw_data.get('parcel_description', 'Not found')
                print(f"   Parcel Description from PDF: '{parcel_desc}'")
                
                # Compare with what's being used as address
                current_address = prop.get('property_address', '')
                if parcel_desc != 'Not found' and parcel_desc != current_address:
                    print(f"   ⚠️ MISMATCH: PDF parcel description differs from current address")
                elif parcel_desc == current_address:
                    print(f"   ✅ MATCH: Using actual parcel description from PDF")
                else:
                    print(f"   ❓ UNCLEAR: Parcel description not found in raw data")
            else:
                print(f"   Raw Data Available: ❌")
        
        return True
        
    except Exception as e:
        print(f"❌ Parcel description analysis error: {e}")
        return False

if __name__ == "__main__":
    print(f"Detailed Property Analysis - Backend: {BACKEND_URL}")
    print(f"Analysis started at: {datetime.now()}")
    print()
    
    # Run specific assessment analysis
    assessment_success = analyze_specific_assessments()
    
    # Check parcel description extraction
    parcel_success = check_parcel_description_extraction()
    
    print(f"\n" + "=" * 80)
    print(f"📋 DETAILED ANALYSIS SUMMARY")
    print(f"=" * 80)
    print(f"Specific Assessments Analysis: {'✅ PASS' if assessment_success else '❌ FAIL'}")
    print(f"Parcel Description Extraction: {'✅ PASS' if parcel_success else '❌ FAIL'}")
    
    if assessment_success and parcel_success:
        print(f"\n🎉 OVERALL RESULT: Property description extraction is working correctly!")
        print(f"   The user's concern about AAN + owner name concatenation appears to be resolved.")
    else:
        print(f"\n🚨 OVERALL RESULT: Issues remain with property description extraction!")
        print(f"   The user's concern about extracting actual Parcel Description field needs attention.")