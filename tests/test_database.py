"""
Database operation tests for Meal Planner.
"""

import pytest
import sqlite3


class TestDatabaseSchema:
    """Test database schema and structure."""

    def test_recipes_table_exists(self, test_db):
        """Verify recipes table exists with expected columns."""
        conn = sqlite3.connect(test_db)
        cursor = conn.execute("PRAGMA table_info(recipes)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        expected = {'id', 'slug', 'name', 'description', 'prep_time',
                   'cook_time', 'total_time', 'servings', 'calories',
                   'protein', 'carbs', 'fat', 'difficulty', 'image_url',
                   'marked_for_deletion', 'marked_at'}
        assert expected.issubset(columns)

    def test_ingredients_table_exists(self, test_db):
        """Verify ingredients table exists."""
        conn = sqlite3.connect(test_db)
        cursor = conn.execute("PRAGMA table_info(ingredients)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'recipe_id' in columns
        assert 'name' in columns

    def test_tags_table_exists(self, test_db):
        """Verify tags table exists."""
        conn = sqlite3.connect(test_db)
        cursor = conn.execute("PRAGMA table_info(tags)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'recipe_id' in columns
        assert 'tag' in columns

    def test_meal_plans_table_exists(self, test_db):
        """Verify meal_plans table exists."""
        conn = sqlite3.connect(test_db)
        cursor = conn.execute("PRAGMA table_info(meal_plans)")
        columns = {row[1] for row in cursor.fetchall()}
        conn.close()

        assert 'id' in columns
        assert 'name' in columns
        assert 'start_date' in columns
        assert 'end_date' in columns


class TestDatabaseOperations:
    """Test database CRUD operations."""

    def test_insert_recipe(self, test_db):
        """Test inserting a new recipe."""
        conn = sqlite3.connect(test_db)
        conn.execute("""
            INSERT INTO recipes (id, slug, name, difficulty)
            VALUES (999, 'new-recipe', 'New Recipe', 'medium')
        """)
        conn.commit()

        result = conn.execute("SELECT * FROM recipes WHERE id = 999").fetchone()
        conn.close()

        assert result is not None
        assert result[2] == 'New Recipe'

    def test_soft_delete_recipe(self, test_db_with_data):
        """Test soft delete functionality."""
        conn = sqlite3.connect(test_db_with_data)

        # Mark recipe for deletion
        conn.execute("""
            UPDATE recipes
            SET marked_for_deletion = 1, marked_at = CURRENT_TIMESTAMP
            WHERE id = 1
        """)
        conn.commit()

        # Verify it's marked
        result = conn.execute("""
            SELECT marked_for_deletion FROM recipes WHERE id = 1
        """).fetchone()
        conn.close()

        assert result[0] == 1

    def test_recipe_with_ingredients(self, test_db_with_data):
        """Test recipe-ingredient relationship."""
        conn = sqlite3.connect(test_db_with_data)
        conn.row_factory = sqlite3.Row

        ingredients = conn.execute("""
            SELECT name FROM ingredients WHERE recipe_id = 1
        """).fetchall()
        conn.close()

        assert len(ingredients) == 2
        ingredient_names = [i['name'] for i in ingredients]
        assert 'Chicken breast' in ingredient_names

    def test_recipe_with_tags(self, test_db_with_data):
        """Test recipe-tag relationship."""
        conn = sqlite3.connect(test_db_with_data)
        conn.row_factory = sqlite3.Row

        tags = conn.execute("""
            SELECT tag FROM tags WHERE recipe_id = 1
        """).fetchall()
        conn.close()

        assert len(tags) == 2
        tag_names = [t['tag'] for t in tags]
        assert 'Easy' in tag_names
        assert 'Chicken' in tag_names
