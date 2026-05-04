#!/usr/bin/env python3
"""
HelloFresh Recipe Scraper
Scrapes recipes from archive.org's Wayback Machine snapshot of hfresh.info
"""

import re
import sqlite3
import time
import yaml
import logging
import argparse
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup
from tqdm import tqdm
from ratelimit import limits, sleep_and_retry

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class RecipeScraper:
    """Scrapes HelloFresh recipes from Wayback Machine"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize scraper with configuration"""
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'HelloFresh-Recipe-Scraper/1.0 (Educational/Personal Use)'
        })
        self.db_conn = None
        self.stats = {
            'recipes_scraped': 0,
            'recipes_failed': 0,
            'recipes_skipped': 0
        }

    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file"""
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)

    def _init_database(self):
        """Initialize SQLite database with schema"""
        db_path = Path(self.config['database']['path'])
        db_path.parent.mkdir(parents=True, exist_ok=True)

        # Check if database exists
        db_exists = db_path.exists()

        self.db_conn = sqlite3.connect(str(db_path))
        self.db_conn.row_factory = sqlite3.Row

        if not db_exists:
            logger.info("Creating database schema...")
            schema_path = Path(self.config['database']['schema_path'])
            with open(schema_path, 'r') as f:
                self.db_conn.executescript(f.read())
            logger.info("Database schema created successfully")

    def _build_wayback_url(self, original_url: str) -> str:
        """Build Wayback Machine URL"""
        timestamp = self.config['wayback']['snapshot_date']
        base_url = self.config['wayback']['base_url']
        return base_url.format(timestamp=timestamp, url=original_url)

    @sleep_and_retry
    @limits(calls=1, period=2.5)  # Rate limit: 1 request per 2.5 seconds
    def _fetch_page(self, url: str, retries: int = 3) -> Optional[BeautifulSoup]:
        """Fetch and parse a page with rate limiting and retries"""
        wayback_url = self._build_wayback_url(url)

        for attempt in range(retries):
            try:
                logger.debug(f"Fetching: {wayback_url}")
                response = self.session.get(
                    wayback_url,
                    timeout=self.config['scraper']['timeout']
                )
                response.raise_for_status()
                return BeautifulSoup(response.content, 'lxml')

            except requests.RequestException as e:
                logger.warning(f"Attempt {attempt + 1}/{retries} failed: {e}")
                if attempt < retries - 1:
                    time.sleep(self.config['scraper']['retry_delay'])
                else:
                    logger.error(f"Failed to fetch {url} after {retries} attempts")
                    return None

    def discover_recipes(self) -> List[Dict]:
        """Discover all recipe URLs from the main recipe page"""
        region = self.config['scraper']['region']
        base_url = self.config['wayback']['original_url']
        recipes_url = f"{base_url}/{region}"

        logger.info(f"Discovering recipes from {recipes_url}...")
        soup = self._fetch_page(recipes_url)

        if not soup:
            logger.error("Failed to fetch recipe list page")
            return []

        recipes = []
        # Find all recipe links - they follow pattern: /en-US/recipes/{slug}-{id}
        recipe_links = soup.find_all('a', href=re.compile(r'/recipes/[\w-]+-\d+'))

        for link in recipe_links:
            href = link.get('href')
            # Extract recipe ID and slug from URL
            match = re.search(r'/recipes/([\w-]+)-(\d+)', href)
            if match:
                slug = match.group(1)
                recipe_id = int(match.group(2))

                # Clean URL - remove Wayback Machine prefix if present
                clean_href = href
                if 'web.archive.org' in href:
                    # Extract original URL from Wayback URL
                    wayback_match = re.search(r'web\.archive\.org/web/\d+/(.*)', href)
                    if wayback_match:
                        clean_href = wayback_match.group(1)

                # Build full URL with original domain
                if clean_href.startswith('/'):
                    full_url = f"{base_url}{clean_href}"
                elif clean_href.startswith('http'):
                    full_url = clean_href
                else:
                    full_url = f"{base_url}/{clean_href}"

                recipes.append({
                    'id': recipe_id,
                    'slug': slug,
                    'url': full_url
                })

        # Remove duplicates
        unique_recipes = {r['id']: r for r in recipes}.values()
        logger.info(f"Discovered {len(unique_recipes)} unique recipes")

        # Limit if configured
        max_recipes = self.config['scraper']['max_recipes']
        if max_recipes > 0:
            unique_recipes = list(unique_recipes)[:max_recipes]
            logger.info(f"Limiting to {max_recipes} recipes")

        return list(unique_recipes)

    def _extract_recipe_data(self, soup: BeautifulSoup, recipe_info: Dict) -> Optional[Dict]:
        """Extract all recipe data from the page"""
        try:
            data = {
                'id': recipe_info['id'],
                'slug': recipe_info['slug'],
                'url': recipe_info['url']
            }

            # Recipe name and description
            name_tag = soup.find('h1') or soup.find(class_=re.compile(r'heading|title'))
            data['name'] = name_tag.get_text(strip=True) if name_tag else None

            desc_tag = soup.find('meta', {'name': 'description'})
            data['description'] = desc_tag['content'] if desc_tag else None

            # Difficulty and timing
            data['difficulty'] = self._extract_difficulty(soup)
            data['prep_time'], data['cook_time'], data['total_time'] = self._extract_times(soup)

            # Servings
            servings_match = re.search(r'(\d+)\s*servings?', soup.get_text(), re.IGNORECASE)
            data['servings'] = int(servings_match.group(1)) if servings_match else 2

            # Nutrition
            data['nutrition'] = self._extract_nutrition(soup)

            # External links
            data['hellofresh_url'] = self._extract_hellofresh_link(soup)
            data['pdf_url'] = self._extract_pdf_link(soup)

            # Image
            data['image_url'] = self._extract_image_url(soup)

            # Ingredients
            if self.config['features']['scrape_ingredients']:
                data['ingredients'] = self._extract_ingredients(soup)

            # Instructions
            if self.config['features']['scrape_instructions']:
                data['instructions'] = self._extract_instructions(soup)

            # Tags and allergens
            if self.config['features']['scrape_tags']:
                data['tags'] = self._extract_tags(soup)

            if self.config['features']['scrape_allergens']:
                data['allergens'] = self._extract_allergens(soup)

            return data

        except Exception as e:
            logger.error(f"Error extracting recipe data: {e}")
            return None

    def _extract_difficulty(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract difficulty level"""
        text = soup.get_text().lower()
        if 'easy' in text:
            return 'Easy'
        elif 'medium' in text or 'moderate' in text:
            return 'Medium'
        elif 'hard' in text or 'difficult' in text:
            return 'Hard'
        return None

    def _extract_times(self, soup: BeautifulSoup) -> Tuple[Optional[int], Optional[int], Optional[int]]:
        """Extract prep time, cook time, and total time in minutes"""
        prep_time = cook_time = total_time = None

        # Look for time patterns like "30 min", "1 hour", etc.
        time_pattern = r'(\d+)\s*(min|minute|hour|hr)s?'
        time_matches = re.findall(time_pattern, soup.get_text(), re.IGNORECASE)

        for value, unit in time_matches:
            minutes = int(value)
            if 'hour' in unit.lower() or 'hr' in unit.lower():
                minutes *= 60

            # Heuristic: first time is usually total, second is cook
            if total_time is None:
                total_time = minutes
            elif cook_time is None:
                cook_time = minutes

        return prep_time, cook_time, total_time

    def _extract_nutrition(self, soup: BeautifulSoup) -> Dict:
        """Extract nutrition information"""
        nutrition = {}

        # Common nutrition patterns
        patterns = {
            'calories': r'(\d+)\s*cal',
            'protein': r'(\d+)g?\s*protein',
            'carbs': r'(\d+)g?\s*carb',
            'fat': r'(\d+)g?\s*fat',
        }

        text = soup.get_text().lower()
        for key, pattern in patterns.items():
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                nutrition[key] = int(match.group(1))

        return nutrition

    def _extract_hellofresh_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract link to original HelloFresh recipe"""
        link = soup.find('a', href=re.compile(r'hellofresh\.com/recipes'))
        return link['href'] if link else None

    def _extract_pdf_link(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract PDF recipe card link"""
        link = soup.find('a', href=re.compile(r'\.pdf'))
        return link['href'] if link else None

    def _extract_image_url(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main recipe image URL"""
        # Try og:image first
        og_image = soup.find('meta', property='og:image')
        if og_image:
            return og_image.get('content')

        # Fallback to first large image
        img = soup.find('img', src=re.compile(r'hellofresh'))
        return img['src'] if img else None

    def _extract_ingredients(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract ingredients list"""
        ingredients = []

        # Look for ingredient images and alt text
        img_tags = soup.find_all('img', alt=True, src=re.compile(r'ingredient'))

        for img in img_tags:
            name = img.get('alt', '').strip()
            if name and name not in ['Cooking Oil', 'Salt', 'Black Pepper']:  # These are often already in pantry
                ingredients.append({
                    'name': name,
                    'image_url': img.get('src'),
                    'quantity': None  # Will be extracted from instructions if available
                })

        return ingredients

    def _extract_instructions(self, soup: BeautifulSoup) -> List[Dict]:
        """Extract cooking instructions"""
        instructions = []

        # Look for step images and descriptions
        step_pattern = re.compile(r'step-')
        step_imgs = soup.find_all('img', alt=True, src=step_pattern)

        for idx, img in enumerate(step_imgs, 1):
            title = img.get('alt', f'Step {idx}')
            # Find associated paragraph text
            parent = img.find_parent()
            description = parent.find('p') if parent else None

            instructions.append({
                'step_number': idx,
                'title': title,
                'description': description.get_text(strip=True) if description else '',
                'image_url': img.get('src')
            })

        return instructions

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract recipe tags"""
        tags = []
        # This would need specific parsing based on the site structure
        # For now, extract from common patterns
        text = soup.get_text().lower()

        tag_keywords = ['quick', 'easy', 'healthy', 'vegetarian', 'vegan', 'gluten-free']
        for keyword in tag_keywords:
            if keyword in text:
                tags.append(keyword.title())

        return tags

    def _extract_allergens(self, soup: BeautifulSoup) -> List[str]:
        """Extract allergen information"""
        allergens = []
        text = soup.get_text().lower()

        # Common allergens
        allergen_list = ['milk', 'eggs', 'fish', 'shellfish', 'tree nuts',
                        'peanuts', 'wheat', 'soybeans', 'sesame']

        for allergen in allergen_list:
            if allergen in text:
                allergens.append(allergen.title())

        return allergens

    def _save_recipe(self, data: Dict):
        """Save recipe and related data to database"""
        try:
            cursor = self.db_conn.cursor()

            # Insert recipe
            cursor.execute("""
                INSERT OR REPLACE INTO recipes (
                    id, slug, name, description, difficulty,
                    prep_time, cook_time, total_time, servings,
                    calories, protein, carbs, fat,
                    image_url, hellofresh_url, pdf_url, region
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                data['id'], data['slug'], data['name'], data['description'],
                data['difficulty'], data.get('prep_time'), data.get('cook_time'),
                data.get('total_time'), data.get('servings', 2),
                data['nutrition'].get('calories'), data['nutrition'].get('protein'),
                data['nutrition'].get('carbs'), data['nutrition'].get('fat'),
                data['image_url'], data['hellofresh_url'], data['pdf_url'],
                self.config['scraper']['region']
            ))

            recipe_id = data['id']

            # Insert ingredients
            if 'ingredients' in data:
                for ing in data['ingredients']:
                    cursor.execute("""
                        INSERT INTO ingredients (recipe_id, name, quantity, image_url)
                        VALUES (?, ?, ?, ?)
                    """, (recipe_id, ing['name'], ing.get('quantity'), ing.get('image_url')))

            # Insert instructions
            if 'instructions' in data:
                for inst in data['instructions']:
                    cursor.execute("""
                        INSERT INTO instructions (recipe_id, step_number, title, description, image_url)
                        VALUES (?, ?, ?, ?, ?)
                    """, (recipe_id, inst['step_number'], inst['title'],
                         inst['description'], inst.get('image_url')))

            # Insert tags
            if 'tags' in data:
                for tag in data['tags']:
                    cursor.execute("""
                        INSERT OR IGNORE INTO tags (recipe_id, tag)
                        VALUES (?, ?)
                    """, (recipe_id, tag))

            # Insert allergens
            if 'allergens' in data:
                for allergen in data['allergens']:
                    cursor.execute("""
                        INSERT OR IGNORE INTO allergens (recipe_id, allergen)
                        VALUES (?, ?)
                    """, (recipe_id, allergen))

            self.db_conn.commit()
            self.stats['recipes_scraped'] += 1
            logger.info(f"✓ Saved: {data['name']}")

        except sqlite3.Error as e:
            logger.error(f"Database error saving recipe {data.get('name')}: {e}")
            self.db_conn.rollback()
            self.stats['recipes_failed'] += 1

    def scrape_recipe(self, recipe_info: Dict) -> bool:
        """Scrape a single recipe"""
        # Check if already scraped
        cursor = self.db_conn.cursor()
        cursor.execute("SELECT id FROM recipes WHERE id = ?", (recipe_info['id'],))
        if cursor.fetchone():
            logger.debug(f"Skipping already scraped: {recipe_info['slug']}")
            self.stats['recipes_skipped'] += 1
            return True

        # Fetch and parse
        soup = self._fetch_page(recipe_info['url'])
        if not soup:
            self.stats['recipes_failed'] += 1
            return False

        # Extract data
        data = self._extract_recipe_data(soup, recipe_info)
        if not data:
            self.stats['recipes_failed'] += 1
            return False

        # Save to database
        self._save_recipe(data)
        return True

    def run(self):
        """Main scraper execution"""
        logger.info("=" * 60)
        logger.info("HelloFresh Recipe Scraper Starting")
        logger.info("=" * 60)

        # Initialize database
        self._init_database()

        # Discover recipes
        recipes = self.discover_recipes()
        if not recipes:
            logger.error("No recipes discovered. Exiting.")
            return

        # Scrape each recipe
        logger.info(f"\nScraping {len(recipes)} recipes...")
        for recipe in tqdm(recipes, desc="Scraping recipes"):
            self.scrape_recipe(recipe)
            time.sleep(self.config['scraper']['delay_between_requests'])

        # Print summary
        logger.info("\n" + "=" * 60)
        logger.info("Scraping Complete!")
        logger.info("=" * 60)
        logger.info(f"✓ Recipes scraped: {self.stats['recipes_scraped']}")
        logger.info(f"⊘ Recipes skipped: {self.stats['recipes_skipped']}")
        logger.info(f"✗ Recipes failed:  {self.stats['recipes_failed']}")
        logger.info(f"Database: {self.config['database']['path']}")

    def close(self):
        """Clean up resources"""
        if self.db_conn:
            self.db_conn.close()
        self.session.close()


def main():
    parser = argparse.ArgumentParser(description='Scrape HelloFresh recipes from Wayback Machine')
    parser.add_argument('--config', default='config.yaml', help='Path to config file')
    parser.add_argument('--region', help='Override region (e.g., en-US)')
    parser.add_argument('--max-recipes', type=int, help='Override max recipes to scrape')
    args = parser.parse_args()

    scraper = RecipeScraper(args.config)

    # Override config with CLI args
    if args.region:
        scraper.config['scraper']['region'] = args.region
    if args.max_recipes:
        scraper.config['scraper']['max_recipes'] = args.max_recipes

    try:
        scraper.run()
    except KeyboardInterrupt:
        logger.warning("\n\nScraping interrupted by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
    finally:
        scraper.close()


if __name__ == '__main__':
    main()
