# Meal Planner Web Interface

Flask web app with HelloFresh-style recipe cards. Print-friendly and mobile-responsive.

## Quick Start

```bash
# Install dependencies
pip3 install -r requirements.txt

# Start the server
python3 app.py
```

The app will be available at: **http://localhost:5001**

## Features

### Homepage (/)
- Grid view of all 40 recipes
- Thumbnails, cook time, difficulty, calories
- Click any recipe to view full details

### Recipe Card (/recipe/<id>)
- **HelloFresh-style layout** with hero image
- Prep/cook time, servings, difficulty
- Nutrition info (calories, protein, carbs, fat)
- Ingredient list with quantities
- Step-by-step instructions (numbered)
- **Print button** - Cmd+P for clean printable version
- **Mobile-friendly** - check recipes on your phone while cooking

### Print Mode
- Clean layout (no navigation, buttons, or footer)
- Optimized typography and spacing
- Images sized for printing
- Page break prevention for ingredients/steps
- Ready to print on Sunday for the week

## Usage

### Browse Recipes
1. Open http://localhost:5001
2. Browse the recipe grid
3. Click any recipe for full details

### Print a Recipe
1. Click any recipe
2. Click "Print Recipe" button (or Cmd+P)
3. Print or save as PDF

### View on Phone
1. Open http://localhost:5001 on your phone (same WiFi network)
2. Bookmark your favorite recipes
3. Reference while cooking

## File Structure

```
web/
├── app.py              # Flask application
├── requirements.txt    # Python dependencies
├── templates/
│   ├── base.html      # Base template with navbar
│   ├── index.html     # Recipe grid homepage
│   └── recipe.html    # Single recipe card
└── static/
    └── style.css      # HelloFresh-inspired styles + print CSS
```

## Next Steps

- [ ] Add weekly meal planner
- [ ] Add search by ingredient
- [ ] Add shopping list generator
- [ ] Add favorite/bookmark feature
- [ ] Port to .NET for C# learning (Phase 3)

## Tech Stack

- **Flask 3.0** - Python web framework
- **Jinja2** - HTML templating
- **SQLite** - Recipe database (40 recipes)
- **Print CSS** - Clean print layouts
- **Mobile-first** - Responsive design

## Development

The server runs in debug mode with auto-reload:
- Edit templates or CSS
- Refresh browser to see changes
- No restart needed

## Port Note

Uses port **5001** instead of 5000 to avoid macOS AirPlay port conflict.
