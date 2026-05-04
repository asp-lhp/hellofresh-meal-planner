# Meal Planner

A personal meal planning and grocery ordering system with Google OAuth authentication.

## Overview

This project scrapes HelloFresh recipes from archive.org, stores them in SQLite, provides a .NET API for meal planning, and includes a Flask web UI with user authentication.

## Tech Stack

- **Web UI**: Flask 3.0 with Jinja2 templates
- **API**: .NET 10 Minimal API with Entity Framework Core
- **Database**: SQLite
- **Auth**: Google OAuth 2.0 via Authlib + Flask-Login
- **Scraper**: Python 3.11+ with BeautifulSoup4

## Project Structure

```
meal-planner/
├── web/                  # Flask web application
│   ├── app.py           # Main Flask app with routes
│   ├── auth.py          # Google OAuth implementation
│   ├── templates/       # Jinja2 templates
│   └── static/          # CSS, JS assets
├── api/                  # .NET 10 Minimal API
│   └── MealPlanner.Api/ # EF Core models, endpoints
├── database/            
│   ├── recipes.db       # SQLite database
│   └── migrations/      # Python migration scripts
├── scraper/             # Recipe scraper
└── openclaw/            # OpenClaw integration (future)
```

## Current Status

### Completed (May 2026)

**User Authentication Milestone:**
- [x] Google OAuth login/logout flow (STR-35)
- [x] Route protection with `@login_required` (STR-36)
- [x] Multi-user data scoping for meal plans (STR-38)
- [x] Data migration to first user (STR-40)
- [x] Users table with Flask-Login integration
- [x] Database migrations for user_id columns

**Protected Routes:**
- All `/meal-plans/*` routes require login
- All `/admin/*` routes require login
- Recipe deletion requires login
- Shopping list and Walmart export verify ownership

**Kroger Integration:**
- [x] Settings page with store credentials (STR-39)
- [x] Kroger OAuth 2.0 flow with PKCE
- [x] Token storage per user
- [x] Cart API integration (/kroger/cart/add)
- [x] Product search API (/kroger/products/search)

### Remaining Work

**Kroger Cart UI** (Next up)
- Add "Send to Kroger" button on shopping list page
- Product matching (map ingredients to Kroger UPCs)
- Store location selection

## Quick Start

### Prerequisites

- Python 3.11+
- .NET 10 SDK
- Google Cloud Console project with OAuth credentials

### Environment Setup

Create `web/.env`:
```bash
API_BASE_URL=http://localhost:5098/api
DATABASE_PATH=/path/to/meal-planner/database/recipes.db
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-random-secret-key
```

### Running the Application

1. **Start the .NET API**
   ```bash
   cd api/MealPlanner.Api
   dotnet run
   # API runs on http://localhost:5098
   ```

2. **Start the Flask Web App**
   ```bash
   cd web
   source venv/bin/activate  # if using virtualenv
   pip install -r requirements.txt
   python app.py
   # Web app runs on http://localhost:5001
   ```

3. **Run Database Migrations** (if needed)
   ```bash
   cd database/migrations
   python3 run_migrations.py
   ```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Enable "Google+ API" or configure OAuth consent screen
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `http://localhost:5001/auth/google/callback`
6. Copy Client ID and Client Secret to `.env`

### Kroger API Setup

1. Go to [Kroger Developer Portal](https://developer.kroger.com/)
2. Create an account and register a new application
3. Request the following scopes: `cart.basic:write`, `product.compact`
4. Add redirect URI: `http://localhost:5001/kroger/callback`
5. Sign in to Meal Planner and go to Settings
6. Enter your Kroger Client ID and Client Secret, save
7. Click "Connect to Kroger" to authorize

## Database Schema

```sql
-- User tables (new)
users (id, google_id, email, name, avatar_url, created_at, last_login)
user_preferences (user_id, default_servings, preferred_store, theme, ...)

-- Core tables
recipes (id, slug, name, description, difficulty, ..., marked_for_deletion)
ingredients (id, recipe_id, name, quantity, image_url)
instructions (id, recipe_id, step_number, description, image_url)
tags (id, recipe_id, tag)
allergens (id, recipe_id, allergen)

-- Meal planning tables (user-scoped)
meal_plans (id, name, start_date, end_date, user_id, created_at)
meal_plan_recipes (id, meal_plan_id, recipe_id, servings, scheduled_date)
shopping_lists (id, meal_plan_id, user_id, generated_at)
shopping_list_items (id, shopping_list_id, item_name, quantity, ...)
```

## API Endpoints

### .NET API (port 5098)

- `GET /api/recipes` - List all recipes
- `GET /api/recipes/{id}` - Get recipe details
- `GET /api/recipes/search` - Search with filters
- `GET /api/meal-plans?userId=1` - List user's meal plans
- `POST /api/meal-plans` - Create meal plan (with userId)
- `GET /api/meal-plans/{id}` - Get meal plan details
- `POST /api/shopping-lists/generate/{mealPlanId}` - Generate shopping list

### Flask Routes (port 5001)

**Public:**
- `/` - Recipe grid
- `/recipe/{id}` - Recipe detail
- `/search` - Search recipes

**Protected (requires login):**
- `/meal-plans` - User's meal plans
- `/meal-plans/create` - Create new meal plan
- `/meal-plans/{id}` - View meal plan (ownership verified)
- `/meal-plans/{id}/shopping-list` - Shopping list
- `/admin/*` - Admin functions

**Auth:**
- `/auth/login` - Redirect to Google OAuth
- `/auth/google/callback` - OAuth callback
- `/auth/logout` - Sign out
- `/auth/me` - Current user info (JSON)

**Kroger Integration:**
- `/kroger/authorize` - Start Kroger OAuth flow
- `/kroger/callback` - Kroger OAuth callback
- `/kroger/disconnect` - Disconnect Kroger account
- `/kroger/status` - Check connection status (JSON)
- `/kroger/cart/add` - Add items to Kroger cart (POST)
- `/kroger/products/search` - Search Kroger products

## Development Notes

### Key Files Modified for Auth

- `web/auth.py` - Google OAuth setup, User model, login routes
- `web/kroger.py` - Kroger OAuth and Cart API integration
- `web/app.py` - Route protection, user context injection, settings
- `web/templates/base.html` - Login/logout UI in navbar
- `web/templates/settings.html` - User settings with store credentials
- `api/.../Models/MealPlan.cs` - Added UserId property
- `api/.../DTOs/MealPlanDtos.cs` - Added UserId to DTOs
- `api/.../Program.cs` - User filtering on meal plan endpoints
- `database/migrations/run_migrations.py` - User tables and credentials migration

### Testing Auth Flow

1. Start both API and Flask app
2. Visit http://localhost:5001
3. Click "Sign in with Google"
4. Complete OAuth flow
5. Should redirect back with user avatar in navbar
6. Try accessing `/meal-plans` - should show only your plans

## Linear Project

Project tracked in Linear: **Meal Planner** (Strafford workspace)

Key tickets:
- STR-35: Google OAuth implementation (Done)
- STR-36: Route protection (Done)
- STR-38: User data scoping (Done)
- STR-39: Settings page (Backlog)
- STR-40: Data migration (Done)

## License

Personal project - MIT

---

**Last updated: May 3, 2026** (Kroger OAuth integration added)
