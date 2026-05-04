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
