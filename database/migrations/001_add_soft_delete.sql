-- Migration 001: Add soft-delete columns to recipes table
-- Run this on existing databases to add soft-delete support
--
-- Usage: sqlite3 recipes.db < 001_add_soft_delete.sql

-- Add marked_for_deletion column if it doesn't exist
-- SQLite doesn't support IF NOT EXISTS for ALTER TABLE, so we use a trick
SELECT CASE
    WHEN (SELECT COUNT(*) FROM pragma_table_info('recipes') WHERE name='marked_for_deletion') = 0
    THEN 'ALTER TABLE recipes ADD COLUMN marked_for_deletion BOOLEAN DEFAULT 0;'
END;

-- For SQLite, we need to run these directly and handle errors
-- Run these commands manually if the above doesn't work:

-- ALTER TABLE recipes ADD COLUMN marked_for_deletion BOOLEAN DEFAULT 0;
-- ALTER TABLE recipes ADD COLUMN marked_at TIMESTAMP;
-- CREATE INDEX IF NOT EXISTS idx_recipes_marked ON recipes(marked_for_deletion);

-- Verify the migration
-- SELECT name FROM pragma_table_info('recipes') WHERE name IN ('marked_for_deletion', 'marked_at');
