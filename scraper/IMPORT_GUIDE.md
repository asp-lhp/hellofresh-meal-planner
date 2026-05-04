# Recipe URL Import Guide

Import recipes from any website using the `import_url.py` script powered by **recipe-scrapers** (supports 600+ sites).

---

## Quick Start

### Import a single recipe:
```bash
python3 import_url.py "https://www.bbcgoodfood.com/recipes/spaghetti-bolognese-recipe"
```

### Import multiple recipes from a file:
```bash
python3 import_url.py --file recipe_urls.txt
```

### Specify region/tag:
```bash
python3 import_url.py "https://..." --region "italian"
```

---

## Supported Sites (600+)

recipe-scrapers supports **600+ recipe websites**. Here are the most reliable ones:

### ✅ Highly Reliable (Always Work)
- **BBC Good Food** - https://www.bbcgoodfood.com/
- **Budget Bytes** - https://www.budgetbytes.com/
- **Simply Recipes** - https://www.simplyrecipes.com/
- **Serious Eats** - https://www.seriouseats.com/
- **Bon Appétit** - https://www.bonappetit.com/
- **Epicurious** - https://www.epicurious.com/
- **Taste of Home** - https://www.tasteofhome.com/

### ⚠️ Sometimes Work
- **Food Network** - https://www.foodnetwork.com/ (may require specific URLs)
- **NYT Cooking** - https://cooking.nytimes.com/ (paywall)
- **Delish** - https://www.delish.com/

### ❌ Often Blocked
- **AllRecipes** - https://www.allrecipes.com/ (blocks scrapers)
- **Tasty** - https://tasty.co/ (JS-heavy)

---

## What Gets Imported

### ✅ Always Imported
- Recipe name
- Ingredients list
- Cooking instructions (step-by-step)
- Source URL

### 🎯 Usually Imported (if available)
- Prep time, cook time, total time
- Servings/yields
- Nutrition info (calories, protein, carbs, fat)
- Images
- Category/cuisine tags

### ⚠️ Sometimes Missing
- Difficulty level (site-dependent)
- Allergen information (rarely provided)
- Detailed nutrition (varies by site)

---

## Batch Import from File

Create a text file with URLs (one per line):

**recipe_urls.txt:**
```
# My favorite recipes
https://www.bbcgoodfood.com/recipes/spaghetti-bolognese-recipe
https://www.budgetbytes.com/easy-fried-rice/
https://www.simplyrecipes.com/recipes/tacos/

# Lines starting with # are comments
https://www.seriouseats.com/the-best-lasagna-recipe
```

Then import:
```bash
python3 import_url.py --file recipe_urls.txt --region "favorites"
```

---

## Troubleshooting

### 403 Forbidden Error
**Problem:** Site blocks scrapers
**Solution:** Try a different site or use a VPN

```
ERROR: 403 Client Error: Forbidden
```

### No Ingredients Found
**Problem:** Site uses non-standard schema
**Solution:** File an issue with recipe-scrapers or scrape manually

### Duplicate Recipe
**Problem:** Recipe already exists in database
**Solution:** This is normal - the script will skip it

```
WARNING: Recipe already exists or constraint violation
```

---

## Advanced Usage

### Custom Database Path
```bash
python3 import_url.py "https://..." --db /path/to/recipes.db
```

### Check What Was Imported
```bash
cd ../database
./query.sh stats
```

### See All Imported Recipes
```bash
sqlite3 recipes.db "SELECT name FROM recipes WHERE region='imported';"
```

---

## Finding Recipe URLs

### Google Search Tips
```
site:bbcgoodfood.com chicken curry
site:budgetbytes.com pasta
site:seriouseats.com beef
```

### Recipe Collections
- [BBC Good Food - Quick & Easy](https://www.bbcgoodfood.com/recipes/collection/quick)
- [Budget Bytes - Beginner](https://www.budgetbytes.com/category/recipes/difficulty/beginner/)
- [Simply Recipes - Popular](https://www.simplyrecipes.com/recipes/popular/)

---

## Supported Site List

Full list of 600+ supported sites:
https://github.com/hhursev/recipe-scrapers#scrapers-available-for

**Popular ones include:**
101cookbooks, acouplecooks, afgonist, akispetretzikis, allrecipes, altonbrown, amazingribs, ambitiouskitchen, archanaskitchen, argiro, averiecooks, baking-sense, bbc, bbcgoodfood, bestrecipes, bettycrocker, biancazapatka, bigoven, blueapron, bonappetit, bowlofdelicious, budgetbytes, cafedelites, castironketo, chefkoch, closetcooking, cookieandkate, cookpad, cookstr, cooktalk, copykat, countryliving, creativecanning, cucchiaio, cuisineaz, cybercook, davidlebovitz, delish, downshiftology, driscolls, eatingwell, eatliverun, eatsmarter, eatwell101, epicurious, finedininglovers, fitmencook, food, foodandwine, foodnetwork, foodrepublic, forksoverknives, forktospoon, giallozafferano, gimmesomeoven, godt, goodfooddiscoveries, goodhousekeeping, goodtoknow, gousto, greatbritishchefs, grimgrains, halfbakedharvest, hassanchef, headbangerskitchen, healthy-delicious, hellofresh, homechef, hundredandonecookbooks, innit, inspiralized, jamieoliver, jocooks, joshuaweissman, juliegoodwin, justataste, justbento, justeat, justonecookbook, kennymcgovern, kingarthur, kitchenstories, kochbar, kuchengoetter, kwestiasmaku, leanandgreendishes, lekkerensimpel, littlespicejar, livelyflair, lovingitvegan, maangchi, madensverden, madewithlau, marleyspoon, marthastewart, matprat, mccormick, meal-prep, melskitchencafe, mindmegette, minimalistbaker, misya, mob, modernproper, momsdish, momswithcrockpots, moulinex, mybakingaddiction, mykitchen101, mykitchen101en, myrecipes, naturallyella, nihhealthyeating, nrk, number-2-pencil, nutritionix, nutritionvalue, nytimes, ohmyveggies, ohsheglows, onceuponachef, panelinha, paninihappy, popsugar, practicalselfreliance, pressureluckcooking, primalpalate, projectgezond, przepisy, purplecarrot, rachlmansfield, rainbowplantlife, realfoodwithjessica, realsimple, recipetineats, reciperunner, reidblackwell, rezeptwelt, rosanna, sageandpith, sallybakingaddiction, saveur, seriouseats, simplyquinoa, simplyrecipes, simplywhisked, skinnytaste, smulweb, sobeys, southerncastiron, southernliving, spendwithpennies, springlane, steamykitchen, streetkitchen, sunbasket, sweetcsdesigns, sweetpeasandsaffron, sweetcsdesigns, tasteofhome, tastesoflizzyt, tastykitchen, theclevercarrot, thehappyfoodie, thekitchn, thepioneerwoman, therecipecritic, thespruceeats, thevintagemixer, thewoksoflife, tidymom, timesofindia, tine, tudogostoso, twopeasandtheirpod, unsophisticook, usapears, valdemarsro, vanderbilt, vegrecipesofindia, waitrose, watchwhatueat, wbur, wearenotmartha, weissguy, whatsgabycooking, wholefoodsmarket, wickedspatula, williams-sonoma, womensweeklyfood, womensweeklyfood, woolworths, yemek, yummly, zenbelly

---

## Example Session

```bash
# Import a single recipe
python3 import_url.py "https://www.bbcgoodfood.com/recipes/chilli-con-carne-recipe"
# ✓ Successfully imported: Chilli con carne recipe
#   - 16 ingredients
#   - 16 steps

# Check database
cd ../database
./query.sh stats
# Recipes: 27

# Import 10 more recipes
cd ../scraper
python3 import_url.py --file recipe_urls.txt
# [1/10] Processing: https://www.bbcgoodfood.com/...
# ✓ Successfully imported: Spaghetti Bolognese
# ...
# Import Complete!
# ✓ Success: 8
# ✗ Failed: 2
# Total: 10

# Check new total
cd ../database
./query.sh stats
# Recipes: 35
```

---

## Next Steps

1. **Import your favorite recipes**
2. **Build meal plans** (coming in .NET API)
3. **Generate shopping lists** (OpenClaw integration)

Happy importing! 🍳
