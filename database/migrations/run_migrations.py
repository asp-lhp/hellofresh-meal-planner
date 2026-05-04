#!/usr/bin/env python3
"""
Database migration runner for Meal Planner.
Run this to apply any pending migrations to your database.

Usage:
    python run_migrations.py [database_path]

Example:
    python run_migrations.py ../recipes.db
"""

import sqlite3
import sys
from pathlib import Path


def get_existing_columns(conn, table_name):
    """Get list of existing column names for a table."""
    cursor = conn.execute(f"PRAGMA table_info({table_name})")
    return {row[1] for row in cursor.fetchall()}


def get_existing_indexes(conn):
    """Get list of existing index names."""
    cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
    return {row[0] for row in cursor.fetchall()}


def migration_001_soft_delete(conn):
    """Add soft-delete columns to recipes table."""
    print("Migration 001: Adding soft-delete columns...")

    existing_cols = get_existing_columns(conn, 'recipes')
    existing_indexes = get_existing_indexes(conn)

    changes_made = False

    # Add marked_for_deletion column
    if 'marked_for_deletion' not in existing_cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN marked_for_deletion BOOLEAN DEFAULT 0")
        print("  - Added column: marked_for_deletion")
        changes_made = True
    else:
        print("  - Column already exists: marked_for_deletion")

    # Add marked_at column
    if 'marked_at' not in existing_cols:
        conn.execute("ALTER TABLE recipes ADD COLUMN marked_at TIMESTAMP")
        print("  - Added column: marked_at")
        changes_made = True
    else:
        print("  - Column already exists: marked_at")

    # Add index on marked_for_deletion
    if 'idx_recipes_marked' not in existing_indexes:
        conn.execute("CREATE INDEX idx_recipes_marked ON recipes(marked_for_deletion)")
        print("  - Added index: idx_recipes_marked")
        changes_made = True
    else:
        print("  - Index already exists: idx_recipes_marked")

    return changes_made


def table_exists(conn, table_name):
    """Check if a table exists."""
    cursor = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (table_name,)
    )
    return cursor.fetchone() is not None


def migration_004_add_users(conn):
    """Add users, user_preferences tables and user_id columns."""
    print("Migration 004: Adding users and authentication...")

    existing_indexes = get_existing_indexes(conn)
    changes_made = False

    # Create users table
    if not table_exists(conn, 'users'):
        conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                google_id TEXT UNIQUE NOT NULL,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                avatar_url TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                last_login TIMESTAMP
            )
        """)
        print("  - Created table: users")
        changes_made = True
    else:
        print("  - Table already exists: users")

    # Create indexes on users
    if 'idx_users_google_id' not in existing_indexes:
        conn.execute("CREATE INDEX idx_users_google_id ON users(google_id)")
        print("  - Added index: idx_users_google_id")
        changes_made = True

    if 'idx_users_email' not in existing_indexes:
        conn.execute("CREATE INDEX idx_users_email ON users(email)")
        print("  - Added index: idx_users_email")
        changes_made = True

    # Create user_preferences table
    if not table_exists(conn, 'user_preferences'):
        conn.execute("""
            CREATE TABLE user_preferences (
                user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
                default_servings INTEGER DEFAULT 2,
                preferred_store TEXT,
                dietary_restrictions TEXT,
                theme TEXT DEFAULT 'light',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP
            )
        """)
        print("  - Created table: user_preferences")
        changes_made = True
    else:
        print("  - Table already exists: user_preferences")

    # Add user_id to meal_plans
    meal_plan_cols = get_existing_columns(conn, 'meal_plans')
    if 'user_id' not in meal_plan_cols:
        conn.execute("ALTER TABLE meal_plans ADD COLUMN user_id INTEGER REFERENCES users(id)")
        print("  - Added column: meal_plans.user_id")
        changes_made = True

    if 'idx_meal_plans_user_id' not in existing_indexes:
        conn.execute("CREATE INDEX idx_meal_plans_user_id ON meal_plans(user_id)")
        print("  - Added index: idx_meal_plans_user_id")
        changes_made = True

    # Add user_id to shopping_lists
    shopping_list_cols = get_existing_columns(conn, 'shopping_lists')
    if 'user_id' not in shopping_list_cols:
        conn.execute("ALTER TABLE shopping_lists ADD COLUMN user_id INTEGER REFERENCES users(id)")
        print("  - Added column: shopping_lists.user_id")
        changes_made = True

    if 'idx_shopping_lists_user_id' not in existing_indexes:
        conn.execute("CREATE INDEX idx_shopping_lists_user_id ON shopping_lists(user_id)")
        print("  - Added index: idx_shopping_lists_user_id")
        changes_made = True

    # Add user_id to inventory_items
    if table_exists(conn, 'inventory_items'):
        inventory_cols = get_existing_columns(conn, 'inventory_items')
        if 'user_id' not in inventory_cols:
            conn.execute("ALTER TABLE inventory_items ADD COLUMN user_id INTEGER REFERENCES users(id)")
            print("  - Added column: inventory_items.user_id")
            changes_made = True

        if 'idx_inventory_items_user_id' not in existing_indexes:
            conn.execute("CREATE INDEX idx_inventory_items_user_id ON inventory_items(user_id)")
            print("  - Added index: idx_inventory_items_user_id")
            changes_made = True

    return changes_made


def migration_005_grocery_api_credentials(conn):
    """Add grocery store API credential columns to user_preferences."""
    print("Migration 005: Adding grocery API credentials...")

    existing_cols = get_existing_columns(conn, 'user_preferences')
    changes_made = False

    # Kroger API credentials
    kroger_columns = [
        ('kroger_client_id', 'TEXT'),
        ('kroger_client_secret', 'TEXT'),
        ('kroger_access_token', 'TEXT'),
        ('kroger_refresh_token', 'TEXT'),
        ('kroger_token_expires_at', 'TIMESTAMP'),
    ]

    for col_name, col_type in kroger_columns:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE user_preferences ADD COLUMN {col_name} {col_type}")
            print(f"  - Added column: {col_name}")
            changes_made = True
        else:
            print(f"  - Column already exists: {col_name}")

    # Walmart API credentials (future)
    walmart_columns = [
        ('walmart_api_key', 'TEXT'),
    ]

    for col_name, col_type in walmart_columns:
        if col_name not in existing_cols:
            conn.execute(f"ALTER TABLE user_preferences ADD COLUMN {col_name} {col_type}")
            print(f"  - Added column: {col_name}")
            changes_made = True
        else:
            print(f"  - Column already exists: {col_name}")

    return changes_made


def migration_006_add_invite_codes(conn):
    """Add invite_codes table for invite-only access control."""
    print("Migration 006: Adding invite codes for access control...")

    existing_indexes = get_existing_indexes(conn)
    changes_made = False

    # Create invite_codes table
    if not table_exists(conn, 'invite_codes'):
        conn.execute("""
            CREATE TABLE invite_codes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                code TEXT UNIQUE NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                used_by_email TEXT,
                used_at TIMESTAMP,
                revoked_at TIMESTAMP
            )
        """)
        print("  - Created table: invite_codes")
        changes_made = True
    else:
        print("  - Table already exists: invite_codes")

    # Create indexes
    if 'idx_invite_codes_code' not in existing_indexes:
        conn.execute("CREATE INDEX idx_invite_codes_code ON invite_codes(code)")
        print("  - Added index: idx_invite_codes_code")
        changes_made = True

    if 'idx_invite_codes_used_at' not in existing_indexes:
        conn.execute("CREATE INDEX idx_invite_codes_used_at ON invite_codes(used_at)")
        print("  - Added index: idx_invite_codes_used_at")
        changes_made = True

    return changes_made


def run_migrations(db_path):
    """Run all pending migrations."""
    print(f"Running migrations on: {db_path}")
    print("-" * 50)

    conn = sqlite3.connect(db_path)

    try:
        # List of all migrations in order
        migrations = [
            ("001", migration_001_soft_delete),
            ("004", migration_004_add_users),
            ("005", migration_005_grocery_api_credentials),
            ("006", migration_006_add_invite_codes),
        ]

        total_changes = 0
        for version, migration_func in migrations:
            if migration_func(conn):
                total_changes += 1

        conn.commit()
        print("-" * 50)

        if total_changes > 0:
            print(f"Migrations complete. {total_changes} migration(s) applied.")
        else:
            print("Database is up to date. No migrations needed.")

    except Exception as e:
        conn.rollback()
        print(f"Error running migrations: {e}")
        sys.exit(1)
    finally:
        conn.close()


if __name__ == "__main__":
    # Default database path
    default_db = Path(__file__).parent.parent / "recipes.db"

    if len(sys.argv) > 1:
        db_path = sys.argv[1]
    else:
        db_path = str(default_db)

    if not Path(db_path).exists():
        print(f"Error: Database not found: {db_path}")
        sys.exit(1)

    run_migrations(db_path)
