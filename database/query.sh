#!/bin/bash
# Quick database query helper

DB="recipes.db"

# Check if database exists
if [ ! -f "$DB" ]; then
    echo "Database not found! Run the scraper first."
    exit 1
fi

# Function to run formatted query
query() {
    sqlite3 -column -header "$DB" "$1"
}

# Show menu if no arguments
if [ $# -eq 0 ]; then
    echo "=== Recipe Database Quick Queries ==="
    echo ""
    echo "Usage: ./query.sh [option]"
    echo ""
    echo "Options:"
    echo "  stats        - Database statistics"
    echo "  recipes      - List all recipes"
    echo "  easy         - Easy recipes only"
    echo "  quick        - Recipes under 20 minutes"
    echo "  chicken      - All chicken recipes"
    echo "  ingredients  - Most common ingredients"
    echo "  sql 'query'  - Run custom SQL query"
    echo ""
    exit 0
fi

case "$1" in
    stats)
        echo "=== Database Statistics ==="
        query "
        SELECT 'Recipes' as table_name, COUNT(*) as count FROM recipes
        UNION ALL
        SELECT 'Ingredients', COUNT(*) FROM ingredients
        UNION ALL
        SELECT 'Instructions', COUNT(*) FROM instructions
        UNION ALL
        SELECT 'Tags', COUNT(*) FROM tags;
        "
        ;;

    recipes)
        query "
        SELECT id, name, difficulty, cook_time, calories
        FROM recipes
        ORDER BY id;
        "
        ;;

    easy)
        query "
        SELECT name, cook_time, calories
        FROM recipes
        WHERE difficulty = 'Easy'
        ORDER BY cook_time;
        "
        ;;

    quick)
        query "
        SELECT name, cook_time, difficulty
        FROM recipes
        WHERE cook_time <= 20
        ORDER BY cook_time;
        "
        ;;

    chicken)
        query "
        SELECT DISTINCT r.name, r.cook_time, r.calories
        FROM recipes r
        JOIN ingredients i ON r.id = i.recipe_id
        WHERE i.name LIKE '%chicken%'
        ORDER BY r.cook_time;
        "
        ;;

    ingredients)
        query "
        SELECT name, COUNT(*) as recipe_count
        FROM ingredients
        GROUP BY name
        ORDER BY recipe_count DESC
        LIMIT 20;
        "
        ;;

    sql)
        shift
        query "$*"
        ;;

    *)
        echo "Unknown option: $1"
        echo "Run './query.sh' for help"
        exit 1
        ;;
esac
