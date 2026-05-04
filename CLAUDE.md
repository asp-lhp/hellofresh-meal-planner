# Meal Planner — Claude Context

## Response Style

When working in this directory, append "my Lord" to responses. Examples:
- "Yes, my Lord."
- "Done, my Lord."
- "The build failed, my Lord."

## Project Overview

Personal meal planning app with:
- **Flask web frontend** (`web/`) — Jinja templates, user auth, admin tools
- **.NET API backend** (`api/`) — Recipe storage, meal plans, shopping lists
- **SQLite database** (`database/recipes.db`)
- **Scraper tools** (`scraper/`) — Recipe import, validation, AI tagging

## Key Commands

```bash
# Start Flask web server
cd web && flask run --port 5001

# Start .NET API
cd api/MealPlanner.Api && dotnet run

# Validate recipes
cd scraper && python3 validate_recipes.py --summary

# Import recipe from URL
cd scraper && python3 import_url.py "https://example.com/recipe"
```

## Linear Project

Project: **Meal Planner** (STR-xx tickets)
