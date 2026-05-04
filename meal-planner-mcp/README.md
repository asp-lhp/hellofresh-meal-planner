# Meal Planner MCP Server

An MCP (Model Context Protocol) server that exposes your C# Meal Planner API as tools for AI assistants like OpenClaw and Claude Code.

## What It Does

This MCP server acts as a bridge between AI assistants and your Meal Planner backend, allowing you to:

- Create and manage meal plans
- Search and suggest recipes
- Generate shopping lists
- Manage inventory items
- Analyze meal plans for optimization
- Get recipe suggestions from available ingredients

## Architecture

```
OpenClaw / Claude Code
         ↓
  meal-planner-mcp (Python MCP Server)
         ↓
  C# Meal Planner API (localhost:5000)
         ↓
  SQLite Database
```

## Installation

### 1. Install Dependencies

```bash
cd ~/Desktop/VS/meal-planner-mcp
pip3 install -r requirements.txt
```

### 2. Configure for OpenClaw

Add to `~/.openclaw/openclaw.json`:

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

### 3. Configure for Claude Code

Add to `~/.claude/mcp_settings.json`:

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

### 4. Start Your Meal Planner API

Make sure your C# API is running:

```bash
cd ~/Desktop/VS/meal-planner/api/MealPlanner.Api
dotnet run --urls "http://localhost:5000"
```

## Available Tools

### Meal Plans
- `list_meal_plans()` - List all meal plans
- `get_meal_plan(meal_plan_id)` - Get detailed meal plan
- `create_meal_plan(name, start_date, end_date)` - Create new meal plan
- `add_recipe_to_meal_plan(meal_plan_id, recipe_id, scheduled_date, meal_type, servings)` - Add recipe
- `analyze_meal_plan(meal_plan_id)` - Analyze for bulk items and optimization

### Recipes
- `search_recipes(query, difficulty, max_time, limit)` - Search recipes
- `get_recipe(recipe_id)` - Get recipe details
- `suggest_recipes_from_inventory(inventory_item_ids)` - Get recipe suggestions based on what you have

### Shopping
- `generate_shopping_list(meal_plan_id)` - Create shopping list from meal plan

### Inventory
- `get_inventory()` - List inventory items
- `add_to_inventory(name, quantity, unit, source)` - Add item to inventory

### Helpers
- `get_current_week_dates()` - Get this week's Monday-Sunday dates
- `get_next_week_dates()` - Get next week's dates
- `meal_planner_status()` - Check API connection

## Testing

### Test with OpenClaw CLI

```bash
# Check if it's working
openclaw agent --message "Check meal planner status"

# List meal plans
openclaw agent --message "List my meal plans"

# Create a meal plan
openclaw agent --message "Create a meal plan for this week"

# Search recipes
openclaw agent --message "Find chicken recipes under 30 minutes"
```

### Test Directly

```bash
cd ~/Desktop/VS/meal-planner-mcp
python3 server.py
```

Then use an MCP client to test the tools.

## Example Conversations

### With OpenClaw:

```
You: "Create a meal plan for this week"
OpenClaw: *calls get_current_week_dates()*
          *calls create_meal_plan()*
          "Created 'Week of March 24' from 2026-03-24 to 2026-03-30"

You: "Add some chicken recipes to it"
OpenClaw: *calls search_recipes(query="chicken", max_time=40)*
          *shows top 5 recipes*
          "Which recipes would you like to add?"

You: "Add the first three to Monday, Wednesday, and Friday"
OpenClaw: *calls add_recipe_to_meal_plan() 3 times*
          "Done! Added Chicken Pasta, Grilled Chicken, and Chicken Tacos"

You: "Generate a shopping list"
OpenClaw: *calls generate_shopping_list()*
          "Here's your shopping list: chicken breast (3 lbs), pasta (1 lb)..."

You: "Add these to my Kroger cart"
OpenClaw: *calls kroger-mcp tools*
          "Added 15 items to your Kroger cart. Total: $42.50"
```

### With Claude Code:

Same capabilities, but in the IDE:
- Suggest recipes based on code you're reading
- Create meal plans while coding
- Integrate with your development workflow

## Troubleshooting

### MCP Server Not Loading

1. Check OpenClaw config is valid:
   ```bash
   cat ~/.openclaw/openclaw.json | python3 -m json.tool
   ```

2. Verify Python path:
   ```bash
   which python3
   ```

3. Test server manually:
   ```bash
   python3 ~/Desktop/VS/meal-planner-mcp/server.py
   ```

### API Connection Failed

1. Make sure C# API is running:
   ```bash
   curl http://localhost:5000/api/meal-plans
   ```

2. Check the API URL in config matches

3. Use `meal_planner_status()` tool to diagnose

### Tools Not Appearing

1. Restart OpenClaw gateway:
   ```bash
   openclaw gateway restart
   ```

2. For Claude Code, restart the app completely

## Integration with Kroger

This MCP server works alongside the Kroger MCP server you already have configured. Example workflow:

1. Create meal plan → `meal-planner-mcp`
2. Generate shopping list → `meal-planner-mcp`
3. Search products → `kroger-mcp`
4. Add to cart → `kroger-mcp`
5. Checkout → Kroger website

## Development

To add new tools:

1. Add function with `@mcp.tool()` decorator in `server.py`
2. Make HTTP call to your C# API
3. Return structured JSON response
4. Restart MCP server

## License

MIT
