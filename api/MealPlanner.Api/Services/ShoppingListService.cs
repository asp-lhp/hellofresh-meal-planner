using Microsoft.EntityFrameworkCore;
using MealPlanner.Api.Data;
using MealPlanner.Api.Models;
using System.Text.Json;

namespace MealPlanner.Api.Services;

public class ShoppingListService
{
    private readonly MealPlannerContext _db;

    public ShoppingListService(MealPlannerContext db)
    {
        _db = db;
    }

    /// <summary>
    /// Generate a shopping list from a meal plan
    /// </summary>
    public async Task<ShoppingList> GenerateShoppingList(int mealPlanId)
    {
        // Load meal plan with recipes and their ingredients
        var mealPlan = await _db.MealPlans
            .Include(m => m.Recipes)
                .ThenInclude(mr => mr.Recipe)
                    .ThenInclude(r => r.Ingredients)
            .FirstOrDefaultAsync(m => m.Id == mealPlanId);

        if (mealPlan == null)
            throw new InvalidOperationException($"Meal plan {mealPlanId} not found");

        // Create shopping list
        var shoppingList = new ShoppingList
        {
            MealPlanId = mealPlanId
        };

        _db.ShoppingLists.Add(shoppingList);
        await _db.SaveChangesAsync(); // Save to get ID

        // Collect all ingredients from all recipes
        var ingredientsByRecipe = new Dictionary<string, List<string>>();

        foreach (var mealPlanRecipe in mealPlan.Recipes)
        {
            var recipeName = mealPlanRecipe.Recipe.Name;

            foreach (var ingredient in mealPlanRecipe.Recipe.Ingredients)
            {
                var ingredientKey = NormalizeIngredientName(ingredient.Name);

                if (!ingredientsByRecipe.ContainsKey(ingredientKey))
                {
                    ingredientsByRecipe[ingredientKey] = new List<string>();
                }

                ingredientsByRecipe[ingredientKey].Add(recipeName);
            }
        }

        // Create shopping list items
        var displayOrder = 0;

        foreach (var (ingredientName, recipeNames) in ingredientsByRecipe.OrderBy(x => x.Key))
        {
            // Try to find matching food for normalization
            var food = await FindFoodByName(ingredientName);

            var item = new ShoppingListItem
            {
                ShoppingListId = shoppingList.Id,
                FoodId = food?.Id,
                ItemName = food?.Name ?? ingredientName,
                Quantity = recipeNames.Count.ToString(), // Simple count for now
                Unit = "servings", // Simplified for MVP
                Aisle = food?.Aisle ?? "other",
                DisplayOrder = displayOrder++,
                IsBulkItem = food?.IsBulkItem ?? false,
                BulkItemNote = food?.BulkItemNote,
                Checked = false,
                UsedInRecipes = JsonSerializer.Serialize(recipeNames)
            };

            _db.ShoppingListItems.Add(item);
        }

        await _db.SaveChangesAsync();

        return shoppingList;
    }

    /// <summary>
    /// Normalize ingredient name for matching
    /// </summary>
    private string NormalizeIngredientName(string name)
    {
        return name.ToLowerInvariant()
            .Replace("boneless", "")
            .Replace("skinless", "")
            .Replace("fresh", "")
            .Replace("organic", "")
            .Trim();
    }

    /// <summary>
    /// Find food by name (case-insensitive, fuzzy match)
    /// </summary>
    private async Task<Food?> FindFoodByName(string ingredientName)
    {
        // Try exact match first
        var exactMatch = await _db.Foods
            .FirstOrDefaultAsync(f => f.Name.ToLower() == ingredientName.ToLower());

        if (exactMatch != null)
            return exactMatch;

        // Try contains match
        var containsMatch = await _db.Foods
            .FirstOrDefaultAsync(f => ingredientName.ToLower().Contains(f.Name.ToLower()));

        return containsMatch;
    }
}
