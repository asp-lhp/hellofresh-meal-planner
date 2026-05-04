# OpenClaw Integration - Shopping List Export

Export your shopping lists as structured JSON for OpenClaw AI assistant skills!

## What You Built

A clean JSON export endpoint that makes your shopping lists consumable by any OpenClaw skill:
- ✅ Structured JSON format optimized for AI assistants
- ✅ Items grouped by aisle for efficient shopping
- ✅ Bulk item warnings included
- ✅ Recipe traceability (which items are used in which recipes)
- ✅ Region-aware (en-US, en-AU, en-CA)

## Quick Start

### 1. Generate Shopping List
```bash
# Create meal plan
curl -X POST http://localhost:5098/api/meal-plans \
  -H "Content-Type: application/json" \
  -d '{"name":"This Week","startDate":"2026-03-24","endDate":"2026-03-30"}'
# Returns: {"id": 1}

# Add recipes to meal plan
curl -X POST http://localhost:5098/api/meal-plans/1/recipes \
  -d '{"recipeId":896233052,"scheduledDate":"2026-03-25","mealType":"dinner","servings":4}'

# Generate shopping list
curl -X POST http://localhost:5098/api/shopping-lists/generate/1
# Returns: {"id": 1, "totalItems": 47}
```

### 2. Export for OpenClaw
```bash
# Export as JSON
curl http://localhost:5098/api/shopping-lists/1/export | jq . > shopping-list.json

# Or save directly
curl http://localhost:5098/api/shopping-lists/1/export -o shopping-list.json
```

### 3. Use with OpenClaw Skills
```bash
# Example: Pass to OpenClaw's "anylist" skill for grocery list management
openclaw agent --message "Add these items to my grocery list" --attach shopping-list.json

# Example: Use with "clawringhouse" AI shopping concierge
openclaw agent --message "Order these groceries from Amazon Fresh" --attach shopping-list.json

# Example: Custom skill integration
cat shopping-list.json | openclaw exec my-amazon-fresh-skill
```

## API Endpoint

### GET /api/shopping-lists/{id}/export

Export shopping list in OpenClaw-optimized JSON format.

**Response Format:**
```json
{
  "version": "1.0",
  "generatedAt": "2026-03-21T23:47:39.536779Z",
  "mealPlan": {
    "name": "Test Week",
    "startDate": "2026-03-24T00:00:00",
    "endDate": "2026-03-30T00:00:00"
  },
  "totalItems": 47,
  "items": [
    {
      "name": "pork",
      "quantity": "1",
      "unit": "servings",
      "aisle": "meat",
      "isBulkItem": true,
      "bulkNote": "Consider freezing excess",
      "usedInRecipes": ["Slow cooker pulled pork"],
      "category": "meat"
    },
    {
      "name": "chicken breast",
      "quantity": "2",
      "unit": "lbs",
      "aisle": "meat",
      "isBulkItem": false,
      "bulkNote": null,
      "usedInRecipes": [
        "Chicken tikka masala",
        "One-Pan Chicken Enchiladas Verdes"
      ],
      "category": "meat"
    }
  ],
  "itemsByAisle": {
    "meat": [
      {
        "name": "pork",
        "quantity": "1",
        "unit": "servings",
        "isBulkItem": true
      },
      {
        "name": "chicken breast",
        "quantity": "2",
        "unit": "lbs",
        "isBulkItem": false
      }
    ],
    "produce": [...],
    "dairy": [...],
    "pantry": [...]
  },
  "instructions": {
    "totalRecipes": 4,
    "message": "Shopping list generated from meal plan. Items organized by aisle for efficient shopping.",
    "regions": ["en-US", "en-AU", "en-CA"]
  }
}
```

## OpenClaw Skills You Can Use

Based on the [awesome-openclaw-skills](https://github.com/VoltAgent/awesome-openclaw-skills) registry (5,400+ skills):

### 1. Grocery Management
- **[anylist](https://clawskills.sh/skills/mjrussell-anylist)** - Manage grocery and shopping lists via AnyList
- **[clawringhouse](https://clawskills.sh/skills/francoisjosephlacroix-clawringhouse)** - AI shopping concierge that anticipates needs
- **[cookidoo](https://clawskills.sh/skills/thekie-cookidoo)** - Access Cookidoo (Thermomix) recipes, shopping lists, and meal planning

### 2. Amazon Integration
- **[amazon-orders](https://clawskills.sh/skills/pfernandez98-amazon-orders)** - Download and query your Amazon order history
- **[amazon-product-api-skill](https://clawskills.sh/skills/phheng-amazon-product-api-skill)** - Extract structured product listings from Amazon
- **Custom Amazon Fresh Skill** - Build your own (see below)

### 3. Shopping & E-commerce
- **[add-wish](https://clawskills.sh/skills/leebellon-add-wish)** - Save any product to a universal wishlist
- **[atoship](https://clawskills.sh/skills/atoship-dev-atoship)** - Ship packages with AI

## Building a Custom Amazon Fresh Skill

### Option 1: Simple HTTP Forwarder
Create a skill that POSTs the shopping list to Amazon Fresh (requires Amazon Fresh API access):

```javascript
// openclaw-skill.js
export default async function amazonFreshOrder({ shoppingList }) {
  const response = await fetch('https://api.amazonfresh.com/orders', {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${process.env.AMAZON_FRESH_TOKEN}`,
      'Content-Type': 'application/json'
    },
    body: JSON.stringify({
      items: shoppingList.items.map(item => ({
        name: item.name,
        quantity: item.quantity,
        unit: item.unit
      }))
    })
  });

  return await response.json();
}
```

### Option 2: AI-Powered Product Matching
Let OpenClaw's AI match your ingredient names to Amazon Fresh products:

```bash
# Install OpenClaw
npm install -g openclaw@latest

# Create custom skill
mkdir -p ~/.openclaw/skills/amazon-fresh
cat > ~/.openclaw/skills/amazon-fresh/skill.js << 'EOF'
export default async function({ shoppingList, agent }) {
  const results = [];

  for (const item of shoppingList.items) {
    // Use AI to find best Amazon Fresh product match
    const match = await agent.think(`
      Find the best Amazon Fresh product for:
      - Item: ${item.name}
      - Quantity: ${item.quantity} ${item.unit}
      - Used in: ${item.usedInRecipes.join(', ')}
      ${item.isBulkItem ? `- BULK ITEM: ${item.bulkNote}` : ''}

      Return product ID and price.
    `);

    results.push({ item: item.name, match });
  }

  return { orderSummary: results };
}
EOF

# Use the skill
curl http://localhost:5098/api/shopping-lists/1/export | \
  openclaw agent --skill amazon-fresh
```

## Workflow Examples

### Example 1: Sunday Meal Prep → Grocery Delivery
```bash
# 1. Plan your week
curl -X POST /api/meal-plans \
  -d '{"name":"Week of March 24","startDate":"2026-03-24","endDate":"2026-03-30"}'

# 2. Add recipes
curl -X POST /api/meal-plans/1/recipes -d '{"recipeId":123456,...}'
curl -X POST /api/meal-plans/1/recipes -d '{"recipeId":789012,...}'

# 3. Generate shopping list
curl -X POST /api/shopping-lists/generate/1

# 4. Export for OpenClaw
curl /api/shopping-lists/1/export > weekly-groceries.json

# 5. Order with AI assistant
openclaw agent \
  --message "Order these groceries from Amazon Fresh for Sunday delivery" \
  --attach weekly-groceries.json
```

### Example 2: Farmers Market + Meal Planning
```bash
# 1. Add farmers market items to inventory
curl -X POST /api/inventory \
  -d '{"locationName":"fridge","itemName":"prawns","quantity":1.5,"unit":"lbs"}'

# 2. Get recipe suggestions
curl -X POST /api/recipes/suggest-from-inventory -d '{"inventoryItemIds":[5]}'
# Returns: Recipes using prawns

# 3. Build meal plan around inventory
curl -X POST /api/meal-plans/1/recipes -d '{"recipeId":<prawn-recipe>,...}'

# 4. Generate shopping list (excludes prawns - already have them!)
curl -X POST /api/shopping-lists/generate/1

# 5. Export and order remaining items
curl /api/shopping-lists/1/export | \
  openclaw agent --message "Order missing ingredients from Amazon Fresh"
```

### Example 3: Bulk Item Warning → AI Decision
```bash
# 1. Analyze meal plan
curl /api/meal-plans/1/analyze
# Returns: "pork is typically sold in 3-5 lbs. You're only using it once this week."

# 2. Ask OpenClaw for suggestions
openclaw agent --message "I have a bulk pork warning. Show me 2 more pork recipes for this week."

# 3. Add suggested recipes
curl -X POST /api/meal-plans/1/recipes -d '{"recipeId":<carnitas>,...}'
curl -X POST /api/meal-plans/1/recipes -d '{"recipeId":<pork-fried-rice>,...}'

# 4. Regenerate shopping list (no more warning!)
curl -X POST /api/shopping-lists/generate/1

# 5. Export and order
curl /api/shopping-lists/1/export | openclaw agent --skill amazon-fresh
```

## JSON Schema

For skill developers, here's the export schema:

```typescript
interface ShoppingListExport {
  version: string;
  generatedAt: string;  // ISO 8601
  mealPlan: {
    name: string;
    startDate: string;
    endDate: string;
  };
  totalItems: number;
  items: Array<{
    name: string;
    quantity: string;
    unit: string;
    aisle: string | null;
    isBulkItem: boolean;
    bulkNote: string | null;
    usedInRecipes: string[];
    category: string | null;
  }>;
  itemsByAisle: {
    [aisleName: string]: Array<{
      name: string;
      quantity: string;
      unit: string;
      isBulkItem: boolean;
    }>;
  };
  instructions: {
    totalRecipes: number;
    message: string;
    regions: string[];
  };
}
```

## Integration Checklist

- [x] Export endpoint built (`GET /api/shopping-lists/{id}/export`)
- [x] JSON format optimized for AI consumption
- [x] Bulk item warnings included
- [x] Aisle grouping for efficient shopping
- [x] Recipe traceability preserved
- [ ] OpenClaw installed (`npm install -g openclaw@latest`)
- [ ] Choose OpenClaw skill (anylist, clawringhouse, or custom)
- [ ] Set up Amazon Fresh API access (if using custom skill)
- [ ] Test export → OpenClaw → order workflow
- [ ] Automate weekly meal plan → grocery delivery

## Troubleshooting

**Q: OpenClaw can't parse my shopping list JSON**
```bash
# Validate JSON format
curl /api/shopping-lists/1/export | jq . > /dev/null && echo "Valid JSON"

# Check version
curl /api/shopping-lists/1/export | jq .version
# Should return: "1.0"
```

**Q: Amazon Fresh doesn't recognize ingredient names**
```bash
# Use AI to normalize names first
curl /api/shopping-lists/1/export | \
  openclaw agent --message "Convert these ingredient names to Amazon Fresh product names"
```

**Q: Bulk items still showing warnings**
```bash
# Analyze meal plan first
curl /api/meal-plans/1/analyze

# Add more recipes using bulk items
# Regenerate shopping list - warnings will disappear
```

## Next Steps

1. **Install OpenClaw**: `npm install -g openclaw@latest`
2. **Test Export**: `curl http://localhost:5098/api/shopping-lists/1/export | jq .`
3. **Choose Integration Path**:
   - Simple: Use existing skills (anylist, clawringhouse)
   - Advanced: Build custom Amazon Fresh skill
4. **Automate**: Set up weekly cron job for meal plan → export → order

## Resources

- [OpenClaw Documentation](https://docs.openclaw.ai)
- [OpenClaw Skills Registry](https://github.com/VoltAgent/awesome-openclaw-skills)
- [Meal Planner API Docs](./MEAL_PLANNING.md)
- [Shopping Lists Guide](./SHOPPING_LISTS.md)
- [Bulk Item Intelligence](./BULK_ITEM_INTELLIGENCE.md)

---

**Ready to automate your grocery shopping!** 🦞🛒
