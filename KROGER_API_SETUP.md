# 🛒 Kroger API Integration - Setup Guide

## What This Gives You

**Complete automated grocery ordering** from your meal planner:

```
Meal Plan → Shopping List → Export JSON → Kroger Cart → Order Placed
```

## 🎯 Features Available

### Kroger MCP Server Tools

**Products**:
- `search_products` - Find products by name
- `get_product_details` - Get pricing & details
- `bulk_add_to_cart` - Add multiple items at once

**Stores**:
- `search_locations` - Find Kroger near you
- `set_preferred_location` - Save your store
- `get_location_details` - Store hours, pharmacy, etc.

**Cart**:
- `add_items_to_cart` - Add single item
- `bulk_add_to_cart` - Add multiple items (perfect for shopping lists!)
- `view_current_cart` - See what's in cart
- `mark_order_placed` - Track orders

**Rate Limits** (Free API):
- Products: 10,000 calls/day
- Locations: 1,600 calls/day
- Cart: 5,000 calls/day

## 📝 Step 1: Get Kroger API Credentials (5 min)

1. **Create Kroger Developer Account**:
   - Go to: https://developer.kroger.com
   - Click "Sign Up" (top right)
   - Create account (free!)

2. **Register Your Application**:
   - Go to: https://developer.kroger.com/manage/apps/register
   - Fill in:
     - **App Name**: Meal Planner
     - **App Description**: Personal meal planning and automated grocery shopping
     - **Redirect URI**: `http://localhost:8000/callback`
     - **Environment**: Production

3. **Get Your Credentials**:
   - After registering, you'll see:
     - `CLIENT_ID` (long string)
     - `CLIENT_SECRET` (longer string)
   - **Copy these** - we'll use them next!

## 🔧 Step 2: Install Kroger MCP Server

```bash
# Install with uv (recommended)
uv pip install kroger-mcp

# Or with pip
pip install kroger-mcp
```

## ⚙️  Step 3: Configure for Claude Code

Edit your Claude Code MCP config:

**File**: `~/.claude/mcp_settings.json`

```json
{
  "mcpServers": {
    "kroger": {
      "command": "uvx",
      "args": ["kroger-mcp"],
      "env": {
        "KROGER_CLIENT_ID": "YOUR_CLIENT_ID_HERE",
        "KROGER_CLIENT_SECRET": "YOUR_CLIENT_SECRET_HERE",
        "KROGER_REDIRECT_URI": "http://localhost:8000/callback",
        "KROGER_USER_ZIP_CODE": "YOUR_ZIP_CODE"
      }
    }
  }
}
```

**Replace**:
- `YOUR_CLIENT_ID_HERE` - from Step 1
- `YOUR_CLIENT_SECRET_HERE` - from Step 1
- `YOUR_ZIP_CODE` - your location

## 🧪 Step 4: Test the Integration

Restart Claude Code, then test:

```
Me: "Find Kroger stores near my zip code"
Claude: [Uses search_locations tool]

Me: "Set the first one as my preferred store"
Claude: [Uses set_preferred_location tool]

Me: "Search for chicken breast"
Claude: [Uses search_products tool]

Me: "Add 2 lbs of chicken breast to my cart"
Claude: [Uses add_items_to_cart tool]
```

## 🎯 Step 5: Connect to Meal Planner

Now the magic happens! Here's the complete workflow:

### Option 1: Ask Claude to Order
```bash
# Export shopping list
curl http://localhost:5098/api/shopping-lists/1/export > groceries.json

# Tell Claude
"Add all items from this shopping list to my Kroger cart"
[Attach groceries.json]
```

**What Claude does**:
1. Reads your shopping list JSON
2. For each item:
   - Searches Kroger products
   - Picks best match
   - Adds correct quantity to cart
3. Shows you summary
4. You finish checkout on Kroger.com

### Option 2: Automated Script
```bash
# Create automated ordering script
cat > ~/Desktop/VS/kroger-order.sh << 'EOF'
#!/bin/bash

LIST_ID=$1

# Export from meal planner
curl -s http://localhost:5098/api/shopping-lists/${LIST_ID}/export > /tmp/order.json

# Tell Claude to add to cart
openclaw agent --local --session-id kroger \
  --message "Add all items from this JSON to my Kroger cart. Match products carefully and show me what you added." \
  < /tmp/order.json

echo "Cart updated! Finish checkout at kroger.com"
EOF

chmod +x ~/Desktop/VS/kroger-order.sh

# Use it
./kroger-order.sh 1  # Order shopping list #1
```

## 📊 Complete Workflow Example

### Sunday Meal Prep → Kroger Order

```bash
# 1. Plan meals for the week
curl -X POST http://localhost:5098/api/meal-plans \
  -d '{"name":"This Week","startDate":"2026-03-24","endDate":"2026-03-30"}'

# 2. Add recipes
curl -X POST http://localhost:5098/api/meal-plans/1/recipes \
  -d '{"recipeId":123456,"scheduledDate":"2026-03-25","mealType":"dinner","servings":4}'

# 3. Check for bulk item warnings
curl http://localhost:5098/api/meal-plans/1/analyze

# 4. Generate shopping list
curl -X POST http://localhost:5098/api/shopping-lists/generate/1

# 5. Export for Kroger
curl http://localhost:5098/api/shopping-lists/1/export > groceries.json

# 6. Add to Kroger cart
openclaw agent --local --session-id kroger \
  --message "Add all items from this shopping list to my Kroger cart" \
  < groceries.json

# 7. Finish checkout on kroger.com
# Done!
```

## 🛡️ Authentication Flow

First time using cart features:

1. Claude tries to add item to cart
2. You'll see a URL: `http://localhost:8000/login?...`
3. **Paste URL in browser**
4. Login to your **Kroger shopping account** (not developer account)
5. Authorize the app
6. Done! Token saved for future use

**Note**: Developer account ≠ Shopping account
- Developer account: For API credentials
- Shopping account: Your actual Kroger.com account

## 💰 Cost Analysis

### API Credits
- **Free Tier**: 10,000 product searches/day
- **Your Usage**: ~50 searches per shopping list
- **Result**: 200 shopping lists/day (way more than needed!)

### Compared to Manual
```
Manual Shopping:
  - 1 hour at store
  - Gas/time cost: ~$10
  - Weekly: $520/year

With Kroger API:
  - 5 minutes to review cart
  - Kroger pickup: Free (or $5 delivery)
  - Weekly: $0-260/year

Savings: 50-100% of time + cost
```

## 🔄 Integration with QMD Memory

With QMD/Engram configured, Claude remembers:

```
First time:
  You: "Add chicken breast to cart"
  Claude: [Searches, picks random brand]

After learning (QMD):
  You: "I prefer Mary's Organic chicken breast"
  QMD: [Stores preference]

Next time:
  You: "Add chicken breast to cart"
  Claude: [Recalls Mary's Organic preference]
  Claude: [Adds correct brand automatically!]
```

## 📝 Local Cart Tracking

Kroger API limitation: Can ADD but not VIEW cart

**Solution**: MCP server tracks locally

**Files created**:
- `kroger_cart.json` - Current cart items
- `kroger_order_history.json` - Past orders

**Usage**:
```
# View local cart
"What's in my Kroger cart?"

# After ordering on kroger.com
"Mark this order as placed"
# Moves cart to history
```

## 🎓 Smart Features

### 1. Bulk Add from Shopping List
```json
{
  "items": [
    {"name": "chicken breast", "quantity": "2", "unit": "lbs"},
    {"name": "milk", "quantity": "1", "unit": "gallon"},
    {"name": "eggs", "quantity": "1", "unit": "dozen"}
  ]
}
```

Claude uses `bulk_add_to_cart` - one API call for all!

### 2. Smart Product Matching
```
Shopping list: "chicken breast"

Claude searches and picks:
  ✓ Best price
  ✓ Preferred brand (from QMD memory)
  ✓ Correct quantity/unit
  ✓ In stock at your store
```

### 3. Store Optimization
```
You: "Find stores near 90274"
Claude: [Shows 5 stores with hours, distance, pharmacy]

You: "Pick the one with pharmacy open until 9pm"
Claude: [Sets as preferred]
```

## 🐛 Troubleshooting

### "401 Unauthorized"
```bash
# Re-authenticate
openclaw agent --local --session-id kroger \
  --message "Force re-authentication for Kroger"
```

### "Product not found"
```
Shopping list says: "chicken breast"
Kroger has: "Boneless Skinless Chicken Breast"

Solution:
  - Add more details to your Food database
  - Or Claude asks: "Which chicken breast? Here are 5 options..."
```

### "Rate limit exceeded"
```
Error after 10,000 searches in one day

Solution:
  - Use bulk operations
  - Cache product IDs in database
  - Spread requests over multiple days
```

## 📚 Documentation

- **Kroger MCP Server**: https://github.com/CupOfOwls/kroger-mcp
- **Kroger API Docs**: https://developer.kroger.com
- **Kroger API Python**: https://github.com/CupOfOwls/kroger-api

## ✅ Setup Checklist

- [ ] Created Kroger developer account
- [ ] Registered app, got CLIENT_ID and CLIENT_SECRET
- [ ] Installed kroger-mcp (`uv pip install kroger-mcp`)
- [ ] Configured `~/.claude/mcp_settings.json`
- [ ] Restarted Claude Code
- [ ] Tested: "Find Kroger stores near me"
- [ ] Set preferred location
- [ ] Tested: "Add milk to cart" (triggers auth)
- [ ] Authorized Kroger shopping account
- [ ] Tested full shopping list export → cart

## 🚀 Next Steps

1. Get Kroger API credentials (5 min)
2. Install & configure kroger-mcp
3. Test with simple items
4. Try full shopping list import
5. Set up automated weekly ordering!

---

**Ready to automate your grocery shopping!** 🛒🤖
