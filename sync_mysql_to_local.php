<?php
require_once __DIR__ . '/frontend-php/config/database.php';

echo "=== SYNCING VPS MYSQL DATA TO LOCAL DEV MONGODB ===\n";

try {
    // Connect to local MongoDB
    $local_mongodb = getDB();
    if (!$local_mongodb) {
        die("❌ Local MongoDB connection failed\n");
    }
    echo "✅ Local MongoDB connected\n";
    
    // Clear local collections first
    echo "\n🗑️ Clearing local MongoDB data...\n";
    $local_mongodb->properties->deleteMany([]);
    $local_mongodb->users->deleteMany([]);
    $local_mongodb->user_favorites->deleteMany([]);
    $local_mongodb->pvsc_data->deleteMany([]);
    echo "✅ Cleared local MongoDB collections\n";
    
    // Connect to VPS MySQL via SSH tunnel or remote connection
    $vps_host = '5.252.52.41';
    $vps_user = 'root';
    $vps_pass = '527iDUjHGHjx8';
    
    // Create temporary files for data transfer
    $temp_dir = '/tmp/vps_sync';
    shell_exec("mkdir -p $temp_dir");
    
    // Export MySQL data from VPS to CSV files
    $tables = ['properties', 'users', 'user_favorites', 'pvsc_data'];
    
    foreach ($tables as $table) {
        echo "\n📊 Exporting $table from VPS MySQL...\n";
        
        $csv_file = "$temp_dir/$table.csv";
        $export_cmd = "sshpass -p '$vps_pass' ssh -o StrictHostKeyChecking=no $vps_user@$vps_host \"mysql -u root -p tax_sale_compass -e 'SELECT * FROM $table' --batch --raw > /tmp/$table.csv\"";
        shell_exec($export_cmd);
        
        // Copy file from VPS to local
        $copy_cmd = "sshpass -p '$vps_pass' scp -o StrictHostKeyChecking=no $vps_user@$vps_host:/tmp/$table.csv $csv_file";
        shell_exec($copy_cmd);
        
        if (file_exists($csv_file)) {
            echo "✅ Downloaded $table data\n";
        } else {
            echo "❌ Failed to download $table data\n";
        }
    }
    
    // Now let's just copy the entire VPS migration script approach
    // But run the MySQL connection through SSH tunnel
    echo "\n🔄 Running direct MySQL to MongoDB migration...\n";
    
    // Create SSH tunnel to VPS MySQL
    $tunnel_cmd = "sshpass -p '$vps_pass' ssh -o StrictHostKeyChecking=no -L 3307:localhost:3306 $vps_user@$vps_host -N &";
    shell_exec($tunnel_cmd);
    sleep(2); // Wait for tunnel to establish
    
    // Now connect to MySQL through the tunnel
    $mysql = new PDO("mysql:host=127.0.0.1;port=3307;dbname=tax_sale_compass", "root", "");
    $mysql->setAttribute(PDO::ATTR_ERRMODE, PDO::ERRMODE_EXCEPTION);
    echo "✅ Connected to VPS MySQL via SSH tunnel\n";
    
    // Run the migration logic (similar to the original migration script)
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
    }
    
    if (!empty($properties)) {
        $result = $local_mongodb->properties->insertMany($properties);
        echo "✅ Migrated " . $result->getInsertedCount() . " properties to local dev\n";
    }
    
    // Migrate PVSC Data
    echo "\n🏠 Migrating PVSC data...\n";
    $stmt = $mysql->query("SELECT * FROM pvsc_data");
    $pvsc_data = [];
    
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
    }
    
    if (!empty($pvsc_data)) {
        $result = $local_mongodb->pvsc_data->insertMany($pvsc_data);
        echo "✅ Migrated " . $result->getInsertedCount() . " PVSC records to local dev\n";
    }
    
    // Migrate Users
    echo "\n👤 Migrating users...\n";
    $stmt = $mysql->query("SELECT * FROM users");
    $users = [];
    
    while ($row = $stmt->fetch(PDO::FETCH_ASSOC)) {
        $user = [
            'id' => 'mysql_user_' . $row['id'],
            'email' => $row['email'],
            'username' => explode('@', $row['email'])[0],
            'password_hash' => $row['password'],
            'subscription_tier' => $row['subscription_tier'],
            'is_admin' => (bool)$row['is_admin'],
            'created_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['created_at']) * 1000),
            'updated_at' => new MongoDB\BSON\UTCDateTime(strtotime($row['updated_at']) * 1000)
        ];
        $users[] = $user;
    }
    
    if (!empty($users)) {
        $result = $local_mongodb->users->insertMany($users);
        echo "✅ Migrated " . $result->getInsertedCount() . " users to local dev\n";
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
        $result = $local_mongodb->user_favorites->insertMany($favorites);
        echo "✅ Migrated " . $result->getInsertedCount() . " user favorites to local dev\n";
    }
    
    echo "\n🎉 LOCAL DEV SYNC COMPLETED!\n";
    echo "\n=== LOCAL DEV SUMMARY ===\n";
    echo "Properties: " . $local_mongodb->properties->countDocuments([]) . "\n";
    echo "PVSC Data: " . $local_mongodb->pvsc_data->countDocuments([]) . "\n";
    echo "Users: " . $local_mongodb->users->countDocuments([]) . "\n";
    echo "Favorites: " . $local_mongodb->user_favorites->countDocuments([]) . "\n";
    
    // Kill SSH tunnel
    shell_exec("pkill -f 'ssh.*3307:localhost:3306'");
    
} catch (Exception $e) {
    echo "❌ Sync failed: " . $e->getMessage() . "\n";
    echo "Stack trace: " . $e->getTraceAsString() . "\n";
    // Kill SSH tunnel on error
    shell_exec("pkill -f 'ssh.*3307:localhost:3306'");
}
?>