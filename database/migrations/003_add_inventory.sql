-- Migration: Add Inventory Tracking
-- Created: 2026-03-21
-- Description: Adds inventory_locations and inventory_items tables for freezer/pantry tracking

-- Create inventory_locations table
CREATE TABLE IF NOT EXISTS inventory_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_freezer INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Create inventory_items table
CREATE TABLE IF NOT EXISTS inventory_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    location_id INTEGER NOT NULL,
    food_id INTEGER,
    item_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    added_date TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    used_date TEXT,
    notes TEXT,
    is_used_up INTEGER DEFAULT 0,
    FOREIGN KEY (location_id) REFERENCES inventory_locations(id) ON DELETE CASCADE,
    FOREIGN KEY (food_id) REFERENCES foods(id) ON DELETE SET NULL
);

-- Create indexes
CREATE INDEX IF NOT EXISTS idx_inventory_items_location_id ON inventory_items(location_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_food_id ON inventory_items(food_id);
CREATE INDEX IF NOT EXISTS idx_inventory_items_expires_at ON inventory_items(expires_at);
CREATE INDEX IF NOT EXISTS idx_inventory_items_is_used_up ON inventory_items(is_used_up);

-- Seed default locations
INSERT OR IGNORE INTO inventory_locations (name, description, is_freezer, display_order) VALUES
('freezer', 'Freezer storage', 1, 1),
('fridge', 'Refrigerator', 0, 2),
('pantry', 'Pantry / dry goods', 0, 3);
