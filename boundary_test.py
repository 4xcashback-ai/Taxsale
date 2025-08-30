#!/usr/bin/env python3
"""
Boundary Thumbnail Generation Testing - Review Request Focus
Tests the specific boundary thumbnail generation endpoints requested
"""

import requests
import json
import sys
from datetime import datetime
import time

# Get backend URL from environment
BACKEND_URL = "https://taxsalecompass.ca/api"

def test_boundary_thumbnail_generation():
    """Test Boundary Thumbnail Generation System - Review Request Focus"""
    print("🖼️ Testing Boundary Thumbnail Generation System...")
    print("🎯 FOCUS: Generate fresh boundary thumbnails for specific properties")
    print("📋 REQUIREMENTS: POST /api/generate-boundary-thumbnail/{assessment_number}")
    
    # Test properties from review request
    test_assessments = ["00079006", "00125326", "00374059"]
    
    results = {}
    
    for assessment in test_assessments:
        print(f"\n🔧 Testing Assessment: {assessment}")
        
        try:
            # Generate boundary thumbnail
            generate_response = requests.post(
                f"{BACKEND_URL}/generate-boundary-thumbnail/{assessment}", 
                timeout=60
            )
            
            if generate_response.status_code == 200:
                result = generate_response.json()
                print(f"   ✅ Boundary thumbnail generation SUCCESS - HTTP 200")
                print(f"      Status: {result.get('status')}")
                print(f"      Assessment: {result.get('assessment_number')}")
                print(f"      Thumbnail filename: {result.get('thumbnail_filename')}")
                
                # Check for red boundary lines in static map URL
                static_map_url = result.get('static_map_url', '')
                if "color:0xff0000" in static_map_url or "color=0xff0000" in static_map_url:
                    print(f"   ✅ Red boundary lines detected in URL")
                else:
                    print(f"   ⚠️ Red boundary lines not clearly detected")
                
                # Test serving the generated image
                thumbnail_filename = result.get('thumbnail_filename')
                if thumbnail_filename:
                    image_response = requests.get(
                        f"{BACKEND_URL}/boundary-image/{thumbnail_filename}",
                        timeout=30
                    )
                    
                    if image_response.status_code == 200:
                        image_size = len(image_response.content)
                        print(f"   ✅ Image served successfully - Size: {image_size} bytes")
                        
                        # Check if image has substantial size (indicates boundaries)
                        if image_size > 50000:  # 50KB+
                            print(f"   ✅ Substantial image size - likely has boundary data")
                        else:
                            print(f"   ⚠️ Small image size - may be plain satellite image")
                    else:
                        print(f"   ❌ Failed to serve image: HTTP {image_response.status_code}")
                
                results[assessment] = {
                    "success": True,
                    "filename": thumbnail_filename,
                    "image_size": image_size if 'image_size' in locals() else 0,
                    "has_red_boundaries": "color:0xff0000" in static_map_url or "color=0xff0000" in static_map_url
                }
                
            elif generate_response.status_code == 404:
                print(f"   ❌ Assessment {assessment} not found")
                results[assessment] = {"success": False, "error": "Not found"}
                
            elif generate_response.status_code == 400:
                print(f"   ❌ Bad request - likely missing coordinates or boundary data")
                try:
                    error_detail = generate_response.json()
                    print(f"      Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"      Raw response: {generate_response.text}")
                results[assessment] = {"success": False, "error": "Bad request"}
                
            else:
                print(f"   ❌ Generation failed with status {generate_response.status_code}")
                try:
                    error_detail = generate_response.json()
                    print(f"      Error: {error_detail.get('detail', 'Unknown error')}")
                except:
                    print(f"      Raw response: {generate_response.text}")
                results[assessment] = {"success": False, "error": f"HTTP {generate_response.status_code}"}
                
        except Exception as e:
            print(f"   ❌ Exception during generation: {e}")
            results[assessment] = {"success": False, "error": str(e)}
    
    return results

def test_batch_generation():
    """Test batch boundary thumbnail generation"""
    print(f"\n🔧 Testing Batch Generation: POST /api/generate-all-boundary-thumbnails")
    
    try:
        batch_response = requests.post(
            f"{BACKEND_URL}/generate-all-boundary-thumbnails",
            timeout=300  # 5 minutes for batch operation
        )
        
        if batch_response.status_code == 200:
            result = batch_response.json()
            print(f"   ✅ Batch generation completed - HTTP 200")
            print(f"      Total processed: {result.get('total_processed', 0)}")
            print(f"      Successful: {result.get('successful', 0)}")
            print(f"      Failed: {result.get('failed', 0)}")
            
            return {
                "success": True,
                "total_processed": result.get('total_processed', 0),
                "successful": result.get('successful', 0),
                "failed": result.get('failed', 0)
            }
        else:
            print(f"   ❌ Batch generation failed with status {batch_response.status_code}")
            try:
                error_detail = batch_response.json()
                print(f"      Error: {error_detail.get('detail', 'Unknown error')}")
            except:
                print(f"      Raw response: {batch_response.text}")
            return {"success": False, "error": f"HTTP {batch_response.status_code}"}
            
    except Exception as e:
        print(f"   ❌ Exception during batch generation: {e}")
        return {"success": False, "error": str(e)}

def test_property_image_endpoint():
    """Test property image endpoint that serves boundary images"""
    print(f"\n🔧 Testing Property Image Endpoint: GET /api/property-image/{{assessment_number}}")
    
    test_assessments = ["00079006", "00125326", "00374059"]
    
    for assessment in test_assessments:
        print(f"\n   Testing Assessment: {assessment}")
        
        try:
            image_response = requests.get(
                f"{BACKEND_URL}/property-image/{assessment}",
                timeout=30
            )
            
            if image_response.status_code == 200:
                image_size = len(image_response.content)
                content_type = image_response.headers.get('content-type', '')
                
                print(f"   ✅ Property image served - Size: {image_size} bytes")
                print(f"      Content-Type: {content_type}")
                
                # Check if this is likely a boundary image vs satellite image
                if image_size > 50000:  # Larger images likely have boundary overlays
                    print(f"   ✅ Large image - likely boundary thumbnail")
                else:
                    print(f"   ⚠️ Small image - may be plain satellite image")
                    
            elif image_response.status_code == 404:
                print(f"   ❌ No image available for assessment {assessment}")
            else:
                print(f"   ❌ Failed to get image: HTTP {image_response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Exception getting property image: {e}")

def main():
    """Main test execution"""
    print("🚀 Starting Boundary Thumbnail Generation Testing")
    print("🎯 REVIEW REQUEST FOCUS: Fresh boundary thumbnail generation")
    print("=" * 80)
    
    # Test API connection first
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=30)
        if response.status_code == 200:
            print("✅ API connection successful")
        else:
            print(f"❌ API connection failed: {response.status_code}")
            return
    except Exception as e:
        print(f"❌ API connection error: {e}")
        return
    
    # Test individual boundary thumbnail generation
    print(f"\n1️⃣ INDIVIDUAL BOUNDARY THUMBNAIL GENERATION")
    individual_results = test_boundary_thumbnail_generation()
    
    # Test property image endpoint
    print(f"\n2️⃣ PROPERTY IMAGE ENDPOINT TESTING")
    test_property_image_endpoint()
    
    # Test batch generation
    print(f"\n3️⃣ BATCH BOUNDARY THUMBNAIL GENERATION")
    batch_results = test_batch_generation()
    
    # Summary
    print(f"\n" + "=" * 80)
    print("📋 BOUNDARY THUMBNAIL GENERATION TEST SUMMARY")
    print("=" * 80)
    
    print(f"\n🎯 INDIVIDUAL GENERATION RESULTS:")
    successful_individual = 0
    for assessment, result in individual_results.items():
        if result.get('success'):
            successful_individual += 1
            has_boundaries = "✅" if result.get('has_red_boundaries') else "⚠️"
            print(f"   {assessment}: ✅ Success - {result.get('image_size', 0)} bytes {has_boundaries}")
        else:
            print(f"   {assessment}: ❌ Failed - {result.get('error', 'Unknown error')}")
    
    print(f"\n📊 BATCH GENERATION RESULTS:")
    if batch_results.get('success'):
        print(f"   ✅ Batch generation successful")
        print(f"   📊 Total processed: {batch_results.get('total_processed', 0)}")
        print(f"   ✅ Successful: {batch_results.get('successful', 0)}")
        print(f"   ❌ Failed: {batch_results.get('failed', 0)}")
    else:
        print(f"   ❌ Batch generation failed: {batch_results.get('error', 'Unknown error')}")
    
    print(f"\n🎯 KEY FINDINGS:")
    print(f"   Individual generations successful: {successful_individual}/3")
    print(f"   Batch generation: {'✅ Working' if batch_results.get('success') else '❌ Failed'}")
    
    # Check for the specific issue mentioned in review request
    boundary_issue_detected = False
    for assessment, result in individual_results.items():
        if result.get('success') and not result.get('has_red_boundaries'):
            boundary_issue_detected = True
            break
    
    if boundary_issue_detected:
        print(f"\n⚠️ ISSUE DETECTED: Some thumbnails generated without red boundary lines")
        print(f"   This matches the reported issue: 'boundary thumbnails showing without red boundary lines'")
    else:
        print(f"\n✅ NO BOUNDARY LINE ISSUES: All successful generations include red boundary lines")
    
    print(f"\n🎉 Boundary thumbnail generation testing completed!")

if __name__ == "__main__":
    main()