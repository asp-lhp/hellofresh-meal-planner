# Meal Planner MCP - Quick Start Guide

## ✅ What's Been Built

You now have a **Model Context Protocol (MCP) server** that connects OpenClaw and Claude Code to your Meal Planner C# API!

```
OpenClaw / Claude Code
         ↓
  meal-planner-mcp (Python)
         ↓
  C# Meal Planner API
         ↓
  SQLite Database
```

## 📦 Installation Complete

✅ MCP server created at: `~/Desktop/VS/meal-planner-mcp/`
✅ Dependencies installed (fastmcp, httpx)
✅ OpenClaw configured: `~/.openclaw/openclaw.json`
✅ 16 tools available for AI assistants

## 🛠️ Available Tools

### Meal Plans
- `list_meal_plans()` - List all meal plans
- `get_meal_plan(meal_plan_id)` - Get meal plan details
- `create_meal_plan(name, start_date, end_date)` - Create new plan
- `add_recipe_to_meal_plan(...)` - Add recipe to plan
- `analyze_meal_plan(meal_plan_id)` - Check for bulk items

### Recipes
- `search_recipes(query, difficulty, max_time, limit)` - Find recipes
- `get_recipe(recipe_id)` - Get recipe details
- `suggest_recipes_from_inventory(inventory_item_ids)` - Get suggestions

### Shopping
- `generate_shopping_list(meal_plan_id)` - Create shopping list

### Inventory
- `get_inventory()` - List inventory items
- `add_to_inventory(name, quantity, unit, source)` - Add items

### Helpers
- `get_current_week_dates()` - Get this week's dates
- `get_next_week_dates()` - Get next week's dates
- `meal_planner_status()` - Check API connection

## 🚀 How to Use

### Step 1: Start Your C# API

```bash
cd ~/Desktop/VS/meal-planner/api/MealPlanner.Api
dotnet run --urls "http://localhost:5000"
```

Leave this running in one terminal.

### Step 2: Use with OpenClaw CLI

```bash
# Check status
openclaw agent --message "Check meal planner status"

# List meal plans
openclaw agent --message "Show me my meal plans"

# Create a new meal plan
openclaw agent --message "Create a meal plan for this week called 'Healthy Week'"

# Search recipes
openclaw agent --message "Find easy chicken recipes under 30 minutes"

# Generate shopping list
openclaw agent --message "Generate a shopping list for meal plan #1"
```

### Step 3: Use with Claude Code

1. **Add to Claude Code config** (`~/.claude/mcp_settings.json`):

```json
{
  "mcpServers": {
    "meal-planner": {
      "command": "/Library/Frameworks/Python.framework/Versions/3.12/bin/python3",
      "args": ["/Users/andresprague/Desktop/VS/meal-planner-mcp/server.py"],
      "env": {
        "MEAL_PLANNER_API_URL": "http://localhost:5000/api"
      }
    }
  }
}
```

2. **Restart Claude Code**

3. **Use in your IDE:**
   - "Create a meal plan for next week"
   - "Search for vegetarian recipes"
   - "Generate shopping list and add to Kroger cart"

## 🔗 Integration with Kroger

Your meal planner MCP works alongside Kroger! Example workflow:

```
1. "Create a meal plan for this week" → meal-planner-mcp
2. "Add 5 chicken recipes to it" → meal-planner-mcp
3. "Generate shopping list" → meal-planner-mcp
4. "Add these items to my Kroger cart" → kroger-mcp
5. "Checkout" → Kroger website
```

## 💡 Example Conversations

### With OpenClaw:

```
You: "Create a meal plan for this week"

OpenClaw:
*calls get_current_week_dates()*
*calls create_meal_plan("Week of March 24", "2026-03-24", "2026-03-30")*

✓ Created "Week of March 24" from March 24 to March 30
```

```
You: "Find easy recipes under 30 minutes"

OpenClaw:
*calls search_recipes(difficulty="easy", max_time=30, limit=10)*

Found 10 recipes:
1. Chicken Pasta (25 min) ⭐4.5
2. Quick Stir Fry (20 min) ⭐4.7
3. Simple Tacos (15 min) ⭐4.3
...
```

```
You: "Add recipe #692 to Monday dinner for 2 people"

OpenClaw:
*calls add_recipe_to_meal_plan(1, 692, "2026-03-24", "dinner", 2)*

✓ Added "Mozzarella-Cauli Bites" to Monday dinner (2 servings)
```

```
You: "Generate shopping list and add to Kroger"

OpenClaw:
*calls generate_shopping_list(1)*
*calls kroger search_products for each item*
*calls kroger add_to_cart for each*

✓ Added 15 items to your Kroger cart
Total: $42.50
```

## 🧪 Testing

### Test the MCP Server Directly:

```bash
cd ~/Desktop/VS/meal-planner-mcp
python3 server.py
```

You should see:
```
🖥  Server: Meal Planner
INFO Starting MCP server 'Meal Planner' with transport 'stdio'
```

Press Ctrl+C to stop.

### Test API Connection:

```bash
# Make sure API is running
curl http://localhost:5000/api/meal-plans
```

Should return JSON with meal plans.

## 🔧 Troubleshooting

### "Could not connect to Meal Planner API"

1. Make sure C# API is running:
   ```bash
   curl http://localhost:5000/api/health
   ```

2. Check the API URL in config matches

3. Look at server logs for errors

### "MCP Server not loading in OpenClaw"

1. Validate config:
   ```bash
   cat ~/.openclaw/openclaw.json | python3 -m json.tool
   ```

2. Test server manually:
   ```bash
   python3 ~/Desktop/VS/meal-planner-mcp/server.py
   ```

3. Check OpenClaw logs:
   ```bash
   openclaw gateway logs
   ```

### "Tools not appearing"

1. For OpenClaw: Restart gateway
   ```bash
   openclaw gateway restart
   ```

2. For Claude Code: Fully quit and restart the app

## 📚 Documentation

- **Full README**: `~/Desktop/VS/meal-planner-mcp/README.md`
- **Server Code**: `~/Desktop/VS/meal-planner-mcp/server.py`
- **Interface Options**: `~/Desktop/VS/OPENCLAW_INTERFACE_OPTIONS.md`

## 🎯 Next Steps

1. **Test it**: Try the example commands above
2. **Integrate with Kroger**: Use both MCP servers together
3. **Build workflows**: Combine meal planning + shopping automation
4. **Add more tools**: Extend `server.py` with new capabilities

## 🚀 You're Ready!

Your Meal Planner is now accessible to AI assistants. Start with:

```bash
openclaw agent --message "Check meal planner status"
```

Happy meal planning! 🍽️
