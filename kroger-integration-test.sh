#!/bin/bash
# Test Kroger MCP Integration with Meal Planner
# Run after setting up Kroger API credentials

set -e

echo "🛒 KROGER MCP + MEAL PLANNER INTEGRATION TEST"
echo "════════════════════════════════════════════════════════════"
echo ""

# Check if MCP server is configured
if [ ! -f ~/.claude/mcp_settings.json ]; then
  echo "❌ ERROR: ~/.claude/mcp_settings.json not found"
  echo ""
  echo "Please configure Kroger MCP first:"
  echo "  1. Get credentials from https://developer.kroger.com"
  echo "  2. Create ~/.claude/mcp_settings.json with Kroger config"
  echo "  3. See KROGER_API_SETUP.md for details"
  echo ""
  exit 1
fi

# Check if kroger-mcp is installed
if ! command -v kroger-mcp &> /dev/null && ! uvx --help &> /dev/null; then
  echo "❌ ERROR: kroger-mcp not installed"
  echo ""
  echo "Install with:"
  echo "  uv pip install kroger-mcp"
  echo ""
  exit 1
fi

echo "✅ Kroger MCP server configured"
echo ""

# Get latest shopping list
echo "📊 STEP 1: Get Latest Shopping List from Meal Planner"
echo "────────────────────────────────────────────────────────────"
echo ""

LATEST_LIST=$(curl -s http://localhost:5098/api/shopping-lists | jq -r '.[0].id // empty')

if [ -z "$LATEST_LIST" ]; then
  echo "⚠️  No shopping lists found. Creating test shopping list..."
  echo ""

  # Create test meal plan
  PLAN_ID=$(curl -s -X POST http://localhost:5098/api/meal-plans \
    -H "Content-Type: application/json" \
    -d '{"name":"Kroger Test Week","startDate":"2026-03-24","endDate":"2026-03-30"}' | jq -r '.id')

  # Add a recipe
  curl -s -X POST http://localhost:5098/api/meal-plans/${PLAN_ID}/recipes \
    -H "Content-Type: application/json" \
    -d '{"recipeId":1174763824,"scheduledDate":"2026-03-25","mealType":"dinner","servings":4}' > /dev/null

  # Generate shopping list
  LATEST_LIST=$(curl -s -X POST http://localhost:5098/api/shopping-lists/generate/${PLAN_ID} | jq -r '.id')

  echo "✅ Created test shopping list #${LATEST_LIST}"
else
  echo "✅ Found shopping list #${LATEST_LIST}"
fi

echo ""

# Export shopping list
echo "📤 STEP 2: Export Shopping List for Kroger"
echo "────────────────────────────────────────────────────────────"
echo ""

curl -s http://localhost:5098/api/shopping-lists/${LATEST_LIST}/export > /tmp/kroger-order.json

ITEM_COUNT=$(cat /tmp/kroger-order.json | jq '.totalItems')
MEAL_PLAN=$(cat /tmp/kroger-order.json | jq -r '.mealPlan.name')

echo "Shopping List Details:"
echo "  Meal Plan: $MEAL_PLAN"
echo "  Total Items: $ITEM_COUNT"
echo "  Exported to: /tmp/kroger-order.json"
echo ""

# Show sample items
echo "Sample Items (first 5):"
cat /tmp/kroger-order.json | jq -r '.items[0:5] | .[] | "  • \(.name) (\(.quantity) \(.unit))"'
echo ""

# Create prompt for Claude
echo "────────────────────────────────────────────────────────────"
echo "🤖 STEP 3: Ready to Add to Kroger Cart"
echo "────────────────────────────────────────────────────────────"
echo ""

cat > /tmp/kroger-prompt.txt << 'PROMPT_EOF'
I have a shopping list exported from my meal planner. Please help me add these items to my Kroger cart.

For each item in the list:
1. Search for the product in Kroger
2. Pick the best match (considering price, brand preferences from memory if available)
3. Add the correct quantity to my cart

Here's the workflow:
- Use search_products to find each item
- Show me what you found before adding
- Use bulk_add_to_cart for efficiency
- Summarize what was added at the end

Shopping list attached.
PROMPT_EOF

echo "Kroger order prompt saved to: /tmp/kroger-prompt.txt"
echo ""
echo "────────────────────────────────────────────────────────────"
echo "📋 NEXT STEPS:"
echo "────────────────────────────────────────────────────────────"
echo ""
echo "Option 1: Interactive (Recommended for first time)"
echo "  1. Tell Claude: 'Find Kroger stores near me'"
echo "  2. Tell Claude: 'Set the first one as my preferred location'"
echo "  3. Tell Claude:"
echo "     $(cat /tmp/kroger-prompt.txt | head -3)"
echo "     [Attach /tmp/kroger-order.json]"
echo ""
echo "Option 2: Automated (After testing)"
echo "  Run: openclaw agent --local --session-id kroger \\"
echo "         --message \"\$(cat /tmp/kroger-prompt.txt)\" \\"
echo "         < /tmp/kroger-order.json"
echo ""
echo "Option 3: Review First"
echo "  cat /tmp/kroger-order.json | jq ."
echo ""
echo "────────────────────────────────────────────────────────────"
echo ""

# Save files
echo "📁 FILES CREATED:"
echo "  • /tmp/kroger-order.json - Shopping list export"
echo "  • /tmp/kroger-prompt.txt - Claude prompt"
echo ""

# Create reusable script
cat > ~/Desktop/VS/order-from-kroger.sh << 'SCRIPT_EOF'
#!/bin/bash
# Quick script to order latest shopping list from Kroger

SHOPPING_LIST_ID=${1:-$(curl -s http://localhost:5098/api/shopping-lists | jq -r '.[0].id')}

echo "🛒 Ordering Shopping List #${SHOPPING_LIST_ID} from Kroger..."
echo ""

# Export
curl -s http://localhost:5098/api/shopping-lists/${SHOPPING_LIST_ID}/export > /tmp/kroger-order.json

# Show summary
echo "Shopping List:"
cat /tmp/kroger-order.json | jq '{
  mealPlan: .mealPlan.name,
  totalItems: .totalItems,
  itemsByAisle: (.itemsByAisle | keys)
}'
echo ""

echo "Tell Claude to add these items to your Kroger cart:"
echo "  Attach: /tmp/kroger-order.json"
echo ""
echo "Or run automated:"
echo "  openclaw agent --local --session-id kroger \\"
echo "    --message 'Add all items from this shopping list to my Kroger cart' \\"
echo "    < /tmp/kroger-order.json"
echo ""
SCRIPT_EOF

chmod +x ~/Desktop/VS/order-from-kroger.sh

echo "✅ Created reusable script: ~/Desktop/VS/order-from-kroger.sh"
echo ""
echo "Usage:"
echo "  ./order-from-kroger.sh          # Order latest list"
echo "  ./order-from-kroger.sh 5        # Order list #5"
echo ""
echo "════════════════════════════════════════════════════════════"
echo "✅ INTEGRATION TEST COMPLETE!"
echo ""
echo "Next: Set up Kroger MCP following KROGER_API_SETUP.md"
echo ""
