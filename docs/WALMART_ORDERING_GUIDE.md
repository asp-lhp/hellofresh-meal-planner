# 🛒 Walmart Grocery Ordering via OpenClaw

## Complete End-to-End Workflow

Your meal planner is now integrated with Walmart through OpenClaw browser automation!

---

## 🎯 Quick Start (3 Steps)

### 1. Create Your Meal Plan
Visit http://localhost:5001 and create a meal plan with recipes.

### 2. Export Shopping List
```bash
# Export shopping list for meal plan #1
curl "http://localhost:5001/meal-plans/1/export-walmart" > /tmp/walmart-order.json
```

### 3. Order from Walmart via OpenClaw
```bash
./walmart-order.sh 1
```

That's it! OpenClaw will automate the entire Walmart ordering process.

---

## 📋 What the Script Does

The `walmart-order.sh` script automates:

1. ✅ **Export** - Gets your shopping list from the meal planner
2. ✅ **Navigate** - Opens Walmart.com in automated browser
3. ✅ **Search** - Finds each item in your list
4. ✅ **Add to Cart** - Adds correct quantities
5. ✅ **Handle Substitutions** - Asks for your approval
6. ✅ **Schedule Delivery** - Picks your delivery window
7. ✅ **Review** - Shows total cost before checkout
8. ⏸️ **Pause** - Waits for your approval to complete payment

---

## 🔧 Manual Workflow (If You Prefer)

### Step 1: Export Shopping List
```bash
# For meal plan #1
curl "http://localhost:5001/meal-plans/1/export-walmart" > walmart-groceries.json

# View the export
cat walmart-groceries.json | jq '.'
```

### Step 2: Start OpenClaw Session
```bash
openclaw agent --local --session-id walmart-order \
  --message "I need to order groceries from Walmart. I'll provide the shopping list." \
  < walmart-groceries.json
```

### Step 3: OpenClaw Will Guide You Through:
```
🤖 OpenClaw: I'll help you order from Walmart. Here's what I found:
    - 47 items across 6 aisles
    - Estimated total: $127 (based on typical prices)

    Should I start adding items to your Walmart cart?

👤 You: Yes, please proceed

🤖 OpenClaw: Opening Walmart.com...
    Are you logged in to your Walmart account?

👤 You: Yes

🤖 OpenClaw: Great! Starting to add items...
    [1/47] Adding 2 lbs ground beef...
    [2/47] Adding 1 dozen eggs...
    ...

    ⚠️  Item not found: "organic heirloom tomatoes"
    Closest match: "Organic Tomatoes on the Vine (1 lb)"
    Should I add this instead?

👤 You: Yes, that works

🤖 OpenClaw: All items added to cart!
    Summary:
    - 45/47 items added
    - 2 items substituted (with your approval)
    - Total: $132.47

    Ready to schedule delivery?

👤 You: Yes, Sunday 10am-12pm

🤖 OpenClaw: Perfect! I've selected:
    - Delivery: Sunday, March 24, 10:00 AM - 12:00 PM
    - Delivery fee: $0 (Walmart+ member)
    - Total: $132.47

    Ready to proceed to checkout?

👤 You: Yes

🤖 OpenClaw: ✅ Order ready for checkout!
    Please review and complete payment manually.

    Order #: [Walmart will provide]
    Delivery: Sunday, March 24, 10-12pm
```

---

## 📦 Export Format

The export endpoint creates a Walmart-optimized format:

```json
{
  "version": "1.0",
  "platform": "walmart",
  "mealPlan": {
    "id": 1,
    "name": "Weekly Meal Plan",
    "startDate": "2026-03-24",
    "endDate": "2026-03-30"
  },
  "totalItems": 47,
  "items": [
    {
      "name": "ground beef",
      "quantity": 2,
      "unit": "lbs",
      "aisle": "Meat",
      "searchTerm": "ground beef",
      "recipes": ["Spaghetti Bolognese", "Tacos"],
      "notes": ""
    }
  ],
  "metadata": {
    "exportedAt": "2026-03-21T20:00:00Z",
    "storeName": "Walmart",
    "deliveryPreference": "schedule"
  }
}
```

---

## 🎨 Customizing the Workflow

### Change Delivery Preferences
Edit `walmart-order.sh` line 107:
```bash
# Prefer pickup instead of delivery
"deliveryPreference": "pickup"
```

### Add Budget Limits
```bash
openclaw agent --local --session-id walmart-order \
  --message "Order these groceries from Walmart, but keep total under $100" \
  < walmart-groceries.json
```

### Optimize for Deals
```bash
openclaw agent --local --session-id walmart-order \
  --message "Order from Walmart and suggest cheaper alternatives where available" \
  < walmart-groceries.json
```

---

## 🔐 Authentication

### First Time Setup:
1. Run the script: `./walmart-order.sh 1`
2. OpenClaw will open Walmart.com
3. When prompted, manually log in to your Walmart account
4. OpenClaw will remember your session

### Walmart+ Benefits:
- Free delivery on $35+ orders
- Free shipping, no minimums
- Early access to deals
- Mobile scan & go

**Cost**: $12.95/month or $98/year

---

## 🐛 Troubleshooting

### "OpenClaw not found"
```bash
pip install openclaw
```

### "No API key configured"
```bash
export ANTHROPIC_API_KEY="your-key-here"
```

### "Can't find item"
OpenClaw will:
1. Search for the item
2. Show closest matches
3. Ask you to choose
4. Remember your preference for next time

### "Session expired"
Just run the script again - OpenClaw will prompt you to log in.

---

## 💡 Pro Tips

### 1. Review Before Ordering
```bash
# Just export, don't order yet
curl "http://localhost:5001/meal-plans/1/export-walmart" | jq '.'
```

### 2. Order Multiple Plans
```bash
# Order this week + next week
./walmart-order.sh 1
./walmart-order.sh 2
```

### 3. Save Money
```bash
openclaw agent --local \
  --message "Compare prices at Walmart vs Target for this list" \
  < walmart-groceries.json
```

### 4. Inventory Check
```bash
# Tell OpenClaw what you already have
openclaw agent --local \
  --message "I already have: milk, eggs, butter. Order the rest from Walmart" \
  < walmart-groceries.json
```

---

## 🚀 Advanced Usage

### Compare Multiple Stores
```bash
openclaw agent --local --session-id grocery-compare \
  --message "Find the cheapest option: Walmart, Target, or Amazon Fresh" \
  < walmart-groceries.json
```

### Recurring Orders
```bash
# Create a weekly cron job
0 9 * * 0 cd ~/Desktop/VS && ./walmart-order.sh 1
```

### Bulk Buying
```bash
openclaw agent --local \
  --message "For items used 3+ times this month, suggest buying in bulk" \
  < walmart-groceries.json
```

---

## 📊 Cost Breakdown

| Component | Cost |
|-----------|------|
| Meal Planner | Free |
| OpenClaw | Free (open source) |
| Claude API | ~$0.50-1.00 per order |
| Walmart+ | $12.95/month |
| **Total** | **~$13/month + groceries** |

**ROI**:
- Saves ~2 hours/week on meal planning
- Eliminates impulse purchases
- Optimizes for deals automatically
- Never forgets items

---

## ✅ MVP Complete!

You now have:
- ✅ Meal planning with 190+ recipes
- ✅ AI-powered recipe tagging
- ✅ Shopping list generation
- ✅ Walmart ordering automation
- ✅ Delivery scheduling
- ✅ Substitution handling
- ✅ Full checkout workflow

**Next Steps:**
1. Create your first meal plan
2. Run `./walmart-order.sh 1`
3. Let OpenClaw handle the rest!

---

## 📚 Additional Resources

- [OpenClaw Documentation](https://docs.openclaw.ai)
- [Walmart+ Benefits](https://www.walmart.com/plus)
- [Meal Planner API Docs](api/MealPlanner.Api/README.md)
- [OPENCLAW_STATUS.md](OPENCLAW_STATUS.md) - Setup guide

---

**🎉 Happy grocery shopping! Your automated meal planning system is ready to use.**
