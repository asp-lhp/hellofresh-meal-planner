-- Migration: Add Meal Planning Tables
-- Created: 2026-03-21
-- Description: Adds meal_plans and meal_plan_recipes tables for weekly meal planning

-- Create meal_plans table
CREATE TABLE IF NOT EXISTS meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create meal_plan_recipes table (join table)
CREATE TABLE IF NOT EXISTS meal_plan_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_plan_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    scheduled_date TEXT NOT NULL,
    meal_type TEXT DEFAULT 'dinner',
    servings INTEGER DEFAULT 2,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_meal_plan_recipes_meal_plan_id
    ON meal_plan_recipes(meal_plan_id);

CREATE INDEX IF NOT EXISTS idx_meal_plan_recipes_recipe_id
    ON meal_plan_recipes(recipe_id);

CREATE INDEX IF NOT EXISTS idx_meal_plan_recipes_scheduled_date
    ON meal_plan_recipes(scheduled_date);

CREATE INDEX IF NOT EXISTS idx_meal_plans_start_date
    ON meal_plans(start_date);
