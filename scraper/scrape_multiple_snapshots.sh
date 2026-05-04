#!/bin/bash
# Scrape multiple Wayback Machine snapshots to maximize recipe collection

CONFIG_FILE="config.yaml"
BACKUP_FILE="config.yaml.backup"

# Backup original config
cp "$CONFIG_FILE" "$BACKUP_FILE"

# Array of snapshot dates to try
SNAPSHOTS=(
    "20250324235726"  # March 24, 2025 (most recent)
    "20250113112404"  # January 13, 2025
    "20241224204903"  # December 24, 2024
    "20240911205036"  # September 11, 2024
    "20240809033538"  # August 9, 2024
    "20240428215626"  # April 28, 2024
)

echo "========================================"
echo "Multi-Snapshot Recipe Scraper"
echo "========================================"
echo "Will try ${#SNAPSHOTS[@]} different snapshots"
echo ""

for snapshot in "${SNAPSHOTS[@]}"; do
    echo "----------------------------------------"
    echo "Trying snapshot: $snapshot"
    echo "----------------------------------------"

    # Update config file with new snapshot
    sed -i.bak "s/snapshot_date: \".*\"/snapshot_date: \"$snapshot\"/" "$CONFIG_FILE"

    # Run scraper (max 50 recipes per snapshot)
    python3 scrape.py --max-recipes 50

    echo ""
    echo "Snapshot $snapshot complete!"
    echo ""
    sleep 2
done

# Restore original config
mv "$BACKUP_FILE" "$CONFIG_FILE"

echo "========================================"
echo "All snapshots processed!"
echo "========================================"
echo "Check database for total recipe count:"
echo "  cd ../database"
echo "  ./query.sh stats"
