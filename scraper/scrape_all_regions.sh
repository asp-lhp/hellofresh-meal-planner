#!/bin/bash
# Scrape recipes from all HelloFresh regions

CONFIG_FILE="config.yaml"

# Array of regions to scrape
REGIONS=(
    "en-US"  # United States (already have 11)
    "en-AU"  # Australia
    "en-CA"  # Canada (English)
    "fr-CA"  # Canada (French)
    "de-DE"  # Germany
    "de-AT"  # Austria
    "de-CH"  # Switzerland
    "nl-BE"  # Belgium (Dutch)
    "fr-BE"  # Belgium (French)
    "da-DK"  # Denmark
    "es-ES"  # Spain
)

echo "========================================"
echo "Multi-Region Recipe Scraper"
echo "========================================"
echo "Will scrape ${#REGIONS[@]} different regions"
echo ""

for region in "${REGIONS[@]}"; do
    echo "----------------------------------------"
    echo "Scraping region: $region"
    echo "----------------------------------------"

    # Run scraper for this region (max 50 per region)
    python3 scrape.py --region "$region" --max-recipes 50

    echo ""
    echo "Region $region complete!"
    echo ""

    # Check database stats
    echo "Current database stats:"
    cd ../database
    sqlite3 recipes.db "SELECT COUNT(*) || ' recipes' FROM recipes;"
    cd ../scraper

    echo ""
    sleep 2
done

echo "========================================"
echo "All regions processed!"
echo "========================================"
echo "Final database stats:"
cd ../database
./query.sh stats
