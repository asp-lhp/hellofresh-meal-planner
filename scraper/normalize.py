#!/usr/bin/env python3
"""
Recipe Data Normalization
Standardizes quantities, units, and instructions for consistent data
"""

import re
from typing import Tuple, List, Optional, Dict

# Unicode fraction to ASCII mapping
FRACTION_MAP = {
    '½': '1/2', '⅓': '1/3', '¼': '1/4', '¾': '3/4',
    '⅔': '2/3', '⅛': '1/8', '⅜': '3/8', '⅝': '5/8', '⅞': '7/8',
    '⅕': '1/5', '⅖': '2/5', '⅗': '3/5', '⅘': '4/5',
    '⅙': '1/6', '⅚': '5/6', '⅐': '1/7', '⅑': '1/9', '⅒': '1/10',
}

# Unit standardization (long form → short form)
UNIT_ALIASES = {
    # Volume - tablespoons
    'tablespoon': 'tbsp', 'tablespoons': 'tbsp', 'tblsp': 'tbsp',
    'tblsps': 'tbsp', 'tbsps': 'tbsp', 'T': 'tbsp', 'Tbsp': 'tbsp',

    # Volume - teaspoons
    'teaspoon': 'tsp', 'teaspoons': 'tsp', 'tsps': 'tsp', 't': 'tsp',

    # Weight - pounds
    'pound': 'lb', 'pounds': 'lb', 'lbs': 'lb', 'Lbs': 'lb',

    # Weight - ounces
    'ounce': 'oz', 'ounces': 'oz', 'ozs': 'oz',

    # Volume - cups
    'cups': 'cup', 'Cup': 'cup', 'Cups': 'cup',

    # Weight - grams
    'grams': 'g', 'gram': 'g', 'gm': 'g', 'gms': 'g',

    # Weight - kilograms
    'kilogram': 'kg', 'kilograms': 'kg', 'kgs': 'kg',

    # Volume - milliliters
    'milliliter': 'ml', 'milliliters': 'ml', 'millilitre': 'ml',
    'millilitres': 'ml', 'mL': 'ml', 'ML': 'ml',

    # Volume - liters
    'liter': 'L', 'liters': 'L', 'litre': 'L', 'litres': 'L',

    # Count
    'clove': 'clove', 'cloves': 'cloves',
    'piece': 'piece', 'pieces': 'pieces', 'pcs': 'pieces',
}

# Vague amounts that shouldn't be aggregated in shopping lists
VAGUE_AMOUNTS = {
    'to taste', 'to serve', 'for brushing', 'for garnish', 'for serving',
    'as needed', 'sprinkling', 'pinch', 'a pinch', 'handful', 'some',
    'optional', 'for topping', 'for decoration', 'dash', 'a dash',
}

# Common ingredient name normalizations (for grocery matching)
INGREDIENT_ALIASES = {
    'green onion': 'scallion', 'green onions': 'scallions',
    'spring onion': 'scallion', 'spring onions': 'scallions',
    'capsicum': 'bell pepper', 'capsicums': 'bell peppers',
    'coriander': 'cilantro', 'fresh coriander': 'fresh cilantro',
    'aubergine': 'eggplant', 'aubergines': 'eggplants',
    'courgette': 'zucchini', 'courgettes': 'zucchinis',
    'rocket': 'arugula',
    'prawns': 'shrimp', 'prawn': 'shrimp',
    'mince': 'ground meat', 'beef mince': 'ground beef',
    'pork mince': 'ground pork', 'chicken mince': 'ground chicken',
}


def normalize_fractions(text: str) -> str:
    """Convert unicode fractions to ASCII equivalents."""
    for unicode_frac, ascii_frac in FRACTION_MAP.items():
        text = text.replace(unicode_frac, ascii_frac)
    return text


def normalize_units(text: str) -> str:
    """Standardize unit names to short forms."""
    result = text
    for long_form, short_form in UNIT_ALIASES.items():
        # Word boundary match to avoid partial replacements
        pattern = rf'\b{re.escape(long_form)}\b'
        result = re.sub(pattern, short_form, result, flags=re.IGNORECASE)
    return result


def normalize_spacing(text: str) -> str:
    """Fix spacing around units (e.g., '200g' → '200 g')."""
    # Add space between number and unit if missing
    text = re.sub(r'(\d)(g|ml|oz|lb|kg|L)\b', r'\1 \2', text)
    # Normalize multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def normalize_quantity(raw: str) -> str:
    """
    Full normalization pipeline for ingredient quantities.

    Args:
        raw: Raw quantity string (e.g., "1 ½ tablespoons")

    Returns:
        Normalized quantity (e.g., "1 1/2 tbsp")
    """
    if not raw:
        return ""

    text = raw.strip()
    text = normalize_fractions(text)
    text = normalize_units(text)
    text = normalize_spacing(text)

    return text


def is_vague_amount(quantity: str) -> bool:
    """Check if quantity is vague and shouldn't be aggregated."""
    if not quantity:
        return True
    lower = quantity.lower().strip()
    return lower in VAGUE_AMOUNTS or any(v in lower for v in VAGUE_AMOUNTS)


def parse_ingredient(raw_ingredient: str) -> Tuple[str, str, str]:
    """
    Parse raw ingredient string into quantity, name, and normalized name.

    Args:
        raw_ingredient: Full ingredient string (e.g., "1 1/2 cups flour, sifted")

    Returns:
        Tuple of (quantity, name, normalized_name)
        - quantity: "1 1/2 cup"
        - name: "flour, sifted"
        - normalized_name: "flour"
    """
    text = normalize_fractions(raw_ingredient.strip())

    # Build unit pattern with word boundaries
    all_units = sorted(
        set(list(UNIT_ALIASES.keys()) + list(UNIT_ALIASES.values())),
        key=len,
        reverse=True  # Match longer units first
    )
    unit_pattern = '|'.join(re.escape(u) for u in all_units)

    # Pattern to extract quantity from start of string
    # Matches: "1", "1/2", "1 1/2", "2-3", "200 g", "1 cup", etc.
    # The unit must be followed by word boundary or space
    quantity_pattern = rf'^([\d\s/\-\.]+(?:\s*(?:{unit_pattern})\b)?)\s+(.+)$'

    match = re.match(quantity_pattern, text, re.IGNORECASE)

    if match:
        quantity = normalize_quantity(match.group(1).strip())
        name = match.group(2).strip()
    else:
        # Try simpler pattern: just numbers at start
        simple_match = re.match(r'^([\d\s/\-\.]+)\s+(.+)$', text)
        if simple_match:
            quantity = normalize_quantity(simple_match.group(1).strip())
            name = simple_match.group(2).strip()
        else:
            # No clear quantity
            quantity = ""
            name = text

    # Generate normalized name for grocery matching
    normalized = normalize_ingredient_name(name)

    return quantity, name, normalized


def normalize_ingredient_name(name: str) -> str:
    """
    Normalize ingredient name for grocery matching.
    Removes prep instructions, normalizes regional terms.

    Args:
        name: Ingredient name (e.g., "chicken breast, diced")

    Returns:
        Normalized name (e.g., "chicken breast")
    """
    if not name:
        return ""

    text = name.lower().strip()

    # Remove prep instructions after comma
    text = re.split(r',|\(', text)[0].strip()

    # Remove common prep words
    prep_words = [
        'chopped', 'diced', 'minced', 'sliced', 'crushed', 'peeled',
        'grated', 'shredded', 'julienned', 'cubed', 'halved', 'quartered',
        'thinly', 'finely', 'roughly', 'coarsely', 'fresh', 'dried',
        'frozen', 'thawed', 'room temperature', 'softened', 'melted',
        'divided', 'plus more', 'optional', 'for garnish',
    ]
    for word in prep_words:
        text = re.sub(rf'\b{word}\b', '', text, flags=re.IGNORECASE)

    # Apply ingredient aliases (regional terms)
    for alias, canonical in INGREDIENT_ALIASES.items():
        text = re.sub(rf'\b{re.escape(alias)}\b', canonical, text, flags=re.IGNORECASE)

    # Clean up extra spaces
    text = re.sub(r'\s+', ' ', text).strip()

    return text


def is_garbage_instruction(text: str) -> bool:
    """
    Check if instruction step is garbage (e.g., "step 1", "step 2").

    Args:
        text: Instruction text

    Returns:
        True if this is a garbage placeholder step
    """
    if not text:
        return True

    cleaned = text.strip().lower()

    # Match "step 1", "step 2", etc. with nothing else meaningful
    if re.match(r'^step\s*\d+\.?$', cleaned):
        return True

    # Very short content is likely garbage
    if len(cleaned) < 10 and re.match(r'^step\s', cleaned):
        return True

    return False


def normalize_instructions(steps: List[Dict]) -> List[Dict]:
    """
    Filter garbage steps and renumber remaining instructions.

    Args:
        steps: List of instruction dicts with 'description' key

    Returns:
        Cleaned and renumbered instruction list
    """
    real_steps = [
        s for s in steps
        if not is_garbage_instruction(s.get('description', ''))
    ]

    for i, step in enumerate(real_steps, 1):
        step['step_number'] = i

    return real_steps


def normalize_instructions_list(steps: List[str]) -> List[str]:
    """
    Filter garbage steps from a simple string list.

    Args:
        steps: List of instruction strings

    Returns:
        Cleaned instruction list (strings only, no garbage)
    """
    return [s for s in steps if not is_garbage_instruction(s)]
