#!/usr/bin/env python3
"""
Test different approaches to access the Halifax PDF
"""

import requests
import time

def test_pdf_access_methods():
    """Test different methods to access the Halifax PDF"""
    pdf_url = "https://www.halifax.ca/media/91654"
    
    print("🔍 Testing Different PDF Access Methods")
    print("=" * 50)
    
    # Method 1: Basic request (current implementation)
    print("\n1. Basic Request (Current Implementation):")
    try:
        response = requests.get(pdf_url, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Size: {len(response.content)} bytes")
        else:
            print(f"   Error: {response.reason}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 2: With User-Agent header
    print("\n2. With User-Agent Header:")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Size: {len(response.content)} bytes")
        else:
            print(f"   Error: {response.reason}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 3: With full browser headers
    print("\n3. With Full Browser Headers:")
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    try:
        response = requests.get(pdf_url, headers=headers, timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Size: {len(response.content)} bytes")
        else:
            print(f"   Error: {response.reason}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 4: With session and referrer
    print("\n4. With Session and Referrer:")
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': 'https://www.halifax.ca/home-property/property-taxes/tax-sale'
    })
    
    try:
        # First visit the main page
        main_response = session.get('https://www.halifax.ca/home-property/property-taxes/tax-sale', timeout=30)
        print(f"   Main page status: {main_response.status_code}")
        
        # Then try to get the PDF
        time.sleep(1)  # Small delay
        response = session.get(pdf_url, timeout=30)
        print(f"   PDF status: {response.status_code}")
        if response.status_code == 200:
            print(f"   Content-Type: {response.headers.get('content-type', 'unknown')}")
            print(f"   Size: {len(response.content)} bytes")
        else:
            print(f"   Error: {response.reason}")
    except Exception as e:
        print(f"   Exception: {e}")
    
    # Method 5: Check if URL is still valid
    print("\n5. Testing Main Tax Sale Page:")
    try:
        response = requests.get('https://www.halifax.ca/home-property/property-taxes/tax-sale', 
                              headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'}, 
                              timeout=30)
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            # Look for PDF links in the page
            content = response.text.lower()
            if 'pdf' in content:
                print("   ✅ Page contains PDF references")
            if '91654' in content:
                print("   ✅ Page contains the specific PDF ID (91654)")
            if 'schedule' in content:
                print("   ✅ Page contains 'schedule' references")
        else:
            print(f"   Error: {response.reason}")
    except Exception as e:
        print(f"   Exception: {e}")

if __name__ == "__main__":
    test_pdf_access_methods()