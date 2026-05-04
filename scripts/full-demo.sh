#!/bin/bash
# Complete Meal Planner Demonstration
# All features without needing OpenClaw

echo "🍽️  COMPLETE MEAL PLANNER DEMO"
echo "════════════════════════════════════════════════════════════"
echo ""

# PHASE 1: Farmers Market Scenario
echo "📍 SCENARIO: Saturday at the Farmers Market"
echo "You bought fresh prawns (1.5 lbs) and chicken (3 lbs)"
echo ""

echo "➜ Adding to inventory..."
PRAWNS=$(curl -s -X POST http://localhost:5098/api/inventory \
  -H "Content-Type: application/json" \
  -d '{"locationName":"fridge","itemName":"prawns","quantity":1.5,"unit":"lbs"}' | jq -r '.id')
echo "   ✅ Added prawns (ID: $PRAWNS)"

CHICKEN=$(curl -s -X POST http://localhost:5098/api/inventory \
  -H "Content-Type: application/json" \
  -d '{"locationName":"fridge","itemName":"chicken breast","quantity":3,"unit":"lbs"}' | jq -r '.id')
echo "   ✅ Added chicken breast (ID: $CHICKEN)"
echo ""

# PHASE 2: Get Recipe Suggestions
echo "📊 Getting recipe suggestions based on inventory..."
SUGGESTIONS=$(curl -s -X POST http://localhost:5098/api/recipes/suggest-from-inventory \
  -H "Content-Type: application/json" \
  -d "{\"inventoryItemIds\":[$PRAWNS,$CHICKEN]}")

echo "   Found recipes:"
echo "$SUGGESTIONS" | jq -r '.recipes[0:3] | .[] | "   • \(.recipeName) (uses \(.matchScore) inventory items, \(.matchPercentage)% match)"'
echo ""

# PHASE 3: Create Meal Plan
echo "📅 Creating meal plan for the week..."
PLAN=$(curl -s -X POST http://localhost:5098/api/meal-plans \
  -H "Content-Type: application/json" \
  -d '{"name":"Farmers Market Week","startDate":"2026-03-24","endDate":"2026-03-30"}')
PLAN_ID=$(echo $PLAN | jq -r '.id')
echo "   ✅ Created meal plan: Farmers Market Week (ID: $PLAN_ID)"
echo ""

# Add top 3 recipes
echo "➜ Adding top 3 recipes to meal plan..."
RECIPE_IDS=$(echo "$SUGGESTIONS" | jq -r '.recipes[0:3] | .[].recipeId')
DATES=("2026-03-24" "2026-03-26" "2026-03-28")
i=0
for recipe_id in $RECIPE_IDS; do
  RECIPE_NAME=$(curl -s http://localhost:5098/api/recipes/$recipe_id | jq -r '.name')
  curl -s -X POST http://localhost:5098/api/meal-plans/$PLAN_ID/recipes \
    -H "Content-Type: application/json" \
    -d "{\"recipeId\":$recipe_id,\"scheduledDate\":\"${DATES[$i]}\",\"mealType\":\"dinner\",\"servings\":4}" > /dev/null
  echo "   ✅ ${DATES[$i]}: $RECIPE_NAME"
  ((i++))
done
echo ""

# PHASE 4: Analyze for Bulk Items
echo "⚠️  Analyzing meal plan for bulk item warnings..."
ANALYSIS=$(curl -s http://localhost:5098/api/meal-plans/$PLAN_ID/analyze)
WARNINGS=$(echo $ANALYSIS | jq -r '.bulkItemWarnings | length')

if [ "$WARNINGS" -gt 0 ]; then
  echo "$ANALYSIS" | jq -r '.bulkItemWarnings[] | "   ⚠️  \(.foodName) - \(.recommendation)"'
else
  echo "   ✅ No bulk item warnings! Good meal variety."
fi
echo ""

# PHASE 5: Generate Shopping List
echo "🛒 Generating shopping list..."
SHOP_LIST=$(curl -s -X POST http://localhost:5098/api/shopping-lists/generate/$PLAN_ID)
LIST_ID=$(echo $SHOP_LIST | jq -r '.id')
TOTAL_ITEMS=$(echo $SHOP_LIST | jq -r '.totalItems')
echo "   ✅ Shopping list #$LIST_ID: $TOTAL_ITEMS items"
echo ""

# PHASE 6: Export for OpenClaw
echo "🦞 Exporting for OpenClaw/AI tools..."
curl -s http://localhost:5098/api/shopping-lists/$LIST_ID/export > ~/Desktop/VS/farmers-market-list.json
echo "   ✅ Saved to: farmers-market-list.json"
echo ""

# PHASE 7: Show Summary
echo "════════════════════════════════════════════════════════════"
echo "📊 SUMMARY"
echo "════════════════════════════════════════════════════════════"
curl -s http://localhost:5098/api/shopping-lists/$LIST_ID/export | jq '{
  scenario: "Used farmers market inventory to plan meals",
  mealPlan: .mealPlan.name,
  totalRecipes: (.items[0].usedInRecipes | length),
  totalItems: .totalItems,
  aisles: (.itemsByAisle | keys),
  bulkWarnings: [.items[] | select(.isBulkItem) | .name],
  sampleMeals: [.items[0:3] | .[].usedInRecipes[0]]
}'
echo ""

echo "════════════════════════════════════════════════════════════"
echo "✅ COMPLETE! Your weekly meal plan is ready."
echo ""
echo "Files created:"
echo "  • farmers-market-list.json - OpenClaw export"
echo "  • Meal plan #$PLAN_ID in database"
echo "  • Shopping list #$LIST_ID in database"
echo ""
