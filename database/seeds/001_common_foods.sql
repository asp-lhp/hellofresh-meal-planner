-- Seed common foods for ingredient normalization
-- Format: (name, aisle, preferred_unit, is_bulk_item, typical_package_size, freezes_well, shelf_life_days)

-- Meat & Poultry
INSERT INTO foods (name, plural_name, aisle, aisle_order, preferred_unit, is_bulk_item, typical_package_size, bulk_item_note, freezes_well, shelf_life_days) VALUES
('chicken', 'chickens', 'meat', 1, 'lbs', 0, NULL, NULL, 1, 180),
('chicken breast', 'chicken breasts', 'meat', 2, 'lbs', 0, '1-2 lbs', NULL, 1, 180),
('chicken thigh', 'chicken thighs', 'meat', 3, 'lbs', 0, '1-2 lbs', NULL, 1, 180),
('ground beef', NULL, 'meat', 4, 'lbs', 0, '1 lb', NULL, 1, 120),
('beef', NULL, 'meat', 5, 'lbs', 0, NULL, NULL, 1, 180),
('pork', NULL, 'meat', 6, 'lbs', 1, '3-5 lbs', 'Consider freezing excess', 1, 180),
('pork shoulder', 'pork shoulders', 'meat', 7, 'lbs', 1, '4-6 lbs', 'Plan to freeze 2-3 lbs or add another pork recipe', 1, 180),
('salmon', NULL, 'meat', 8, 'lbs', 0, '1-1.5 lbs', NULL, 1, 90),
('tilapia', NULL, 'meat', 9, 'lbs', 0, '1 lb', NULL, 1, 90);

-- Set parent relationships (chicken breast -> chicken)
UPDATE foods SET parent_food_id = (SELECT id FROM foods WHERE name = 'chicken') WHERE name IN ('chicken breast', 'chicken thigh');
UPDATE foods SET parent_food_id = (SELECT id FROM foods WHERE name = 'beef') WHERE name = 'ground beef';
UPDATE foods SET parent_food_id = (SELECT id FROM foods WHERE name = 'pork') WHERE name = 'pork shoulder';

-- Produce
INSERT INTO foods (name, plural_name, aisle, aisle_order, preferred_unit, freezes_well, shelf_life_days) VALUES
('onion', 'onions', 'produce', 1, 'whole', 0, 14),
('garlic', NULL, 'produce', 2, 'cloves', 0, 21),
('tomato', 'tomatoes', 'produce', 3, 'whole', 0, 7),
('bell pepper', 'bell peppers', 'produce', 4, 'whole', 0, 7),
('lettuce', NULL, 'produce', 5, 'head', 0, 5),
('carrot', 'carrots', 'produce', 6, 'lbs', 0, 14),
('potato', 'potatoes', 'produce', 7, 'lbs', 0, 14);

-- Dairy
INSERT INTO foods (name, plural_name, aisle, aisle_order, preferred_unit, freezes_well, shelf_life_days) VALUES
('milk', NULL, 'dairy', 1, 'cups', 0, 7),
('cheese', NULL, 'dairy', 2, 'oz', 0, 30),
('butter', NULL, 'dairy', 3, 'sticks', 1, 180),
('eggs', NULL, 'dairy', 4, 'whole', 0, 21),
('yogurt', NULL, 'dairy', 5, 'cups', 0, 14);

-- Pantry
INSERT INTO foods (name, plural_name, aisle, aisle_order, preferred_unit, freezes_well, shelf_life_days) VALUES
('olive oil', NULL, 'pantry', 1, 'tbsp', 0, 365),
('salt', NULL, 'pantry', 2, 'tsp', 0, NULL),
('pepper', NULL, 'pantry', 3, 'tsp', 0, 365),
('flour', NULL, 'pantry', 4, 'cups', 0, 180),
('sugar', NULL, 'pantry', 5, 'cups', 0, 365),
('rice', NULL, 'pantry', 6, 'cups', 0, 365),
('pasta', NULL, 'pantry', 7, 'lbs', 0, 365);

-- Frozen
INSERT INTO foods (name, plural_name, aisle, aisle_order, preferred_unit, freezes_well, shelf_life_days) VALUES
('frozen peas', NULL, 'frozen', 1, 'cups', 1, 365),
('frozen corn', NULL, 'frozen', 2, 'cups', 1, 365),
('ice cream', NULL, 'frozen', 3, 'pints', 1, 180);
