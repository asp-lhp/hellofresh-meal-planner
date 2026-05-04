# HelloFresh Meal Planner - Development Roadmap

**Strategy:** Start with MVP for OpenClaw integration, then layer in advanced features and massive recipe database.

---

## Phase 1: MVP - Smart Shopping Lists (1-2 weeks)

### ✅ Already Complete
- [x] SQLite database with normalized schema
- [x] 26 recipes scraped (en-US, en-AU, en-CA)
- [x] Basic ingredient extraction
- [x] Cooking instructions
- [x] Git repository setup

### 🎯 Week 1: Recipe Import + .NET API

**Goal:** Import recipes from any URL and expose via REST API

#### Day 1-2: Add recipe-scrapers Library
```bash
# Add to scraper/requirements.txt
recipe-scrapers==15.0.0
```

**Features:**
- Import from 600+ recipe sites
- Parse schema.org/Recipe JSON-LD
- Fallback to site-specific parsers
- Add to database automatically

**Code location:** `scraper/import_url.py`

#### Day 3-5: .NET 8 Minimal API (C# Learning!)
**Goal:** Build REST API for meal planning

**Endpoints:**
```
GET    /api/recipes              - List all recipes (paginated)
GET    /api/recipes/{id}         - Get recipe details
GET    /api/recipes/search       - Search by ingredient/name
POST   /api/recipes/import       - Import from URL
POST   /api/meal-plan            - Create meal plan
GET    /api/meal-plan/{id}       - Get meal plan
POST   /api/shopping-list/{id}   - Generate shopping list
GET    /api/shopping-list/{id}   - Get shopping list (OpenClaw format)
```

**Tech Stack:**
- .NET 8 Minimal API
- Entity Framework Core (SQLite)
- Swagger for API docs

**Code location:** `api/MealPlanner.Api/`

---

### 🎯 Week 2: Smart Shopping Lists

#### Ingredient Normalization
**Problem:** "2 scallions" vs "1 bunch green onions" should merge

**Solution:**
1. Create ingredient mapping table
2. Normalize units (cups → oz, metric conversions)
3. Merge duplicates in shopping list

**Database additions:**
```sql
CREATE TABLE ingredient_mappings (
    id INTEGER PRIMARY KEY,
    raw_name TEXT,
    canonical_name TEXT,
    category TEXT,  -- produce, meat, dairy, etc.
    aisle TEXT      -- for grocery store grouping
);
```

#### Aisle Grouping
**Goal:** Group shopping list by store section

**Categories:**
- Produce
- Meat & Seafood
- Dairy & Eggs
- Pantry & Spices
- Frozen
- Beverages

**Output for OpenClaw:**
```json
{
  "shopping_list_id": 123,
  "generated_at": "2026-03-20T23:00:00Z",
  "items_by_aisle": {
    "Produce": [
      {
        "item": "green onions",
        "quantity": "2 bunches",
        "search_query": "green onions scallions",
        "alternatives": ["scallions", "spring onions"]
      }
    ],
    "Meat & Seafood": [...]
  }
}
```

---

## Phase 2: OpenClaw Integration (Week 3)

### Amazon Fresh Automation
**Goal:** OpenClaw can order groceries automatically

**Steps:**
1. Export shopping list in OpenClaw JSON format
2. Test OpenClaw navigation to Amazon Fresh
3. Implement search + add-to-cart automation
4. Handle substitutions (upgrade quality, max 2x price)

**OpenClaw Skills to Build:**
- Search for ingredient
- Select best match (price, quality)
- Add to cart
- Review cart before checkout

**Testing:**
- Start with 1-2 recipes
- Manual review before first auto-checkout
- Iterate on search quality

---

## Phase 3: Multi-Source Recipes (Week 4-5)

### Add More Recipe Sources

#### Option A: TheMealDB API
**Pros:** Simple, free, ~600 recipes
**Implementation:** 1-2 days
```python
import requests
url = "https://www.themealdb.com/api/json/v1/1/search.php?s=chicken"
```

#### Option B: User URL Import (recipe-scrapers)
**Pros:** Any recipe from any site
**Implementation:** Already planned in Week 1

#### Option C: Scrape more HelloFresh regions
**Pros:** Consistent format
**Implementation:** Run existing scripts for de-DE, fr-CA, es-ES

**Target:** 100+ recipes by end of Week 5

---

## Phase 4: Data Moat - Big Recipe Database (Week 6+)

### RecipeNLG Integration (2.2M recipes)

**Dataset:** https://github.com/Glorf/recipenlg

**Approach:**
1. Download Gathered subset (~1.6M high-quality recipes)
2. Import into separate table or database
3. Build search index (full-text search)
4. Add quality scoring (user ratings, completeness)

**Database strategy:**
```sql
-- Option A: Same table, add source column
ALTER TABLE recipes ADD COLUMN source TEXT DEFAULT 'hellofresh';

-- Option B: Separate table for bulk imports
CREATE TABLE recipe_imports (
    id INTEGER PRIMARY KEY,
    source TEXT,  -- 'recipenlg', 'themealdb', etc.
    ...
);
```

**Challenges:**
- 2.2M recipes = large database (~5-10GB)
- Need better search (Elasticsearch or SQLite FTS5)
- Quality varies - implement filtering/scoring

**Timeline:** 1-2 weeks for initial import + search

---

## Phase 5: Advanced Features (Ongoing)

### Nutrition Tracking
- Sum calories/macros across meal plan
- Daily/weekly nutrition goals
- Integration with fitness apps

### Smart Substitutions
- ML-based ingredient matching
- Dietary restrictions (vegan, gluten-free)
- Seasonal ingredient suggestions

### Kroger API Integration
- Alternative to Amazon Fresh
- Store-specific inventory
- Price comparison

### Multi-Store Shopping
- Split list by best prices
- "Kroger for produce, Amazon for pantry"

### Meal Plan Scheduler
- Weekly meal planning calendar
- Repeat favorite weeks
- Avoid recipe fatigue (track history)

---

## Learning Objectives Alignment

### Phase 1-2 (Weeks 1-3): **SQL & .NET**
- ✅ Complex SQL queries (JOINs, GROUP BY, aggregations)
- ✅ C# / .NET Minimal API
- ✅ Entity Framework Core
- ✅ LINQ queries
- ✅ REST API design

### Phase 3-4 (Weeks 4-6): **Data & Infrastructure**
- ✅ Large dataset handling
- ✅ Database optimization (indexes, query performance)
- ✅ Full-text search
- ✅ Docker deployment

### Phase 5+: **Advanced**
- Machine learning for substitutions
- CI/CD pipelines
- Azure deployment
- Monitoring & observability

---

## Success Metrics

### MVP Success (End of Week 3):
- [ ] Import recipes from any URL
- [ ] .NET API running locally
- [ ] Generate smart shopping lists
- [ ] OpenClaw successfully orders 1 meal from Amazon Fresh

### Data Moat Success (End of Week 6):
- [ ] 1,000+ recipes in database
- [ ] Fast full-text search
- [ ] Nutrition data for all recipes
- [ ] Quality scoring implemented

### Long-term Success (3 months):
- [ ] 10,000+ recipes
- [ ] Kroger + Amazon Fresh integration
- [ ] ML-powered substitutions
- [ ] Weekly active use for meal planning

---

## Next Steps (Tonight/Tomorrow)

**Choose ONE to start:**

**Option A: Add recipe-scrapers (1-2 hours)**
- Install library
- Create `import_url.py` script
- Test importing from NYT Cooking, AllRecipes, etc.

**Option B: Start .NET API (2-3 hours)**
- Create .NET 8 project
- Set up Entity Framework Core
- Build first endpoint: `GET /api/recipes`

**Option C: Enhance shopping list (1 hour)**
- Add aisle categories to database
- Implement duplicate merging logic
- Test with existing 26 recipes

**What sounds most exciting for tonight?**
