-- Migration 004: Add users and authentication support
-- For STR-34: Create users database schema and migrations

-- ============================================================================
-- USER ACCOUNTS
-- ============================================================================

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    google_id TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    name TEXT,
    avatar_url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_users_google_id ON users(google_id);
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);

-- ============================================================================
-- USER PREFERENCES
-- ============================================================================

CREATE TABLE IF NOT EXISTS user_preferences (
    user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    default_servings INTEGER DEFAULT 2,
    preferred_store TEXT,
    dietary_restrictions TEXT,  -- JSON array
    theme TEXT DEFAULT 'light',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP
);

-- ============================================================================
-- ADD user_id TO EXISTING TABLES (nullable for existing data)
-- ============================================================================

-- meal_plans.user_id
-- ALTER TABLE meal_plans ADD COLUMN user_id INTEGER REFERENCES users(id);

-- shopping_lists.user_id
-- ALTER TABLE shopping_lists ADD COLUMN user_id INTEGER REFERENCES users(id);

-- inventory_items.user_id (if table exists)
-- ALTER TABLE inventory_items ADD COLUMN user_id INTEGER REFERENCES users(id);
