"""
Curated Tag Categories for Recipe Classification
Based on HelloFresh style, but simplified to 25-30 useful tags
"""

TAG_CATEGORIES = {
    "CUISINE": [
        "Mexican",
        "Italian",
        "Asian",
        "Indian",
        "American",
        "Mediterranean",
        "Thai",
        "French"
    ],

    "DIETARY": [
        "Vegetarian",
        "Vegan",
        "Gluten-Free",
        "Dairy-Free",
        "Low-Carb",
        "High-Protein"
    ],

    "COOKING_STYLE": [
        "One Pot",
        "Quick",
        "Easy Prep",
        "Make-Ahead",
        "Slow Cooker",
        "Air Fryer"
    ],

    "MEAL_TYPE": [
        "Breakfast",
        "Lunch",
        "Dinner",
        "Snack",
        "Drinks"
    ],

    "PROTEIN": [
        "Chicken",
        "Beef",
        "Pork",
        "Fish",
        "Seafood",
        "Plant-Based"
    ]
}

# Flatten for easy lookup
ALL_TAGS = []
for category_tags in TAG_CATEGORIES.values():
    ALL_TAGS.extend(category_tags)

# Tag descriptions for AI context
TAG_DESCRIPTIONS = {
    "Mexican": "Tacos, enchiladas, burritos, quesadillas, or uses Mexican spices/ingredients",
    "Italian": "Pasta, pizza, risotto, or uses Italian ingredients like parmesan, basil, tomatoes",
    "Asian": "General Asian cuisine if not specifically Thai/Indian (Chinese, Japanese, Korean, Vietnamese)",
    "Indian": "Curry, tikka masala, naan, uses Indian spices like garam masala, turmeric",
    "American": "Classic American dishes like burgers, BBQ, mac and cheese, fried chicken",
    "Mediterranean": "Greek, Middle Eastern, uses olive oil, feta, hummus, pita",
    "Thai": "Pad thai, curry, uses Thai basil, lemongrass, fish sauce",
    "French": "French cooking techniques or classic dishes",

    "Vegetarian": "No meat (but may contain dairy/eggs)",
    "Vegan": "No animal products at all",
    "Gluten-Free": "Contains no wheat, barley, rye, or gluten-containing ingredients",
    "Dairy-Free": "No milk, cheese, butter, cream, or dairy products",
    "Low-Carb": "Under 30g carbs per serving",
    "High-Protein": "30g+ protein per serving",

    "One Pot": "Cooked in a single pot/pan (minimal cleanup)",
    "Quick": "30 minutes or less total time",
    "Easy Prep": "10 minutes or less prep time",
    "Make-Ahead": "Can be prepared in advance and reheated",
    "Slow Cooker": "Uses slow cooker or crockpot",
    "Air Fryer": "Uses air fryer",

    "Breakfast": "Typical breakfast food",
    "Lunch": "Good for lunch",
    "Dinner": "Dinner recipe",
    "Snack": "Snack or appetizer",
    "Drinks": "Beverages, smoothies, cocktails, or drink recipes",

    "Chicken": "Contains chicken as main protein",
    "Beef": "Contains beef as main protein",
    "Pork": "Contains pork as main protein",
    "Fish": "Contains fish (salmon, tilapia, cod, etc.)",
    "Seafood": "Contains seafood (shrimp, crab, shellfish, etc.)",
    "Plant-Based": "Main protein from plants (tofu, beans, lentils, etc.)"
}

def get_tag_prompt(recipe_name: str, ingredients: list, instructions: str,
                   prep_time: int = None, total_time: int = None,
                   protein: int = None, carbs: int = None) -> str:
    """Generate prompt for AI to suggest tags"""

    ingredients_text = "\n".join([f"- {ing}" for ing in ingredients[:20]])

    prompt = f"""Analyze this recipe and suggest appropriate tags from the curated list.

Recipe: {recipe_name}

Ingredients:
{ingredients_text}

Instructions: {instructions[:500]}...

Nutrition:
- Protein: {protein}g (per serving)
- Carbs: {carbs}g (per serving)

Timing:
- Prep time: {prep_time} min
- Total time: {total_time} min

Available Tags (choose ONLY from this list):

CUISINE: {', '.join(TAG_CATEGORIES['CUISINE'])}
DIETARY: {', '.join(TAG_CATEGORIES['DIETARY'])}
COOKING_STYLE: {', '.join(TAG_CATEGORIES['COOKING_STYLE'])}
MEAL_TYPE: {', '.join(TAG_CATEGORIES['MEAL_TYPE'])}
PROTEIN: {', '.join(TAG_CATEGORIES['PROTEIN'])}

Rules:
1. Choose 3-6 tags total
2. Pick the MOST relevant tags only
3. Use tag descriptions for guidance:
{chr(10).join([f'   - {tag}: {desc}' for tag, desc in TAG_DESCRIPTIONS.items()])}

4. Auto-apply based on data:
   - If total_time <= 30: add "Quick"
   - If prep_time <= 10: add "Easy Prep"
   - If protein >= 30: add "High-Protein"
   - If carbs < 30: add "Low-Carb"

5. Return ONLY a JSON array of tag names, nothing else.

Example output: ["Mexican", "Chicken", "Quick", "Dinner", "One Pot"]
"""

    return prompt
