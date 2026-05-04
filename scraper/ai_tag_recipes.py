#!/usr/bin/env python3
"""
AI-Powered Recipe Tagging System
Uses Claude API to analyze recipes and suggest appropriate tags
"""

import os
import sys
import sqlite3
import json
import anthropic
from pathlib import Path
from tag_categories import get_tag_prompt, ALL_TAGS, TAG_CATEGORIES

# Database path
DB_PATH = Path(__file__).parent.parent / "database" / "recipes.db"

# Anthropic API key from environment
API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not API_KEY:
    print("❌ Error: ANTHROPIC_API_KEY environment variable not set")
    print("   Get your API key from: https://console.anthropic.com/")
    sys.exit(1)

client = anthropic.Anthropic(api_key=API_KEY)


class RecipeTagger:
    def __init__(self, db_path: str):
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

    def get_recipe_details(self, recipe_id: int):
        """Fetch full recipe details"""
        cursor = self.db_conn.cursor()

        # Get recipe
        recipe = cursor.execute("""
            SELECT id, name, description, prep_time, total_time, protein, carbs
            FROM recipes WHERE id = ?
        """, (recipe_id,)).fetchone()

        if not recipe:
            return None

        # Get ingredients
        ingredients = cursor.execute("""
            SELECT name, quantity FROM ingredients WHERE recipe_id = ?
        """, (recipe_id,)).fetchall()

        # Get instructions
        instructions = cursor.execute("""
            SELECT description FROM instructions
            WHERE recipe_id = ?
            ORDER BY step_number
        """, (recipe_id,)).fetchall()

        return {
            'id': recipe['id'],
            'name': recipe['name'],
            'description': recipe['description'] or '',
            'prep_time': recipe['prep_time'],
            'total_time': recipe['total_time'],
            'protein': recipe['protein'],
            'carbs': recipe['carbs'],
            'ingredients': [f"{i['quantity']} {i['name']}" if i['quantity'] else i['name']
                          for i in ingredients],
            'instructions': ' '.join([i['description'] for i in instructions])
        }

    def suggest_tags(self, recipe: dict) -> list:
        """Use Claude to suggest tags for a recipe"""
        prompt = get_tag_prompt(
            recipe_name=recipe['name'],
            ingredients=recipe['ingredients'],
            instructions=recipe['instructions'],
            prep_time=recipe['prep_time'],
            total_time=recipe['total_time'],
            protein=recipe['protein'],
            carbs=recipe['carbs']
        )

        try:
            message = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = message.content[0].text.strip()

            # Try to parse JSON
            try:
                suggested_tags = json.loads(response_text)
            except json.JSONDecodeError:
                # Sometimes Claude adds extra text, try to extract JSON
                import re
                json_match = re.search(r'\[.*\]', response_text, re.DOTALL)
                if json_match:
                    suggested_tags = json.loads(json_match.group())
                else:
                    print(f"  ⚠️  Could not parse JSON from response: {response_text}")
                    return []

            # Validate tags
            valid_tags = [tag for tag in suggested_tags if tag in ALL_TAGS]

            return valid_tags

        except Exception as e:
            print(f"  ❌ Error calling Claude API: {e}")
            return []

    def get_existing_tags(self, recipe_id: int) -> list:
        """Get current tags for a recipe"""
        cursor = self.db_conn.cursor()
        tags = cursor.execute("""
            SELECT tag FROM tags WHERE recipe_id = ?
        """, (recipe_id,)).fetchall()
        return [tag['tag'] for tag in tags]

    def save_tags(self, recipe_id: int, tags: list):
        """Save tags to database (replace existing)"""
        cursor = self.db_conn.cursor()

        # Delete existing tags
        cursor.execute("DELETE FROM tags WHERE recipe_id = ?", (recipe_id,))

        # Insert new tags
        for tag in tags:
            cursor.execute("""
                INSERT INTO tags (recipe_id, tag) VALUES (?, ?)
            """, (recipe_id, tag))

        self.db_conn.commit()

    def tag_recipe_interactive(self, recipe_id: int):
        """Tag a single recipe with user review"""
        recipe = self.get_recipe_details(recipe_id)
        if not recipe:
            print(f"❌ Recipe {recipe_id} not found")
            return

        print(f"\n{'='*60}")
        print(f"Recipe: {recipe['name']}")
        print(f"{'='*60}")

        # Show recipe info
        print(f"\nIngredients ({len(recipe['ingredients'])}):")
        for ing in recipe['ingredients'][:5]:
            print(f"  - {ing}")
        if len(recipe['ingredients']) > 5:
            print(f"  ... and {len(recipe['ingredients']) - 5} more")

        print(f"\nTiming: Prep {recipe['prep_time']}min | Total {recipe['total_time']}min")
        print(f"Nutrition: Protein {recipe['protein']}g | Carbs {recipe['carbs']}g")

        # Get existing tags
        existing_tags = self.get_existing_tags(recipe_id)
        if existing_tags:
            print(f"\nCurrent tags: {', '.join(existing_tags)}")

        # Get AI suggestions
        print("\n🤖 Analyzing with Claude...")
        suggested_tags = self.suggest_tags(recipe)

        if not suggested_tags:
            print("⚠️  No tags suggested")
            return

        print(f"\n✨ Suggested tags: {', '.join(suggested_tags)}")

        # User review
        print("\nOptions:")
        print("  [a] Approve all")
        print("  [e] Edit (comma-separated)")
        print("  [s] Skip")
        choice = input("\nYour choice: ").strip().lower()

        if choice == 'a':
            self.save_tags(recipe_id, suggested_tags)
            print("✓ Tags saved!")
        elif choice == 'e':
            print(f"\nAvailable tags:\n{', '.join(ALL_TAGS)}")
            custom_tags = input("\nEnter tags (comma-separated): ").strip()
            if custom_tags:
                tags = [t.strip() for t in custom_tags.split(',')]
                # Validate
                valid_tags = [t for t in tags if t in ALL_TAGS]
                if valid_tags:
                    self.save_tags(recipe_id, valid_tags)
                    print("✓ Custom tags saved!")
                else:
                    print("❌ No valid tags entered")
        elif choice == 's':
            print("⊘ Skipped")
        else:
            print("❌ Invalid choice")

    def tag_all_recipes_batch(self, limit: int = None, auto_approve: bool = False):
        """Tag all recipes automatically"""
        cursor = self.db_conn.cursor()

        # Get all recipes
        query = """
            SELECT id, name
            FROM recipes
            WHERE marked_for_deletion = 0 OR marked_for_deletion IS NULL
            ORDER BY id
        """
        if limit:
            query += f" LIMIT {limit}"

        recipes = cursor.execute(query).fetchall()

        print(f"\n🏷️  Tagging {len(recipes)} recipes...")
        print(f"Auto-approve: {'YES' if auto_approve else 'NO (interactive)'}\n")

        success_count = 0
        skip_count = 0
        error_count = 0

        for idx, recipe_row in enumerate(recipes, 1):
            recipe_id = recipe_row['id']
            recipe_name = recipe_row['name']

            print(f"\n[{idx}/{len(recipes)}] {recipe_name}")

            if auto_approve:
                # Auto mode
                recipe = self.get_recipe_details(recipe_id)
                suggested_tags = self.suggest_tags(recipe)

                if suggested_tags:
                    self.save_tags(recipe_id, suggested_tags)
                    print(f"  ✓ Tagged: {', '.join(suggested_tags)}")
                    success_count += 1
                else:
                    print("  ⊘ No tags suggested")
                    skip_count += 1
            else:
                # Interactive mode
                try:
                    self.tag_recipe_interactive(recipe_id)
                    success_count += 1
                except KeyboardInterrupt:
                    print("\n\n⚠️  Interrupted by user")
                    break
                except Exception as e:
                    print(f"  ❌ Error: {e}")
                    error_count += 1

        print(f"\n{'='*60}")
        print("Tagging Complete!")
        print(f"{'='*60}")
        print(f"✓ Success: {success_count}")
        print(f"⊘ Skipped: {skip_count}")
        print(f"✗ Failed:  {error_count}")
        print(f"Total:     {len(recipes)}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='AI-powered recipe tagging')
    parser.add_argument('--recipe-id', type=int, help='Tag a specific recipe')
    parser.add_argument('--batch', action='store_true', help='Tag all recipes')
    parser.add_argument('--auto', action='store_true', help='Auto-approve all suggestions')
    parser.add_argument('--limit', type=int, help='Limit number of recipes to process')

    args = parser.parse_args()

    tagger = RecipeTagger(db_path=DB_PATH)

    try:
        tagger.connect_db()

        if args.recipe_id:
            # Tag single recipe
            tagger.tag_recipe_interactive(args.recipe_id)
        elif args.batch:
            # Tag all recipes
            tagger.tag_all_recipes_batch(limit=args.limit, auto_approve=args.auto)
        else:
            print("Usage:")
            print("  python ai_tag_recipes.py --recipe-id 692")
            print("  python ai_tag_recipes.py --batch --limit 10")
            print("  python ai_tag_recipes.py --batch --auto")

    finally:
        tagger.close_db()


if __name__ == '__main__':
    main()
