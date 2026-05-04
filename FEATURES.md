# Feature Backlog

Ideas and features to revisit later. Organized by priority and phase.

## High Priority (MVP Features)

### 📸 Missing Recipe Images
**Problem:** Some recipes don't have images, especially from scraped sources
**Solutions:**
- **Option A:** Search for images via Unsplash/Pexels API using recipe name
- **Option B:** Generate AI images (DALL-E, Stable Diffusion) based on recipe title/ingredients
- **Option C:** Use placeholder images with recipe category icons
- **Implementation:** Add to scraper or web app as fallback

### 📅 Weekly Meal Planner
**User Story:** Select 7 recipes for the week, view in calendar format
**Features:**
- Drag-and-drop recipe selection
- Calendar view (Mon-Sun)
- Print all 7 recipes at once
- Generate combined shopping list
- Save/load meal plans

**Tech:**
- Flask route: `/meal-plan/create`
- New table: `meal_plans`, `meal_plan_recipes`
- Frontend: Simple form or drag-drop UI

### 🛒 Smart Shopping List Generator
**User Story:** Generate shopping list from selected recipes, dedupe ingredients
**Features:**
- Aggregate ingredients across multiple recipes
- Merge duplicates ("2 chicken breasts" + "1 lb chicken" = "~1.5 lbs chicken")
- Group by aisle (produce, dairy, meat, pantry)
- Export to OpenClaw JSON format
- Smart substitutions (upgrade quality, max 2x price)

**Tech:**
- Flask route: `/shopping-list/<meal_plan_id>`
- Ingredient normalization logic
- Aisle mapping database

### 🔍 Recipe Search
**User Story:** Find recipes by ingredient, name, or dietary filter
**Features:**
- Search by ingredient ("chicken", "pasta")
- Filter by difficulty, cook time, calories
- Filter by allergens (exclude nuts, dairy)
- Filter by tags (Asian, Italian, vegetarian)

**Tech:**
- Flask route: `/search?q=chicken&max_time=30`
- SQLite full-text search or simple LIKE queries

## Medium Priority (Nice to Have)

### ⭐ Favorites/Bookmarks
**User Story:** Mark favorite recipes for quick access
**Features:**
- Star/heart icon on recipe cards
- "My Favorites" page
- Local storage or database tracking

**Tech:**
- New table: `user_favorites` (recipe_id, created_at)
- Or use browser localStorage for single-user

### 📱 Progressive Web App (PWA)
**User Story:** Add meal planner to phone home screen, works offline
**Features:**
- Installable web app
- Offline recipe viewing (cached)
- Push notifications ("Time to cook!")

**Tech:**
- Service worker
- Web app manifest
- Cache API for offline recipes

### 📊 Nutrition Tracking Dashboard
**User Story:** See total nutrition for the week
**Features:**
- Weekly calorie totals
- Macros breakdown (protein/carbs/fat)
- Charts and visualizations
- Goal setting (2000 cal/day target)

**Tech:**
- Aggregate nutrition from meal plan
- Chart.js or similar for visualization

### 🤖 OpenClaw Auto-Order Integration
**User Story:** One-click grocery ordering via OpenClaw
**Features:**
- Export shopping list to OpenClaw JSON
- Trigger Amazon Fresh order
- Substitution rules (quality upgrades)
- Order history tracking

**Tech:**
- OpenClaw API integration
- JSON export endpoint
- Webhook for order confirmation

## Low Priority (Future Ideas)

### 🍽️ Meal Prep Mode
**User Story:** Batch cook recipes for the week
**Features:**
- Filter recipes good for meal prep
- Portion calculator (cook 4x servings)
- Storage instructions
- Reheating tips

### 📝 Recipe Notes & Ratings
**User Story:** Add personal notes and rate recipes
**Features:**
- 5-star rating system
- Personal notes ("Add more garlic!", "Kids loved this")
- Modifications tracking ("Used turkey instead of beef")

**Tech:**
- New tables: `recipe_ratings`, `recipe_notes`

### 🎯 Smart Recipe Recommendations
**User Story:** Get recipe suggestions based on past favorites
**Features:**
- "You might like..." recommendations
- Based on cuisine preferences
- Based on cooking frequency
- Seasonal suggestions

**Tech:**
- Simple collaborative filtering
- Or rule-based (if you liked X, try Y)

### 📦 Ingredient Inventory Tracking
**User Story:** Track what's in the pantry, suggest recipes
**Features:**
- Add items to pantry inventory
- "What can I make with X, Y, Z?"
- Expiration tracking
- Auto-remove used ingredients

**Tech:**
- New table: `pantry_inventory`
- Recipe matching algorithm

### 🌍 Multi-User / Family Mode
**User Story:** Share meal plans with family members
**Features:**
- User accounts
- Shared meal plans
- Dietary preferences per user
- Voting on recipes

**Tech:**
- User authentication (Flask-Login)
- Multi-tenancy database design

## Scraper Improvements

### 🌐 More Recipe Sources
**Current:** HelloFresh (Wayback), BBC Good Food, Budget Bytes
**Add:**
- Simply Recipes (if we can bypass 403)
- Serious Eats (if we can bypass 403)
- TheMealDB API (5,000+ recipes)
- RecipeNLG dataset (2.2M recipes)
- Tasty API
- Bon Appétit

### 🖼️ Better Image Scraping
**Current:** Some recipes missing step-by-step photos
**Improve:**
- Prioritize sites with process photos
- Download and store images locally (avoid broken links)
- Resize/optimize images for web

### 🔄 Incremental Updates
**Current:** One-time scrape
**Add:**
- Weekly scraper runs
- Update existing recipes if changed
- Track recipe version history

## .NET API Features (Phase 3 - C# Learning)

### Port Flask App to .NET
**Goal:** Rebuild Flask app in C# as learning project
**Features:**
- Minimal API with Entity Framework Core
- Same routes as Flask version
- LINQ queries (SQL in C#)
- Dependency injection
- RESTful API design

**Stack:**
- .NET 8 Minimal API
- Entity Framework Core
- SQLite provider
- Swagger/OpenAPI docs

### API Endpoints to Build
```
GET    /api/recipes               # List all recipes
GET    /api/recipes/{id}          # Get recipe details
GET    /api/recipes/search        # Search recipes
POST   /api/meal-plans            # Create meal plan
GET    /api/meal-plans/{id}       # Get meal plan
GET    /api/shopping-lists/{id}   # Generate shopping list
POST   /api/openclaw/order        # Send to OpenClaw
```

## Documentation Improvements

### Video Tutorial
- Record screen demo of using the app
- Show scraping → browsing → printing workflow

### User Guide
- Step-by-step setup instructions
- Common troubleshooting
- FAQ section

### Developer Docs
- Architecture diagram
- Database schema diagram
- API documentation
- Contribution guide

## Infrastructure (Phase 5)

### Docker Containerization
- Dockerfile for scraper
- Dockerfile for Flask/NET API
- Docker Compose for full stack

### CI/CD Pipeline
- GitHub Actions
- Auto-run tests
- Deploy on push to main

### Deployment
- Deploy to fly.io / Railway / Heroku
- Public URL for family access
- HTTPS with Let's Encrypt

---

## How to Use This File

**Adding Features:**
1. Add to appropriate priority section
2. Include user story and technical notes
3. Link to GitHub issues if created

**Picking Next Feature:**
1. Start with High Priority
2. Choose based on learning goals
3. Mark completed features with ✅

**Completed Features:**
- ✅ Recipe database (SQLite)
- ✅ Multi-source scraping (HelloFresh, BBC, Budget Bytes)
- ✅ Flask web interface
- ✅ HelloFresh-style recipe cards
- ✅ Print-friendly CSS
- ✅ Mobile-responsive design
- ✅ Recipe URL import (600+ sites supported)

---

**Last Updated:** 2026-03-21
**Current Phase:** 3 (Building .NET API)
