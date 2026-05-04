# Meal Planning API - C# Learning Guide

Complete guide to the meal planning endpoints you just built!

## What You Built

A full-featured meal planning API with:
- ✅ Create weekly meal plans
- ✅ Add recipes to specific days
- ✅ Track servings and meal types
- ✅ View full weekly schedule
- ✅ Remove recipes or delete plans

## C# Concepts You Learned

### 1. **One-to-Many Relationships**
```csharp
public class MealPlan
{
    public int Id { get; set; }
    public ICollection<MealPlanRecipe> Recipes { get; set; } // One plan has many recipes
}

public class MealPlanRecipe
{
    public int MealPlanId { get; set; }
    public MealPlan MealPlan { get; set; } // Many-to-one relationship
}
```

### 2. **DTOs (Data Transfer Objects)**
Separate your API contracts from internal models:
```csharp
// Request DTO - what the API accepts
public class CreateMealPlanRequest
{
    public string Name { get; set; }
    public DateTime StartDate { get; set; }
}

// Response DTO - what the API returns
public class MealPlanSummary
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int RecipeCount { get; set; }
}
```

### 3. **POST Endpoints (Creating Data)**
```csharp
app.MapPost("/api/meal-plans", async (CreateMealPlanRequest request, MealPlannerContext db) =>
{
    var mealPlan = new MealPlan { Name = request.Name, ... };
    db.MealPlans.Add(mealPlan);
    await db.SaveChangesAsync();
    return Results.Created($"/api/meal-plans/{mealPlan.Id}", response);
});
```

### 4. **Include() - Eager Loading**
Load related data in one query:
```csharp
var mealPlan = await db.MealPlans
    .Include(m => m.Recipes)           // Load recipes
        .ThenInclude(mr => mr.Recipe)  // Load recipe details
    .FirstOrDefaultAsync(m => m.Id == id);
```

### 5. **LINQ Projections**
Transform data with `Select()`:
```csharp
var summary = await db.MealPlans
    .Select(m => new MealPlanSummary
    {
        Id = m.Id,
        RecipeCount = m.Recipes.Count  // Aggregate in database
    })
    .ToListAsync();
```

### 6. **RESTful Response Codes**
```csharp
return Results.Created(...);     // 201 Created
return Results.Ok(...);          // 200 OK
return Results.NotFound(...);    // 404 Not Found
```

## API Endpoints

### Create Meal Plan
```bash
POST /api/meal-plans
Content-Type: application/json

{
  "name": "Week of March 24",
  "startDate": "2026-03-24",
  "endDate": "2026-03-30"
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Week of March 24",
  "startDate": "2026-03-24T00:00:00",
  "endDate": "2026-03-30T00:00:00",
  "recipeCount": 0,
  "createdAt": "2026-03-21T23:10:01Z"
}
```

### Add Recipe to Plan
```bash
POST /api/meal-plans/1/recipes
Content-Type: application/json

{
  "recipeId": 692,
  "scheduledDate": "2026-03-24",
  "mealType": "dinner",
  "servings": 2
}
```

**Response (201 Created):**
```json
{
  "id": 1,
  "recipeId": 692,
  "recipeName": "Mozzarella-Cauli Bites & Smashed Potatoes",
  "recipeImageUrl": "...",
  "totalTime": 40,
  "scheduledDate": "2026-03-24T00:00:00",
  "mealType": "dinner",
  "servings": 2
}
```

### Get Meal Plan Details
```bash
GET /api/meal-plans/1
```

**Response (200 OK):**
```json
{
  "id": 1,
  "name": "Week of March 24",
  "startDate": "2026-03-24T00:00:00",
  "endDate": "2026-03-30T00:00:00",
  "createdAt": "2026-03-21T23:10:01Z",
  "recipes": [
    {
      "id": 1,
      "recipeId": 692,
      "recipeName": "Mozzarella-Cauli Bites & Smashed Potatoes",
      "recipeImageUrl": "...",
      "totalTime": 40,
      "calories": null,
      "scheduledDate": "2026-03-24T00:00:00",
      "mealType": "dinner",
      "servings": 2
    }
  ]
}
```

### List All Meal Plans
```bash
GET /api/meal-plans
```

**Response (200 OK):**
```json
[
  {
    "id": 1,
    "name": "Week of March 24",
    "startDate": "2026-03-24T00:00:00",
    "endDate": "2026-03-30T00:00:00",
    "recipeCount": 7,
    "createdAt": "2026-03-21T23:10:01Z"
  }
]
```

### Remove Recipe from Plan
```bash
DELETE /api/meal-plans/1/recipes/3
```

**Response (200 OK):**
```json
{
  "message": "Recipe removed from meal plan"
}
```

### Delete Meal Plan
```bash
DELETE /api/meal-plans/1
```

**Response (200 OK):**
```json
{
  "message": "Meal plan deleted"
}
```

## Database Schema

```sql
CREATE TABLE meal_plans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE meal_plan_recipes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    meal_plan_id INTEGER NOT NULL,
    recipe_id INTEGER NOT NULL,
    scheduled_date TEXT NOT NULL,
    meal_type TEXT DEFAULT 'dinner',
    servings INTEGER DEFAULT 2,
    added_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id) ON DELETE CASCADE,
    FOREIGN KEY (recipe_id) REFERENCES recipes(id) ON DELETE CASCADE
);
```

## Testing Examples

### Create a Full Week Plan

```bash
# 1. Create meal plan
PLAN_ID=$(curl -s -X POST http://localhost:5098/api/meal-plans \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Week of March 24",
    "startDate": "2026-03-24",
    "endDate": "2026-03-30"
  }' | jq -r '.id')

# 2. Add Monday dinner
curl -X POST http://localhost:5098/api/meal-plans/$PLAN_ID/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "recipeId": 692,
    "scheduledDate": "2026-03-24",
    "mealType": "dinner",
    "servings": 2
  }'

# 3. Add Tuesday dinner
curl -X POST http://localhost:5098/api/meal-plans/$PLAN_ID/recipes \
  -H "Content-Type: application/json" \
  -d '{
    "recipeId": 6984,
    "scheduledDate": "2026-03-25",
    "mealType": "dinner",
    "servings": 2
  }'

# 4. View full plan
curl http://localhost:5098/api/meal-plans/$PLAN_ID | jq .
```

## EF Core Relationship Configuration

```csharp
// In MealPlannerContext.cs
modelBuilder.Entity<MealPlanRecipe>(entity =>
{
    entity.HasOne(e => e.MealPlan)
        .WithMany(m => m.Recipes)
        .HasForeignKey(e => e.MealPlanId)
        .OnDelete(DeleteBehavior.Cascade);  // Delete recipes when plan is deleted

    entity.HasOne(e => e.Recipe)
        .WithMany()
        .HasForeignKey(e => e.RecipeId)
        .OnDelete(DeleteBehavior.Cascade);
});
```

## Common Patterns Explained

### Pattern 1: Find vs FirstOrDefaultAsync
```csharp
// FindAsync - Fast for primary key lookups
var plan = await db.MealPlans.FindAsync(id);

// FirstOrDefaultAsync - For queries with filters or includes
var plan = await db.MealPlans
    .Include(m => m.Recipes)
    .FirstOrDefaultAsync(m => m.Id == id);
```

### Pattern 2: Add vs AddRange
```csharp
// Add single entity
db.MealPlans.Add(mealPlan);

// Add multiple entities
db.MealPlanRecipes.AddRange(recipes);
```

### Pattern 3: Projection for Performance
```csharp
// Bad - Loads all fields
var plans = await db.MealPlans.ToListAsync();

// Good - Only loads needed fields
var plans = await db.MealPlans
    .Select(m => new { m.Id, m.Name })
    .ToListAsync();
```

## Next Steps

Now that you have meal planning working, you can:

1. **Build UI in Flask** - Display meal plans in web app
2. **Add Shopping List Generation** - Aggregate ingredients from week's recipes
3. **Add Inventory** - Track what's in your freezer
4. **Smart Suggestions** - Recipes that use frozen items first

## Comparison: Python vs C#

| Task | Python/Flask | C#/.NET |
|------|-------------|---------|
| Create Plan | `db.execute("INSERT...")` | `db.MealPlans.Add(plan)` |
| Load Relations | Manual JOIN | `Include(m => m.Recipes)` |
| Validation | Manual checks | Built-in model validation |
| Type Safety | Runtime errors | Compile-time errors |
| Performance | Good | Excellent |

---

**Great job!** You just built a complete meal planning API in C# with proper architecture, DTOs, and EF Core relationships.
