#!/usr/bin/env python3
"""
NYT Cooking Recipe Importer
Imports recipes from NYT Cooking using your authenticated session cookie.

Usage:
    # Single recipe
    python nyt_import.py "https://cooking.nytimes.com/recipes/1026415-beef-fried-rice"

    # Bulk import from a file (one URL per line)
    python nyt_import.py --file nyt_urls.txt

    # With skip-existing flag (safe to re-run)
    python nyt_import.py --file nyt_urls.txt --skip-existing

Setup:
    Cookie is read from .env file in this directory (NYT_COOKIE=your_cookie_value)
    or from the NYT_COOKIE environment variable.
"""

import sys
import os
import sqlite3
import argparse
import logging
import re
import hashlib
from pathlib import Path
from typing import Optional, Dict, List

# Load .env file if present
env_path = Path(__file__).parent / ".env"
if env_path.exists():
    with open(env_path) as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                os.environ.setdefault(key.strip(), value.strip())

from recipe_scrapers import scrape_html
import requests

try:
    from tqdm import tqdm
    HAS_TQDM = True
except ImportError:
    HAS_TQDM = False

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Default DB path (relative to scraper directory)
DEFAULT_DB = str(Path(__file__).parent.parent / "database" / "recipes.db")


def get_nyt_cookie() -> str:
    """Get the NYT session cookie from environment"""
    cookie = os.environ.get("NYT_COOKIE", "").strip()
    if not cookie:
        raise ValueError(
            "NYT_COOKIE not set. Add it to scraper/.env or set the environment variable.\n"
            "Example: NYT_COOKIE=your_cookie_value_here"
        )
    return cookie


def fetch_nyt_recipe(url: str, cookie: str) -> Optional[object]:
    """Fetch and parse an NYT Cooking recipe using authenticated session"""
    # Strip tracking params from URL for cleaner slugs
    clean_url = url.split("?")[0]

    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Referer": "https://cooking.nytimes.com/",
    }
    cookies = {
        "nyt-s": cookie,
        "nyt-a": "auto",  # helps avoid bot detection
    }

    response = requests.get(clean_url, headers=headers, cookies=cookies, timeout=30)
    response.raise_for_status()

    if "You must be a subscriber" in response.text or "Log in" in response.text[:2000]:
        raise ValueError("Cookie appears expired — grab a fresh nyt-s cookie from your browser.")

    scraper = scrape_html(html=response.content, org_url=clean_url)
    return scraper, clean_url


def safe_call(func, default=None):
    """Safely call a scraper method"""
    try:
        result = func() if callable(func) else func
        return result if result is not None else default
    except Exception:
        return default


def extract_nutrient(nutrients: dict, key: str) -> Optional[int]:
    """Extract numeric value from nutrient dict"""
    try:
        value = nutrients.get(key)
        if not value:
            return None
        numeric = re.search(r'\d+', str(value))
        return int(numeric.group()) if numeric else None
    except Exception:
        return None


def slugify(text: str) -> str:
    text = text.lower()
    text = re.sub(r'[^\w\s-]', '', text)
    text = re.sub(r'[-\s]+', '-', text)
    return text[:100]


def save_recipe(conn: sqlite3.Connection, scraper, url: str) -> Optional[int]:
    """Extract recipe data and save to database"""
    cursor = conn.cursor()

    # Generate stable ID from URL
    recipe_id = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)

    name = scraper.title()
    if not name:
        logger.warning(f"Could not extract recipe name from {url}")
        return None

    description = safe_call(scraper.description)
    image_url = safe_call(scraper.image)
    total_time = safe_call(scraper.total_time)
    cook_time = safe_call(scraper.cook_time)
    prep_time = safe_call(scraper.prep_time)

    # Servings
    yields_str = safe_call(scraper.yields)
    servings = None
    if yields_str:
        m = re.search(r'\d+', str(yields_str))
        servings = int(m.group()) if m else None

    # Nutrition
    nutrients = safe_call(scraper.nutrients) or {}
    calories = extract_nutrient(nutrients, 'calories')
    protein = extract_nutrient(nutrients, 'proteinContent')
    carbs = extract_nutrient(nutrients, 'carbohydrateContent')
    fat = extract_nutrient(nutrients, 'fatContent')
    fiber = extract_nutrient(nutrients, 'fiberContent')
    sodium = extract_nutrient(nutrients, 'sodiumContent')

    # Ingredients — NYT returns full strings like "2 tablespoons olive oil"
    ingredients = safe_call(scraper.ingredients, default=[])

    # Instructions
    instructions_raw = safe_call(scraper.instructions, default="")
    if isinstance(instructions_raw, str):
        instruction_steps = [s.strip() for s in instructions_raw.split('\n') if s.strip()]
    elif isinstance(instructions_raw, list):
        instruction_steps = instructions_raw
    else:
        instruction_steps = []

    # Tags
    tags = []
    category = safe_call(scraper.category)
    cuisine = safe_call(scraper.cuisine)
    if category:
        tags.extend([t.strip() for t in str(category).split(',') if t.strip()])
    if cuisine:
        tags.extend([t.strip() for t in str(cuisine).split(',') if t.strip()])
    tags.append("nyt-cooking")  # Source tag

    # Wipe old data for this recipe (safe re-import)
    for table in ("ingredients", "instructions", "tags", "allergens"):
        cursor.execute(f"DELETE FROM {table} WHERE recipe_id = ?", (recipe_id,))

    # Insert recipe
    cursor.execute("""
        INSERT OR REPLACE INTO recipes (
            id, slug, name, description,
            prep_time, cook_time, total_time, servings,
            calories, protein, carbs, fat, fiber, sodium,
            image_url, hellofresh_url, region
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        recipe_id, slugify(name), name, description,
        prep_time, cook_time, total_time, servings or 2,
        calories, protein, carbs, fat, fiber, sodium,
        image_url, url, "nyt-cooking"
    ))

    # Ingredients
    for ingredient in ingredients:
        cursor.execute(
            "INSERT INTO ingredients (recipe_id, name) VALUES (?, ?)",
            (recipe_id, ingredient)
        )

    # Instructions
    for idx, step in enumerate(instruction_steps, 1):
        cursor.execute(
            "INSERT INTO instructions (recipe_id, step_number, description) VALUES (?, ?, ?)",
            (recipe_id, idx, step)
        )

    # Tags
    for tag in tags:
        cursor.execute(
            "INSERT OR IGNORE INTO tags (recipe_id, tag) VALUES (?, ?)",
            (recipe_id, tag)
        )

    conn.commit()
    return recipe_id


def import_url(url: str, conn: sqlite3.Connection, cookie: str) -> bool:
    """Import a single NYT recipe URL"""
    try:
        clean_url = url.split("?")[0]
        logger.info(f"Fetching: {clean_url}")
        scraper, clean_url = fetch_nyt_recipe(url, cookie)
        recipe_id = save_recipe(conn, scraper, clean_url)
        if recipe_id:
            name = scraper.title()
            ingredients_count = len(safe_call(scraper.ingredients, default=[]))
            logger.info(f"  ✓ '{name}' — {ingredients_count} ingredients, id={recipe_id}")
            return True
        return False
    except ValueError as e:
        logger.error(f"  ✗ Auth error: {e}")
        return False
    except Exception as e:
        logger.error(f"  ✗ Failed {url}: {e}")
        return False


def import_from_file(file_path: str, conn: sqlite3.Connection, cookie: str,
                     skip_existing: bool = False) -> Dict[str, int]:
    """Import multiple URLs from a file (one per line, # for comments)"""
    stats = {"success": 0, "failed": 0, "skipped": 0, "total": 0}

    with open(file_path) as f:
        urls = [line.strip() for line in f if line.strip().startswith("http")]

    stats["total"] = len(urls)
    logger.info(f"Found {stats['total']} URLs to import\n")

    iterator = tqdm(urls, desc="Importing", unit="recipe") if HAS_TQDM else urls

    for url in iterator:
        clean_url = url.split("?")[0]

        if skip_existing:
            url_hash = int(hashlib.md5(clean_url.encode()).hexdigest()[:8], 16)
            exists = conn.execute(
                "SELECT 1 FROM recipes WHERE id = ?", (url_hash,)
            ).fetchone()
            if exists:
                stats["skipped"] += 1
                continue

        if import_url(url, conn, cookie):
            stats["success"] += 1
        else:
            stats["failed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(description="Import NYT Cooking recipes")
    parser.add_argument("url", nargs="?", help="Single recipe URL")
    parser.add_argument("--file", "-f", help="File with one URL per line")
    parser.add_argument("--db", default=DEFAULT_DB, help="Database path")
    parser.add_argument("--skip-existing", action="store_true",
                        help="Skip URLs already in the database")
    args = parser.parse_args()

    if not args.url and not args.file:
        parser.error("Provide a URL or use --file nyt_urls.txt")

    try:
        cookie = get_nyt_cookie()
    except ValueError as e:
        logger.error(str(e))
        sys.exit(1)

    conn = sqlite3.connect(args.db)
    conn.row_factory = sqlite3.Row

    try:
        if args.file:
            stats = import_from_file(args.file, conn, cookie,
                                     skip_existing=args.skip_existing)
            print("\n" + "=" * 50)
            print("Import Complete")
            print("=" * 50)
            print(f"  ✓ Success:  {stats['success']}")
            print(f"  ⊘ Skipped:  {stats['skipped']}")
            print(f"  ✗ Failed:   {stats['failed']}")
            print(f"  Total:      {stats['total']}")
        else:
            success = import_url(args.url, conn, cookie)
            sys.exit(0 if success else 1)
    finally:
        conn.close()


if __name__ == "__main__":
    main()
