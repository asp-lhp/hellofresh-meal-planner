#!/usr/bin/env python3
"""
Generate realistic ingredient quantities using AI based on recipe names and standard servings
"""

import sqlite3
import json
from pathlib import Path
import os
from anthropic import Anthropic

DB_PATH = Path(__file__).parent.parent / "database" / "recipes.db"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")


def get_meal_plan_ingredients(meal_plan_id):
    """Get all unique ingredients from a meal plan with recipe context"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    results = conn.execute("""
        SELECT
            i.name as ingredient_name,
            GROUP_CONCAT(DISTINCT r.name) as recipe_names,
            COUNT(DISTINCT r.id) as recipe_count,
            MAX(mpr.servings) as servings
        FROM meal_plan_recipes mpr
        JOIN recipes r ON mpr.recipe_id = r.id
        JOIN ingredients i ON r.id = i.recipe_id
        WHERE mpr.meal_plan_id = ?
        GROUP BY i.name
        ORDER BY i.name
    """, (meal_plan_id,)).fetchall()

    conn.close()
    return [dict(row) for row in results]


def generate_quantities_with_ai(ingredients):
    """Use Claude to generate realistic quantities for ingredients"""
    client = Anthropic(api_key=ANTHROPIC_API_KEY)

    ingredient_list = []
    for ing in ingredients:
        ingredient_list.append({
            'name': ing['ingredient_name'],
            'used_in': ing['recipe_names'].split(','),
            'recipe_count': ing['recipe_count'],
            'servings_per_recipe': ing['servings']
        })

    prompt = f"""You are a grocery shopping assistant. Given this list of ingredients and the recipes they're used in, provide realistic shopping quantities.

For each ingredient, determine:
1. The standard package size you'd buy at a grocery store
2. The total amount needed across all recipes
3. A practical "buy this" recommendation

Ingredients:
{json.dumps(ingredient_list, indent=2)}

For each ingredient, respond with JSON in this exact format:
{{
  "ingredient_name": "the ingredient name",
  "quantity_needed": "total amount needed (e.g., '3 cloves', '2 cups', '1 lb')",
  "package_to_buy": "what to actually buy (e.g., '1 bulb of garlic', '1 bag (2 lb) carrots', '1 bottle (12 oz)')",
  "notes": "any helpful shopping notes"
}}

Return a JSON array of all ingredients. Be specific and practical for grocery shopping."""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4000,
        messages=[{"role": "user", "content": prompt}]
    )

    # Parse the response
    response_text = message.content[0].text

    # Extract JSON from response (it might be wrapped in markdown code blocks)
    if "```json" in response_text:
        response_text = response_text.split("```json")[1].split("```")[0].strip()
    elif "```" in response_text:
        response_text = response_text.split("```")[1].split("```")[0].strip()

    return json.loads(response_text)


if __name__ == "__main__":
    import sys
    meal_plan_id = int(sys.argv[1]) if len(sys.argv) > 1 else 1

    print(f"📋 Generating quantities for Meal Plan #{meal_plan_id}...")
    print("=" * 60)

    # Get ingredients
    ingredients = get_meal_plan_ingredients(meal_plan_id)
    print(f"\n✓ Found {len(ingredients)} unique ingredients")

    # Generate quantities with AI
    print("\n🤖 Using AI to generate realistic quantities...")
    quantities = generate_quantities_with_ai(ingredients)

    print(f"\n✓ Generated quantities for {len(quantities)} ingredients")

    # Save to file
    output_file = Path(__file__).parent.parent / "web" / f"ingredients_with_quantities_{meal_plan_id}.json"
    with open(output_file, 'w') as f:
        json.dump(quantities, f, indent=2)

    print(f"\n✓ Saved to: {output_file}")

    # Print sample
    print("\n📝 Sample quantities:")
    for ing in quantities[:5]:
        print(f"  • {ing['ingredient_name']}: {ing['package_to_buy']}")
        print(f"     └─ Needed: {ing['quantity_needed']}")
