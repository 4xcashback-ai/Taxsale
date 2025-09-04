#!/usr/bin/env python3
"""
Comprehensive Database Structure Analysis for Tax Sale Compass
Analyzes current database structure and identifies potential production issues
"""

import pymongo
import json
import sys
import os
from datetime import datetime
from collections import defaultdict
import pprint

# Database connection details
MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DB_NAME = os.environ.get('DB_NAME', 'test_database')

def connect_to_database():
    """Connect to MongoDB database"""
    try:
        print(f"🔗 Connecting to database...")
        print(f"   URL: {MONGO_URL}")
        print(f"   Database: {DB_NAME}")
        
        client = pymongo.MongoClient(MONGO_URL, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.server_info()
        
        db = client[DB_NAME]
        print(f"   ✅ Connected successfully")
        
        return client, db
    except Exception as e:
        print(f"   ❌ Failed to connect: {e}")
        return None, None

def analyze_collection_structure(db, collection_name):
    """Analyze detailed structure of a collection"""
    print(f"\n🔍 DETAILED ANALYSIS: {collection_name}")
    print("-" * 60)
    
    try:
        collection = db[collection_name]
        
        # Get collection stats
        try:
            stats = db.command("collStats", collection_name)
            doc_count = stats.get('count', 0)
            size = stats.get('size', 0)
            avg_obj_size = stats.get('avgObjSize', 0)
            storage_size = stats.get('storageSize', 0)
        except:
            doc_count = collection.count_documents({})
            size = 0
            avg_obj_size = 0
            storage_size = 0
        
        print(f"📊 Collection Statistics:")
        print(f"   Documents: {doc_count}")
        print(f"   Size: {size} bytes ({size/1024:.1f} KB)")
        print(f"   Storage Size: {storage_size} bytes ({storage_size/1024:.1f} KB)")
        print(f"   Average Object Size: {avg_obj_size} bytes")
        
        # Get indexes
        indexes = list(collection.list_indexes())
        print(f"\n📋 Indexes ({len(indexes)}):")
        for idx in indexes:
            name = idx.get('name', 'unnamed')
            key = dict(idx.get('key', {}))
            unique = idx.get('unique', False)
            sparse = idx.get('sparse', False)
            print(f"   - {name}: {key} (unique={unique}, sparse={sparse})")
        
        # Analyze sample documents
        samples = list(collection.find().limit(10))
        if samples:
            print(f"\n📋 Sample Document Analysis:")
            
            # Get all unique fields across samples
            all_fields = set()
            field_types = defaultdict(set)
            field_presence = defaultdict(int)
            
            for doc in samples:
                for key, value in doc.items():
                    all_fields.add(key)
                    field_presence[key] += 1
                    
                    if value is None:
                        field_types[key].add("null")
                    elif isinstance(value, bool):
                        field_types[key].add("boolean")
                    elif isinstance(value, int):
                        field_types[key].add("integer")
                    elif isinstance(value, float):
                        field_types[key].add("float")
                    elif isinstance(value, str):
                        field_types[key].add("string")
                    elif isinstance(value, datetime):
                        field_types[key].add("datetime")
                    elif isinstance(value, list):
                        field_types[key].add("array")
                    elif isinstance(value, dict):
                        field_types[key].add("object")
                    else:
                        field_types[key].add(str(type(value).__name__))
            
            print(f"   Total unique fields: {len(all_fields)}")
            print(f"   Field analysis (presence/types):")
            
            for field in sorted(all_fields):
                presence = field_presence[field]
                types = list(field_types[field])
                presence_pct = (presence / len(samples)) * 100
                print(f"     {field}: {presence}/{len(samples)} ({presence_pct:.0f}%) - {', '.join(types)}")
        
        # Check for potential issues
        issues = []
        
        # Check for missing indexes on important fields
        if collection_name == 'tax_sales':
            important_fields = ['assessment_number', 'municipality_name', 'status', 'sale_date']
            indexed_fields = set()
            for idx in indexes:
                for field in idx.get('key', {}):
                    indexed_fields.add(field)
            
            missing_indexes = set(important_fields) - indexed_fields
            if missing_indexes:
                issues.append(f"Missing indexes on important fields: {missing_indexes}")
        
        elif collection_name == 'users':
            important_fields = ['email', 'id']
            indexed_fields = set()
            for idx in indexes:
                for field in idx.get('key', {}):
                    indexed_fields.add(field)
            
            missing_indexes = set(important_fields) - indexed_fields
            if missing_indexes:
                issues.append(f"Missing indexes on important fields: {missing_indexes}")
        
        elif collection_name == 'municipalities':
            important_fields = ['id', 'name']
            indexed_fields = set()
            for idx in indexes:
                for field in idx.get('key', {}):
                    indexed_fields.add(field)
            
            missing_indexes = set(important_fields) - indexed_fields
            if missing_indexes:
                issues.append(f"Missing indexes on important fields: {missing_indexes}")
        
        # Check for data quality issues
        if samples:
            # Check for required fields
            if collection_name == 'tax_sales':
                required_fields = ['id', 'municipality_name', 'property_address']
                for field in required_fields:
                    missing_count = sum(1 for doc in samples if field not in doc or not doc[field])
                    if missing_count > 0:
                        issues.append(f"Required field '{field}' missing in {missing_count}/{len(samples)} samples")
            
            elif collection_name == 'municipalities':
                required_fields = ['id', 'name', 'website_url', 'scraper_type']
                for field in required_fields:
                    missing_count = sum(1 for doc in samples if field not in doc or not doc[field])
                    if missing_count > 0:
                        issues.append(f"Required field '{field}' missing in {missing_count}/{len(samples)} samples")
            
            elif collection_name == 'users':
                required_fields = ['id', 'email', 'subscription_tier']
                for field in required_fields:
                    missing_count = sum(1 for doc in samples if field not in doc or not doc[field])
                    if missing_count > 0:
                        issues.append(f"Required field '{field}' missing in {missing_count}/{len(samples)} samples")
        
        if issues:
            print(f"\n⚠️ Potential Issues:")
            for issue in issues:
                print(f"   - {issue}")
        else:
            print(f"\n✅ No obvious issues detected")
        
        return {
            'document_count': doc_count,
            'size_bytes': size,
            'storage_size_bytes': storage_size,
            'avg_object_size': avg_obj_size,
            'indexes': indexes,
            'field_count': len(all_fields) if samples else 0,
            'issues': issues,
            'samples': samples[:3]  # Keep first 3 samples for reference
        }
        
    except Exception as e:
        print(f"   ❌ Error analyzing {collection_name}: {e}")
        return {'error': str(e)}

def check_production_readiness(db):
    """Check if database is ready for production deployment"""
    print(f"\n🔍 PRODUCTION READINESS ASSESSMENT")
    print("=" * 60)
    
    issues = []
    warnings = []
    
    # Check collections exist
    collections = db.list_collection_names()
    required_collections = ['tax_sales', 'municipalities', 'users']
    
    for collection in required_collections:
        if collection not in collections:
            issues.append(f"Required collection '{collection}' missing")
        else:
            print(f"✅ Required collection '{collection}' exists")
    
    # Check for admin user
    try:
        admin_user = db.users.find_one({"email": "admin@taxsalecompass.ca"})
        if admin_user:
            print(f"✅ Admin user exists")
            if admin_user.get('subscription_tier') != 'paid':
                warnings.append("Admin user should have 'paid' subscription tier")
        else:
            issues.append("Admin user not found in database")
    except Exception as e:
        warnings.append(f"Could not check admin user: {e}")
    
    # Check municipalities data
    try:
        municipalities = list(db.municipalities.find())
        if len(municipalities) < 3:
            warnings.append(f"Only {len(municipalities)} municipalities found, expected at least 3")
        else:
            print(f"✅ {len(municipalities)} municipalities configured")
        
        # Check municipality configuration
        for muni in municipalities:
            if not muni.get('scraper_type'):
                warnings.append(f"Municipality '{muni.get('name')}' missing scraper_type")
            if not muni.get('website_url'):
                warnings.append(f"Municipality '{muni.get('name')}' missing website_url")
    except Exception as e:
        issues.append(f"Could not check municipalities: {e}")
    
    # Check tax sales data
    try:
        total_properties = db.tax_sales.count_documents({})
        active_properties = db.tax_sales.count_documents({"status": "active"})
        inactive_properties = db.tax_sales.count_documents({"status": "inactive"})
        
        print(f"✅ Tax sales data: {total_properties} total ({active_properties} active, {inactive_properties} inactive)")
        
        if total_properties == 0:
            warnings.append("No tax sale properties in database")
        
        # Check for properties with coordinates
        properties_with_coords = db.tax_sales.count_documents({
            "latitude": {"$exists": True, "$ne": None},
            "longitude": {"$exists": True, "$ne": None}
        })
        coord_percentage = (properties_with_coords / total_properties * 100) if total_properties > 0 else 0
        
        if coord_percentage < 50:
            warnings.append(f"Only {coord_percentage:.1f}% of properties have coordinates")
        else:
            print(f"✅ {coord_percentage:.1f}% of properties have coordinates")
        
        # Check for boundary data
        properties_with_boundary = db.tax_sales.count_documents({
            "boundary_screenshot": {"$exists": True, "$ne": None}
        })
        boundary_percentage = (properties_with_boundary / total_properties * 100) if total_properties > 0 else 0
        
        if boundary_percentage < 30:
            warnings.append(f"Only {boundary_percentage:.1f}% of properties have boundary screenshots")
        else:
            print(f"✅ {boundary_percentage:.1f}% of properties have boundary screenshots")
        
    except Exception as e:
        issues.append(f"Could not check tax sales data: {e}")
    
    # Check indexes
    try:
        for collection_name in required_collections:
            collection = db[collection_name]
            indexes = list(collection.list_indexes())
            
            if len(indexes) <= 1:  # Only default _id index
                warnings.append(f"Collection '{collection_name}' has no custom indexes")
    except Exception as e:
        warnings.append(f"Could not check indexes: {e}")
    
    return issues, warnings

def comprehensive_database_analysis():
    """Perform comprehensive database analysis"""
    print("🎯 COMPREHENSIVE DATABASE STRUCTURE ANALYSIS")
    print("=" * 80)
    print("🎯 ANALYSIS FOCUS:")
    print("   1. Collection Structure and Statistics")
    print("   2. Schema Analysis and Field Types")
    print("   3. Index Configuration")
    print("   4. Data Quality Assessment")
    print("   5. Production Readiness Check")
    print("=" * 80)
    
    # Connect to database
    client, db = connect_to_database()
    
    if db is None:
        print("❌ Cannot proceed without database connection")
        return False
    
    # Get all collections
    collections = db.list_collection_names()
    print(f"\n📋 Found {len(collections)} collections: {', '.join(collections)}")
    
    # Analyze each collection
    collection_analyses = {}
    
    for collection_name in collections:
        collection_analyses[collection_name] = analyze_collection_structure(db, collection_name)
    
    # Production readiness check
    issues, warnings = check_production_readiness(db)
    
    # Final Assessment
    print(f"\n" + "=" * 80)
    print("📊 DATABASE ANALYSIS - FINAL ASSESSMENT")
    print("=" * 80)
    
    print(f"📋 SUMMARY:")
    print(f"   Total collections: {len(collections)}")
    print(f"   Critical issues: {len(issues)}")
    print(f"   Warnings: {len(warnings)}")
    
    # Show issues and warnings
    if issues:
        print(f"\n❌ CRITICAL ISSUES:")
        for i, issue in enumerate(issues, 1):
            print(f"   {i}. {issue}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS:")
        for i, warning in enumerate(warnings, 1):
            print(f"   {i}. {warning}")
    
    # Collection-specific issues
    collection_issues = []
    for collection_name, analysis in collection_analyses.items():
        if 'issues' in analysis and analysis['issues']:
            collection_issues.extend([f"{collection_name}: {issue}" for issue in analysis['issues']])
    
    if collection_issues:
        print(f"\n⚠️ COLLECTION-SPECIFIC ISSUES:")
        for i, issue in enumerate(collection_issues, 1):
            print(f"   {i}. {issue}")
    
    # Key findings for production deployment
    print(f"\n🔍 KEY FINDINGS FOR PRODUCTION DEPLOYMENT:")
    
    # Database structure
    key_collections = ['tax_sales', 'municipalities', 'users', 'favorites']
    missing_key_collections = [col for col in key_collections if col not in collections]
    
    if missing_key_collections:
        print(f"   ❌ Missing key collections: {', '.join(missing_key_collections)}")
    else:
        print(f"   ✅ All key collections present")
    
    # Data volume
    total_docs = sum(analysis.get('document_count', 0) for analysis in collection_analyses.values())
    print(f"   📊 Total documents across all collections: {total_docs}")
    
    # Index status
    total_indexes = sum(len(analysis.get('indexes', [])) for analysis in collection_analyses.values())
    print(f"   📊 Total indexes across all collections: {total_indexes}")
    
    # Overall assessment
    critical_issue_count = len(issues) + len([issue for issue in collection_issues if 'missing' in issue.lower()])
    
    if critical_issue_count == 0:
        print(f"\n🎉 DATABASE ANALYSIS: EXCELLENT!")
        print(f"   ✅ Database structure is well-configured")
        print(f"   ✅ All required collections and data present")
        print(f"   ✅ Ready for production deployment")
        success = True
    elif critical_issue_count <= 2:
        print(f"\n⚠️ DATABASE ANALYSIS: GOOD WITH MINOR ISSUES")
        print(f"   ⚠️ Few issues found, but overall structure is solid")
        print(f"   🔧 Address minor issues before production deployment")
        success = True
    else:
        print(f"\n❌ DATABASE ANALYSIS: NEEDS ATTENTION")
        print(f"   ❌ Multiple issues found")
        print(f"   🔧 Database needs optimization before production")
        success = False
    
    # Recommendations
    print(f"\n💡 RECOMMENDATIONS FOR VPS DEPLOYMENT:")
    print(f"   1. Ensure MongoDB connection string is updated for VPS environment")
    print(f"   2. Create database backups before deployment")
    print(f"   3. Verify all environment variables are properly configured")
    print(f"   4. Test admin authentication with production credentials")
    print(f"   5. Validate all municipality scrapers work in production")
    
    if warnings:
        print(f"   6. Address warnings to improve data quality")
    
    if collection_issues:
        print(f"   7. Optimize indexes for better performance")
    
    # Close connection
    if client:
        client.close()
    
    return success

if __name__ == "__main__":
    try:
        success = comprehensive_database_analysis()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Database analysis interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Database analysis failed with error: {e}")
        sys.exit(1)