#!/usr/bin/env python3
"""
TheMealDB API Importer
Import recipes from TheMealDB public API (free, no key required)
"""

import sys
import sqlite3
import requests
import logging
from pathlib import Path
from typing import Optional, Dict, List
import time

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class MealDBImporter:
    """Import recipes from TheMealDB API"""

    def __init__(self, db_path: str = "../database/recipes.db"):
        self.db_path = db_path
        self.db_conn = None
        self.base_url = "https://www.themealdb.com/api/json/v1/1"

    def connect_db(self):
        """Connect to SQLite database"""
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row

    def close_db(self):
        """Close database connection"""
        if self.db_conn:
            self.db_conn.close()

    def fetch_recipes_by_letter(self, letter: str) -> List[Dict]:
        """Fetch all recipes starting with a letter"""
        url = f"{self.base_url}/search.php?f={letter}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        return data.get('meals', []) or []

    def fetch_all_recipes(self, limit: Optional[int] = None) -> List[Dict]:
        """Fetch recipes from all letters A-Z"""
        all_meals = []
        letters = 'abcdefghijklmnopqrstuvwxyz'

        for letter in letters:
            logger.info(f"Fetching recipes starting with '{letter.upper()}'...")
            try:
                meals = self.fetch_recipes_by_letter(letter)
                all_meals.extend(meals)
                logger.info(f"  Found {len(meals)} recipes")

                if limit and len(all_meals) >= limit:
                    all_meals = all_meals[:limit]
                    break

                # Be nice to the API
                time.sleep(0.5)
            except Exception as e:
                logger.error(f"  Error fetching letter {letter}: {e}")
                continue

        return all_meals

    def extract_ingredients(self, meal: Dict) -> List[tuple]:
        """Extract ingredients from meal data"""
        ingredients = []
        for i in range(1, 21):  # TheMealDB has up to 20 ingredients
            ingredient = meal.get(f'strIngredient{i}')
            measure = meal.get(f'strMeasure{i}')

            if ingredient and ingredient.strip():
                quantity = measure.strip() if measure else ""
                ingredients.append((ingredient.strip(), quantity))

        return ingredients

    def extract_instructions(self, meal: Dict) -> List[str]:
        """Extract step-by-step instructions from meal data"""
        instructions_text = meal.get('strInstructions', '')

        # Split by newlines and numbered steps
        steps = []
        for line in instructions_text.split('\n'):
            line = line.strip()
            if line and len(line) > 3:  # Skip empty or very short lines
                # Remove step numbers if present (e.g., "1.", "STEP 1", etc.)
                line = line.lstrip('0123456789.)-STEP ')
                if line:
                    steps.append(line)

        return steps

    def import_meal(self, meal: Dict, region: str = "mealdb") -> bool:
        """Import a single meal into the database"""
        try:
            # Generate unique ID from meal ID
            meal_id = int(meal['idMeal'])

            # Extract data
            name = meal.get('strMeal', 'Unknown Recipe')
            description = meal.get('strInstructions', '')[:200] if meal.get('strInstructions') else None
            category = meal.get('strCategory')
            area = meal.get('strArea')
            image_url = meal.get('strMealThumb')
            youtube_url = meal.get('strYouTube')
            source_url = meal.get('strSource')

            # Insert recipe
            cursor = self.db_conn.cursor()
            cursor.execute("""
                INSERT OR IGNORE INTO recipes
                (id, slug, name, description, image_url, servings, region, hellofresh_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                meal_id,
                meal.get('strMeal', '').lower().replace(' ', '-'),
                name,
                description,
                image_url,
                4,  # Default servings
                region,
                source_url or f"https://www.themealdb.com/meal/{meal_id}"
            ))

            if cursor.rowcount == 0:
                logger.debug(f"  Recipe '{name}' already exists, skipping")
                return False

            # Insert ingredients
            ingredients = self.extract_ingredients(meal)
            for idx, (ingredient, quantity) in enumerate(ingredients, 1):
                cursor.execute("""
                    INSERT INTO ingredients (recipe_id, name, quantity)
                    VALUES (?, ?, ?)
                """, (meal_id, ingredient, quantity))

            # Insert instructions
            instructions = self.extract_instructions(meal)
            for step_num, instruction in enumerate(instructions, 1):
                cursor.execute("""
                    INSERT INTO instructions (recipe_id, step_number, description)
                    VALUES (?, ?, ?)
                """, (meal_id, step_num, instruction))

            # Insert tags
            if category:
                cursor.execute("""
                    INSERT INTO tags (recipe_id, tag)
                    VALUES (?, ?)
                """, (meal_id, category.lower()))

            if area:
                cursor.execute("""
                    INSERT INTO tags (recipe_id, tag)
                    VALUES (?, ?)
                """, (meal_id, area.lower()))

            self.db_conn.commit()
            logger.info(f"✓ Imported: {name}")
            logger.info(f"  - {len(ingredients)} ingredients")
            logger.info(f"  - {len(instructions)} steps")
            return True

        except Exception as e:
            logger.error(f"Error importing meal '{meal.get('strMeal', 'unknown')}': {e}")
            self.db_conn.rollback()
            return False

    def import_all(self, limit: Optional[int] = None):
        """Import all available recipes from TheMealDB"""
        logger.info("Fetching recipes from TheMealDB API...")
        meals = self.fetch_all_recipes(limit=limit)

        logger.info(f"\nImporting {len(meals)} recipes...")

        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, meal in enumerate(meals, 1):
            logger.info(f"\n[{idx}/{len(meals)}] Processing: {meal.get('strMeal', 'Unknown')}")

            try:
                if self.import_meal(meal):
                    success_count += 1
                else:
                    skip_count += 1
            except Exception as e:
                logger.error(f"Failed to import: {e}")
                error_count += 1

        logger.info("\n" + "="*60)
        logger.info("Import Complete!")
        logger.info("="*60)
        logger.info(f"✓ Success:  {success_count}")
        logger.info(f"⊘ Skipped:  {skip_count} (already exist)")
        logger.info(f"✗ Failed:   {error_count}")
        logger.info(f"Total:      {len(meals)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Import recipes from TheMealDB API')
    parser.add_argument('--limit', type=int, help='Maximum number of recipes to import')
    parser.add_argument('--db', default='../database/recipes.db', help='Database path')

    args = parser.parse_args()

    importer = MealDBImporter(db_path=args.db)

    try:
        importer.connect_db()
        importer.import_all(limit=args.limit)
    finally:
        importer.close_db()


if __name__ == '__main__':
    main()
