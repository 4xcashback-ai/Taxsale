#!/bin/bash

# Post-Scraping Tasks for Tax Sale Compass
# Runs automatically after property scraping to perform maintenance tasks

LOG_FILE="/var/log/post_scraping_tasks.log"
SCRIPT_DIR="/var/www/tax-sale-compass/scripts"

# Function to log with timestamp
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "=== Starting Post-Scraping Tasks ==="

# Check if we're in the right directory
cd /var/www/tax-sale-compass || {
    log "ERROR: Could not change to application directory"
    exit 1
}

# 1. Generate thumbnails for new properties only (properties without thumbnail_path)
log "Step 1: Generating thumbnails for newly scraped properties only..."

# Use PHP to generate thumbnails only for properties that don't have thumbnails yet
php << 'EOF' >> "$LOG_FILE" 2>&1
<?php
require_once __DIR__ . '/batch_thumbnail_generator.php';

echo "Generating thumbnails for newly scraped properties only...\n";

try {
    $generator = new BatchThumbnailGenerator();
    
    // Only generate for properties that don't have thumbnails yet
    $generator->generateMissingThumbnails();
    
    echo "✅ Thumbnail generation for new properties completed\n";
} catch (Exception $e) {
    echo "❌ Error: " . $e->getMessage() . "\n";
}
?>
EOF

if [ $? -eq 0 ]; then
    log "✅ Thumbnail generation completed successfully"
else
    log "⚠️ Thumbnail generation completed with warnings/errors"
fi

# 2. Clean up old thumbnails
log "Step 2: Cleaning up orphaned thumbnails..."
php "$SCRIPT_DIR/batch_thumbnail_generator.php" --cleanup >> "$LOG_FILE" 2>&1

if [ $? -eq 0 ]; then
    log "✅ Thumbnail cleanup completed successfully"
else
    log "⚠️ Thumbnail cleanup completed with warnings/errors"
fi

# 3. Generate statistics
log "Step 3: Generating thumbnail statistics..."
php "$SCRIPT_DIR/batch_thumbnail_generator.php" --stats >> "$LOG_FILE" 2>&1

# 4. Optimize thumbnail directory
log "Step 4: Optimizing thumbnail directory permissions..."
chown -R www-data:www-data /var/www/tax-sale-compass/frontend-php/assets/thumbnails/
chmod -R 755 /var/www/tax-sale-compass/frontend-php/assets/thumbnails/

# 5. Clear any old caches if needed
log "Step 5: Clearing application caches..."
# Add any cache clearing logic here if needed

# 6. Database maintenance (optional)
log "Step 6: Database maintenance..."
# Could add database optimization, cleanup, etc.

log "=== Post-Scraping Tasks Completed ==="

# Send summary email or notification (optional)
# Could integrate with notification system here

exit 0