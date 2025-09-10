# VPS Featured Properties Debug Checklist

## Issue: Featured properties showing "No properties available" on VPS

### Step 1: Check Database Connection on VPS
Create this file on your VPS at `/path/to/your/app/debug_vps.php`:

```php
<?php
require_once 'config/database.php';

echo "<h2>VPS Database Diagnostic</h2>";
echo "DB_HOST: " . DB_HOST . "<br>";
echo "DB_USER: " . DB_USER . "<br>";
echo "DB_NAME: " . DB_NAME . "<br>";
echo "Connection: ";

try {
    $db = getDB();
    if ($db === null) {
        echo "<span style='color: red;'>FAILED - NULL</span><br>";
    } else {
        echo "<span style='color: green;'>SUCCESS</span><br>";
        
        // Check properties table
        $stmt = $db->query("SELECT COUNT(*) as count FROM properties");
        $count = $stmt->fetch();
        echo "Properties count: " . $count['count'] . "<br>";
        
        if ($count['count'] > 0) {
            $stmt = $db->query("SELECT assessment_number, civic_address, status FROM properties LIMIT 3");
            $properties = $stmt->fetchAll();
            echo "<table border='1'>";
            echo "<tr><th>Assessment #</th><th>Address</th><th>Status</th></tr>";
            foreach ($properties as $prop) {
                echo "<tr><td>" . $prop['assessment_number'] . "</td><td>" . $prop['civic_address'] . "</td><td>" . $prop['status'] . "</td></tr>";
            }
            echo "</table>";
        }
    }
} catch (Exception $e) {
    echo "<span style='color: red;'>ERROR: " . $e->getMessage() . "</span>";
}
?>
```

### Step 2: Check VPS Environment Variables
On your VPS, check if these environment variables are set:
```bash
echo "DB_HOST: $DB_HOST"
echo "DB_USER: $DB_USER" 
echo "DB_NAME: $DB_NAME"
echo "GOOGLE_MAPS_API_KEY: $GOOGLE_MAPS_API_KEY"
```

### Step 3: Check VPS Database
Log into your VPS database and verify:
```sql
USE tax_sale_compass;  -- or your database name
SELECT COUNT(*) FROM properties;
SELECT assessment_number, civic_address, status FROM properties LIMIT 5;
```

### Step 4: Check VPS PHP Error Logs
```bash
tail -f /var/log/php-fpm/www-error.log
# or
tail -f /var/log/nginx/error.log
```

### Step 5: Test Landing Page Logic on VPS
Add this temporary debug code to your VPS `search.php` file after line 14:

```php
// TEMPORARY DEBUG - REMOVE AFTER FIXING
error_log("=== LANDING PAGE DEBUG ===");
error_log("User logged in: " . ($is_logged_in ? 'YES' : 'NO'));
if (!$is_logged_in) {
    error_log("Fetching properties for landing...");
    // ... existing property fetching code
    error_log("Properties found: " . count($landing_properties));
    foreach ($landing_properties as $prop) {
        error_log("Property: " . $prop['assessment_number'] . " - " . $prop['civic_address']);
    }
}
```

## Common VPS Issues:

1. **Database not created** - Properties table doesn't exist on VPS
2. **Wrong database credentials** - Different credentials on VPS vs dev
3. **Environment variables not set** - VPS missing env vars
4. **PHP version differences** - Different PHP version on VPS
5. **File permissions** - Config files not readable
6. **Web server configuration** - Nginx/Apache not configured properly

## Quick Fixes to Try:

1. **Check database exists:**
   ```bash
   mysql -u username -p -e "SHOW DATABASES LIKE 'tax_sale_compass';"
   ```

2. **Import database schema if missing:**
   ```bash
   mysql -u username -p database_name < /path/to/mysql_schema.sql
   ```

3. **Set environment variables in VPS .env file or server config**

4. **Check file permissions:**
   ```bash
   chmod 644 config/database.php
   ```

5. **Restart web services:**
   ```bash
   sudo systemctl restart nginx
   sudo systemctl restart php-fpm
   ```