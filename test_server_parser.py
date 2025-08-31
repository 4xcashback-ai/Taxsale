#!/usr/bin/env python3
"""
Test the actual server parsing function
"""

import sys
import os
sys.path.append('/app/backend')

# Import the actual parsing function from the server
from server import parse_victoria_county_pdf

# The actual PDF text
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

if __name__ == "__main__":
    print("Testing actual server parsing function...")
    try:
        properties = parse_victoria_county_pdf(pdf_text, "test-municipality-id")
        print(f"Result: {len(properties)} properties found")
        
        for i, prop in enumerate(properties):
            print(f"{i+1}. AAN: {prop.get('assessment_number')}, Owner: {prop.get('owner_name')}")
            print(f"   Address: {prop.get('property_address')}")
            print(f"   PID: {prop.get('pid_number')}, Tax: ${prop.get('opening_bid', 0):.2f}")
            print(f"   Type: {prop.get('property_type')}")
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()