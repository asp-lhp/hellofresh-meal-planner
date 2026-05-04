# SQL Practice Queries - Recipe Database

These queries help you practice SQL skills from your learning path (Phase 1).

## Getting Started

```bash
cd database
sqlite3 recipes.db
```

Enable better formatting:
```sql
.mode column
.headers on
.width 40 10 10 10
```

---

## Basic SELECT Queries

### 1. View all recipes
```sql
SELECT id, name, difficulty, cook_time, calories
FROM recipes
LIMIT 10;
```

### 2. Filter by difficulty
```sql
SELECT name, cook_time, calories
FROM recipes
WHERE difficulty = 'Easy'
ORDER BY cook_time;
```

### 3. Find quick recipes (under 20 minutes)
```sql
SELECT name, cook_time, difficulty
FROM recipes
WHERE cook_time <= 20
ORDER BY cook_time;
```

---

## JOINs (The Most Important SQL Skill)

### 4. Recipes with their ingredient count
```sql
SELECT
    r.name,
    COUNT(i.id) as ingredient_count,
    r.difficulty
FROM recipes r
LEFT JOIN ingredients i ON r.id = i.recipe_id
GROUP BY r.id
ORDER BY ingredient_count DESC;
```

### 5. Find all chicken recipes
```sql
SELECT DISTINCT r.name, r.cook_time, r.calories
FROM recipes r
JOIN ingredients i ON r.id = i.recipe_id
WHERE i.name LIKE '%chicken%'
ORDER BY r.cook_time;
```

### 6. Recipes with multiple specific ingredients
```sql
-- Chicken AND rice recipes
SELECT DISTINCT r.name
FROM recipes r
JOIN ingredients i1 ON r.id = i1.recipe_id
JOIN ingredients i2 ON r.id = i2.recipe_id
WHERE i1.name LIKE '%chicken%'
  AND i2.name LIKE '%rice%';
```

---

## Aggregations (GROUP BY, SUM, AVG, COUNT)

### 7. Average cook time by difficulty
```sql
SELECT
    difficulty,
    AVG(cook_time) as avg_cook_time,
    COUNT(*) as recipe_count
FROM recipes
WHERE difficulty IS NOT NULL
GROUP BY difficulty;
```

### 8. Top 10 highest protein recipes
```sql
SELECT name, protein, calories,
       ROUND(protein * 4.0 / NULLIF(calories, 0) * 100, 1) as protein_pct
FROM recipes
WHERE protein IS NOT NULL
ORDER BY protein DESC
LIMIT 10;
```

### 9. Ingredient frequency (most common ingredients)
```sql
SELECT
    name,
    COUNT(*) as recipe_count
FROM ingredients
GROUP BY name
ORDER BY recipe_count DESC
LIMIT 20;
```

---

## Subqueries

### 10. Recipes with more ingredients than average
```sql
SELECT r.name, COUNT(i.id) as ingredient_count
FROM recipes r
LEFT JOIN ingredients i ON r.id = i.recipe_id
GROUP BY r.id
HAVING COUNT(i.id) > (
    SELECT AVG(ing_count)
    FROM (
        SELECT COUNT(*) as ing_count
        FROM ingredients
        GROUP BY recipe_id
    )
);
```

### 11. Healthiest recipes (low cal, high protein)
```sql
SELECT name, calories, protein,
       ROUND(protein * 4.0 / calories * 100, 1) as protein_pct
FROM recipes
WHERE calories > 0
  AND protein > 0
  AND calories < (SELECT AVG(calories) FROM recipes WHERE calories > 0)
  AND protein > (SELECT AVG(protein) FROM recipes WHERE protein > 0)
ORDER BY protein_pct DESC;
```

---

## Complex Queries (Multiple JOINs)

### 12. Full recipe breakdown
```sql
SELECT
    r.name as recipe,
    r.difficulty,
    r.cook_time,
    COUNT(DISTINCT i.id) as ingredients,
    COUNT(DISTINCT ins.id) as steps,
    r.calories
FROM recipes r
LEFT JOIN ingredients i ON r.id = i.recipe_id
LEFT JOIN instructions ins ON r.id = ins.recipe_id
GROUP BY r.id
ORDER BY r.name;
```

### 13. Recipes with tags
```sql
SELECT
    r.name,
    GROUP_CONCAT(t.tag, ', ') as tags,
    r.difficulty
FROM recipes r
LEFT JOIN tags t ON r.id = t.recipe_id
GROUP BY r.id
HAVING tags IS NOT NULL;
```

---

## Window Functions (Advanced)

### 14. Rank recipes by protein within each difficulty level
```sql
SELECT
    name,
    difficulty,
    protein,
    RANK() OVER (PARTITION BY difficulty ORDER BY protein DESC) as protein_rank
FROM recipes
WHERE protein IS NOT NULL
  AND difficulty IS NOT NULL;
```

---

## Practical Queries for Meal Planning

### 15. Week of easy dinners under 30 minutes
```sql
SELECT name, cook_time, calories
FROM recipes
WHERE difficulty = 'Easy'
  AND cook_time <= 30
ORDER BY RANDOM()
LIMIT 7;
```

### 16. Calculate total nutrition for a meal plan
```sql
-- Replace these IDs with actual recipe IDs from your database
SELECT
    SUM(calories) as total_calories,
    SUM(protein) as total_protein,
    SUM(carbs) as total_carbs,
    SUM(fat) as total_fat,
    COUNT(*) as meals
FROM recipes
WHERE id IN (297746, 696966);  -- Your selected recipes
```

### 17. Shopping list for specific recipes
```sql
-- Aggregated ingredients for multiple recipes
SELECT
    i.name as ingredient,
    COUNT(*) as times_needed,
    GROUP_CONCAT(r.name, ' | ') as used_in_recipes
FROM ingredients i
JOIN recipes r ON i.recipe_id = r.id
WHERE r.id IN (297746, 696966)  -- Your meal plan
GROUP BY i.name
ORDER BY times_needed DESC, i.name;
```

---

## Useful Views (Already Created in Schema)

### 18. Use the recipe summary view
```sql
SELECT * FROM vw_recipe_summary
WHERE ingredient_count >= 5
LIMIT 10;
```

### 19. Use the nutrition view
```sql
SELECT * FROM vw_recipe_nutrition
WHERE calories_per_serving < 500
ORDER BY protein_per_serving DESC;
```

---

## Database Exploration

### 20. See table structure
```sql
.schema recipes
.schema ingredients
.schema instructions
```

### 21. Count records in each table
```sql
SELECT 'recipes' as table_name, COUNT(*) as count FROM recipes
UNION ALL
SELECT 'ingredients', COUNT(*) FROM ingredients
UNION ALL
SELECT 'instructions', COUNT(*) FROM instructions
UNION ALL
SELECT 'tags', COUNT(*) FROM tags
UNION ALL
SELECT 'allergens', COUNT(*) FROM allergens;
```

---

## Tips for Learning SQL

1. **Start simple**: Master SELECT, WHERE, ORDER BY first
2. **JOINs are crucial**: Practice LEFT JOIN vs INNER JOIN
3. **GROUP BY unlocks power**: Use with COUNT, SUM, AVG
4. **Use EXPLAIN**: See query execution plan
   ```sql
   EXPLAIN QUERY PLAN
   SELECT * FROM recipes WHERE difficulty = 'Easy';
   ```
5. **Indexes matter**: Check what indexes exist
   ```sql
   .indexes recipes
   ```

---

## Challenge Exercises

Try to write queries for these scenarios:

1. Find recipes that use chicken but NOT rice
2. Calculate average calories per ingredient for each recipe
3. Find the recipe with the most steps
4. List all recipes with their allergens in one row (comma-separated)
5. Find recipes that take longer to cook than they take to prep
6. Build a "balanced meal plan" - 7 recipes with varied protein sources

---

## Export Results

```sql
-- Export to CSV
.mode csv
.output my_query_results.csv
SELECT * FROM recipes WHERE difficulty = 'Easy';
.output stdout
.mode column
```

Happy querying! 🎯
