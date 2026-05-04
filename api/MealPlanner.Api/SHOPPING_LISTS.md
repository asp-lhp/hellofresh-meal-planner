# Shopping List Generation - Phase 2 Complete

Complete shopping list system with food normalization and aisle grouping!

## What You Built

A smart shopping list generator that:
- ✅ Extracts all ingredients from a meal plan's recipes
- ✅ Normalizes ingredients to common foods (chicken breast → chicken)
- ✅ Consolidates duplicate items across recipes
- ✅ Groups items by aisle (meat, produce, dairy, pantry)
- ✅ Flags bulk items (pork shoulder) with usage notes
- ✅ Tracks which recipes use each ingredient

## New Models

### Food (Hierarchical Normalization)
```csharp
public class Food
{
    public int Id { get; set; }
    public string Name { get; set; }
    public int? ParentFoodId { get; set; }  // Supports hierarchy
    public Food? ParentFood { get; set; }

    // Organization
    public string? Aisle { get; set; }  // "meat", "produce", "dairy"
    public int? AisleOrder { get; set; }

    // Bulk item handling
    public bool IsBulkItem { get; set; }
    public string? TypicalPackageSize { get; set; }  // "4-6 lbs"
    public string? BulkItemNote { get; set; }

    // Freezer awareness
    public bool FreezesWell { get; set; }
    public int? ShelfLifeDays { get; set; }
}
```

### ShoppingList & ShoppingListItem
```csharp
public class ShoppingList
{
    public int Id { get; set; }
    public int MealPlanId { get; set; }
    public ICollection<ShoppingListItem> Items { get; set; }
}

public class ShoppingListItem
{
    public int? FoodId { get; set; }  // Link to normalized food
    public string ItemName { get; set; }
    public string Quantity { get; set; }
    public string? Aisle { get; set; }
    public bool IsBulkItem { get; set; }
    public string? UsedInRecipes { get; set; }  // JSON array
}
```

## Food Hierarchy Example

```
chicken (parent)
├── chicken breast (child)
└── chicken thigh (child)

pork (parent)
└── pork shoulder (child, bulk item)
```

When recipes use "boneless chicken breast" and "chicken thighs", they both map to parent "chicken" for consolidation.

## API Endpoints

### Generate Shopping List
```bash
POST /api/shopping-lists/generate/{mealPlanId}
```

**Response:**
```json
{
  "id": 1,
  "mealPlanId": 1,
  "mealPlanName": "Week of March 24",
  "totalItems": 24,
  "itemsByAisle": {
    "meat": [
      {
        "itemName": "tilapia",
        "quantity": "1",
        "unit": "servings",
        "usedInRecipes": ["Swicy Poke-Inspired Tilapia Bowls"]
      }
    ],
    "pantry": [
      {
        "itemName": "rice",
        "quantity": "3",
        "unit": "servings",
        "usedInRecipes": ["Recipe 1", "Recipe 2", "Recipe 3"]
      }
    ],
    "produce": [
      {
        "itemName": "garlic",
        "quantity": "3",
        "unit": "servings",
        "usedInRecipes": ["Recipe A", "Recipe B", "Recipe C"]
      }
    ]
  }
}
```

### Get Shopping List
```bash
GET /api/shopping-lists/{id}
```

**Response (Grouped by Aisle):**
```json
{
  "mealPlanName": "Week of March 24",
  "totalItems": 24,
  "aisles": [
    {
      "aisleName": "meat",
      "items": [...]
    },
    {
      "aisleName": "produce",
      "items": [...]
    }
  ]
}
```

### Toggle Item Checked
```bash
PATCH /api/shopping-lists/{id}/items/{itemId}/check
```

**Response:**
```json
{
  "itemId": 5,
  "isChecked": true
}
```

## ShoppingListService - Business Logic

The `ShoppingListService` handles the complex logic:

```csharp
public async Task<ShoppingList> GenerateShoppingList(int mealPlanId)
{
    // 1. Load meal plan with all recipes and ingredients
    // 2. Normalize ingredient names (remove "boneless", "fresh", etc.)
    // 3. Find matching Food for each ingredient
    // 4. Consolidate duplicates
    // 5. Group by aisle
    // 6. Flag bulk items
    // 7. Track which recipes use each ingredient
}
```

### Ingredient Normalization

```csharp
private string NormalizeIngredientName(string name)
{
    return name.ToLowerInvariant()
        .Replace("boneless", "")
        .Replace("skinless", "")
        .Replace("fresh", "")
        .Replace("organic", "")
        .Trim();
}
```

### Food Matching

```csharp
private async Task<Food?> FindFoodByName(string ingredientName)
{
    // Try exact match first
    var exactMatch = await _db.Foods
        .FirstOrDefaultAsync(f => f.Name.ToLower() == ingredientName.ToLower());

    if (exactMatch != null)
        return exactMatch;

    // Try contains match (ingredient contains food name)
    var containsMatch = await _db.Foods
        .FirstOrDefaultAsync(f => ingredientName.ToLower().Contains(f.Name.ToLower()));

    return containsMatch;
}
```

## Database Schema

```sql
CREATE TABLE foods (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    parent_food_id INTEGER,
    aisle TEXT,
    is_bulk_item INTEGER DEFAULT 0,
    bulk_item_note TEXT,
    freezes_well INTEGER DEFAULT 0,
    FOREIGN KEY (parent_food_id) REFERENCES foods(id)
);

CREATE TABLE shopping_lists (
    id INTEGER PRIMARY KEY,
    meal_plan_id INTEGER NOT NULL,
    generated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (meal_plan_id) REFERENCES meal_plans(id)
);

CREATE TABLE shopping_list_items (
    id INTEGER PRIMARY KEY,
    shopping_list_id INTEGER NOT NULL,
    food_id INTEGER,
    item_name TEXT NOT NULL,
    quantity TEXT NOT NULL,
    aisle TEXT,
    is_bulk_item INTEGER DEFAULT 0,
    bulk_item_note TEXT,
    checked INTEGER DEFAULT 0,
    used_in_recipes TEXT,
    FOREIGN KEY (shopping_list_id) REFERENCES shopping_lists(id),
    FOREIGN KEY (food_id) REFERENCES foods(id)
);
```

## Seeded Foods (31 total)

**Meat & Poultry:**
- chicken, chicken breast, chicken thigh
- beef, ground beef
- pork, pork shoulder (bulk item!)
- salmon, tilapia

**Produce:**
- onion, garlic, tomato, bell pepper
- lettuce, carrot, potato

**Dairy:**
- milk, cheese, butter, eggs, yogurt

**Pantry:**
- olive oil, salt, pepper, flour, sugar, rice, pasta

**Frozen:**
- frozen peas, frozen corn, ice cream

## C# Learning Concepts

### 1. Service Layer Pattern
```csharp
// Separate business logic from endpoints
builder.Services.AddScoped<ShoppingListService>();

// Inject into endpoints
app.MapPost("/api/shopping-lists/generate/{id}",
    async (int id, ShoppingListService service) => { ... });
```

### 2. Self-Referencing Relationships
```csharp
public class Food
{
    public int? ParentFoodId { get; set; }
    public Food? ParentFood { get; set; }
    public ICollection<Food> ChildFoods { get; set; }
}

// EF Core configuration
entity.HasOne(e => e.ParentFood)
    .WithMany(f => f.ChildFoods)
    .HasForeignKey(e => e.ParentFoodId)
    .OnDelete(DeleteBehavior.Restrict);  // Prevent cascade delete loops
```

### 3. JSON Serialization for Storage
```csharp
// Store array of recipe names as JSON string
item.UsedInRecipes = JsonSerializer.Serialize(recipeNames);

// Deserialize when reading
var recipes = JsonSerializer.Deserialize<List<string>>(item.UsedInRecipes ?? "[]");
```

### 4. Dictionary GroupBy
```csharp
var itemsByAisle = list.Items
    .GroupBy(i => i.Aisle ?? "Other")
    .ToDictionary(
        g => g.Key,
        g => g.OrderBy(i => i.DisplayOrder).ToList()
    );
```

## Testing Example

```bash
# 1. Create a meal plan (or use existing ID: 1)

# 2. Generate shopping list
curl -X POST http://localhost:5098/api/shopping-lists/generate/1 | jq .

# 3. View by aisle
LIST_ID=1
curl http://localhost:5098/api/shopping-lists/$LIST_ID | jq .

# 4. Check off an item
curl -X PATCH http://localhost:5098/api/shopping-lists/1/items/5/check
```

## Output Example

```json
{
  "mealPlanName": "Week of March 24",
  "totalItems": 24,
  "aisles": [
    {
      "aisleName": "meat",
      "items": [
        {
          "itemName": "tilapia",
          "quantity": "1",
          "unit": "servings",
          "isBulkItem": false,
          "usedInRecipes": ["Tilapia Bowls"]
        }
      ]
    },
    {
      "aisleName": "pantry",
      "items": [
        {
          "itemName": "rice",
          "quantity": "3",
          "unit": "servings",
          "usedInRecipes": ["Salmon Bowls", "Tilapia Bowls", "Steak"]
        }
      ]
    }
  ]
}
```

## Next Phase: Bulk Item Intelligence

The foundation is in place for:
- **Bulk item warnings:** "Pork shoulder is 4-6 lbs, but you only need 2 lbs. Add another pork recipe or plan to freeze."
- **Inventory integration:** Check if you already have items in freezer
- **Smart consolidation:** Better quantity aggregation (1 cup + 2 cups = 3 cups)
- **Unit conversion:** Convert "2 cups" to "1 pint" or "8 oz"

## OpenClaw Integration Ready

The shopping list format is ready for OpenClaw:
```json
{
  "shoppingList": [
    {
      "item": "tilapia",
      "quantity": "1 lb",
      "searchQuery": "tilapia fresh",
      "maxPriceMultiplier": 2.0
    }
  ]
}
```

---

**Phase 2 Complete!** You now have intelligent shopping list generation with ingredient normalization and aisle grouping.
