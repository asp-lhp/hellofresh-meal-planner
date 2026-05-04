#!/usr/bin/env python3
"""
Fetch ingredient quantities from HelloFresh recipes
"""

import sqlite3
import json
import sys
from pathlib import Path
import requests
from recipe_scrapers import scrape_html

DB_PATH = Path(__file__).parent.parent / "database" / "recipes.db"


def get_recipe_ingredients(url):
    """Fetch and parse ingredient quantities from HelloFresh URL"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        }
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()

        scraper = scrape_html(html=response.content, org_url=url)
        ingredients = scraper.ingredients()

        return ingredients
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return []


def get_meal_plan_recipes(meal_plan_id):
    """Get all recipes in a meal plan with their HelloFresh URLs"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    recipes = conn.execute("""
        SELECT DISTINCT r.id, r.name, r.hellofresh_url
        FROM meal_plan_recipes mpr
        JOIN recipes r ON mpr.recipe_id = r.id
        WHERE mpr.meal_plan_id = ?
        AND r.hellofresh_url IS NOT NULL
    """, (meal_plan_id,)).fetchall()

    conn.close()
    return recipes


def aggregate_ingredients(meal_plan_id):
    """Aggregate all ingredients with their quantities for a meal plan"""
    recipes = get_meal_plan_recipes(meal_plan_id)

    all_ingredients = {}

    for recipe in recipes:
        print(f"\nFetching: {recipe['name']}...")
        ingredients_list = get_recipe_ingredients(recipe['hellofresh_url'])

        if not ingredients_list:
            print(f"  ⚠️  No ingredients found")
            continue

        print(f"  ✓ Found {len(ingredients_list)} ingredients")

        for ing in ingredients_list:
            # Parse ingredient string (e.g., "2 cups diced carrots")
            # Store in a structured way
            ingredient_key = ing.lower().strip()

            if ingredient_key not in all_ingredients:
                all_ingredients[ingredient_key] = {
                    'original': ing,
                    'recipes': []
                }

            all_ingredients[ingredient_key]['recipes'].append(recipe['name'])

    return all_ingredients


if __name__ == "__main__":
    meal_plan_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    print(f"📋 Fetching ingredients for Meal Plan #{meal_plan_id}...")
    print("=" * 60)

    ingredients = aggregate_ingredients(meal_plan_id)

    print(f"\n\n📊 Summary: {len(ingredients)} unique ingredients")
    print("=" * 60)

    # Output as JSON
    output = {
        'meal_plan_id': meal_plan_id,
        'ingredients': ingredients
    }

    output_file = Path(__file__).parent.parent / "web" / f"ingredients_meal_plan_{meal_plan_id}.json"
    with open(output_file, 'w') as f:
        json.dump(output, f, indent=2)

    print(f"\n✓ Saved to: {output_file}")

    # Print some examples
    print("\n📝 Sample ingredients:")
    for i, (key, data) in enumerate(list(ingredients.items())[:10]):
        print(f"  • {data['original']}")
        if i >= 9:
            break
