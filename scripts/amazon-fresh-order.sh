#!/bin/bash
# Amazon Fresh Grocery Order Automation via OpenClaw
# Usage: ./amazon-fresh-order.sh <meal_plan_id>

set -e

MEAL_PLAN_ID=${1:-1}
EXPORT_FILE="/tmp/amazon-fresh-order-${MEAL_PLAN_ID}.json"

echo "🛒 Amazon Fresh Grocery Order Automation"
echo "========================================"
echo ""

# Step 1: Export shopping list
echo "📋 Exporting shopping list for Meal Plan #${MEAL_PLAN_ID}..."
curl -s "http://localhost:5001/meal-plans/${MEAL_PLAN_ID}/export-walmart" > "$EXPORT_FILE"

if [ ! -s "$EXPORT_FILE" ]; then
    echo "❌ Failed to export shopping list"
    exit 1
fi

# Show summary
echo "✓ Export complete!"
echo ""
echo "Shopping List Summary:"
cat "$EXPORT_FILE" | jq '{
  mealPlan: .mealPlan.name,
  totalItems: .totalItems,
  items: .items | length
}'
echo ""

# Step 2: Check for OpenClaw
if ! command -v openclaw &> /dev/null; then
    echo "❌ OpenClaw not found. Please install it first:"
    echo "   pip install openclaw"
    exit 1
fi

# Step 3: Check for API key
if [ -z "$ANTHROPIC_API_KEY" ]; then
    echo "⚠️  ANTHROPIC_API_KEY not set. Checking ~/.openclaw/..."
    if [ -f ~/.openclaw/agents/main/agent/auth-profiles.json ]; then
        echo "✓ Found OpenClaw configuration"
    else
        echo "❌ No API key configured. Please set ANTHROPIC_API_KEY or configure OpenClaw"
        exit 1
    fi
fi

echo "🤖 Starting OpenClaw automation..."
echo "===================================="
echo ""

# Step 4: Launch OpenClaw with Amazon Fresh ordering prompt
PROMPT_MESSAGE="I need you to order groceries from Amazon Fresh for delivery. Here's what to do:

IMPORTANT: Use browser automation to complete this entire workflow.

## Step 1: Navigate to Amazon Fresh
1. Go to https://www.amazon.com/alm/storefront
2. If not logged in, pause and let me log in manually
3. Check delivery address is set correctly

## Step 2: Add Items to Cart
For each item in the shopping list:
1. Use the search bar to find the item using the searchTerm field
2. Select the best match (prefer exact brand/quantity when available)
3. Click 'Add to cart' with the specified quantity
4. If item not found, note it for manual review

## Step 3: Review & Handle Substitutions
1. Review all items in cart
2. For each item, check Amazon's substitute suggestions
3. Note any substitutions that look good
4. Ask me to approve substitutions before proceeding

## Step 4: Schedule Delivery
1. Go to cart and click 'Proceed to checkout'
2. Select delivery window (ask me for preferred time)
3. Review delivery fees (should be free with Prime)
4. DO NOT complete payment yet - stop here

## Step 5: Final Review
1. Show me:
   - Total items ordered
   - Items not found
   - Substitutions made
   - Total cost
   - Delivery window
2. Wait for my approval to complete checkout

## Shopping List (JSON Format):
$(cat "$EXPORT_FILE")"

openclaw agent --local --session-id "amazon-fresh-$(date +%Y%m%d-%H%M%S)" --message "$PROMPT_MESSAGE"

echo ""
echo "✅ OpenClaw session complete!"
echo ""
echo "Export file saved at: $EXPORT_FILE"
