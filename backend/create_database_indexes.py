#!/usr/bin/env python3
"""
Database Index Creation Script for Tax Sale Compass
Creates performance-critical indexes for all collections
"""

import os
import sys
import pymongo
from pymongo import ASCENDING, DESCENDING
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_indexes():
    """Create all necessary database indexes for optimal performance"""
    
    # Get database connection details
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    db_name = os.environ.get('DB_NAME', 'test_database')
    
    print("🚀 Creating Database Indexes for Tax Sale Compass")
    print("=" * 60)
    print(f"Database URL: {mongo_url}")
    print(f"Database Name: {db_name}")
    print()
    
    try:
        # Connect to MongoDB
        print("🔗 Connecting to MongoDB...")
        client = pymongo.MongoClient(mongo_url, serverSelectionTimeoutMS=10000)
        client.server_info()  # Test connection
        db = client[db_name]
        print("✅ Connected successfully")
        print()
        
        # Index creation results
        results = {}
        
        # 1. TAX_SALES Collection Indexes
        print("📋 Creating indexes for 'tax_sales' collection...")
        tax_sales = db.tax_sales
        
        # Check existing indexes first
        existing_indexes = [idx['name'] for idx in tax_sales.list_indexes()]
        print(f"   Existing indexes: {existing_indexes}")
        
        tax_sales_indexes = [
            # Single field indexes
            ("assessment_number_1", [("assessment_number", ASCENDING)]),
            ("municipality_name_1", [("municipality_name", ASCENDING)]),
            ("status_1", [("status", ASCENDING)]),
            ("sale_date_1", [("sale_date", ASCENDING)]),
            ("latitude_1", [("latitude", ASCENDING)]),
            ("longitude_1", [("longitude", ASCENDING)]),
            
            # Compound indexes for common queries
            ("municipality_status_1", [("municipality_name", ASCENDING), ("status", ASCENDING)]),
            ("status_sale_date_1", [("status", ASCENDING), ("sale_date", ASCENDING)]),
            ("municipality_sale_date_1", [("municipality_name", ASCENDING), ("sale_date", ASCENDING)]),
        ]
        
        tax_sales_created = 0
        for index_name, index_spec in tax_sales_indexes:
            try:
                if index_name not in existing_indexes:
                    tax_sales.create_index(index_spec, name=index_name, background=True)
                    print(f"   ✅ Created index: {index_name}")
                    tax_sales_created += 1
                else:
                    print(f"   ⏭️ Index already exists: {index_name}")
            except Exception as e:
                print(f"   ❌ Failed to create index {index_name}: {e}")
        
        results['tax_sales'] = tax_sales_created
        
        # 2. USERS Collection Indexes
        print("\n👥 Creating indexes for 'users' collection...")
        users = db.users
        
        existing_indexes = [idx['name'] for idx in users.list_indexes()]
        print(f"   Existing indexes: {existing_indexes}")
        
        users_indexes = [
            ("email_1", [("email", ASCENDING)]),
            ("id_1", [("id", ASCENDING)]),
            ("subscription_tier_1", [("subscription_tier", ASCENDING)]),
        ]
        
        users_created = 0
        for index_name, index_spec in users_indexes:
            try:
                if index_name not in existing_indexes:
                    users.create_index(index_spec, name=index_name, unique=(index_name in ["email_1", "id_1"]), background=True)
                    print(f"   ✅ Created index: {index_name}")
                    users_created += 1
                else:
                    print(f"   ⏭️ Index already exists: {index_name}")
            except Exception as e:
                print(f"   ❌ Failed to create index {index_name}: {e}")
        
        results['users'] = users_created
        
        # 3. MUNICIPALITIES Collection Indexes
        print("\n🏢 Creating indexes for 'municipalities' collection...")
        municipalities = db.municipalities
        
        existing_indexes = [idx['name'] for idx in municipalities.list_indexes()]
        print(f"   Existing indexes: {existing_indexes}")
        
        municipalities_indexes = [
            ("name_1", [("name", ASCENDING)]),
            ("id_1", [("id", ASCENDING)]),
            ("scraper_type_1", [("scraper_type", ASCENDING)]),
            ("schedule_enabled_1", [("schedule_enabled", ASCENDING)]),
        ]
        
        municipalities_created = 0
        for index_name, index_spec in municipalities_indexes:
            try:
                if index_name not in existing_indexes:
                    municipalities.create_index(index_spec, name=index_name, unique=(index_name in ["name_1", "id_1"]), background=True)
                    print(f"   ✅ Created index: {index_name}")
                    municipalities_created += 1
                else:
                    print(f"   ⏭️ Index already exists: {index_name}")
            except Exception as e:
                print(f"   ❌ Failed to create index {index_name}: {e}")
        
        results['municipalities'] = municipalities_created
        
        # 4. FAVORITES Collection Indexes
        print("\n⭐ Creating indexes for 'favorites' collection...")
        favorites = db.favorites
        
        existing_indexes = [idx['name'] for idx in favorites.list_indexes()]
        print(f"   Existing indexes: {existing_indexes}")
        
        favorites_indexes = [
            ("user_id_1", [("user_id", ASCENDING)]),
            ("property_id_1", [("property_id", ASCENDING)]),
            ("created_at_1", [("created_at", DESCENDING)]),
            ("user_property_1", [("user_id", ASCENDING), ("property_id", ASCENDING)]),
        ]
        
        favorites_created = 0
        for index_name, index_spec in favorites_indexes:
            try:
                if index_name not in existing_indexes:
                    favorites.create_index(index_spec, name=index_name, unique=(index_name == "user_property_1"), background=True)
                    print(f"   ✅ Created index: {index_name}")
                    favorites_created += 1
                else:
                    print(f"   ⏭️ Index already exists: {index_name}")
            except Exception as e:
                print(f"   ❌ Failed to create index {index_name}: {e}")
        
        results['favorites'] = favorites_created
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 INDEX CREATION SUMMARY")
        print("=" * 60)
        
        total_created = sum(results.values())
        for collection, count in results.items():
            print(f"   {collection}: {count} new indexes created")
        
        print(f"\n✅ Total new indexes created: {total_created}")
        
        if total_created > 0:
            print("\n⚡ PERFORMANCE IMPROVEMENT EXPECTED:")
            print("   - Faster property searches by assessment number")
            print("   - Faster municipality filtering")
            print("   - Faster status-based queries")
            print("   - Faster user authentication")
            print("   - Faster favorites retrieval")
        
        # Test a few queries to verify indexes are working
        print("\n🧪 Testing index performance...")
        
        # Test property lookup
        assessment_test = tax_sales.find_one({"assessment_number": {"$exists": True}})
        if assessment_test:
            test_assessment = assessment_test["assessment_number"]
            result = tax_sales.find({"assessment_number": test_assessment}).explain()
            execution_stats = result.get('executionStats', {})
            if execution_stats.get('executionTimeMillis', 0) < 50:
                print("   ✅ Assessment number queries optimized")
            else:
                print("   ⚠️ Assessment number queries may need optimization")
        
        print("\n🎉 Database optimization complete!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating indexes: {e}")
        return False
    finally:
        if 'client' in locals():
            client.close()

if __name__ == "__main__":
    success = create_indexes()
    sys.exit(0 if success else 1)