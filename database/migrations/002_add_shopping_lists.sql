-- Migration: Add Shopping Lists and Food Normalization
-- Created: 2026-03-21
-- Description: Adds foods, shopping_lists, and shopping_list_items tables

-- Create foods table (normalized ingredients)
CREATE TABLE IF NOT EXISTS foods (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    plural_name TEXT,
    parent_food_id INTEGER,
    aisle TEXT,
    aisle_order INTEGER,
    preferred_unit TEXT,
    is_bulk_item INTEGER DEFAULT 0,
    typical_package_size TEXT,
    bulk_item_note TEXT,
    freezes_well INTEGER DEFAULT 0,
    shelf_life_days INTEGER,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_food_id) REFERENCES foods(id)
);

-- Create shopping_lists table
CREATE TABLE IF NOT EXISTS shopping_lists (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_plan_id INTEGER NOT NULL,
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE
);

-- Create shopping_list_items table
CREATE TABLE IF NOT EXISTS shopping_list_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    shopping_list_id INTEGER NOT NULL,
    food_id INTEGER,
    item_name TEXT NOT NULL,
    quantity TEXT NOT NULL,
    unit TEXT,
    aisle TEXT,
    display_order INTEGER DEFAULT 0,
    is_bulk_item INTEGER DEFAULT 0,
    bulk_item_note TEXT,
    checked INTEGER DEFAULT 0,
    used_in_recipes TEXT,
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_foods_name ON foods(name);
CREATE INDEX IF NOT EXISTS idx_foods_parent_food_id ON foods(parent_food_id);
CREATE INDEX IF NOT EXISTS idx_foods_aisle ON foods(aisle);
CREATE INDEX IF NOT EXISTS idx_shopping_lists_meal_plan_id ON shopping_lists(meal_plan_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_items_shopping_list_id ON shopping_list_items(shopping_list_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_items_food_id ON shopping_list_items(food_id);
CREATE INDEX IF NOT EXISTS idx_shopping_list_items_aisle ON shopping_list_items(aisle);
