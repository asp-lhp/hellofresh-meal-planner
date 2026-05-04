"""
Pytest fixtures for Meal Planner tests.
"""

import pytest
import sqlite3
import tempfile
import os
import sys
from pathlib import Path

# Add project paths
sys.path.insert(0, str(Path(__file__).parent.parent / 'web'))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scraper'))


@pytest.fixture
def test_db():
    """Create a temporary test database with schema."""
    # Create temp file
    fd, db_path = tempfile.mkstemp(suffix='.db')
    os.close(fd)

    # Load schema
    schema_path = Path(__file__).parent.parent / 'database' / 'schema.sql'
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row

    with open(schema_path, 'r') as f:
        schema = f.read()
        conn.executescript(schema)

    conn.commit()

    yield db_path

    # Cleanup
    conn.close()
    os.unlink(db_path)


@pytest.fixture
def test_db_with_data(test_db):
    """Test database with sample recipe data."""
    conn = sqlite3.connect(test_db)
    conn.row_factory = sqlite3.Row

    # Insert sample recipe
    conn.execute("""
        INSERT INTO recipes (id, slug, name, description, prep_time, cook_time,
                           total_time, servings, calories, protein, difficulty)
        VALUES (1, 'test-recipe', 'Test Recipe', 'A test recipe description',
                10, 20, 30, 4, 500, 25, 'easy')
    """)

    # Insert ingredients
    conn.execute("""
        INSERT INTO ingredients (recipe_id, name, quantity)
        VALUES (1, 'Chicken breast', '2 lbs')
    """)
    conn.execute("""
        INSERT INTO ingredients (recipe_id, name, quantity)
        VALUES (1, 'Olive oil', '2 tbsp')
    """)

    # Insert instructions
    conn.execute("""
        INSERT INTO instructions (recipe_id, step_number, description)
        VALUES (1, 1, 'Preheat oven to 375F')
    """)
    conn.execute("""
        INSERT INTO instructions (recipe_id, step_number, description)
        VALUES (1, 2, 'Season chicken and bake for 25 minutes')
    """)

    # Insert tags
    conn.execute("INSERT INTO tags (recipe_id, tag) VALUES (1, 'Easy')")
    conn.execute("INSERT INTO tags (recipe_id, tag) VALUES (1, 'Chicken')")

    conn.commit()
    conn.close()

    yield test_db


@pytest.fixture
def flask_app(test_db_with_data):
    """Create Flask test client."""
    # Set environment before importing app
    os.environ['DATABASE_PATH'] = test_db_with_data
    os.environ['API_BASE_URL'] = 'http://localhost:5098/api'

    from app import app
    app.config['TESTING'] = True
    app.config['DATABASE_PATH'] = test_db_with_data

    with app.test_client() as client:
        yield client


@pytest.fixture
def sample_recipe_data():
    """Sample recipe data for import tests."""
    return {
        'name': 'Sample Test Recipe',
        'description': 'A delicious test recipe',
        'url': 'https://example.com/recipe/test',
        'prep_time': 15,
        'cook_time': 30,
        'total_time': 45,
        'servings': 4,
        'calories': 450,
        'protein': 30,
        'carbs': 40,
        'fat': 15,
        'ingredients': ['2 cups rice', '1 lb chicken', '2 tbsp soy sauce'],
        'instructions': ['Cook rice', 'Grill chicken', 'Combine and serve']
    }
