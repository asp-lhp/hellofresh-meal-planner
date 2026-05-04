# Recipe Import Normalization — Discovery

**Ticket:** STR-27  
**Date:** 2026-05-03  
**Status:** In Progress

---

## Executive Summary

Recipe data quality varies significantly by source. 229 active recipes have:
- **18%** with prep_time, **27%** with cook_time, **35%** with total_time
- **21%** with calories, **25%** with protein
- **15 recipes** with zero ingredients (broken imports)
- **37 recipes** with garbage instruction steps ("step 1", "step 2" interleaved)

---

## Data Completeness Analysis

| Field | Has Data | Missing | % Complete |
|-------|----------|---------|------------|
| name | 229 | 0 | 100% |
| image_url | 229 | 0 | 100% |
| servings | 229 | 0 | 100% |
| total_time | 80 | 149 | 35% |
| cook_time | 61 | 168 | 27% |
| protein | 57 | 172 | 25% |
| calories | 49 | 180 | 21% |
| carbs | 45 | 184 | 20% |
| prep_time | 41 | 188 | 18% |
| difficulty | 26 | 203 | 11% |

---

## Recipe Sources

| Source | Count | Notes |
|--------|-------|-------|
| MealDB | 149 | Free API, inconsistent data quality |
| NYT Cooking | 30 | Subscription wall, high quality |
| HelloFresh (en-US) | 11 | Good structure |
| BBC Good Food | 9 | Good quality |
| HelloFresh (en-CA) | 8 | Good structure |
| HelloFresh (en-AU) | 7 | Good structure |
| Manual (Facebook) | 6 | Variable quality |
| Web Import | 4 | Variable |
| Other | 5 | Misc sources |

**207 recipes** have `hellofresh_url` set (HelloFresh origin).

---

## Critical Issues

### 1. Recipes with Zero Ingredients (15 recipes)

These are completely broken and unusable for shopping lists.

| ID | Name |
|----|------|
| 692 | Mozzarella-Cauli Bites & Smashed Potatoes |
| 6984 | Cheesy Beef Taco Mac Pasta |
| 69777 | Swedish-Inspired Burgers |
| 692519 | BBQ Beef Loaded Fries |
| 6942207 | Prawn Wontons & Garlic Noodle Stir-Fry |
| 6942251 | Umami Beef, Prawn & Garlic-Chilli Oil Rice Noodles |
| 6942253 | Golden Prawn Wontons & Garlic Noodles |
| 6965510 | Pad Thai with Chicken Thighs |
| 6965521 | Pad Thai with Tofu |
| 6965522 | Korean Beef Bulgogi and Kimchi |
| 6970045 | Chipotle Salmon and Farro Bowls |
| 69655101 | Mediterranean Za'atar Double Salmon |
| 69655115 | Vietnamese Lemongrass Chicken |
| 69141241623 | Cantonese-Style Steamed Barramundi & Prawns |
| 69422081353 | Pork Gyoza & Garlic Noodle Stir-Fry |

**Root cause:** HelloFresh API returns recipe metadata but ingredients in a different structure that wasn't parsed.

**Fix:** Re-scrape these URLs or manually add ingredients.

### 2. Garbage Instruction Steps (37 recipes, 115 bad steps)

Pattern: Odd-numbered steps contain "step 1", "step 2" placeholders, even-numbered steps contain actual content.

**Example (recipe 53262):**
```
Step 1: "step 1"           ← garbage
Step 2: "Finely chop..."   ← real content
Step 3: "step 2"           ← garbage
Step 4: "When ready..."    ← real content
```

**Root cause:** Scraper capturing step headers along with step content.

**Fix:** Migration script to delete rows where `description LIKE 'step %' AND LENGTH(description) < 10`, then renumber remaining steps.

### 3. Missing Nutrition Data (78-80% missing)

Only ~50 recipes have calories/protein/carbs. This limits nutrition tracking features.

**Options:**
1. **AI estimation:** Use Claude to estimate nutrition from ingredients
2. **External API:** Query USDA FoodData Central or Nutritionix
3. **Accept gaps:** Display "N/A" gracefully, don't block features

**Recommendation:** Option 1 (AI estimation) for reasonable accuracy without API costs.

---

## Ingredient Quantity Normalization

### Current State

| Format Type | Count | Examples |
|-------------|-------|----------|
| Other/numeric | 1451 | "2", "4 Cloves", "1 medium" |
| Grams | 381 | "800g", "200g", "150 g" |
| Teaspoon variants | 189 | "1 tsp", "1 teaspoon", "½ tsp" |
| Tablespoon variants | 143 | "1 tbsp", "1 tablespoon", "1 tblsp" |
| Cups | 84 | "1 cup", "1/2 cup", "1 1/2 cup" |
| Vague amounts | 34 | "to taste", "for brushing", "as needed" |
| Ounces | 32 | "4 oz", "8 ounces" |
| Pounds | 22 | "1 lb", "2 Lbs", "1 pound" |

### Unit Standardization Map

```python
UNIT_ALIASES = {
    # Tablespoons
    'tablespoon': 'tbsp', 'tablespoons': 'tbsp', 'tblsp': 'tbsp', 'T': 'tbsp',
    
    # Teaspoons
    'teaspoon': 'tsp', 'teaspoons': 'tsp', 't': 'tsp',
    
    # Pounds
    'pound': 'lb', 'pounds': 'lb', 'lbs': 'lb',
    
    # Ounces
    'ounce': 'oz', 'ounces': 'oz',
    
    # Cups
    'cups': 'cup',
    
    # Grams (normalize spacing)
    'g': 'g', 'grams': 'g', 'gram': 'g',
}

FRACTION_MAP = {
    '½': '1/2', '⅓': '1/3', '¼': '1/4', '¾': '3/4',
    '⅔': '2/3', '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8',
}
```

### Vague Amounts

Keep as-is but flag as "non-aggregatable" for shopping list generation:
- "to taste" → exclude from shopping list totals
- "for brushing" → exclude
- "as needed" → exclude

---

## Proposed Normalization Pipeline

### Phase 1: Data Cleanup (One-time migrations)

1. **Delete garbage instruction steps**
   ```sql
   DELETE FROM instructions 
   WHERE LOWER(description) LIKE 'step %' AND LENGTH(description) < 10;
   ```

2. **Renumber instruction steps** (Python script after deletion)

3. **Mark incomplete recipes** for manual review
   - Add `needs_review` boolean column
   - Flag recipes with 0 ingredients

### Phase 2: Import-time Normalization

Add normalization to `scraper/import_url.py`:

```python
def normalize_quantity(raw: str) -> str:
    """Standardize ingredient quantities."""
    text = raw.strip()
    
    # Unicode fractions → ASCII
    for unicode, ascii in FRACTION_MAP.items():
        text = text.replace(unicode, ascii)
    
    # Unit aliases
    for long, short in UNIT_ALIASES.items():
        text = re.sub(rf'\b{long}\b', short, text, flags=re.IGNORECASE)
    
    # Normalize spacing around units
    text = re.sub(r'(\d)\s*(g|ml|oz|lb)\b', r'\1 \2', text)
    
    return text

def normalize_instructions(steps: list) -> list:
    """Filter garbage steps and renumber."""
    real_steps = [s for s in steps if not is_garbage_step(s['description'])]
    for i, step in enumerate(real_steps, 1):
        step['step_number'] = i
    return real_steps
```

### Phase 3: AI Enrichment (Optional)

For recipes missing nutrition data:

```python
def estimate_nutrition(recipe: dict) -> dict:
    """Use Claude to estimate nutrition from ingredients."""
    prompt = f"""
    Estimate per-serving nutrition for this recipe:
    Name: {recipe['name']}
    Servings: {recipe['servings']}
    Ingredients: {recipe['ingredients']}
    
    Return JSON: {{"calories": int, "protein": int, "carbs": int, "fat": int}}
    """
    # Call Claude API, parse response
```

---

## Recipe Completeness Requirements

A recipe is **complete** when it has:

### Required (blocks meal planning)
- [ ] `name` — non-empty
- [ ] `ingredients[]` — at least 1 ingredient
- [ ] `instructions[]` — at least 1 step with real content
- [ ] `servings` — positive integer

### Important (degrades experience)
- [ ] `total_time` OR (`prep_time` + `cook_time`)
- [ ] `image_url` — valid URL
- [ ] `calories` — for nutrition tracking

### Nice to Have
- [ ] `difficulty`
- [ ] `protein`, `carbs`, `fat`
- [ ] All ingredient quantities in standard format

### Completeness Score

```python
def completeness_score(recipe: dict) -> float:
    """Return 0.0-1.0 completeness score."""
    required = ['name', 'ingredients', 'instructions', 'servings']
    important = ['total_time', 'image_url', 'calories']
    nice = ['difficulty', 'protein', 'carbs']
    
    score = 0.0
    score += sum(0.15 for f in required if has_field(recipe, f))  # 60%
    score += sum(0.10 for f in important if has_field(recipe, f)) # 30%
    score += sum(0.033 for f in nice if has_field(recipe, f))     # 10%
    
    return min(score, 1.0)
```

---

## Recommended Actions

### Immediate (this sprint)

1. **Run garbage instruction cleanup migration**
   - Delete 115 garbage steps across 37 recipes
   - Renumber remaining steps

2. **Mark 15 zero-ingredient recipes for deletion or manual fix**
   - Either re-scrape from source URLs
   - Or soft-delete if source no longer available

3. **Add `needs_review` column to recipes table**

### Near-term (next sprint)

4. **Add normalization to import pipeline**
   - Unit standardization
   - Fraction conversion
   - Garbage step filtering

5. **Create recipe audit dashboard**
   - Show completeness scores
   - Filter by missing fields
   - Bulk actions for cleanup

### Future (backlog)

6. **AI nutrition estimation** for recipes missing calories/protein
7. **Ingredient deduplication** ("green onions" = "scallions")

---

## Open Questions

1. **Metric vs Imperial:** Should we store both? Convert on display based on user preference?
2. **MealDB quality:** 149 recipes from MealDB — worth keeping or should we audit/cull?
3. **Subscription sources:** How to handle NYT Cooking paywall for re-scraping?

---

*Document generated: 2026-05-03*
