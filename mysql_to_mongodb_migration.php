<?php
require_once __DIR__ . '/frontend-php/config/database.php';

echo "=== COMPLETE MYSQL TO MONGODB MIGRATION ===\n";

try {
    // Connect to MongoDB
    $mongodb = getDB();
    if (!$mongodb) {
        die("❌ MongoDB connection failed\n");
    }
    echo "✅ MongoDB connected\n";
    
    // Connect to MySQL
    $mysql = new PDO("mysql:host=localhost;dbname=tax_sale_compass", "root", "");
    $mysql->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "✅ MySQL connected\n";
    
    // Clear existing MongoDB collections
    echo "\n🗑️ Clearing existing MongoDB data...\n";
    $mongodb->properties->deleteMany([]);
    $mongodb->users->deleteMany([]);
    $mongodb->user_favorites->deleteMany([]);
    $mongodb->pvsc_data->deleteMany([]);
    echo "✅ Cleared MongoDB collections\n";
    
    // Migrate Properties
    echo "\n📋 Migrating properties...\n";
    $stmt = $mysql->query("SELECT * FROM properties");
    $properties = [];
    $property_count = 0;
    
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $property = [
            'assessment_number' => $row['assessment_number'],
            'owner_name' => $row['owner_name'],
            'civic_address' => $row['civic_address'],
            'parcel_description' => $row['parcel_description'],
            'pid_number' => $row['pid_number'],
            'primary_pid' => $row['primary_pid'],
            'secondary_pids' => $row['secondary_pids'],
            'pid_count' => (int)$row['pid_count'],
            'opening_bid' => $row['opening_bid'] ? (float)$row['opening_bid'] : null,
            'property_type' => $row['property_type'],
            'tax_year' => $row['tax_year'] ? (int)$row['tax_year'] : null,
            'total_taxes' => $row['total_taxes'] ? (float)$row['total_taxes'] : null,
            'hst_applicable' => (bool)$row['hst_applicable'],
            'redeemable' => (bool)$row['redeemable'],
            'status' => $row['status'],
            'sale_date' => $row['sale_date'],
            'auction_type' => $row['auction_type'],
            'municipality' => $row['municipality'],
            'province' => $row['province'],
            'latitude' => $row['latitude'] ? (float)$row['latitude'] : null,
            'longitude' => $row['longitude'] ? (float)$row['longitude'] : null,
            'boundary_data' => $row['boundary_data'] ? json_decode($row['boundary_data'], true) : null,
            'pvsc_assessment_value' => $row['pvsc_assessment_value'] ? (float)$row['pvsc_assessment_value'] : null,
            'pvsc_assessment_year' => $row['pvsc_assessment_year'] ? (int)$row['pvsc_assessment_year'] : null,
            'thumbnail_path' => $row['thumbnail_path'],
            'favorite_count' => (int)$row['favorite_count'],
            'created_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['created_at']) * 1000),
            'updated_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['updated_at']) * 1000)
        ];
        $properties[] = $property;
        $property_count++;
        
        if ($property_count % 10 == 0) {
            echo "  Processed $property_count properties...\n";
        }
    }
    
    if (!empty($properties)) {
        $result = $mongodb->properties->insertMany($properties);
        echo "✅ Migrated " . $result->getInsertedCount() . " properties\n";
    }
    
    // Migrate PVSC Data
    echo "\n🏠 Migrating PVSC data...\n";
    $stmt = $mysql->query("SELECT * FROM pvsc_data");
    $pvsc_data = [];
    $pvsc_count = 0;
    
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $pvsc = [
            'assessment_number' => $row['assessment_number'],
            'ain' => $row['ain'],
            'civic_address' => $row['civic_address'],
            'legal_description' => $row['legal_description'],
            'pid_number' => $row['pid_number'],
            'latitude' => $row['latitude'] ? (float)$row['latitude'] : null,
            'longitude' => $row['longitude'] ? (float)$row['longitude'] : null,
            'municipal_unit' => $row['municipal_unit'],
            'planning_district' => $row['planning_district'],
            'assessed_value' => $row['assessed_value'] ? (float)$row['assessed_value'] : null,
            'taxable_assessed_value' => $row['taxable_assessed_value'] ? (float)$row['taxable_assessed_value'] : null,
            'capped_assessment_value' => $row['capped_assessment_value'] ? (float)$row['capped_assessment_value'] : null,
            'assessment_year' => $row['assessment_year'] ? (int)$row['assessment_year'] : null,
            'property_type' => $row['property_type'],
            'property_use' => $row['property_use'],
            'land_size' => $row['land_size'] ? (float)$row['land_size'] : null,
            'land_size_unit' => $row['land_size_unit'],
            'building_size' => $row['building_size'] ? (float)$row['building_size'] : null,
            'building_size_unit' => $row['building_size_unit'],
            'dwelling_type' => $row['dwelling_type'],
            'year_built' => $row['year_built'] ? (int)$row['year_built'] : null,
            'number_of_bedrooms' => $row['number_of_bedrooms'] ? (int)$row['number_of_bedrooms'] : null,
            'number_of_bathrooms' => $row['number_of_bathrooms'] ? (float)$row['number_of_bathrooms'] : null,
            'basement_type' => $row['basement_type'],
            'garage' => $row['garage'],
            'heating_type' => $row['heating_type'],
            'exterior_finish' => $row['exterior_finish'],
            'roof_type' => $row['roof_type'],
            'building_class' => $row['building_class'],
            'building_type' => $row['building_type'],
            'building_style' => $row['building_style'],
            'construction_type' => $row['construction_type'],
            'construction_quality' => $row['construction_quality'],
            'under_construction' => $row['under_construction'],
            'occupancy_type' => $row['occupancy_type'],
            'living_units' => $row['living_units'] ? (int)$row['living_units'] : null,
            'last_sale_date' => $row['last_sale_date'],
            'last_sale_price' => $row['last_sale_price'] ? (float)$row['last_sale_price'] : null,
            'previous_sale_date' => $row['previous_sale_date'],
            'previous_sale_price' => $row['previous_sale_price'] ? (float)$row['previous_sale_price'] : null,
            'neighborhood_code' => $row['neighborhood_code'],
            'zoning' => $row['zoning'],
            'school_district' => $row['school_district'],
            'data_source' => $row['data_source'],
            'raw_json' => $row['raw_json'] ? json_decode($row['raw_json'], true) : null,
            'scraped_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['scraped_at']) * 1000),
            'updated_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['updated_at']) * 1000)
        ];
        $pvsc_data[] = $pvsc;
        $pvsc_count++;
        
        if ($pvsc_count % 10 == 0) {
            echo "  Processed $pvsc_count PVSC records...\n";
        }
    }
    
    if (!empty($pvsc_data)) {
        $result = $mongodb->pvsc_data->insertMany($pvsc_data);
        echo "✅ Migrated " . $result->getInsertedCount() . " PVSC records\n";
    } else {
        echo "ℹ️ No PVSC data found to migrate\n";
    }
    
    // Migrate Users
    echo "\n👤 Migrating users...\n";
    $stmt = $mysql->query("SELECT * FROM users");
    $users = [];
    
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $user = [
            'id' => 'mysql_user_' . $row['id'],
            'email' => $row['email'],
            'username' => explode('@', $row['email'])[0], // Create username from email
            'password_hash' => $row['password'],
            'subscription_tier' => $row['subscription_tier'],
            'is_admin' => (bool)$row['is_admin'],
            'created_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['created_at']) * 1000),
            'updated_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['updated_at']) * 1000)
        ];
        $users[] = $user;
    }
    
    if (!empty($users)) {
        $result = $mongodb->users->insertMany($users);
        echo "✅ Migrated " . $result->getInsertedCount() . " users\n";
    } else {
        echo "ℹ️ No users found to migrate\n";
    }
    
    // Migrate User Favorites
    echo "\n⭐ Migrating user favorites...\n";
    $stmt = $mysql->query("SELECT * FROM user_favorites");
    $favorites = [];
    
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $favorite = [
            'user_id' => 'mysql_user_' . $row['user_id'],
            'assessment_number' => $row['assessment_number'],
            'created_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['favorited_at']) * 1000)
        ];
        $favorites[] = $favorite;
    }
    
    if (!empty($favorites)) {
        $result = $mongodb->user_favorites->insertMany($favorites);
        echo "✅ Migrated " . $result->getInsertedCount() . " user favorites\n";
    } else {
        echo "ℹ️ No user favorites found to migrate\n";
    }
    
    echo "\n🎉 COMPLETE MIGRATION FINISHED!\n";
    echo "\n=== MIGRATION SUMMARY ===\n";
    echo "Properties: " . $mongodb->properties->countDocuments([]) . "\n";
    echo "PVSC Data: " . $mongodb->pvsc_data->countDocuments([]) . "\n";
    echo "Users: " . $mongodb->users->countDocuments([]) . "\n";
    echo "Favorites: " . $mongodb->user_favorites->countDocuments([]) . "\n";
    
} catch (Exception $e) {
    echo "❌ Migration failed: " . $e->getMessage() . "\n";
    echo "Stack trace: " . $e->getTraceAsString() . "\n";
}
?>