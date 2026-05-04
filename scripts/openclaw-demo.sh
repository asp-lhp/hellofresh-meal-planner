#!/bin/bash
# OpenClaw Integration Demo - Meal Planner to Grocery Shopping

echo "🦞 MEAL PLANNER → OPENCLAW DEMO"
echo "════════════════════════════════════════"
echo ""

# Step 1: Create a fresh meal plan
echo "📋 Step 1: Creating meal plan..."
MEAL_PLAN=$(curl -s -X POST http://localhost:5098/api/meal-plans \
  -H "Content-Type: application/json" \
  -d '{"name":"Demo Week","startDate":"2026-03-24","endDate":"2026-03-30"}')
MEAL_PLAN_ID=$(echo $MEAL_PLAN | jq -r '.id')
echo "   ✅ Created meal plan #$MEAL_PLAN_ID"
echo ""

# Step 2: Add some recipes
echo "📝 Step 2: Adding recipes to meal plan..."
curl -s -X POST http://localhost:5098/api/meal-plans/$MEAL_PLAN_ID/recipes \
  -H "Content-Type: application/json" \
  -d '{"recipeId":896233052,"scheduledDate":"2026-03-25","mealType":"dinner","servings":4}' > /dev/null
echo "   ✅ Added: Slow cooker pulled pork"

curl -s -X POST http://localhost:5098/api/meal-plans/$MEAL_PLAN_ID/recipes \
  -H "Content-Type: application/json" \
  -d '{"recipeId":1174763824,"scheduledDate":"2026-03-26","mealType":"dinner","servings":4}' > /dev/null
echo "   ✅ Added: Chicken tikka masala"
echo ""

# Step 3: Analyze for bulk items
echo "⚠️  Step 3: Analyzing for bulk item warnings..."
ANALYSIS=$(curl -s http://localhost:5098/api/meal-plans/$MEAL_PLAN_ID/analyze)
WARNINGS=$(echo $ANALYSIS | jq -r '.bulkItemWarnings[] | "   ⚠️  \(.foodName) - \(.recommendation)"')
if [ -n "$WARNINGS" ]; then
  echo "$WARNINGS"
else
  echo "   ✅ No bulk item warnings!"
fi
echo ""

# Step 4: Generate shopping list
echo "🛒 Step 4: Generating shopping list..."
SHOPPING_LIST=$(curl -s -X POST http://localhost:5098/api/shopping-lists/generate/$MEAL_PLAN_ID)
LIST_ID=$(echo $SHOPPING_LIST | jq -r '.id')
TOTAL_ITEMS=$(echo $SHOPPING_LIST | jq -r '.totalItems')
echo "   ✅ Generated shopping list #$LIST_ID with $TOTAL_ITEMS items"
echo ""

# Step 5: Export for OpenClaw
echo "🦞 Step 5: Exporting for OpenClaw..."
curl -s http://localhost:5098/api/shopping-lists/$LIST_ID/export > ~/Desktop/VS/openclaw-export.json
FILE_SIZE=$(ls -lh ~/Desktop/VS/openclaw-export.json | awk '{print $5}')
echo "   ✅ Saved to openclaw-export.json ($FILE_SIZE)"
echo ""

# Show export summary
echo "📊 EXPORT SUMMARY:"
cat ~/Desktop/VS/openclaw-export.json | jq '{
  mealPlan: .mealPlan.name,
  totalItems: .totalItems,
  aisles: (.itemsByAisle | keys),
  bulkItems: [.items[] | select(.isBulkItem) | .name]
}'
echo ""

echo "════════════════════════════════════════"
echo "✅ READY FOR OPENCLAW!"
echo ""
echo "Next step: Configure OpenClaw and run:"
echo "  openclaw agent --local --session-id demo \\"
echo "    --message \"Create an Amazon Fresh order from this list\" \\"
echo "    < openclaw-export.json"
echo ""

