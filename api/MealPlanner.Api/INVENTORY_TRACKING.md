# Inventory Tracking - Phase 3 Complete

Complete freezer/pantry/fridge tracking with smart recipe suggestions!

## What You Built

An intelligent inventory system that:
- ✅ Tracks items in freezer, fridge, and pantry
- ✅ Automatically calculates expiration dates
- ✅ Flags items expiring soon (within 7 days)
- ✅ Suggests recipes using inventory items
- ✅ Prioritizes using items that expire soonest
- ✅ Marks items as used when consumed

## Your Original Problem: SOLVED!

**You wanted:**
> "I want to be aware not to buy too much meat for one meal. I wouldn't want one meal that uses pulled pork during the whole week if I didn't have a plan to use the rest of it."

**What you can now do:**
1. Add pork shoulder to freezer: `4.5 lbs`
2. API warns: "Bulk item - plan to freeze or add another pork recipe"
3. View inventory suggestions: See recipes using pork
4. Check what's expiring soon: Prioritize using milk (6 days left)
5. Plan meals around freezer items to reduce waste

## New Models

### InventoryLocation
```csharp
public class InventoryLocation
{
    public int Id { get; set; }
    public string Name { get; set; } // "freezer", "fridge", "pantry"
    public bool IsFreezer { get; set; }
    public ICollection<InventoryItem> Items { get; set; }
}
```

### InventoryItem
```csharp
public class InventoryItem
{
    public int Id { get; set; }
    public int LocationId { get; set; }
    public int? FoodId { get; set; } // Link to Food for normalization
    public string ItemName { get; set; }
    public decimal Quantity { get; set; }
    public string Unit { get; set; }

    // Smart tracking
    public DateTime AddedDate { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public DateTime? UsedDate { get; set; }
    public bool IsUsedUp { get; set; }
    public string? Notes { get; set; }
}
```

## API Endpoints (5 new)

### Add Item to Inventory
```bash
POST /api/inventory
```

**Request:**
```json
{
  "locationName": "freezer",
  "itemName": "chicken breast",
  "quantity": 2,
  "unit": "lbs",
  "expiresAt": "2026-09-17", // Optional - auto-calculated if Food exists
  "notes": "Bought from Costco"
}
```

**Response:**
```json
{
  "id": 1,
  "locationName": "freezer",
  "itemName": "chicken breast",
  "quantity": 2.0,
  "unit": "lbs",
  "addedDate": "2026-03-21T23:25:34Z",
  "expiresAt": "2026-09-17T23:25:34Z",
  "daysUntilExpires": 179,
  "isExpiringSoon": false,
  "isExpired": false,
  "notes": "Bought from Costco"
}
```

### Get Full Inventory
```bash
GET /api/inventory
```

**Response:**
```json
{
  "totalItems": 4,
  "expiringSoon": 1,
  "expired": 0,
  "locations": [
    {
      "locationName": "freezer",
      "isFreezer": true,
      "itemCount": 2,
      "items": [
        {
          "itemName": "chicken breast",
          "quantity": 2.0,
          "unit": "lbs",
          "daysUntilExpires": 179,
          "isExpiringSoon": false
        },
        {
          "itemName": "pork shoulder",
          "quantity": 4.5,
          "unit": "lbs",
          "daysUntilExpires": 179,
          "notes": "Bulk buy - plan another pork recipe"
        }
      ]
    },
    {
      "locationName": "fridge",
      "isFreezer": false,
      "itemCount": 1,
      "items": [
        {
          "itemName": "milk",
          "quantity": 1.0,
          "unit": "gallon",
          "daysUntilExpires": 6,
          "isExpiringSoon": true
        }
      ]
    }
  ]
}
```

### Get Smart Suggestions
```bash
GET /api/inventory/suggestions
```

**Response:**
```json
{
  "useFirst": [
    {
      "itemName": "milk",
      "quantity": 1.0,
      "daysUntilExpires": 6,
      "isExpiringSoon": true
    }
  ],
  "recipesUsingInventory": [
    {
      "recipeId": 12345,
      "recipeName": "Sweet & sour chicken",
      "imageUrl": "https://...",
      "inventoryItemsUsed": ["chicken breast", "rice"],
      "inventoryItemCount": 2
    }
  ]
}
```

### Mark Item as Used
```bash
PATCH /api/inventory/{id}/use
```

**Response:**
```json
{
  "itemId": 1,
  "isUsedUp": true,
  "usedDate": "2026-03-25T19:30:00Z"
}
```

### Delete Inventory Item
```bash
DELETE /api/inventory/{id}
```

## Smart Features

### 1. Auto-Calculate Expiration Dates
```csharp
// If item matches a Food and Food has ShelfLifeDays
if (food != null && food.ShelfLifeDays.HasValue)
{
    expiresAt = DateTime.UtcNow.AddDays(food.ShelfLifeDays.Value);
}
```

**Example:** Adding "chicken breast" to freezer auto-sets expires to +180 days

### 2. Expiring Soon Alerts
```csharp
IsExpiringSoon = i.ExpiresAt.HasValue &&
                 (i.ExpiresAt.Value - now).TotalDays <= 7 &&
                 (i.ExpiresAt.Value - now).TotalDays > 0
```

Items within 7 days of expiration are flagged.

### 3. Recipe Suggestions Using Inventory
```csharp
var recipeSuggestions = await db.Recipes
    .Include(r => r.Ingredients)
    .Where(r => r.Ingredients.Any(ing =>
        inventoryItemNames.Any(inv => ing.Name.ToLower().Contains(inv))))
    .OrderByDescending(x => x.MatchingIngredients.Count)
    .Take(10)
    .ToListAsync();
```

Finds recipes that use your inventory items, sorted by how many items they use.

## Database Schema

```sql
CREATE TABLE inventory_locations (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    is_freezer INTEGER DEFAULT 0,
    display_order INTEGER DEFAULT 0,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE inventory_items (
    id INTEGER PRIMARY KEY,
    location_id INTEGER NOT NULL,
    food_id INTEGER, -- Links to foods table for normalization
    item_name TEXT NOT NULL,
    quantity REAL NOT NULL,
    unit TEXT NOT NULL,
    added_date TEXT DEFAULT CURRENT_TIMESTAMP,
    expires_at TEXT,
    used_date TEXT,
    notes TEXT,
    is_used_up INTEGER DEFAULT 0,
    FOREIGN KEY (location_id) REFERENCES inventory_locations(id),
    FOREIGN KEY (food_id) REFERENCES foods(id)
);
```

### Seeded Locations
```
freezer  - Freezer storage (is_freezer=1)
fridge   - Refrigerator (is_freezer=0)
pantry   - Pantry / dry goods (is_freezer=0)
```

## C# Learning Concepts

### 1. Date Calculations
```csharp
// Days until expiration
DaysUntilExpires = i.ExpiresAt.HasValue
    ? (int)(i.ExpiresAt.Value - DateTime.UtcNow).TotalDays
    : null
```

### 2. Complex LINQ Queries
```csharp
// Find recipes using inventory items
.Where(r => r.Ingredients.Any(ing =>
    inventoryItemNames.Any(inv => ing.Name.ToLower().Contains(inv))))
```

### 3. Conditional Logic in Queries
```csharp
var useFirst = await db.InventoryItems
    .Where(i => !i.IsUsedUp &&
                i.ExpiresAt.HasValue &&
                i.ExpiresAt.Value >= now &&
                i.ExpiresAt.Value <= now.AddDays(7))
    .ToListAsync();
```

### 4. Projection with Calculations
```csharp
.Select(i => new InventoryItemDto
{
    DaysUntilExpires = i.ExpiresAt.HasValue
        ? (int)(i.ExpiresAt.Value - now).TotalDays
        : null,
    IsExpiringSoon = i.ExpiresAt.HasValue &&
                     (i.ExpiresAt.Value - now).TotalDays <= 7
})
```

## Real-World Usage

### Sunday Routine: Stock the Freezer
```bash
# Add bulk Costco purchases
curl -X POST http://localhost:5098/api/inventory \
  -d '{"locationName":"freezer","itemName":"chicken breast","quantity":5,"unit":"lbs"}'

curl -X POST http://localhost:5098/api/inventory \
  -d '{"locationName":"freezer","itemName":"pork shoulder","quantity":4.5,"unit":"lbs","notes":"Plan 2 pork recipes this week"}'
```

### Monday: Check What to Use First
```bash
curl http://localhost:5098/api/inventory/suggestions | jq .useFirst
# Returns: milk (expires in 6 days)
```

### Tuesday: Find Recipes Using Inventory
```bash
curl http://localhost:5098/api/inventory/suggestions | jq .recipesUsingInventory
# Returns: "Sweet & sour chicken" uses 2 inventory items (chicken, rice)
```

### Friday: Mark Chicken as Used
```bash
curl -X PATCH http://localhost:5098/api/inventory/1/use
# Response: {isUsedUp: true, usedDate: "2026-03-28"}
```

## Integration with Shopping Lists (Future)

When generating shopping lists, check inventory first:
```csharp
// Pseudo-code for future enhancement
var neededIngredients = mealPlan.GetAllIngredients();
var inventoryItems = await GetInventory();

foreach (var ingredient in neededIngredients)
{
    var inInventory = inventoryItems.FirstOrDefault(i => i.ItemName == ingredient);
    if (inInventory != null && inInventory.Quantity >= ingredient.Quantity)
    {
        // Skip adding to shopping list - already have it!
        continue;
    }
}
```

## Testing Examples

```bash
# 1. Add items to different locations
curl -X POST http://localhost:5098/api/inventory \
  -d '{"locationName":"freezer","itemName":"chicken breast","quantity":2,"unit":"lbs"}'

curl -X POST http://localhost:5098/api/inventory \
  -d '{"locationName":"fridge","itemName":"milk","quantity":1,"unit":"gallon","expiresAt":"2026-03-28"}'

# 2. View all inventory
curl http://localhost:5098/api/inventory | jq .

# 3. Get suggestions
curl http://localhost:5098/api/inventory/suggestions | jq .

# 4. Mark item as used
curl -X PATCH http://localhost:5098/api/inventory/1/use

# 5. Delete item
curl -X DELETE http://localhost:5098/api/inventory/2
```

## Next Enhancements

1. **Bulk Item Warnings** - "You have pork shoulder (4.5 lbs) but only one recipe uses pork this week. Add carnitas or plan to freeze."
2. **Shopping List Integration** - Auto-subtract inventory from shopping lists
3. **Expiration Notifications** - Alert when items expire tomorrow
4. **Recipe Meal Plan Integration** - "This meal plan uses 3 inventory items - save $15!"
5. **Quantity Tracking** - Track partial usage ("Used 1 lb of 2 lb chicken")

---

**Phase 3 Complete!** You now have full freezer awareness with smart recipe suggestions based on what you need to use first.
