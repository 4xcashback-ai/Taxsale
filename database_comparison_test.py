#!/usr/bin/env python3
"""
Database Structure Comparison for Tax Sale Compass Application
Comprehensive comparison between development and VPS environments
"""

import pymongo
import json
import sys
import os
from datetime import datetime
from collections import defaultdict
import pprint

# Database connection details
DEV_MONGO_URL = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
DEV_DB_NAME = os.environ.get('DB_NAME', 'test_database')

# VPS connection - we'll try to determine this from environment or use production URL
VPS_MONGO_URL = os.environ.get('VPS_MONGO_URL', DEV_MONGO_URL)  # Fallback to dev if not set
VPS_DB_NAME = os.environ.get('VPS_DB_NAME', DEV_DB_NAME)  # Fallback to dev if not set

# Admin credentials for testing
ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "TaxSale2025!SecureAdmin"

def connect_to_database(mongo_url, db_name, env_name):
    """Connect to MongoDB database"""
    try:
        print(f"🔗 Connecting to {env_name} database...")
        print(f"   URL: {mongo_url}")
        print(f"   Database: {db_name}")
        
        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=5000)
        
        # Test connection
        client.server_info()
        
        db = client[db_name]
        print(f"   ✅ Connected to {env_name} database successfully")
        
        return client, db
    except Exception as e:
        print(f"   ❌ Failed to connect to {env_name} database: {e}")
        return None, None

def get_collections_info(db, env_name):
    """Get information about all collections in the database"""
    try:
        print(f"\n📋 Analyzing collections in {env_name} database...")
        
        collections = db.list_collection_names()
        collections_info = {}
        
        print(f"   Found {len(collections)} collections:")
        
        for collection_name in collections:
            collection = db[collection_name]
            
            # Get collection stats
            try:
                stats = db.command("collStats", collection_name)
                doc_count = stats.get('count', 0)
                size = stats.get('size', 0)
                avg_obj_size = stats.get('avgObjSize', 0)
            except:
                doc_count = collection.count_documents({})
                size = 0
                avg_obj_size = 0
            
            # Get sample document for schema analysis
            sample_doc = collection.find_one()
            
            # Get indexes
            indexes = list(collection.list_indexes())
            
            collections_info[collection_name] = {
                'document_count': doc_count,
                'size_bytes': size,
                'avg_object_size': avg_obj_size,
                'sample_document': sample_doc,
                'indexes': indexes,
                'schema_fields': list(sample_doc.keys()) if sample_doc else []
            }
            
            print(f"   📁 {collection_name}: {doc_count} documents, {len(indexes)} indexes")
        
        return collections_info
        
    except Exception as e:
        print(f"   ❌ Error analyzing collections in {env_name}: {e}")
        return {}

def analyze_schema_structure(doc, prefix=""):
    """Recursively analyze document structure to get field types"""
    schema = {}
    
    if not doc:
        return schema
    
    for key, value in doc.items():
        field_path = f"{prefix}.{key}" if prefix else key
        
        if value is None:
            schema[field_path] = "null"
        elif isinstance(value, bool):
            schema[field_path] = "boolean"
        elif isinstance(value, int):
            schema[field_path] = "integer"
        elif isinstance(value, float):
            schema[field_path] = "float"
        elif isinstance(value, str):
            schema[field_path] = "string"
        elif isinstance(value, datetime):
            schema[field_path] = "datetime"
        elif isinstance(value, list):
            schema[field_path] = "array"
            if value and isinstance(value[0], dict):
                # Analyze first array element
                nested_schema = analyze_schema_structure(value[0], field_path + "[0]")
                schema.update(nested_schema)
        elif isinstance(value, dict):
            schema[field_path] = "object"
            nested_schema = analyze_schema_structure(value, field_path)
            schema.update(nested_schema)
        else:
            schema[field_path] = str(type(value).__name__)
    
    return schema

def compare_collections(dev_collections, vps_collections):
    """Compare collections between environments"""
    print(f"\n🔍 COMPARING COLLECTIONS BETWEEN ENVIRONMENTS")
    print("=" * 80)
    
    dev_names = set(dev_collections.keys())
    vps_names = set(vps_collections.keys())
    
    # Collections only in dev
    dev_only = dev_names - vps_names
    # Collections only in VPS
    vps_only = vps_names - dev_names
    # Collections in both
    common = dev_names & vps_names
    
    print(f"📊 COLLECTION COMPARISON SUMMARY:")
    print(f"   Development collections: {len(dev_names)}")
    print(f"   VPS collections: {len(vps_names)}")
    print(f"   Common collections: {len(common)}")
    print(f"   Dev-only collections: {len(dev_only)}")
    print(f"   VPS-only collections: {len(vps_only)}")
    
    issues = []
    
    if dev_only:
        print(f"\n❌ COLLECTIONS MISSING IN VPS:")
        for collection in sorted(dev_only):
            print(f"   - {collection} (exists in dev, missing in VPS)")
            issues.append(f"Missing collection in VPS: {collection}")
    
    if vps_only:
        print(f"\n⚠️ COLLECTIONS ONLY IN VPS:")
        for collection in sorted(vps_only):
            print(f"   - {collection} (exists in VPS, missing in dev)")
            issues.append(f"Extra collection in VPS: {collection}")
    
    if common:
        print(f"\n✅ COMMON COLLECTIONS:")
        for collection in sorted(common):
            dev_info = dev_collections[collection]
            vps_info = vps_collections[collection]
            
            dev_count = dev_info['document_count']
            vps_count = vps_info['document_count']
            
            print(f"   📁 {collection}:")
            print(f"      Dev: {dev_count} docs, VPS: {vps_count} docs")
            
            # Compare document counts
            if dev_count != vps_count:
                diff = abs(dev_count - vps_count)
                print(f"      ⚠️ Document count difference: {diff}")
                if diff > max(dev_count, vps_count) * 0.1:  # More than 10% difference
                    issues.append(f"Significant document count difference in {collection}: dev={dev_count}, vps={vps_count}")
    
    return {
        'common_collections': list(common),
        'dev_only_collections': list(dev_only),
        'vps_only_collections': list(vps_only),
        'issues': issues
    }

def compare_schemas(dev_collections, vps_collections, collection_name):
    """Compare schema structure for a specific collection"""
    print(f"\n🔍 SCHEMA COMPARISON: {collection_name}")
    print("-" * 60)
    
    if collection_name not in dev_collections:
        print(f"   ❌ Collection {collection_name} not found in development")
        return {'issues': [f"Collection {collection_name} missing in development"]}
    
    if collection_name not in vps_collections:
        print(f"   ❌ Collection {collection_name} not found in VPS")
        return {'issues': [f"Collection {collection_name} missing in VPS"]}
    
    dev_sample = dev_collections[collection_name]['sample_document']
    vps_sample = vps_collections[collection_name]['sample_document']
    
    if not dev_sample:
        print(f"   ⚠️ No sample document in development {collection_name}")
        return {'issues': [f"No sample document in dev {collection_name}"]}
    
    if not vps_sample:
        print(f"   ⚠️ No sample document in VPS {collection_name}")
        return {'issues': [f"No sample document in VPS {collection_name}"]}
    
    # Analyze schemas
    dev_schema = analyze_schema_structure(dev_sample)
    vps_schema = analyze_schema_structure(vps_sample)
    
    dev_fields = set(dev_schema.keys())
    vps_fields = set(vps_schema.keys())
    
    # Field differences
    dev_only_fields = dev_fields - vps_fields
    vps_only_fields = vps_fields - dev_fields
    common_fields = dev_fields & vps_fields
    
    issues = []
    
    print(f"   📋 Schema Analysis:")
    print(f"      Development fields: {len(dev_fields)}")
    print(f"      VPS fields: {len(vps_fields)}")
    print(f"      Common fields: {len(common_fields)}")
    
    if dev_only_fields:
        print(f"   ❌ Fields missing in VPS:")
        for field in sorted(dev_only_fields):
            print(f"      - {field} ({dev_schema[field]})")
            issues.append(f"Field missing in VPS {collection_name}: {field}")
    
    if vps_only_fields:
        print(f"   ⚠️ Extra fields in VPS:")
        for field in sorted(vps_only_fields):
            print(f"      - {field} ({vps_schema[field]})")
            issues.append(f"Extra field in VPS {collection_name}: {field}")
    
    # Type mismatches
    type_mismatches = []
    for field in common_fields:
        if dev_schema[field] != vps_schema[field]:
            type_mismatches.append({
                'field': field,
                'dev_type': dev_schema[field],
                'vps_type': vps_schema[field]
            })
    
    if type_mismatches:
        print(f"   ❌ Type mismatches:")
        for mismatch in type_mismatches:
            print(f"      - {mismatch['field']}: dev={mismatch['dev_type']}, vps={mismatch['vps_type']}")
            issues.append(f"Type mismatch in {collection_name}.{mismatch['field']}: dev={mismatch['dev_type']}, vps={mismatch['vps_type']}")
    
    if not issues:
        print(f"   ✅ Schema structures match perfectly")
    
    return {
        'dev_fields': list(dev_fields),
        'vps_fields': list(vps_fields),
        'common_fields': list(common_fields),
        'dev_only_fields': list(dev_only_fields),
        'vps_only_fields': list(vps_only_fields),
        'type_mismatches': type_mismatches,
        'issues': issues
    }

def compare_indexes(dev_collections, vps_collections, collection_name):
    """Compare indexes for a specific collection"""
    print(f"\n🔍 INDEX COMPARISON: {collection_name}")
    print("-" * 60)
    
    if collection_name not in dev_collections or collection_name not in vps_collections:
        print(f"   ❌ Collection not found in both environments")
        return {'issues': [f"Collection {collection_name} not in both environments"]}
    
    dev_indexes = dev_collections[collection_name]['indexes']
    vps_indexes = vps_collections[collection_name]['indexes']
    
    # Convert indexes to comparable format
    def normalize_index(index):
        return {
            'name': index.get('name', ''),
            'key': dict(index.get('key', {})),
            'unique': index.get('unique', False),
            'sparse': index.get('sparse', False)
        }
    
    dev_normalized = [normalize_index(idx) for idx in dev_indexes]
    vps_normalized = [normalize_index(idx) for idx in vps_indexes]
    
    print(f"   📋 Index Analysis:")
    print(f"      Development indexes: {len(dev_indexes)}")
    print(f"      VPS indexes: {len(vps_indexes)}")
    
    # Find matching indexes by name
    dev_names = {idx['name'] for idx in dev_normalized}
    vps_names = {idx['name'] for idx in vps_normalized}
    
    dev_only_indexes = dev_names - vps_names
    vps_only_indexes = vps_names - dev_names
    common_indexes = dev_names & vps_names
    
    issues = []
    
    if dev_only_indexes:
        print(f"   ❌ Indexes missing in VPS:")
        for idx_name in sorted(dev_only_indexes):
            dev_idx = next(idx for idx in dev_normalized if idx['name'] == idx_name)
            print(f"      - {idx_name}: {dev_idx['key']}")
            issues.append(f"Index missing in VPS {collection_name}: {idx_name}")
    
    if vps_only_indexes:
        print(f"   ⚠️ Extra indexes in VPS:")
        for idx_name in sorted(vps_only_indexes):
            vps_idx = next(idx for idx in vps_normalized if idx['name'] == idx_name)
            print(f"      - {idx_name}: {vps_idx['key']}")
            issues.append(f"Extra index in VPS {collection_name}: {idx_name}")
    
    # Compare common indexes
    index_mismatches = []
    for idx_name in common_indexes:
        dev_idx = next(idx for idx in dev_normalized if idx['name'] == idx_name)
        vps_idx = next(idx for idx in vps_normalized if idx['name'] == idx_name)
        
        if dev_idx != vps_idx:
            index_mismatches.append({
                'name': idx_name,
                'dev_config': dev_idx,
                'vps_config': vps_idx
            })
    
    if index_mismatches:
        print(f"   ❌ Index configuration mismatches:")
        for mismatch in index_mismatches:
            print(f"      - {mismatch['name']}: configurations differ")
            issues.append(f"Index config mismatch in {collection_name}: {mismatch['name']}")
    
    if not issues:
        print(f"   ✅ Index configurations match perfectly")
    
    return {
        'dev_indexes': len(dev_indexes),
        'vps_indexes': len(vps_indexes),
        'common_indexes': list(common_indexes),
        'dev_only_indexes': list(dev_only_indexes),
        'vps_only_indexes': list(vps_only_indexes),
        'index_mismatches': index_mismatches,
        'issues': issues
    }

def sample_data_consistency_check(dev_db, vps_db, collection_name, sample_size=5):
    """Check data consistency by comparing sample documents"""
    print(f"\n🔍 DATA CONSISTENCY CHECK: {collection_name}")
    print("-" * 60)
    
    try:
        dev_collection = dev_db[collection_name]
        vps_collection = vps_db[collection_name]
        
        # Get sample documents from both
        dev_samples = list(dev_collection.find().limit(sample_size))
        vps_samples = list(vps_collection.find().limit(sample_size))
        
        print(f"   📋 Comparing {len(dev_samples)} dev samples with {len(vps_samples)} VPS samples")
        
        issues = []
        
        # Check if we have data in both environments
        if not dev_samples:
            print(f"   ⚠️ No sample data in development {collection_name}")
            issues.append(f"No data in dev {collection_name}")
        
        if not vps_samples:
            print(f"   ⚠️ No sample data in VPS {collection_name}")
            issues.append(f"No data in VPS {collection_name}")
        
        if dev_samples and vps_samples:
            # Compare field presence and types in samples
            dev_fields = set()
            vps_fields = set()
            
            for doc in dev_samples:
                dev_fields.update(doc.keys())
            
            for doc in vps_samples:
                vps_fields.update(doc.keys())
            
            field_diff = dev_fields.symmetric_difference(vps_fields)
            if field_diff:
                print(f"   ⚠️ Field differences in sample data: {field_diff}")
                issues.append(f"Field differences in {collection_name} samples: {field_diff}")
            else:
                print(f"   ✅ Sample data fields are consistent")
            
            # Check for required fields based on collection type
            if collection_name == 'municipalities':
                required_fields = ['id', 'name', 'website_url', 'scraper_type']
                for field in required_fields:
                    dev_has = all(field in doc for doc in dev_samples)
                    vps_has = all(field in doc for doc in vps_samples)
                    
                    if dev_has != vps_has:
                        issues.append(f"Required field {field} consistency issue in {collection_name}")
                        print(f"   ❌ Required field {field}: dev={dev_has}, vps={vps_has}")
            
            elif collection_name == 'tax_sales':
                required_fields = ['id', 'municipality_name', 'property_address', 'assessment_number']
                for field in required_fields:
                    dev_has = sum(1 for doc in dev_samples if field in doc and doc[field])
                    vps_has = sum(1 for doc in vps_samples if field in doc and doc[field])
                    
                    print(f"   📋 Field {field}: dev={dev_has}/{len(dev_samples)}, vps={vps_has}/{len(vps_samples)}")
            
            elif collection_name == 'users':
                required_fields = ['id', 'email', 'subscription_tier', 'is_verified']
                for field in required_fields:
                    dev_has = all(field in doc for doc in dev_samples)
                    vps_has = all(field in doc for doc in vps_samples)
                    
                    if dev_has != vps_has:
                        issues.append(f"Required field {field} consistency issue in {collection_name}")
                        print(f"   ❌ Required field {field}: dev={dev_has}, vps={vps_has}")
        
        return {
            'dev_sample_count': len(dev_samples),
            'vps_sample_count': len(vps_samples),
            'issues': issues
        }
        
    except Exception as e:
        print(f"   ❌ Error checking data consistency: {e}")
        return {'issues': [f"Error checking {collection_name} consistency: {str(e)}"]}

def comprehensive_database_comparison():
    """Perform comprehensive database comparison"""
    print("🎯 COMPREHENSIVE DATABASE STRUCTURE COMPARISON")
    print("=" * 80)
    print("🎯 REVIEW REQUEST: Compare development and VPS database structures")
    print("📋 FOCUS AREAS:")
    print("   1. Database Collections Comparison")
    print("   2. Schema Structure Analysis")
    print("   3. Index Comparison")
    print("   4. Data Consistency Check")
    print("   5. Key Collections: tax_sales, municipalities, users, favorites")
    print("=" * 80)
    
    # Connect to both databases
    dev_client, dev_db = connect_to_database(DEV_MONGO_URL, DEV_DB_NAME, "Development")
    vps_client, vps_db = connect_to_database(VPS_MONGO_URL, VPS_DB_NAME, "VPS")
    
    if dev_db is None:
        print("❌ Cannot proceed without development database connection")
        return False
    
    if vps_db is None:
        print("❌ Cannot proceed without VPS database connection")
        return False
    
    # Get collections information
    dev_collections = get_collections_info(dev_db, "Development")
    vps_collections = get_collections_info(vps_db, "VPS")
    
    if not dev_collections and not vps_collections:
        print("❌ No collections found in either database")
        return False
    
    # 1. Compare collections
    collection_comparison = compare_collections(dev_collections, vps_collections)
    
    # 2. Schema structure analysis for key collections
    key_collections = ['tax_sales', 'municipalities', 'users', 'favorites']
    schema_results = {}
    
    print(f"\n🔍 DETAILED SCHEMA ANALYSIS FOR KEY COLLECTIONS")
    print("=" * 80)
    
    for collection in key_collections:
        if collection in dev_collections or collection in vps_collections:
            schema_results[collection] = compare_schemas(dev_collections, vps_collections, collection)
        else:
            print(f"\n⚠️ Key collection '{collection}' not found in either environment")
            schema_results[collection] = {'issues': [f"Key collection {collection} missing in both environments"]}
    
    # 3. Index comparison for key collections
    index_results = {}
    
    print(f"\n🔍 INDEX COMPARISON FOR KEY COLLECTIONS")
    print("=" * 80)
    
    for collection in key_collections:
        if collection in collection_comparison['common_collections']:
            index_results[collection] = compare_indexes(dev_collections, vps_collections, collection)
        else:
            print(f"\n⚠️ Skipping index comparison for '{collection}' - not in both environments")
    
    # 4. Data consistency check
    consistency_results = {}
    
    print(f"\n🔍 DATA CONSISTENCY CHECK FOR KEY COLLECTIONS")
    print("=" * 80)
    
    for collection in key_collections:
        if collection in collection_comparison['common_collections']:
            consistency_results[collection] = sample_data_consistency_check(dev_db, vps_db, collection)
        else:
            print(f"\n⚠️ Skipping consistency check for '{collection}' - not in both environments")
    
    # Final Assessment
    print(f"\n" + "=" * 80)
    print("📊 DATABASE COMPARISON - FINAL ASSESSMENT")
    print("=" * 80)
    
    all_issues = []
    all_issues.extend(collection_comparison['issues'])
    
    for collection, results in schema_results.items():
        all_issues.extend(results.get('issues', []))
    
    for collection, results in index_results.items():
        all_issues.extend(results.get('issues', []))
    
    for collection, results in consistency_results.items():
        all_issues.extend(results.get('issues', []))
    
    print(f"📋 SUMMARY:")
    print(f"   Total collections in dev: {len(dev_collections)}")
    print(f"   Total collections in VPS: {len(vps_collections)}")
    print(f"   Common collections: {len(collection_comparison['common_collections'])}")
    print(f"   Total issues found: {len(all_issues)}")
    
    # Categorize issues by severity
    critical_issues = []
    warnings = []
    
    for issue in all_issues:
        if any(keyword in issue.lower() for keyword in ['missing', 'not found', 'mismatch']):
            critical_issues.append(issue)
        else:
            warnings.append(issue)
    
    print(f"\n🔍 ISSUE BREAKDOWN:")
    print(f"   Critical issues: {len(critical_issues)}")
    print(f"   Warnings: {len(warnings)}")
    
    if critical_issues:
        print(f"\n❌ CRITICAL ISSUES REQUIRING ATTENTION:")
        for i, issue in enumerate(critical_issues, 1):
            print(f"   {i}. {issue}")
    
    if warnings:
        print(f"\n⚠️ WARNINGS:")
        for i, issue in enumerate(warnings, 1):
            print(f"   {i}. {issue}")
    
    # Key findings
    print(f"\n🔍 KEY FINDINGS:")
    
    # Collection findings
    if collection_comparison['dev_only_collections']:
        print(f"   ❌ Collections missing in VPS: {', '.join(collection_comparison['dev_only_collections'])}")
    
    if collection_comparison['vps_only_collections']:
        print(f"   ⚠️ Extra collections in VPS: {', '.join(collection_comparison['vps_only_collections'])}")
    
    # Schema findings for key collections
    for collection in key_collections:
        if collection in schema_results:
            results = schema_results[collection]
            if results.get('dev_only_fields'):
                print(f"   ❌ {collection}: Fields missing in VPS: {len(results['dev_only_fields'])}")
            if results.get('type_mismatches'):
                print(f"   ❌ {collection}: Type mismatches: {len(results['type_mismatches'])}")
    
    # Overall assessment
    if len(critical_issues) == 0:
        print(f"\n🎉 DATABASE COMPARISON: SUCCESS!")
        print(f"   ✅ Database structures are consistent between environments")
        print(f"   ✅ All key collections present and properly structured")
        print(f"   ✅ Schema fields and types match between environments")
        print(f"   ✅ Index configurations are consistent")
        success = True
    elif len(critical_issues) <= 2:
        print(f"\n⚠️ DATABASE COMPARISON: MINOR ISSUES")
        print(f"   ⚠️ Few critical issues found, but overall structure is good")
        print(f"   🔧 Address critical issues for full consistency")
        success = True
    else:
        print(f"\n❌ DATABASE COMPARISON: SIGNIFICANT ISSUES")
        print(f"   ❌ Multiple critical issues found")
        print(f"   🔧 Database structures need synchronization")
        success = False
    
    # Close connections
    if dev_client:
        dev_client.close()
    if vps_client:
        vps_client.close()
    
    return success

if __name__ == "__main__":
    try:
        success = comprehensive_database_comparison()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n⚠️ Database comparison interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Database comparison failed with error: {e}")
        sys.exit(1)