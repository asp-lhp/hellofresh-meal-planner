#!/usr/bin/env python3
"""
Flask Web App for Meal Planner
Displays recipes with HelloFresh-style cards, print-friendly
"""

from flask import Flask, render_template, abort, redirect, url_for, request, jsonify
import sqlite3
from pathlib import Path
import httpx
import os
import sys
import logging
from functools import wraps
from time import sleep

# Add scraper directory to path for tag imports
sys.path.append(str(Path(__file__).parent.parent / "scraper"))

app = Flask(__name__)

# Import auth early - needed for @login_required decorator
from auth import init_auth, login_required
from flask_login import current_user

# ============================================================================
# AUTH CONFIGURATION
# ============================================================================

# Google OAuth credentials
app.config['GOOGLE_CLIENT_ID'] = os.getenv('GOOGLE_CLIENT_ID')
app.config['GOOGLE_CLIENT_SECRET'] = os.getenv('GOOGLE_CLIENT_SECRET')
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database path (configurable for deployment)
DB_PATH = Path(os.getenv("DATABASE_PATH", Path(__file__).parent.parent / "database" / "recipes.db"))

# .NET API base URL (configure via environment variable for deployment)
API_BASE_URL = os.getenv("API_BASE_URL", "http://localhost:5098/api")

# Anthropic API key (required for AI features)
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_API_KEY:
    print("WARNING: ANTHROPIC_API_KEY not set. AI features will be disabled.")

# API request configuration
API_TIMEOUT = 30.0  # seconds
API_MAX_RETRIES = 3
API_RETRY_DELAY = 1.0  # seconds


class APIError(Exception):
    """Custom exception for API errors with user-friendly messages."""
    def __init__(self, message, status_code=500, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


def api_request(method, endpoint, json=None, retries=API_MAX_RETRIES):
    """
    Make an API request with retry logic, timeouts, and error handling.

    Args:
        method: HTTP method ('get', 'post', 'put', 'delete')
        endpoint: API endpoint (will be appended to API_BASE_URL)
        json: JSON body for POST/PUT requests
        retries: Number of retry attempts

    Returns:
        Response object on success

    Raises:
        APIError: On failure after all retries
    """
    url = f"{API_BASE_URL}/{endpoint.lstrip('/')}"
    last_error = None

    for attempt in range(retries):
        try:
            with httpx.Client(timeout=API_TIMEOUT) as client:
                if method.lower() == 'get':
                    response = client.get(url)
                elif method.lower() == 'post':
                    response = client.post(url, json=json)
                elif method.lower() == 'put':
                    response = client.put(url, json=json)
                elif method.lower() == 'delete':
                    response = client.delete(url)
                else:
                    raise ValueError(f"Unsupported HTTP method: {method}")

                # Log successful requests
                logger.debug(f"API {method.upper()} {endpoint} -> {response.status_code}")

                return response

        except httpx.ConnectError as e:
            last_error = e
            logger.warning(f"API connection failed (attempt {attempt + 1}/{retries}): {url}")
            if attempt < retries - 1:
                sleep(API_RETRY_DELAY * (attempt + 1))  # Exponential backoff

        except httpx.TimeoutException as e:
            last_error = e
            logger.warning(f"API timeout (attempt {attempt + 1}/{retries}): {url}")
            if attempt < retries - 1:
                sleep(API_RETRY_DELAY * (attempt + 1))

        except httpx.HTTPError as e:
            last_error = e
            logger.error(f"API HTTP error: {e}")
            raise APIError(
                "Unable to communicate with the server. Please try again later.",
                status_code=503,
                details=str(e)
            )

    # All retries exhausted
    logger.error(f"API request failed after {retries} attempts: {url}")
    raise APIError(
        "The meal planning service is temporarily unavailable. Please try again in a few minutes.",
        status_code=503,
        details=str(last_error)
    )


def api_get(endpoint):
    """GET request to API."""
    return api_request('get', endpoint)


def api_post(endpoint, json=None):
    """POST request to API."""
    return api_request('post', endpoint, json=json)


def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def enrich_recipes_with_tags(conn, recipes_raw):
    """
    Add tags to a list of recipe rows.

    Args:
        conn: Database connection
        recipes_raw: List of recipe rows from database

    Returns:
        List of recipe dicts with 'tags' key added
    """
    if not recipes_raw:
        return []

    # Batch fetch all tags for efficiency
    recipe_ids = [r['id'] for r in recipes_raw]
    placeholders = ','.join(['?'] * len(recipe_ids))

    tags_rows = conn.execute(f"""
        SELECT recipe_id, tag FROM tags WHERE recipe_id IN ({placeholders})
    """, recipe_ids).fetchall()

    # Group tags by recipe_id
    tags_by_recipe = {}
    for row in tags_rows:
        recipe_id = row['recipe_id']
        if recipe_id not in tags_by_recipe:
            tags_by_recipe[recipe_id] = []
        tags_by_recipe[recipe_id].append(row['tag'])

    # Build enriched recipe list
    recipes = []
    for recipe in recipes_raw:
        recipe_dict = dict(recipe)
        recipe_dict['tags'] = tags_by_recipe.get(recipe['id'], [])
        recipes.append(recipe_dict)

    return recipes


@app.route('/')
def index():
    """Homepage - show all recipes in grid (exclude deleted)"""
    conn = get_db()

    recipes_raw = conn.execute("""
        SELECT id, slug, name, description, image_url,
               prep_time, cook_time, total_time, servings,
               calories, difficulty, protein
        FROM recipes
        WHERE marked_for_deletion = 0 OR marked_for_deletion IS NULL
        ORDER BY created_at DESC
    """).fetchall()

    recipes = enrich_recipes_with_tags(conn, recipes_raw)
    conn.close()

    return render_template('index.html', recipes=recipes)


@app.route('/recipe/<int:recipe_id>')
def recipe_detail(recipe_id):
    """Single recipe card - HelloFresh style, print-friendly"""
    conn = get_db()

    # Get recipe
    recipe = conn.execute("""
        SELECT * FROM recipes WHERE id = ?
    """, (recipe_id,)).fetchone()

    if not recipe:
        abort(404)

    # Get ingredients
    ingredients = conn.execute("""
        SELECT name, quantity, image_url
        FROM ingredients
        WHERE recipe_id = ?
    """, (recipe_id,)).fetchall()

    # Get instructions
    instructions = conn.execute("""
        SELECT step_number, description, image_url
        FROM instructions
        WHERE recipe_id = ?
        ORDER BY step_number
    """, (recipe_id,)).fetchall()

    # Get tags
    tags = conn.execute("""
        SELECT tag FROM tags WHERE recipe_id = ?
    """, (recipe_id,)).fetchall()

    # Get allergens
    allergens = conn.execute("""
        SELECT allergen FROM allergens WHERE recipe_id = ?
    """, (recipe_id,)).fetchall()

    conn.close()

    return render_template('recipe.html',
                         recipe=recipe,
                         ingredients=ingredients,
                         instructions=instructions,
                         tags=tags,
                         allergens=allergens)


@app.route('/search')
def search():
    """Search recipes by ingredient or name"""
    conn = get_db()

    # Get search parameters
    query = request.args.get('q', '').strip()
    difficulty = request.args.get('difficulty', '').strip()
    max_time = request.args.get('max_time', type=int)

    # Build SQL query
    sql = """
        SELECT DISTINCT r.id, r.slug, r.name, r.description, r.image_url,
               r.prep_time, r.cook_time, r.total_time, r.servings,
               r.calories, r.difficulty, r.protein
        FROM recipes r
        LEFT JOIN ingredients i ON r.id = i.recipe_id
        WHERE (r.marked_for_deletion = 0 OR r.marked_for_deletion IS NULL)
    """
    params = []

    # Search by name or ingredient
    if query:
        sql += " AND (r.name LIKE ? OR i.name LIKE ?)"
        params.extend([f'%{query}%', f'%{query}%'])

    # Filter by difficulty
    if difficulty:
        sql += " AND r.difficulty = ?"
        params.append(difficulty)

    # Filter by max time
    if max_time:
        sql += " AND r.total_time <= ?"
        params.append(max_time)

    sql += " ORDER BY r.name"

    recipes_raw = conn.execute(sql, params).fetchall()
    recipes = enrich_recipes_with_tags(conn, recipes_raw)
    conn.close()

    return render_template('search.html',
                         recipes=recipes,
                         query=query,
                         difficulty=difficulty,
                         max_time=max_time,
                         result_count=len(recipes))


@app.route('/search/advanced')
def search_advanced():
    """Advanced search with full filters"""
    conn = get_db()

    # Get all filter parameters
    query = request.args.get('q', '').strip()
    difficulties = request.args.getlist('difficulty')
    max_prep = request.args.get('max_prep', type=int)
    max_time = request.args.get('max_time', type=int)
    with_ingredient = request.args.get('with_ingredient', '').strip()
    without_ingredient = request.args.get('without_ingredient', '').strip()
    tags = request.args.getlist('tag')

    # Build SQL query
    sql = """
        SELECT DISTINCT r.id, r.slug, r.name, r.description, r.image_url,
               r.prep_time, r.cook_time, r.total_time, r.servings,
               r.calories, r.difficulty, r.protein
        FROM recipes r
        LEFT JOIN ingredients i ON r.id = i.recipe_id
        LEFT JOIN tags t ON r.id = t.recipe_id
        WHERE (r.marked_for_deletion = 0 OR r.marked_for_deletion IS NULL)
    """
    params = []

    # Only show results if filters applied
    results_mode = (query or difficulties or max_prep or max_time or
                   with_ingredient or without_ingredient or tags)

    if results_mode:
        # Search by name
        if query:
            sql += " AND r.name LIKE ?"
            params.append(f'%{query}%')

        # Filter by difficulty
        if difficulties:
            placeholders = ','.join(['?'] * len(difficulties))
            sql += f" AND r.difficulty IN ({placeholders})"
            params.extend(difficulties)

        # Filter by prep time
        if max_prep and max_prep < 270:
            sql += " AND (r.prep_time IS NULL OR r.prep_time <= ?)"
            params.append(max_prep)

        # Filter by total time
        if max_time and max_time < 180:
            sql += " AND (r.total_time IS NULL OR r.total_time <= ?)"
            params.append(max_time)

        # Filter by ingredients (WITH)
        if with_ingredient:
            sql += " AND i.name LIKE ?"
            params.append(f'%{with_ingredient}%')

        # Filter by tags
        if tags:
            placeholders = ','.join(['?'] * len(tags))
            sql += f" AND t.tag IN ({placeholders})"
            params.extend(tags)

        sql += " ORDER BY r.name"

        recipes_raw = conn.execute(sql, params).fetchall()

        # Filter out recipes with unwanted ingredients (post-query)
        filtered_recipes = []
        if without_ingredient:
            for recipe in recipes_raw:
                # Check if recipe has the unwanted ingredient
                has_unwanted = conn.execute("""
                    SELECT COUNT(*) as count FROM ingredients
                    WHERE recipe_id = ? AND name LIKE ?
                """, (recipe['id'], f'%{without_ingredient}%')).fetchone()['count']

                if has_unwanted == 0:
                    filtered_recipes.append(recipe)
        else:
            filtered_recipes = recipes_raw

        recipes = enrich_recipes_with_tags(conn, filtered_recipes)
        conn.close()

        return render_template('search_advanced.html',
                             recipes=recipes,
                             results=True,
                             result_count=len(recipes),
                             query=query,
                             difficulties=difficulties,
                             max_prep=max_prep,
                             max_time=max_time,
                             with_ingredient=with_ingredient,
                             without_ingredient=without_ingredient,
                             selected_tags=tags)

    conn.close()

    # Show welcome page with no results
    return render_template('search_advanced.html',
                         difficulties=difficulties,
                         max_prep=max_prep,
                         max_time=max_time,
                         with_ingredient=with_ingredient,
                         without_ingredient=without_ingredient,
                         selected_tags=tags if 'tags' in locals() else [])


@app.route('/meal-plans/create')
@login_required
def create_meal_plan_page():
    """Page to create a new meal plan"""
    conn = get_db()

    recipes_raw = conn.execute("""
        SELECT id, slug, name, description, image_url,
               prep_time, cook_time, total_time, servings,
               calories, difficulty, protein
        FROM recipes
        WHERE marked_for_deletion = 0 OR marked_for_deletion IS NULL
        ORDER BY name
    """).fetchall()

    recipes = enrich_recipes_with_tags(conn, recipes_raw)
    conn.close()

    return render_template('create_meal_plan.html', recipes=recipes)


@app.route('/meal-plans/create', methods=['POST'])
@login_required
def create_meal_plan():
    """Create a new meal plan via .NET API"""
    data = request.json

    try:
        # Call .NET API to create meal plan with current user's ID
        response = api_post("meal-plans", json={
            "name": data['name'],
            "startDate": data['startDate'],
            "endDate": data['endDate'],
            "userId": current_user.id
        })

        if response.status_code != 201:
            logger.error(f"Failed to create meal plan: {response.status_code} - {response.text}")
            return jsonify({"error": "Failed to create meal plan. Please try again."}), 500

        meal_plan = response.json()
        meal_plan_id = meal_plan['id']

        # Add recipes to the meal plan
        for recipe_data in data['recipes']:
            recipe_response = api_post(f"meal-plans/{meal_plan_id}/recipes", json={
                "recipeId": recipe_data['recipeId'],
                "servings": recipe_data['servings'],
                "mealDate": data['startDate'],  # Default to start date
                "mealType": "dinner"  # Default meal type
            })
            if recipe_response.status_code not in [200, 201]:
                logger.warning(f"Failed to add recipe {recipe_data['recipeId']} to meal plan {meal_plan_id}")

        return jsonify({"id": meal_plan_id, "name": data['name']}), 201

    except APIError as e:
        return jsonify({"error": e.message}), e.status_code


@app.route('/meal-plans')
@login_required
def list_meal_plans():
    """List current user's meal plans"""
    try:
        # Filter meal plans by current user's ID
        response = api_get(f"meal-plans?userId={current_user.id}")
        meal_plans = response.json() if response.status_code == 200 else []
    except APIError as e:
        logger.error(f"Failed to list meal plans: {e.message}")
        meal_plans = []

    return render_template('meal_plans_list.html', meal_plans=meal_plans, api_error=None if meal_plans else "Unable to load meal plans")


@app.route('/meal-plans/<int:meal_plan_id>')
@login_required
def view_meal_plan(meal_plan_id):
    """View a specific meal plan (owned by current user)"""
    try:
        response = api_get(f"meal-plans/{meal_plan_id}")

        if response.status_code == 404:
            abort(404)
        elif response.status_code != 200:
            logger.error(f"Failed to fetch meal plan {meal_plan_id}: {response.status_code}")
            return render_template('error.html',
                message="Unable to load meal plan. Please try again later."), 500

        meal_plan = response.json()

        # Verify ownership - only allow viewing own meal plans
        if meal_plan.get('userId') and meal_plan['userId'] != current_user.id:
            abort(403)

        return render_template('meal_plan_detail.html', meal_plan=meal_plan)

    except APIError as e:
        logger.error(f"API error fetching meal plan {meal_plan_id}: {e.message}")
        return render_template('error.html', message=e.message), e.status_code


@app.route('/meal-plans/<int:meal_plan_id>/shopping-list')
@login_required
def view_shopping_list(meal_plan_id):
    """Generate and view shopping list for a meal plan"""
    try:
        # Verify ownership first
        meal_plan_response = api_get(f"meal-plans/{meal_plan_id}")
        if meal_plan_response.status_code == 404:
            abort(404)
        meal_plan_data = meal_plan_response.json()
        if meal_plan_data.get('userId') and meal_plan_data['userId'] != current_user.id:
            abort(403)

        # Generate shopping list
        generate_response = api_post(f"shopping-lists/generate/{meal_plan_id}")

        if generate_response.status_code not in [200, 201]:
            logger.error(f"Failed to generate shopping list for meal plan {meal_plan_id}: {generate_response.status_code}")
            return render_template('error.html',
                message="Unable to generate shopping list. Please try again later."), 500

        shopping_list_data = generate_response.json()
        shopping_list_id = shopping_list_data.get('id')

        # Get detailed shopping list grouped by aisle
        list_response = api_get(f"shopping-lists/{shopping_list_id}")

        if list_response.status_code != 200:
            logger.error(f"Failed to fetch shopping list {shopping_list_id}: {list_response.status_code}")
            return render_template('error.html',
                message="Unable to load shopping list. Please try again later."), 500

        shopping_list = list_response.json()

        return render_template('shopping_list.html',
                             meal_plan_id=meal_plan_id,
                             shopping_list=shopping_list)

    except APIError as e:
        logger.error(f"API error for shopping list: {e.message}")
        return render_template('error.html', message=e.message), e.status_code


@app.route('/meal-plans/<int:meal_plan_id>/meal-prep')
@login_required
def view_meal_prep_guide(meal_plan_id):
    """Generate and view meal prep guide for batch cooking"""
    try:
        # Verify ownership first
        meal_plan_response = api_get(f"meal-plans/{meal_plan_id}")
        if meal_plan_response.status_code == 404:
            abort(404)
        meal_plan_data = meal_plan_response.json()
        if meal_plan_data.get('userId') and meal_plan_data['userId'] != current_user.id:
            abort(403)

        # Get servings from query param, default to 3
        servings = request.args.get('servings', 3, type=int)

        # Generate meal prep guide
        generate_response = api_post(f"meal-prep/generate/{meal_plan_id}?servings={servings}")

        if generate_response.status_code not in [200, 201]:
            logger.error(f"Failed to generate meal prep guide for meal plan {meal_plan_id}: {generate_response.status_code}")
            return render_template('error.html',
                message="Unable to generate meal prep guide. Please try again later."), 500

        guide = generate_response.json()

        return render_template('meal_prep.html',
                             meal_plan_id=meal_plan_id,
                             guide=guide,
                             servings=servings)

    except APIError as e:
        logger.error(f"API error for meal prep guide: {e.message}")
        return render_template('error.html', message=e.message), e.status_code


@app.route('/recipe/<int:recipe_id>/mark-delete', methods=['POST'])
@login_required
def mark_for_deletion(recipe_id):
    """Mark a recipe for deletion (soft delete)"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE recipes
        SET marked_for_deletion = 1, marked_at = CURRENT_TIMESTAMP
        WHERE id = ?
    """, (recipe_id,))

    conn.commit()
    conn.close()

    return '''
        <div style="text-align: center; padding: 50px; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;">
            <h1>✓ Recipe Marked for Deletion</h1>
            <p>This recipe has been hidden from the site and marked for deletion.</p>
            <p>You can permanently delete it from the admin panel.</p>
            <a href="/" style="color: #ff6b35; text-decoration: none; font-weight: bold;">← Back to Recipes</a> |
            <a href="/admin/pending-deletions" style="color: #ff6b35; text-decoration: none; font-weight: bold;">View Pending Deletions</a>
        </div>
    '''


@app.route('/admin/pending-deletions')
@login_required
def pending_deletions():
    """Admin page - view recipes marked for deletion"""
    conn = get_db()
    recipes = conn.execute("""
        SELECT id, name, marked_at
        FROM recipes
        WHERE marked_for_deletion = 1
        ORDER BY marked_at DESC
    """).fetchall()
    conn.close()

    return render_template('pending_deletions.html', recipes=recipes)


@app.route('/admin/restore/<int:recipe_id>', methods=['POST'])
@login_required
def restore_recipe(recipe_id):
    """Restore a recipe marked for deletion"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE recipes
        SET marked_for_deletion = 0, marked_at = NULL
        WHERE id = ?
    """, (recipe_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('pending_deletions'))


@app.route('/admin/delete-permanent/<int:recipe_id>', methods=['POST'])
@login_required
def delete_permanent(recipe_id):
    """Permanently delete a recipe (hard delete)"""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM recipes WHERE id = ?", (recipe_id,))

    conn.commit()
    conn.close()

    return redirect(url_for('pending_deletions'))


@app.route('/admin/ai-tagging')
@login_required
def ai_tagging_dashboard():
    """Dashboard for AI-powered recipe tagging"""
    conn = get_db()

    # Get recipe stats
    total_recipes = conn.execute("""
        SELECT COUNT(*) as count FROM recipes
        WHERE marked_for_deletion = 0 OR marked_for_deletion IS NULL
    """).fetchone()['count']

    # Get recipes without tags
    untagged = conn.execute("""
        SELECT COUNT(DISTINCT r.id) as count
        FROM recipes r
        LEFT JOIN tags t ON r.id = t.recipe_id
        WHERE (r.marked_for_deletion = 0 OR r.marked_for_deletion IS NULL)
        AND t.recipe_id IS NULL
    """).fetchone()['count']

    # Get next untagged recipe
    next_recipe = conn.execute("""
        SELECT r.id, r.name
        FROM recipes r
        LEFT JOIN tags t ON r.id = t.recipe_id
        WHERE (r.marked_for_deletion = 0 OR r.marked_for_deletion IS NULL)
        AND t.recipe_id IS NULL
        LIMIT 1
    """).fetchone()

    conn.close()

    return render_template('admin_ai_tagging.html',
                         total_recipes=total_recipes,
                         untagged=untagged,
                         next_recipe=next_recipe)


@app.route('/admin/ai-tagging/suggest/<int:recipe_id>')
@login_required
def suggest_tags(recipe_id):
    """Get AI tag suggestions for a recipe"""
    from ai_tag_recipes import RecipeTagger

    tagger = RecipeTagger(db_path=str(DB_PATH))
    try:
        tagger.connect_db()

        # Get recipe details
        recipe = tagger.get_recipe_details(recipe_id)
        if not recipe:
            return jsonify({"error": "Recipe not found"}), 404

        # Get existing tags
        existing_tags = tagger.get_existing_tags(recipe_id)

        # Get AI suggestions
        suggested_tags = tagger.suggest_tags(recipe)

        return jsonify({
            "recipe_id": recipe_id,
            "recipe_name": recipe['name'],
            "existing_tags": existing_tags,
            "suggested_tags": suggested_tags,
            "ingredients_count": len(recipe['ingredients']),
            "prep_time": recipe['prep_time'],
            "total_time": recipe['total_time'],
            "protein": recipe['protein']
        })

    finally:
        tagger.close_db()


@app.route('/admin/ai-tagging/save/<int:recipe_id>', methods=['POST'])
@login_required
def save_tags_route(recipe_id):
    """Save tags for a recipe"""
    from ai_tag_recipes import RecipeTagger
    from tag_categories import ALL_TAGS

    data = request.json
    tags = data.get('tags', [])

    # Validate tags
    valid_tags = [tag for tag in tags if tag in ALL_TAGS]

    tagger = RecipeTagger(db_path=str(DB_PATH))
    try:
        tagger.connect_db()
        tagger.save_tags(recipe_id, valid_tags)

        return jsonify({"success": True, "tags": valid_tags})

    finally:
        tagger.close_db()


@app.route('/admin/ai-tagging/batch', methods=['POST'])
@login_required
def batch_tag_recipes():
    """Auto-tag multiple untagged recipes"""
    from ai_tag_recipes import RecipeTagger

    data = request.json
    limit = data.get('limit', 5)  # Default to 5 recipes per batch

    tagger = RecipeTagger(db_path=str(DB_PATH))
    results = []

    try:
        tagger.connect_db()

        # Get untagged recipes
        cursor = tagger.db_conn.cursor()
        untagged = cursor.execute("""
            SELECT r.id, r.name
            FROM recipes r
            LEFT JOIN tags t ON r.id = t.recipe_id
            WHERE (r.marked_for_deletion = 0 OR r.marked_for_deletion IS NULL)
            AND t.recipe_id IS NULL
            LIMIT ?
        """, (limit,)).fetchall()

        for recipe_row in untagged:
            recipe_id = recipe_row['id']
            recipe_name = recipe_row['name']

            try:
                recipe = tagger.get_recipe_details(recipe_id)
                suggested_tags = tagger.suggest_tags(recipe)

                if suggested_tags:
                    tagger.save_tags(recipe_id, suggested_tags)
                    results.append({
                        'id': recipe_id,
                        'name': recipe_name,
                        'tags': suggested_tags,
                        'status': 'success'
                    })
                else:
                    results.append({
                        'id': recipe_id,
                        'name': recipe_name,
                        'tags': [],
                        'status': 'no_suggestions'
                    })
            except Exception as e:
                results.append({
                    'id': recipe_id,
                    'name': recipe_name,
                    'error': str(e),
                    'status': 'error'
                })

        return jsonify({
            'success': True,
            'processed': len(results),
            'results': results
        })

    finally:
        tagger.close_db()


@app.route('/admin/import-recipe')
@login_required
def import_recipe_page():
    """Page to import recipes from URLs"""
    return render_template('import_recipe.html')


@app.route('/admin/import-recipe/scrape', methods=['POST'])
@login_required
def scrape_recipe():
    """Scrape recipe from URL"""
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scraper'))
    from recipe_scrapers import scrape_html
    import requests

    data = request.json
    url = data.get('url', '').strip()

    if not url:
        return jsonify({"error": "URL is required"}), 400

    try:
        # Fetch HTML with comprehensive browser headers
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

        # Parse with recipe-scrapers
        scraper = scrape_html(html=response.content, org_url=url)

        # Extract data for preview
        def safe_call(func, default=None):
            try:
                result = func() if callable(func) else func
                return result if result else default
            except:
                return default

        recipe_preview = {
            'url': url,
            'name': safe_call(scraper.title, 'Unknown Recipe'),
            'description': safe_call(scraper.description),
            'image_url': safe_call(scraper.image),
            'total_time': safe_call(scraper.total_time),
            'prep_time': safe_call(scraper.prep_time),
            'cook_time': safe_call(scraper.cook_time),
            'yields': safe_call(scraper.yields),
            'ingredients': safe_call(scraper.ingredients, []),
            'instructions': safe_call(scraper.instructions, ''),
            'category': safe_call(scraper.category),
            'cuisine': safe_call(scraper.cuisine)
        }

        # Get nutrition if available
        nutrients = safe_call(scraper.nutrients, {})
        if nutrients:
            recipe_preview['calories'] = nutrients.get('calories')
            recipe_preview['protein'] = nutrients.get('proteinContent')
            recipe_preview['carbs'] = nutrients.get('carbohydrateContent')
            recipe_preview['fat'] = nutrients.get('fatContent')

        return jsonify({
            "success": True,
            "recipe": recipe_preview
        })

    except requests.RequestException as e:
        return jsonify({"error": f"Failed to fetch URL: {str(e)}"}), 400
    except Exception as e:
        return jsonify({"error": f"Failed to parse recipe: {str(e)}"}), 400


@app.route('/admin/import-recipe/save', methods=['POST'])
@login_required
def save_imported_recipe():
    """Save scraped recipe to database"""
    import sys
    import hashlib
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scraper'))
    from import_url import RecipeImporter

    data = request.json
    url = data.get('url')

    if not url:
        return jsonify({"error": "URL is required"}), 400

    # Calculate recipe ID from URL (same logic as import_url.py)
    url_hash = int(hashlib.md5(url.encode()).hexdigest()[:8], 16)
    recipe_id = url_hash

    importer = RecipeImporter(db_path=str(DB_PATH))
    try:
        importer.connect_db()

        # Import the recipe
        success = importer.import_from_url(url, region="web-import")

        if success:
            return jsonify({
                "success": True,
                "message": "Recipe imported successfully!",
                "recipe_id": recipe_id
            })
        else:
            return jsonify({"error": "Failed to import recipe"}), 500

    finally:
        importer.close_db()


@app.route('/meal-plans/<int:meal_plan_id>/export-walmart')
@login_required
def export_walmart(meal_plan_id):
    """Export shopping list in Walmart-optimized format for OpenClaw"""
    try:
        # Verify ownership first
        meal_plan_check = api_get(f"meal-plans/{meal_plan_id}")
        if meal_plan_check.status_code == 404:
            return jsonify({"error": "Meal plan not found"}), 404
        meal_plan_data = meal_plan_check.json()
        if meal_plan_data.get('userId') and meal_plan_data['userId'] != current_user.id:
            return jsonify({"error": "Access denied"}), 403

        # Get shopping list
        generate_response = api_post(f"shopping-lists/generate/{meal_plan_id}")

        if generate_response.status_code not in [200, 201]:
            logger.error(f"Failed to generate shopping list for export: {generate_response.status_code}")
            return jsonify({"error": "Failed to generate shopping list. Please try again."}), 500

        shopping_list_data = generate_response.json()
        shopping_list_id = shopping_list_data.get('id')

        # Get detailed shopping list
        list_response = api_get(f"shopping-lists/{shopping_list_id}")

        if list_response.status_code != 200:
            logger.error(f"Failed to fetch shopping list for export: {list_response.status_code}")
            return jsonify({"error": "Failed to fetch shopping list. Please try again."}), 500

        shopping_list = list_response.json()

        # Get meal plan details
        meal_plan_response = api_get(f"meal-plans/{meal_plan_id}")
        meal_plan = meal_plan_response.json() if meal_plan_response.status_code == 200 else {}

    except APIError as e:
        logger.error(f"API error during Walmart export: {e.message}")
        return jsonify({"error": e.message}), e.status_code

    # Format for Walmart/OpenClaw
    walmart_export = {
        "version": "1.0",
        "platform": "walmart",
        "mealPlan": {
            "id": meal_plan_id,
            "name": meal_plan.get('name', 'Weekly Meal Plan'),
            "startDate": meal_plan.get('startDate'),
            "endDate": meal_plan.get('endDate')
        },
        "totalItems": shopping_list.get('totalItems', 0),
        "items": [],
        "metadata": {
            "exportedAt": shopping_list.get('generatedAt'),
            "storeName": "Walmart",
            "deliveryPreference": "schedule"
        }
    }

    # Convert items to Walmart search-friendly format
    aisles = shopping_list.get('aisles', [])
    for aisle_group in aisles:
        aisle_name = aisle_group.get('aisleName', 'Other')
        for item in aisle_group.get('items', []):
            walmart_item = {
                "name": item.get('itemName'),
                "quantity": item.get('quantity', 1),
                "unit": item.get('unit', 'unit'),
                "aisle": aisle_name.capitalize(),
                "searchTerm": item.get('itemName'),  # Walmart search query
                "recipes": item.get('usedInRecipes', []),
                "notes": item.get('bulkItemNote', '')
            }
            walmart_export["items"].append(walmart_item)

    return jsonify(walmart_export)


# ============================================================================
# INITIALIZE AUTH
# ============================================================================

# Initialize authentication (imports already at top of file)
init_auth(app)

# Initialize Kroger integration
from kroger import init_kroger
init_kroger(app)


@app.context_processor
def inject_user():
    """Make current_user available in all templates."""
    return dict(current_user=current_user)


# ============================================================================
# USER SETTINGS
# ============================================================================

def get_user_preferences(user_id):
    """Get user preferences from database."""
    conn = get_db()
    prefs = conn.execute(
        "SELECT * FROM user_preferences WHERE user_id = ?",
        (user_id,)
    ).fetchone()
    conn.close()

    if prefs:
        return dict(prefs)
    return {
        'default_servings': 2,
        'preferred_store': None,
        'kroger_client_id': None,
        'kroger_client_secret': None,
        'kroger_access_token': None,
        'walmart_api_key': None,
    }


def save_user_preferences(user_id, prefs):
    """Save user preferences to database."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if preferences exist
    existing = cursor.execute(
        "SELECT user_id FROM user_preferences WHERE user_id = ?",
        (user_id,)
    ).fetchone()

    if existing:
        cursor.execute("""
            UPDATE user_preferences SET
                default_servings = ?,
                preferred_store = ?,
                kroger_client_id = ?,
                kroger_client_secret = ?,
                walmart_api_key = ?,
                updated_at = CURRENT_TIMESTAMP
            WHERE user_id = ?
        """, (
            prefs['default_servings'],
            prefs['preferred_store'],
            prefs['kroger_client_id'],
            prefs['kroger_client_secret'],
            prefs['walmart_api_key'],
            user_id
        ))
    else:
        cursor.execute("""
            INSERT INTO user_preferences (
                user_id, default_servings, preferred_store,
                kroger_client_id, kroger_client_secret, walmart_api_key
            ) VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            prefs['default_servings'],
            prefs['preferred_store'],
            prefs['kroger_client_id'],
            prefs['kroger_client_secret'],
            prefs['walmart_api_key']
        ))

    conn.commit()
    conn.close()


@app.route('/settings')
@login_required
def settings_page():
    """Display user settings page."""
    preferences = get_user_preferences(current_user.id)
    success_message = request.args.get('success')
    error_message = request.args.get('error')

    return render_template('settings.html',
                         preferences=preferences,
                         success_message=success_message,
                         error_message=error_message)


@app.route('/settings', methods=['POST'])
@login_required
def save_settings():
    """Save user settings."""
    try:
        prefs = {
            'default_servings': int(request.form.get('default_servings', 2)),
            'preferred_store': request.form.get('preferred_store') or None,
            'kroger_client_id': request.form.get('kroger_client_id') or None,
            'kroger_client_secret': request.form.get('kroger_client_secret') or None,
            'walmart_api_key': request.form.get('walmart_api_key') or None,
        }

        save_user_preferences(current_user.id, prefs)
        return redirect(url_for('settings_page', success='Settings saved successfully!'))

    except Exception as e:
        logger.error(f"Error saving settings: {e}")
        return redirect(url_for('settings_page', error='Failed to save settings. Please try again.'))


if __name__ == '__main__':
    app.run(debug=True, port=5001)
