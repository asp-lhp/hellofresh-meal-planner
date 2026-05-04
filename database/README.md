# Recipe Database

SQLite database for storing scraped HelloFresh recipes.

## Schema

See `schema.sql` for the complete database structure.

## Sample Queries

```sql
-- Top 10 highest protein recipes
SELECT name, protein, calories
FROM recipes
ORDER BY protein DESC
LIMIT 10;

-- Recipes with chicken and rice
SELECT DISTINCT r.name, r.cook_time
FROM recipes r
JOIN ingredients i1 ON r.id = i1.recipe_id
JOIN ingredients i2 ON r.id = i2.recipe_id
WHERE i1.name LIKE '%chicken%'
  AND i2.name LIKE '%rice%';
```
