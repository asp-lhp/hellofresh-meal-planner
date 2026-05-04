-- HelloFresh Recipe Database Schema
-- SQLite database for meal planning and OpenClaw integration

-- Drop tables if they exist (for clean rebuild)
DROP TABLE IF EXISTS shopping_list_items;
DROP TABLE IF EXISTS shopping_lists;
DROP TABLE IF EXISTS meal_plan_recipes;
DROP TABLE IF EXISTS meal_plans;
DROP TABLE IF EXISTS tags;
DROP TABLE IF EXISTS allergens;
DROP TABLE IF EXISTS instructions;
DROP TABLE IF EXISTS ingredients;
DROP TABLE IF EXISTS recipes;

-- ============================================================================
-- CORE RECIPE DATA
-- ============================================================================

CREATE TABLE recipes (
    id INTEGER PRIMARY KEY,
    slug TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    description TEXT,

    -- Recipe metadata
    difficulty TEXT CHECK(difficulty IN ('Easy', 'Medium', 'Hard')),
    prep_time INTEGER,  -- minutes
    cook_time INTEGER,  -- minutes
    total_time INTEGER, -- minutes
    servings INTEGER DEFAULT 2,

    -- Nutrition (per serving)
    calories INTEGER,
    protein INTEGER,    -- grams
    carbs INTEGER,      -- grams
    fat INTEGER,        -- grams
    fiber INTEGER,      -- grams
    sodium INTEGER,     -- mg

    -- Media
    image_url TEXT,

    -- External links
    hellofresh_url TEXT,
    pdf_url TEXT,

    -- Metadata
    region TEXT DEFAULT 'en-US',
    scraped_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Soft delete support
    marked_for_deletion BOOLEAN DEFAULT 0,
    marked_at TIMESTAMP
);

CREATE INDEX idx_recipes_difficulty ON recipes(difficulty);
CREATE INDEX idx_recipes_marked ON recipes(marked_for_deletion);
CREATE INDEX idx_recipes_cook_time ON recipes(cook_time);
CREATE INDEX idx_recipes_calories ON recipes(calories);
CREATE INDEX idx_recipes_region ON recipes(region);

-- ============================================================================
-- INGREDIENTS
-- ============================================================================

CREATE TABLE ingredients (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    name TEXT NOT NULL,
    quantity TEXT,          -- e.g., "2 oz", "1 cup", "4 cloves"
    normalized_name TEXT,   -- Cleaned for grocery matching
    image_url TEXT,

    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE INDEX idx_ingredients_recipe_id ON ingredients(recipe_id);
CREATE INDEX idx_ingredients_name ON ingredients(name);
CREATE INDEX idx_ingredients_normalized_name ON ingredients(normalized_name);

-- ============================================================================
-- COOKING INSTRUCTIONS
-- ============================================================================

CREATE TABLE instructions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    step_number INTEGER NOT NULL,
    title TEXT,
    description TEXT NOT NULL,
    image_url TEXT,

    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE(recipe_id, step_number)
);

CREATE INDEX idx_instructions_recipe_id ON instructions(recipe_id);

-- ============================================================================
-- ALLERGENS & TAGS
-- ============================================================================

CREATE TABLE allergens (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    allergen TEXT NOT NULL CHECK(allergen IN (
        'Milk', 'Eggs', 'Fish', 'Shellfish', 'Tree Nuts',
        'Peanuts', 'Wheat', 'Soybeans', 'Sesame'
    )),

    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE(recipe_id, allergen)
);

CREATE INDEX idx_allergens_recipe_id ON allergens(recipe_id);

CREATE TABLE tags (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    recipe_id INTEGER NOT NULL,
    tag TEXT NOT NULL,

    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE,
    UNIQUE(recipe_id, tag)
);

CREATE INDEX idx_tags_recipe_id ON tags(recipe_id);

-- ============================================================================
-- MEAL PLANNING
-- ============================================================================

CREATE TABLE meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT,
    week_start_date DATE,
    total_calories INTEGER,
    total_cost REAL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE meal_plan_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_plan_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    servings INTEGER DEFAULT 2,
    meal_date DATE,
    meal_type TEXT CHECK(meal_type IN ('Breakfast', 'Lunch', 'Dinner', 'Snack')),

    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

CREATE INDEX idx_meal_plan_recipes_meal_plan_id ON meal_plan_recipes(meal_plan_id);

-- ============================================================================
-- SHOPPING LISTS (for OpenClaw)
-- ============================================================================

CREATE TABLE shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_plan_id INTEGER,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    openclaw_ready BOOLEAN DEFAULT 0,

    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
);

CREATE TABLE shopping_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shopping_list_id INTEGER NOT NULL,
    ingredient TEXT NOT NULL,
    quantity TEXT NOT NULL,
    normalized_ingredient TEXT,    -- For grocery search
    search_query TEXT,              -- What OpenClaw should search for
    max_price_multiplier REAL DEFAULT 2.0,
    category TEXT,                  -- Produce, Meat, Dairy, etc.
    purchased BOOLEAN DEFAULT 0,

    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE
);

CREATE INDEX idx_shopping_list_items_list_id ON shopping_list_items(shopping_list_id);

-- ============================================================================
-- USEFUL VIEWS FOR QUERIES
-- ============================================================================

-- Recipe search with ingredient count
CREATE VIEW vw_recipe_summary AS
SELECT
    r.id,
    r.slug,
    r.name,
    r.difficulty,
    r.cook_time,
    r.calories,
    r.protein,
    COUNT(DISTINCT i.id) as ingredient_count,
    GROUP_CONCAT(DISTINCT t.tag, ', ') as tags
FROM recipes r
LEFT JOIN ingredients i ON r.id = i.recipe_id
LEFT JOIN tags t ON r.id = t.recipe_id
GROUP BY r.id;

-- Quick nutrition lookup
CREATE VIEW vw_recipe_nutrition AS
SELECT
    r.id,
    r.name,
    r.servings,
    r.calories,
    r.protein,
    r.carbs,
    r.fat,
    r.fiber,
    ROUND(r.calories * 1.0 / NULLIF(r.servings, 0), 0) as calories_per_serving,
    ROUND(r.protein * 1.0 / NULLIF(r.servings, 0), 1) as protein_per_serving
FROM recipes r;

-- ============================================================================
-- SAMPLE DATA QUERIES (for testing after scraping)
-- ============================================================================

-- EXAMPLE: Find all chicken recipes under 30 minutes
-- SELECT r.name, r.cook_time, r.calories
-- FROM recipes r
-- JOIN ingredients i ON r.id = i.recipe_id
-- WHERE i.name LIKE '%chicken%'
--   AND r.cook_time <= 30
-- ORDER BY r.calories;

-- EXAMPLE: Top 10 high-protein recipes
-- SELECT name, protein, calories, ROUND(protein * 4.0 / calories * 100, 1) as protein_pct
-- FROM recipes
-- WHERE protein IS NOT NULL
-- ORDER BY protein DESC
-- LIMIT 10;

-- EXAMPLE: Recipes with multiple allergens
-- SELECT r.name, GROUP_CONCAT(a.allergen, ', ') as allergens
-- FROM recipes r
-- JOIN allergens a ON r.id = a.recipe_id
-- GROUP BY r.id
-- HAVING COUNT(a.allergen) > 2;
