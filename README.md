# Meal Planner

A private, self-hosted meal planning app for me and close friends.

## Vision

**Private by default.** Not indexed, not discoverable. Invite-only access.

**Self-hosted.** Runs on infrastructure I control. Custom domain, HTTPS, no tracking.

**Small audience.** 5-15 people who actually cook. Not a startup, not a product.

**Simple over scalable.** If it works for 10 users, that's success.

### Access Model

- Google OAuth for authentication
- Invite-only whitelist — admin approves new users
- No public signup

### Success Looks Like

- I use this weekly for meal planning
- A few friends actually use it
- Shopping trips are faster
- I learned .NET and had fun building it

---

## Features

### Done

**Core**
- [x] SQLite database with normalized schema
- [x] .NET 10 Minimal API with Entity Framework Core
- [x] Flask web UI with Jinja2 templates
- [x] Mobile-responsive design
- [x] Print-friendly recipe cards

**Recipes**
- [x] Recipe library (~26 recipes)
- [x] Recipe search by name/ingredient
- [x] Recipe import from 600+ sites (recipe-scrapers)
- [x] Multi-source scraping (HelloFresh, BBC, Budget Bytes)
- [x] Cooking instructions with step images

**Meal Planning**
- [x] Create/manage meal plans
- [x] Calendar view for weekly planning
- [x] Shopping list generation
- [x] Aisle grouping (produce, dairy, meat, pantry)
- [x] Ingredient deduplication

**Auth & Users**
- [x] Google OAuth login/logout
- [x] Route protection (`@login_required`)
- [x] Multi-user data scoping
- [x] Users table with Flask-Login
- [x] Per-user settings page

**Kroger Integration**
- [x] OAuth 2.0 flow with PKCE
- [x] Token storage per user
- [x] Cart API integration
- [x] Product search API

### In Progress

- [ ] "Send to Kroger" button on shopping list
- [ ] Product matching (ingredients → Kroger UPCs)
- [ ] Store location selection

### Next Up

- [ ] Invite-only whitelist implementation
- [ ] Custom domain + fly.io deployment
- [ ] CI/CD pipeline (GitHub Actions)

### Backlog

**High Priority**
- [ ] Recipe database audit — review all recipes, remove any with missing/bad data, keep only quality entries
- [ ] Better ingredient normalization ("2 scallions" + "1 bunch green onions" → merge)
- [ ] Missing recipe image handling (placeholders or search Unsplash)
- [ ] Full-text search for recipes

**Medium Priority**
- [ ] Favorites/bookmarks for recipes
- [ ] Recipe notes & personal ratings
- [ ] Nutrition tracking dashboard
- [ ] PWA support (installable, offline recipes)

**Low Priority**
- [ ] Multi-store support (Walmart, Amazon Fresh)
- [ ] Meal prep mode (batch cooking, portions)
- [ ] Smart recipe recommendations
- [ ] Ingredient inventory tracking ("what can I make?")
- [ ] Shared meal plans between users

### Not Building

- Social features (comments, sharing)
- Ads or monetization
- Native mobile app
- AI-generated recipes

---

## Roadmap

### Phase 1: Core Features — Done
SQLite, .NET API, Flask UI, Google OAuth, Kroger integration

### Phase 2: Shopping Experience — Current
Complete Kroger cart workflow, ingredient normalization, recipe import polish

### Phase 3: Deploy & Access Control
Custom domain, invite-only whitelist, CI/CD, fly.io hosting

### Phase 4: Polish
Favorites, ratings, nutrition, PWA

---

## Tech Stack

- **Web UI**: Flask 3.0, Jinja2, Tailwind CSS
- **API**: .NET 10 Minimal API, Entity Framework Core
- **Database**: SQLite
- **Auth**: Google OAuth 2.0 (Authlib + Flask-Login)
- **Scraper**: Python 3.11+, BeautifulSoup4
- **Hosting**: fly.io (planned)

## Project Structure

```
meal-planner/
├── web/                  # Flask web application
│   ├── app.py            # Main app with routes
│   ├── auth.py           # Google OAuth
│   ├── kroger.py         # Kroger integration
│   └── templates/        # Jinja2 templates
├── api/                  # .NET 10 Minimal API
│   └── MealPlanner.Api/  # EF Core models, endpoints
├── database/
│   ├── recipes.db        # SQLite database
│   └── migrations/       # Migration scripts
├── scraper/              # Recipe scraper
├── docs/                 # Additional documentation
└── scripts/              # Utility scripts
```

---

## Quick Start

### Prerequisites

- Python 3.11+
- .NET 10 SDK
- Google Cloud project with OAuth credentials

### Environment Setup

Create `web/.env`:
```bash
API_BASE_URL=http://localhost:5098/api
DATABASE_PATH=/path/to/meal-planner/database/recipes.db
GOOGLE_CLIENT_ID=your-client-id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your-client-secret
SECRET_KEY=your-random-secret-key
```

### Running Locally

1. **Start the .NET API**
   ```bash
   cd api/MealPlanner.Api
   dotnet run
   # Runs on http://localhost:5098
   ```

2. **Start the Flask Web App**
   ```bash
   cd web
   source venv/bin/activate
   pip install -r requirements.txt
   python app.py
   # Runs on http://localhost:5001
   ```

3. **Run Migrations** (if needed)
   ```bash
   cd database/migrations
   python3 run_migrations.py
   ```

### Google OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com/)
2. Create/select a project
3. Configure OAuth consent screen
4. Create OAuth 2.0 credentials (Web application)
5. Add redirect URI: `http://localhost:5001/auth/google/callback`
6. Copy Client ID and Secret to `.env`

### Kroger API Setup

1. Register at [Kroger Developer Portal](https://developer.kroger.com/)
2. Create app with scopes: `cart.basic:write`, `product.compact`
3. Add redirect URI: `http://localhost:5001/kroger/callback`
4. In Meal Planner Settings, enter credentials and connect

---

## Linear Project

Tracked in Linear: **Meal Planner** (Strafford workspace)

---

## License

Personal project — MIT

---

*Last updated: May 2026*
