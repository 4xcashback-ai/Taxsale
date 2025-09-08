# Database Migration Instructions

## Scraper Configuration System Migration

### Files Created:
- `/app/database/add_scraper_config.sql` - Main schema migration
- New backend methods in `mysql_config.py`
- New API endpoints in `server_mysql.py` 
- New admin UI in `admin.php`

## Migration Steps

### Step 1: Apply Database Schema
Run the SQL migration to create the scraper_config table:

```bash
# Connect to MySQL database
mysql -u [username] -p tax_sale_compass

# Apply the migration
source /app/database/add_scraper_config.sql

# Or alternatively, run directly:
mysql -u [username] -p tax_sale_compass < /app/database/add_scraper_config.sql
```

### Step 2: Verify Schema Creation
Check that the table was created successfully:

```sql
USE tax_sale_compass;

-- Check table structure
DESCRIBE scraper_config;

-- Check initial data
SELECT municipality, base_url, enabled FROM scraper_config;
```

**Expected Output:**
- Table `scraper_config` should exist with columns: id, municipality, base_url, tax_sale_page_url, pdf_search_patterns, excel_search_patterns, enabled, etc.
- 3 default configurations should be inserted: Halifax Regional Municipality, Victoria County, Cumberland County

### Step 3: Restart Backend Service
```bash
sudo supervisorctl restart backend
```

### Step 4: Verify Backend Integration
Test that backend can access the new table:

```bash
# Check backend logs for any MySQL errors
tail -f /var/log/supervisor/backend.*.log

# Test the API endpoint (replace with your domain)
curl -H "Authorization: Bearer YOUR_TOKEN" http://localhost:8001/api/admin/scraper-configs
```

### Step 5: Test Admin Panel
1. Login to admin panel: `https://yourdomain.com/admin.php`
2. Navigate to "⚙️ Scraper Configuration" section
3. Select a municipality from dropdown
4. Click "Load Configuration" - should show current settings
5. Click "Test Configuration" - should find tax sale files

## Verification Checklist

- [ ] `scraper_config` table exists in database
- [ ] 3 default municipality configurations are present
- [ ] Backend service starts without MySQL errors
- [ ] Admin panel shows "Scraper Configuration" section
- [ ] Municipality dropdown populates with data
- [ ] "Load Configuration" button works
- [ ] "Test Configuration" finds files on municipality websites

## Troubleshooting

### Issue: Table creation fails
**Solution:** Check MySQL permissions and database connection
```sql
SHOW GRANTS FOR CURRENT_USER();
USE tax_sale_compass;
```

### Issue: JSON columns not supported  
**Solution:** Ensure MySQL version 5.7+ or MariaDB 10.2+
```sql
SELECT VERSION();
```

### Issue: Backend can't connect to database
**Solution:** Check backend logs and MySQL credentials in `.env`

### Issue: Admin panel doesn't show new section
**Solution:** Clear browser cache and check for JavaScript errors in console

## Rollback Instructions

If you need to rollback the migration:

```sql
USE tax_sale_compass;
DROP TABLE IF EXISTS scraper_config;
```

**Note:** This will remove all scraper configurations. Make sure to backup any custom configurations first:

```sql
-- Backup configurations
SELECT * FROM scraper_config INTO OUTFILE '/tmp/scraper_config_backup.csv'
FIELDS TERMINATED BY ',' ENCLOSED BY '"'
LINES TERMINATED BY '\n';
```

## Post-Migration Tasks

### 1. Update Existing Configurations
After migration, you should:
- Review and update default URLs for each municipality
- Test each municipality's configuration
- Add search patterns specific to each municipality's website structure

### 2. Configure Municipality-Specific Settings
For each municipality, customize:
- **PDF Search Patterns**: Regex patterns to find PDF files
- **Excel Search Patterns**: Regex patterns to find Excel files  
- **Timeout Settings**: Adjust based on website response times
- **Retry Settings**: Configure retry attempts for failed requests

### 3. Monitor Scraper Performance
- Check scraper logs for any configuration-related errors
- Verify that dynamic file discovery is working
- Test the rescan functionality with the new system

## Migration Complete!

Once all steps are completed successfully, your scraper system will be:
- ✅ Database-driven (no hardcoded URLs)
- ✅ Dynamically discovering tax sale files
- ✅ Fully configurable through admin panel
- ✅ Testable before deployment
- ✅ Easily maintainable for new municipalities