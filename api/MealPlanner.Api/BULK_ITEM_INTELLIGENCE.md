# Bulk Item Intelligence & Inventory-First Planning - Phase 4 Complete

Smart meal planning that prevents waste and helps you use what you already bought!

## What You Built

An intelligent validation system that:
- ✅ Analyzes meal plans for bulk items used only once
- ✅ Warns when large-package items will create waste
- ✅ Suggests recipes based on inventory items (farmers market workflow!)
- ✅ Ranks recipes by how many inventory items they use
- ✅ Prevents the "pork shoulder problem" - buying 4.5 lbs for one recipe

## Your Original Problems: SOLVED!

**Problem 1: Bulk Item Waste**
> "I want to be aware not to buy too much meat for one meal. I wouldn't want one meal that uses pulled pork during the whole week if I didn't have a plan to use the rest of it."

**Solution:**
```bash
# Create meal plan with only one pork recipe
curl -X POST /api/meal-plans/2/recipes -d '{"recipeId":896233052,...}'

# Analyze the meal plan
curl /api/meal-plans/2/analyze
```

**Response:**
```json
{
  "bulkItemWarnings": [{
    "foodName": "pork",
    "timesUsed": 1,
    "usedInRecipes": ["Slow cooker pulled pork"],
    "typicalPackageSize": "3-5 lbs",
    "recommendation": "pork is typically sold in 3-5 lbs. You're only using it once this week. Consider freezing excess"
  }]
}
```

**Problem 2: Using What You Already Bought**
> "When meal planning I might choose to buy something ahead of time, say prawns at the farmers market, so I would want to be able to add some items to my inventory, then ask for meal plans that use what I bought."

**Solution:**
```bash
# 1. Add prawns from farmers market
curl -X POST /api/inventory \
  -d '{"locationName":"fridge","itemName":"prawns","quantity":1,"unit":"lb"}'
# Returns: {"id": 5, ...}

# 2. Get recipes that use prawns
curl -X POST /api/recipes/suggest-from-inventory \
  -d '{"inventoryItemIds":[5]}'
```

**Response:**
```json
{
  "requestedItems": 1,
  "recipesFound": 3,
  "recipes": [
    {
      "recipeName": "Garlic Butter Prawns",
      "matchingIngredients": ["prawns"],
      "matchScore": 1,
      "matchPercentage": 10
    }
  ]
}
```

## New Service: MealPlanValidationService

### Location
`api/MealPlanner.Api/Services/MealPlanValidationService.cs`

### Key Methods

#### 1. AnalyzeMealPlan(int mealPlanId)
Detects waste risks in your meal plan.

```csharp
var analysis = await service.AnalyzeMealPlan(mealPlanId);

// Returns:
// - BulkItemWarnings: Items that should be used more than once
// - OptimizationTips: Ingredients used 3+ times (good for bulk buying)
```

**Logic:**
1. Collect all ingredients from all recipes in meal plan
2. Normalize ingredient names (remove "boneless", "fresh", etc.)
3. Find matching Foods in database
4. Flag bulk items (IsBulkItem = true) used only once
5. Suggest ingredients used 3+ times for bulk buying

#### 2. SuggestRecipesFromInventory(List&lt;int&gt; inventoryItemIds)
Find recipes using what you already have!

```csharp
var matches = await service.SuggestRecipesFromInventory([5, 12, 8]);

// Returns recipes sorted by:
// 1. MatchScore (how many inventory items used)
// 2. MatchPercentage (% of recipe ingredients you have)
```

**Matching Algorithm:**
```csharp
// Get inventory item names: ["chicken breast", "rice", "milk"]
var inventoryFoodNames = inventoryItems.Select(i => i.ItemName.ToLower());

// Find recipes where ANY ingredient contains ANY inventory item
var matches = recipes
    .Where(r => r.Ingredients.Any(ing =>
        inventoryFoodNames.Any(inv =>
            ing.Name.Contains(inv) || inv.Contains(ing.Name)
        )
    ));

// Calculate match score
MatchScore = matchingIngredients.Count
MatchPercentage = (matchingIngredients.Count / totalIngredients) * 100
```

### Response Models

```csharp
public class MealPlanAnalysis
{
    public int MealPlanId { get; set; }
    public string MealPlanName { get; set; }
    public int TotalRecipes { get; set; }
    public List<BulkItemWarning> BulkItemWarnings { get; set; }
    public List<OptimizationTip> OptimizationTips { get; set; }
}

public class BulkItemWarning
{
    public string FoodName { get; set; }
    public int TimesUsed { get; set; }
    public List<string> UsedInRecipes { get; set; }
    public string TypicalPackageSize { get; set; }
    public string Recommendation { get; set; }
}

public class OptimizationTip
{
    public string Category { get; set; } // "Bulk Buy Opportunity"
    public string Message { get; set; }
    public string? Savings { get; set; }
}

public class RecipeMatchScore
{
    public long RecipeId { get; set; }
    public string RecipeName { get; set; }
    public List<string> MatchingIngredients { get; set; }
    public int MatchScore { get; set; }
    public int TotalIngredients { get; set; }
    public int MatchPercentage { get; set; }
}
```

## API Endpoints (2 new)

### GET /api/meal-plans/{id}/analyze
Analyze meal plan for waste and optimization opportunities.

**Example:**
```bash
curl http://localhost:5098/api/meal-plans/2/analyze | jq .
```

**Response:**
```json
{
  "mealPlanId": 2,
  "mealPlanName": "Test Week",
  "totalRecipes": 4,
  "bulkItemWarnings": [
    {
      "foodName": "pork",
      "timesUsed": 1,
      "usedInRecipes": ["Slow cooker pulled pork"],
      "typicalPackageSize": "3-5 lbs",
      "recommendation": "pork is typically sold in 3-5 lbs. You're only using it once this week. Consider freezing excess"
    }
  ],
  "optimizationTips": []
}
```

### POST /api/recipes/suggest-from-inventory
Get recipes matching your inventory items.

**Request:**
```json
{
  "inventoryItemIds": [1, 4]
}
```

**Example:**
```bash
curl -X POST http://localhost:5098/api/recipes/suggest-from-inventory \
  -H "Content-Type: application/json" \
  -d '{"inventoryItemIds":[1,4]}' | jq .
```

**Response:**
```json
{
  "requestedItems": 2,
  "recipesFound": 12,
  "recipes": [
    {
      "recipeId": 2308689758,
      "recipeName": "Sweet & sour chicken",
      "imageUrl": "https://...",
      "totalTime": 65,
      "difficulty": null,
      "matchingIngredients": ["chicken breast", "rice"],
      "matchScore": 2,
      "totalIngredients": 13,
      "matchPercentage": 15
    },
    {
      "recipeName": "One-Pan Chicken Enchiladas Verdes",
      "matchingIngredients": ["chicken breast"],
      "matchScore": 1,
      "totalIngredients": 8,
      "matchPercentage": 12
    }
  ]
}
```

## Real-World Workflows

### Workflow 1: Sunday Farmers Market → Weekly Meal Plan

```bash
# Saturday: Buy prawns and chicken at farmers market
curl -X POST /api/inventory \
  -d '{"locationName":"fridge","itemName":"prawns","quantity":1.5,"unit":"lbs"}'

curl -X POST /api/inventory \
  -d '{"locationName":"fridge","itemName":"chicken breast","quantity":3,"unit":"lbs"}'

# Get inventory IDs
curl /api/inventory | jq '.locations[].items[] | {id, itemName}'
# Returns: [{"id": 1, "itemName": "chicken breast"}, {"id": 5, "itemName": "prawns"}]

# Find recipes using what you bought
curl -X POST /api/recipes/suggest-from-inventory \
  -d '{"inventoryItemIds":[1,5]}' | jq '.recipes[0:5]'

# Returns:
# - Sweet & sour chicken (uses chicken + rice) - MatchScore: 2
# - Garlic prawns (uses prawns) - MatchScore: 1
# - Chicken tikka masala (uses chicken) - MatchScore: 1
```

### Workflow 2: Prevent Pork Shoulder Waste

```bash
# Create meal plan
curl -X POST /api/meal-plans \
  -d '{"name":"This Week","startDate":"2026-03-24","endDate":"2026-03-30"}'
# Returns: {"id": 2}

# Add pulled pork for Wednesday
curl -X POST /api/meal-plans/2/recipes \
  -d '{"recipeId":896233052,"scheduledDate":"2026-03-26","mealType":"dinner","servings":6}'

# Analyze before shopping
curl /api/meal-plans/2/analyze | jq .bulkItemWarnings

# Output:
# [{
#   "foodName": "pork",
#   "timesUsed": 1,
#   "recommendation": "pork is typically sold in 3-5 lbs. You're only using it once..."
# }]

# DECISION: Add carnitas for Friday or plan to freeze excess!
```

### Workflow 3: Multi-Item Inventory Match

```bash
# Check what's in your fridge
curl /api/inventory | jq '.locations[] | select(.locationName=="fridge")'

# Find recipes using multiple items
curl -X POST /api/recipes/suggest-from-inventory \
  -d '{"inventoryItemIds":[1,4,3]}' \
  | jq '.recipes[] | {recipeName, matchScore, matchPercentage}'

# Results sorted by matchScore first, then matchPercentage:
# {
#   "recipeName": "Sweet & sour chicken",
#   "matchScore": 2,        # Uses 2 of your items
#   "matchPercentage": 15   # 2 out of 13 total ingredients
# }
```

## C# Learning Concepts

### 1. Ingredient Normalization
```csharp
private string NormalizeIngredientName(string name)
{
    return name.ToLowerInvariant()
        .Replace("boneless", "")
        .Replace("skinless", "")
        .Replace("fresh", "")
        .Replace("organic", "")
        .Replace("chopped", "")
        .Replace("diced", "")
        .Trim();
}

// "Boneless Skinless Chicken Breast" → "chicken breast"
// "Fresh Diced Tomatoes" → "tomatoes"
```

### 2. Dictionary Tracking
```csharp
var ingredientUsage = new Dictionary<string, IngredientUsageInfo>();

foreach (var ingredient in allIngredients)
{
    var normalizedName = NormalizeIngredientName(ingredient.Name);

    if (!ingredientUsage.ContainsKey(normalizedName))
    {
        ingredientUsage[normalizedName] = new IngredientUsageInfo();
    }

    ingredientUsage[normalizedName].TimesUsed++;
    ingredientUsage[normalizedName].UsedInRecipes.Add(recipeName);
}
```

### 3. LINQ Where + Any for Matching
```csharp
// Find recipes where ANY ingredient contains ANY inventory item
var matches = recipes
    .Where(r => r.Ingredients.Any(ing =>
        inventoryFoodNames.Any(inv =>
            ing.Name.ToLower().Contains(inv) || inv.Contains(ing.Name.ToLower())
        )
    ))
    .ToList();
```

### 4. Complex Projections with Calculations
```csharp
var match = new RecipeMatchScore
{
    RecipeId = recipe.Id,
    RecipeName = recipe.Name,
    MatchingIngredients = matchingIngredients,
    MatchScore = matchingIngredients.Count,
    TotalIngredients = recipe.Ingredients.Count,
    MatchPercentage = (int)((matchingIngredients.Count / (double)recipe.Ingredients.Count) * 100)
};
```

### 5. Multi-Level Sorting
```csharp
return matches
    .OrderByDescending(m => m.MatchScore)        // Primary: Most matches first
    .ThenByDescending(m => m.MatchPercentage)    // Secondary: Highest % first
    .ToList();
```

## Testing Examples

```bash
# 1. Add inventory items
curl -X POST /api/inventory \
  -d '{"locationName":"fridge","itemName":"chicken breast","quantity":2,"unit":"lbs"}'

curl -X POST /api/inventory \
  -d '{"locationName":"pantry","itemName":"rice","quantity":5,"unit":"lbs"}'

# 2. Get recipe suggestions
curl -X POST /api/recipes/suggest-from-inventory \
  -d '{"inventoryItemIds":[1,4]}' | jq '.recipes[] | {recipeName, matchScore}'

# 3. Create meal plan with bulk item
curl -X POST /api/meal-plans \
  -d '{"name":"Week 1","startDate":"2026-03-24","endDate":"2026-03-30"}'

curl -X POST /api/meal-plans/1/recipes \
  -d '{"recipeId":896233052,"scheduledDate":"2026-03-25","mealType":"dinner","servings":4}'

# 4. Analyze for warnings
curl /api/meal-plans/1/analyze | jq .bulkItemWarnings
```

## Integration Points

### With Shopping Lists (Future)
When generating shopping list, check inventory first:
```csharp
// Pseudo-code
var neededIngredients = mealPlan.GetAllIngredients();
var recipeSuggestions = await suggestionService.SuggestRecipesFromInventory(inventoryIds);

// Only shop for what you don't have!
```

### With Meal Planning UI (Future)
```javascript
// Show warning badge on meal plan
if (analysis.bulkItemWarnings.length > 0) {
  showWarningIcon("⚠️ Bulk items detected - review plan");
}

// Suggest additional recipes
analysis.bulkItemWarnings.forEach(warning => {
  const suggestions = await getRecipesUsing(warning.foodName);
  displaySuggestion(`Add another ${warning.foodName} recipe?`, suggestions);
});
```

## Next Enhancements

1. **Auto-Suggest Companion Recipes** - When adding bulk item recipe, automatically suggest 2-3 more using same ingredient
2. **Freezer Plan Generator** - "You'll have 3 lbs pork left - here's a freezing guide"
3. **Inventory Depletion Tracking** - Mark portions of inventory as used (1 lb of 4 lb chicken)
4. **Smart Shopping Integration** - "You have chicken - skip it on shopping list"
5. **Expiration Prioritization** - Boost match score for items expiring soon
6. **Recipe Substitution Suggestions** - "This recipe needs prawns (in your fridge) instead of shrimp"

---

**Phase 4 Complete!** You now have intelligent bulk item detection and can build meal plans around what you bought at the farmers market.
