#!/usr/bin/env python3
"""
Recipe URL Importer
Import recipes from any URL using recipe-scrapers library
Supports 600+ recipe sites
"""

import sys
import sqlite3
import argparse
import logging
from pathlib import Path
from typing import Optional, Dict, List

from recipe_scrapers import scrape_html
import requests

# Local normalization module
from normalize import (
    parse_ingredient,
    normalize_instructions_list,
    normalize_quantity,
)
from validate_recipes import RecipeValidator

# Optional progress bar support
try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecipeImporter:
    """Import recipes from URLs into SQLite database"""

    def __init__(self, db_path: str = "../database/recipes.db"):
        self.db_path = db_path
        self.db_conn = None

    def connect_db(self):
        """Connect to SQLite database"""
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row

    def close_db(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()

    def import_from_url(self, url: str, region: str = "imported") -> bool:
        """
        Import recipe from URL using recipe-scrapers

        Args:
            url: Recipe URL
            region: Region tag (default: 'imported')

        Returns:
            True if successful, False otherwise
        """
        try:
            logger.info(f"Fetching recipe from: {url}")

            # Fetch the HTML with comprehensive browser headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.9',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0'
            }
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()

            # Use recipe-scrapers to parse
            scraper = scrape_html(html=response.content, org_url=url)

            # Extract all available data
            recipe_data = {
                'name': scraper.title(),
                'description': self._safe_call(scraper.description),
                'image_url': self._safe_call(scraper.image),
                'url': url,
                'region': region,
            }

            # Extract timing
            recipe_data['total_time'] = self._safe_call(scraper.total_time)
            recipe_data['cook_time'] = self._safe_call(scraper.cook_time)
            recipe_data['prep_time'] = self._safe_call(scraper.prep_time)

            # Extract servings/yields
            yields_data = self._safe_call(scraper.yields)
            if yields_data:
                # Try to extract number from yields string
                import re
                servings_match = re.search(r'\d+', str(yields_data))
                recipe_data['servings'] = int(servings_match.group()) if servings_match else None
            else:
                recipe_data['servings'] = None

            # Extract nutrition
            nutrients = self._safe_call(scraper.nutrients)
            if nutrients:
                recipe_data['calories'] = self._extract_nutrient(nutrients, 'calories')
                recipe_data['protein'] = self._extract_nutrient(nutrients, 'proteinContent')
                recipe_data['carbs'] = self._extract_nutrient(nutrients, 'carbohydrateContent')
                recipe_data['fat'] = self._extract_nutrient(nutrients, 'fatContent')
            else:
                recipe_data['calories'] = None
                recipe_data['protein'] = None
                recipe_data['carbs'] = None
                recipe_data['fat'] = None

            # Extract and parse ingredients
            raw_ingredients = self._safe_call(scraper.ingredients, default=[])
            ingredients = []
            for raw in raw_ingredients:
                quantity, name, normalized = parse_ingredient(raw)
                ingredients.append({
                    'raw': raw,
                    'quantity': quantity,
                    'name': name,
                    'normalized_name': normalized,
                })

            # Extract instructions and filter garbage
            instructions = self._safe_call(scraper.instructions, default="")
            if isinstance(instructions, str):
                instruction_steps = [s.strip() for s in instructions.split('\n') if s.strip()]
            else:
                instruction_steps = instructions if isinstance(instructions, list) else []
            # Remove garbage steps like "step 1", "step 2"
            instruction_steps = normalize_instructions_list(instruction_steps)

            # Extract tags/category
            category = self._safe_call(scraper.category)
            cuisine = self._safe_call(scraper.cuisine)
            tags = []
            if category:
                tags.append(category)
            if cuisine:
                tags.append(cuisine)

            # Save to database
            recipe_id = self._save_recipe(recipe_data, ingredients, instruction_steps, tags)

            if recipe_id:
                logger.info(f"✓ Successfully imported: {recipe_data['name']}")
                logger.info(f"  - {len(ingredients)} ingredients")
                logger.info(f"  - {len(instruction_steps)} steps")

                # Validate the imported recipe
                self._validate_imported_recipe(recipe_id)

                return True
            else:
                logger.error(f"Failed to save recipe to database")
                return False

        except Exception as e:
            logger.error(f"Error importing recipe from {url}: {e}")
            return False

    def _safe_call(self, func, default=None):
        """Safely call a scraper method that might not be implemented"""
        try:
            result = func() if callable(func) else func
            return result if result else default
        except (NotImplementedError, AttributeError, Exception):
            return default

    def _validate_imported_recipe(self, recipe_id: int):
        """Validate imported recipe and show warnings"""
        try:
            validator = RecipeValidator(self.db_path)
            validator.db_conn = self.db_conn  # Reuse connection
            result = validator.validate_recipe(recipe_id)

            if not result.is_valid:
                logger.warning(f"⚠️  Recipe has validation errors (score: {result.score}/100):")
                for error in result.errors:
                    logger.warning(f"     🔴 {error.field}: {error.message}")
            elif result.warnings:
                logger.info(f"📋 Recipe quality score: {result.score}/100")
                for warning in result.warnings:
                    logger.info(f"     🟡 {warning.field}: {warning.message}")
            else:
                logger.info(f"✅ Recipe passed validation (score: {result.score}/100)")
        except Exception as e:
            logger.debug(f"Validation check skipped: {e}")

    def _extract_nutrient(self, nutrients: dict, key: str) -> Optional[int]:
        """Extract numeric value from nutrient dict"""
        try:
            value = nutrients.get(key)
            if not value:
                return None
            # Remove units and convert to int
            import re
            numeric = re.search(r'\d+', str(value))
            return int(numeric.group()) if numeric else None
        except:
            return None

    def _save_recipe(self, recipe_data: Dict, ingredients: List[str],
                     instructions: List[str], tags: List[str]) -> Optional[int]:
        """Save recipe and related data to database"""
        try:
            cursor = self.db_conn.cursor()

            # Generate a unique ID (use hash of URL)
            import hashlib
            url_hash = int(hashlib.md5(recipe_data['url'].encode()).hexdigest()[:8], 16)
            recipe_id = url_hash

            # Delete existing related data if recipe already exists
            cursor.execute("DELETE FROM ingredients WHERE recipe_id = ?", (recipe_id,))
            cursor.execute("DELETE FROM instructions WHERE recipe_id = ?", (recipe_id,))
            cursor.execute("DELETE FROM tags WHERE recipe_id = ?", (recipe_id,))

            # Insert recipe
            cursor.execute("""
                INSERT OR REPLACE INTO recipes (
                    id, slug, name, description,
                    prep_time, cook_time, total_time, servings,
                    calories, protein, carbs, fat,
                    image_url, hellofresh_url, region
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                recipe_id,
                self._slugify(recipe_data['name']),
                recipe_data['name'],
                recipe_data['description'],
                recipe_data.get('prep_time'),
                recipe_data.get('cook_time'),
                recipe_data.get('total_time'),
                recipe_data.get('servings', 2),
                recipe_data.get('calories'),
                recipe_data.get('protein'),
                recipe_data.get('carbs'),
                recipe_data.get('fat'),
                recipe_data.get('image_url'),
                recipe_data['url'],
                recipe_data['region']
            ))

            # Insert ingredients with parsed quantity and normalized name
            for ing in ingredients:
                cursor.execute("""
                    INSERT INTO ingredients (recipe_id, name, quantity, normalized_name)
                    VALUES (?, ?, ?, ?)
                """, (recipe_id, ing['name'], ing['quantity'], ing['normalized_name']))

            # Insert instructions
            for idx, instruction in enumerate(instructions, 1):
                cursor.execute("""
                    INSERT INTO instructions (recipe_id, step_number, description)
                    VALUES (?, ?, ?)
                """, (recipe_id, idx, instruction))

            # Insert tags
            for tag in tags:
                cursor.execute("""
                    INSERT OR IGNORE INTO tags (recipe_id, tag)
                    VALUES (?, ?)
                """, (recipe_id, tag))

            self.db_conn.commit()
            return recipe_id

        except sqlite3.IntegrityError as e:
            logger.warning(f"Recipe already exists or constraint violation: {e}")
            self.db_conn.rollback()
            return None
        except Exception as e:
            logger.error(f"Database error: {e}")
            self.db_conn.rollback()
            return None

    def _slugify(self, text: str) -> str:
        """Convert text to URL-friendly slug"""
        import re
        text = text.lower()
        text = re.sub(r'[^\w\s-]', '', text)
        text = re.sub(r'[-\s]+', '-', text)
        return text[:100]  # Limit length

    def import_from_file(self, file_path: str, region: str = "imported",
                         skip_existing: bool = False) -> Dict[str, int]:
        """
        Import multiple recipes from a file containing URLs (one per line)

        Args:
            file_path: Path to file with URLs
            region: Region tag for all recipes
            skip_existing: Skip URLs that have already been imported

        Returns:
            Dict with success/failure/skipped counts
        """
        stats = {'success': 0, 'failed': 0, 'skipped': 0, 'total': 0}
        failed_urls = []

        with open(file_path, 'r') as f:
            urls = [line.strip() for line in f if line.strip() and not line.startswith('#')]

        stats['total'] = len(urls)
        logger.info(f"Importing {stats['total']} recipes from {file_path}")

        # Use tqdm progress bar if available
        if HAS_TQDM:
            url_iter = tqdm(urls, desc="Importing recipes", unit="recipe",
                           bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}]')
        else:
            url_iter = urls

        for idx, url in enumerate(url_iter, 1):
            if not HAS_TQDM:
                logger.info(f"\n[{idx}/{stats['total']}] Processing: {url}")

            # Check if already exists (skip_existing mode)
            if skip_existing:
                import hashlib
                url_hash = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)
                cursor = self.db_conn.cursor()
                exists = cursor.execute(
                    "SELECT 1 FROM recipes WHERE id = ?", (url_hash,)
                ).fetchone()
                if exists:
                    stats['skipped'] += 1
                    if HAS_TQDM:
                        url_iter.set_postfix(success=stats['success'],
                                            failed=stats['failed'],
                                            skipped=stats['skipped'])
                    continue

            if self.import_from_url(url, region):
                stats['success'] += 1
            else:
                stats['failed'] += 1
                failed_urls.append(url)

            # Update progress bar postfix
            if HAS_TQDM:
                url_iter.set_postfix(success=stats['success'],
                                    failed=stats['failed'],
                                    skipped=stats['skipped'])

        # Log failed URLs for retry
        if failed_urls:
            logger.warning(f"\nFailed URLs ({len(failed_urls)}):")
            for url in failed_urls:
                logger.warning(f"  - {url}")

        return stats


def main():
    parser = argparse.ArgumentParser(
        description='Import recipes from URLs using recipe-scrapers'
    )
    parser.add_argument('url', nargs='?', help='Recipe URL to import')
    parser.add_argument('--file', '-f', help='File containing URLs (one per line)')
    parser.add_argument('--region', '-r', default='imported',
                       help='Region tag (default: imported)')
    parser.add_argument('--db', default='../database/recipes.db',
                       help='Database path')
    parser.add_argument('--skip-existing', action='store_true',
                       help='Skip URLs already in database')

    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("Either provide a URL or use --file")

    if not HAS_TQDM:
        logger.info("Tip: Install tqdm for progress bars: pip install tqdm")

    importer = RecipeImporter(args.db)
    importer.connect_db()

    try:
        if args.file:
            # Import from file
            stats = importer.import_from_file(args.file, args.region,
                                             skip_existing=args.skip_existing)
            print("\n" + "="*60)
            print("Import Complete!")
            print("="*60)
            print(f"✓ Success: {stats['success']}")
            print(f"⊘ Skipped: {stats['skipped']}")
            print(f"✗ Failed:  {stats['failed']}")
            print(f"Total:     {stats['total']}")
        else:
            # Import single URL
            success = importer.import_from_url(args.url, args.region)
            sys.exit(0 if success else 1)

    finally:
        importer.close_db()


if __name__ == '__main__':
    main()
