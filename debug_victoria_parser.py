#!/usr/bin/env python3
"""
Debug Victoria County PDF Parser
Test the parsing logic with the actual PDF content
"""

import re
import uuid
from datetime import datetime, timezone

# The actual PDF text from the debug endpoint
pdf_text = """MUNICIPALITY OF THE COUNTY OF VICTORIA
TAX SALE BY TENDER BID SUBMISSION
Tuesday, August 26TH, 2025 at 2:00 PM
Last updated: August 22nd, 2025
PUBLIC NOTICE is hereby given in accordance with Sect. 142 of the NS Municipal Government
Act that the lands and premises situated in the Municipality of the County of Victoria, hereunder
described, shall be SOLD BY TENDER BID SUBMISSION, on August 26, 2025, at 2:00pm unless
before said time the amounts due are paid.
The Municipality of the County of Victoria makes no representations or warranties to any purchaser
regarding any property sold at tax sale, including, but not limited to, the environmental condition of any
property, the fitness, geographical or environmental suitability of the land(s) offered for sale for any
particular use. The Municipality does not certify the "legal title", "legal description", "access" or
"boundaries" and the lands offered for sale are BEING SOLD ON AN "AS IS" BASIS ONLY.
PLEASE NOTE: Tax Sales do not in all circumstances clear up defects in the title. A tax deed conveys
only the interest of the assessed owner, whatever that interest may be. If you are intending to clear up
defects in the title of your property by way of a Tax Sale, you are advised to obtain a legal opinion as to
whether this can be done.
The purchaser will be responsible for all property taxes beginning the day of the sale. The Treasurer
has not made any determination as to whether a survey is or is not required.
IMPORTANT INFORMATION:
TERMS: Taxes, interest, and costs owing to be paid immediately at the time of purchase by CASH, MONEY
ORDER, BANK DRAFT, CERTIFIED CHEQUE, OR LAWYER'S TRUST CHEQUE. The balance of the
purchase price, if any, must be paid within three (3) days of sale by cash, money order, bank draft, certified
cheque, or lawyer's trust cheque.
Please note the following definitions:
Land Registered: The property is migrated.
Not Land Registered: The property is not migrated.
Redeemable: The property can be redeemed within six (6) months by the listed owner in this ad.
Not Redeemable: The property cannot be redeemed by the listed owner in this ad.
Redemption of Tax Sale Property- Section 152(1) MGA:
Land sold for non-payment of taxes may be redeemed by the owner, a person with a mortgage, lien
or other charge on the land or a person having an interest in the land within six months after the date
of the sale.
At the time of the tax sale, if any taxes on lands are in arrears for more than six years, no right of
redemption exists.
Properties subject to HST charges will be collected from the successful bidder on top of the
FINAL BID PRICE.
For more information on the properties listed, please go to www.pvsc.ca.
Tax sale listings as well as Tender Bid Terms/Submission forms can be found online at
www.victoriacounty.com or at the Municipal Building at 495 Chebucto St., Baddeck.
Dated at Baddeck, N.S. July 25th, 2025
Municipality of the County of Victoria
www.victoriacounty.com
MUNICIPALITY OF THE COUNTY OF VICTORIA
TAX SALE BY TENDER BID SUBMISSION
Tuesday, August 26TH, 2025 at 2:00 PM
Last updated: August 22nd, 2025
1. AAN: 00254118 / PID: 85006500 – Property assessed to Donald John Beaton.
Land/Dwelling, located at 198 Little Narrows Rd, Little Narrows, 22,230 Sq. Feet +/-.
Redeemable/ Not Land Registered.
Taxes, Interest and Expenses owing: $2,009.03
2. AAN: 00453706 / PID: 85010866/85074276 – Property assessed to Kenneth Ferneyhough. Land/
Dwelling, located at 30 5413 (P) Rd., Middle River, 3,100 Sq. Feet +/-.
Redeemable/ Not Land Registered.
Taxes, Interest and Expenses owing: $1,599.71
3. PAID
4. PAID
5. PAID
6. PAID
7. DEFERRED
8. AAN: 09541209 / PID: 85142388 - Property assessed to Florance Debra Cleaves/Debra Cleaves.
Land only, located at Washabuck Rd., Washabuck Centre, 2.5 Acres +/-.
Non-Redeemable/ Not Land Registered.
Taxes, Interest and Expenses owing: $5,031.96 + HST
9. DEFERRED
10. PAID
11. DEFERRED
12. DEFERRED
Dated at Baddeck, N.S. July 25th, 2025
Municipality of the County of Victoria
www.victoriacounty.com"""

def debug_parse_victoria_county_pdf(pdf_text: str, municipality_id: str = "test-id") -> list:
    """Debug version of the Victoria County PDF parser"""
    properties = []
    
    try:
        print("=== DEBUGGING VICTORIA COUNTY PDF PARSER ===")
        print(f"PDF text length: {len(pdf_text)} characters")
        
        # Extract sale date from PDF header first
        sale_date = "2025-05-15"  # Default fallback
        sale_location = "Victoria County Municipal Office"  # Default
        
        # Look for sale date pattern
        date_patterns = [
            r'(\w+,\s*\w+\s+\d+\w*,?\s*\d{4})\s*at\s*(\d+:\d+\s*[AP]M)',
            r'(\w+\s+\d+\w*,?\s*\d{4})\s*at\s*(\d+:\d+\s*[AP]M)',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            date_match = re.search(pattern, pdf_text, re.IGNORECASE)
            if date_match:
                date_str = date_match.group(1)
                print(f"Found date string: {date_str}")
                # Convert "Tuesday, August 26TH, 2025" to "2025-08-26"
                if "august" in date_str.lower():
                    # Extract day and year
                    day_match = re.search(r'(\d+)', date_str)
                    year_match = re.search(r'(\d{4})', date_str)
                    if day_match and year_match:
                        day = day_match.group(1).zfill(2)
                        year = year_match.group(1)
                        sale_date = f"{year}-08-{day}"
                        print(f"Extracted sale date: {sale_date}")
                break
        
        print(f"Final sale date: {sale_date}")
        
        # Find all numbered entries first
        print("\n=== FINDING ALL NUMBERED ENTRIES ===")
        all_numbered_entries = re.finditer(r'(\d+)\.\s*([^\n]+)', pdf_text)
        
        valid_properties = []
        for entry_match in all_numbered_entries:
            entry_number = entry_match.group(1)
            entry_content = entry_match.group(2).strip()
            
            print(f"Entry {entry_number}: {entry_content}")
            
            # Check if this entry contains actual property data (has AAN)
            if "AAN:" in entry_content:
                print(f"  -> Entry {entry_number} contains property data - extracting full section")
                
                # Extract the full property section from this entry to the next numbered entry
                start_pos = entry_match.start()
                
                # Find the next numbered entry to determine where this property section ends
                next_entry_pattern = rf'{int(entry_number) + 1}\.\s*'
                next_entry_match = re.search(next_entry_pattern, pdf_text[start_pos + 10:])
                
                if next_entry_match:
                    end_pos = start_pos + 10 + next_entry_match.start()
                else:
                    # If no next entry found, look for any next numbered entry
                    any_next_entry = re.search(r'\d+\.\s*', pdf_text[start_pos + 10:])
                    if any_next_entry:
                        end_pos = start_pos + 10 + any_next_entry.start()
                    else:
                        end_pos = len(pdf_text)
                
                section = pdf_text[start_pos:end_pos].strip()
                
                # Extract AAN, PID from the section
                aan_match = re.search(r'AAN:\s*(\d+)', section)
                pid_match = re.search(r'PID:\s*([\d/]+)', section)
                
                valid_properties.append({
                    'entry_number': entry_number,
                    'aan': aan_match.group(1) if aan_match else 'Unknown',
                    'pid': pid_match.group(1) if pid_match else 'Unknown',
                    'section': section
                })
                
                print(f"  -> Property {entry_number}: AAN={valid_properties[-1]['aan']}, PID={valid_properties[-1]['pid']}")
                print(f"  -> Full section: {section}")
            else:
                print(f"  -> Entry {entry_number} is not a property: {entry_content}")
        
        print(f"\n=== FOUND {len(valid_properties)} VALID PROPERTIES ===")
        
        # Process each valid property section
        for i, valid_prop in enumerate(valid_properties):
            section = valid_prop['section']
            entry_number = valid_prop['entry_number']
            
            print(f"\n=== PROCESSING PROPERTY {i+1} (Entry {entry_number}) ===")
            print(f"Section content: {section}")
            
            try:
                # Extract AAN and PID from section with more flexible patterns
                # Handle formats like:
                # "X. AAN: 00254118 / PID: 85006500 – Property assessed to Donald John Beaton."
                # "X. AAN: 00453706 / PID: 85010866/85074276 – Property assessed to Kenneth Ferneyhough."
                
                # Extract AAN
                aan_match = re.search(r'AAN:\s*(\d+)', section)
                assessment_number = aan_match.group(1) if aan_match else None
                print(f"  AAN: {assessment_number}")
                
                # Extract PID (handle multiple PIDs separated by /)
                pid_match = re.search(r'PID:\s*([\d/]+)', section)
                pid_number = pid_match.group(1) if pid_match else None
                print(f"  PID: {pid_number}")
                
                # Extract owner name with flexible patterns
                owner_patterns = [
                    r'Property assessed to\s+([^.]+)\.',
                    r'assessed to\s+([^.]+)\.',
                    r'–\s*Property assessed to\s+([^.]+)\.'
                ]
                
                owner_name = None
                for pattern in owner_patterns:
                    owner_match = re.search(pattern, section, re.IGNORECASE)
                    if owner_match:
                        owner_name = owner_match.group(1).strip()
                        print(f"  Owner (pattern '{pattern}'): {owner_name}")
                        break
                
                if not assessment_number or not owner_name:
                    print(f"  ERROR: Could not parse required fields from section")
                    continue
                    
                print(f"  SUCCESS: Parsed Property #{entry_number}: AAN={assessment_number}, PID={pid_number}, Owner={owner_name}")
                
                # Extract property type and address with flexible patterns
                property_type = "Property"
                property_address = "Address not specified"
                lot_size = None
                
                # Extract property type (before first comma)
                type_match = re.search(r'([^,]+),\s*located at', section, re.IGNORECASE)
                if type_match:
                    property_type = type_match.group(1).strip()
                    print(f"  Property Type: {property_type}")
                
                # Extract address and lot size with flexible patterns
                location_patterns = [
                    # Pattern 1: address with size in Sq. Feet
                    r'located at\s*([^,]+(?:,\s*[^,]+)*),\s*([\d,]+)\s*Sq\.\s*Feet\s*\+/-',
                    # Pattern 2: address with size in Acres
                    r'located at\s*([^,]+(?:,\s*[^,]+)*),\s*([\d.]+)\s*Acres\s*\+/-',
                    # Pattern 3: just address without size
                    r'located at\s*([^,]+(?:,\s*[^,]+)*)'
                ]
                
                for pattern in location_patterns:
                    location_match = re.search(pattern, section, re.IGNORECASE)
                    if location_match:
                        property_address = location_match.group(1).strip()
                        if len(location_match.groups()) > 1:
                            size_number = location_match.group(2).strip()
                            if 'Acres' in pattern:
                                lot_size = f"{size_number} Acres +/-"
                            else:
                                lot_size = f"{size_number} Sq. Feet +/-"
                        print(f"  Address (pattern '{pattern}'): {property_address}")
                        print(f"  Lot Size: {lot_size}")
                        break
                
                # Extract redeemable status
                redeemable = "Unknown"
                if re.search(r'Non-Redeemable', section, re.IGNORECASE):
                    redeemable = "No"
                elif re.search(r'Redeemable', section, re.IGNORECASE):
                    redeemable = "Yes"
                print(f"  Redeemable: {redeemable}")
                
                # Extract tax amount
                tax_match = re.search(r'Taxes[^:]*:\s*\$?([\d,]+\.?\d*)', section)
                opening_bid = 0.0
                
                if tax_match:
                    tax_amount_str = tax_match.group(1).replace(',', '')
                    try:
                        opening_bid = float(tax_amount_str)
                        print(f"  Tax Amount: ${opening_bid:.2f}")
                    except ValueError:
                        print(f"  ERROR: Could not parse tax amount: {tax_amount_str}")
                
                # Create property object
                property_data = {
                    "id": str(uuid.uuid4()),
                    "municipality_id": municipality_id,
                    "assessment_number": assessment_number,
                    "owner_name": owner_name,
                    "property_address": property_address,
                    "pid_number": pid_number,
                    "opening_bid": opening_bid,
                    "municipality_name": "Victoria County",
                    "sale_date": sale_date,
                    "property_type": property_type,
                    "lot_size": lot_size,
                    "sale_location": sale_location,
                    "status": "active",
                    "redeemable": redeemable,
                    "hst_applicable": "No",  # Default for Victoria County
                    "property_description": f"{property_address} {property_type}" + (f" - {lot_size}" if lot_size else ""),
                    "latitude": None,
                    "longitude": None,
                    "scraped_at": datetime.now(timezone.utc),
                    "source_url": "https://victoriacounty.com",
                    "raw_data": {
                        "assessment_number": assessment_number,
                        "pid_number": pid_number,
                        "owner_name": owner_name,
                        "property_address": property_address,
                        "property_type": property_type,
                        "lot_size": lot_size,
                        "redeemable": redeemable,
                        "taxes_owing": f"${opening_bid:.2f}",
                        "sale_date_extracted": sale_date,
                        "raw_section": section[:500]  # Store first 500 chars for debugging
                    }
                }
                
                properties.append(property_data)
                print(f"  ADDED: Victoria County property: AAN {assessment_number}, Owner: {owner_name}")
                
            except Exception as e:
                print(f"  ERROR: Error parsing property section: {e}")
                continue
    
    except Exception as e:
        print(f"ERROR: Victoria County PDF parsing failed: {e}")
    
    print(f"\n=== FINAL RESULT: {len(properties)} PROPERTIES PARSED ===")
    for i, prop in enumerate(properties):
        print(f"{i+1}. AAN: {prop['assessment_number']}, Owner: {prop['owner_name']}")
        print(f"   Address: {prop['property_address']}")
        print(f"   PID: {prop['pid_number']}, Tax: ${prop['opening_bid']:.2f}")
        print(f"   Type: {prop['property_type']}, Size: {prop['lot_size']}")
    
    return properties

if __name__ == "__main__":
    print("Testing Victoria County PDF Parser with actual PDF content...")
    properties = debug_parse_victoria_county_pdf(pdf_text)
    print(f"\nResult: {len(properties)} properties found")