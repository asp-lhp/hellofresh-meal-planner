using Microsoft.EntityFrameworkCore;
using MealPlanner.Api.Data;
using MealPlanner.Api.Models;

namespace MealPlanner.Api.Services;

/// <summary>
/// Validates meal plans for waste reduction and bulk item intelligence
/// </summary>
public class MealPlanValidationService
{
    private readonly MealPlannerContext _db;

    public MealPlanValidationService(MealPlannerContext db)
    {
        _db = db;
    }

    /// <summary>
    /// Analyze meal plan for bulk item warnings
    /// </summary>
    public async Task<MealPlanAnalysis> AnalyzeMealPlan(int mealPlanId)
    {
        var mealPlan = await _db.MealPlans
            .Include(m => m.Recipes)
                .ThenInclude(mr => mr.Recipe)
                    .ThenInclude(r => r.Ingredients)
            .FirstOrDefaultAsync(m => m.Id == mealPlanId);

        if (mealPlan == null)
            throw new InvalidOperationException($"Meal plan {mealPlanId} not found");

        var analysis = new MealPlanAnalysis
        {
            MealPlanId = mealPlanId,
            MealPlanName = mealPlan.Name,
            TotalRecipes = mealPlan.Recipes.Count
        };

        // Collect all ingredients from all recipes
        var ingredientUsage = new Dictionary<string, IngredientUsageInfo>();

        foreach (var mealPlanRecipe in mealPlan.Recipes)
        {
            foreach (var ingredient in mealPlanRecipe.Recipe.Ingredients)
            {
                var normalizedName = NormalizeIngredientName(ingredient.Name);

                if (!ingredientUsage.ContainsKey(normalizedName))
                {
                    ingredientUsage[normalizedName] = new IngredientUsageInfo
                    {
                        IngredientName = normalizedName,
                        UsedInRecipes = new List<string>()
                    };
                }

                ingredientUsage[normalizedName].UsedInRecipes.Add(mealPlanRecipe.Recipe.Name);
                ingredientUsage[normalizedName].TimesUsed++;
            }
        }

        // Find bulk items that are only used once
        foreach (var (ingredientName, usageInfo) in ingredientUsage)
        {
            var food = await FindFoodByName(ingredientName);

            if (food != null && food.IsBulkItem && usageInfo.TimesUsed == 1)
            {
                var warning = new BulkItemWarning
                {
                    FoodName = food.Name,
                    TimesUsed = usageInfo.TimesUsed,
                    UsedInRecipes = usageInfo.UsedInRecipes,
                    TypicalPackageSize = food.TypicalPackageSize,
                    Recommendation = $"{food.Name} is typically sold in {food.TypicalPackageSize}. " +
                                   $"You're only using it once this week. " +
                                   $"{food.BulkItemNote ?? "Consider adding another recipe using this ingredient or plan to freeze the excess."}"
                };

                analysis.BulkItemWarnings.Add(warning);
            }
        }

        // Find items used frequently (good for bulk buying)
        foreach (var (ingredientName, usageInfo) in ingredientUsage.Where(u => u.Value.TimesUsed >= 3))
        {
            var food = await FindFoodByName(ingredientName);

            var tip = new OptimizationTip
            {
                Category = "Bulk Buy Opportunity",
                Message = $"{ingredientName} is used {usageInfo.TimesUsed} times this week. " +
                         $"Good candidate for bulk buying or buying in advance.",
                Savings = food?.IsBulkItem == true ? "Consider buying in bulk to save money" : null
            };

            analysis.OptimizationTips.Add(tip);
        }

        return analysis;
    }

    /// <summary>
    /// Suggest recipes based on inventory items
    /// </summary>
    public async Task<List<RecipeMatchScore>> SuggestRecipesFromInventory(List<int> inventoryItemIds)
    {
        // Get inventory items
        var inventoryItems = await _db.InventoryItems
            .Include(i => i.Food)
            .Where(i => inventoryItemIds.Contains(i.Id) && !i.IsUsedUp)
            .ToListAsync();

        if (!inventoryItems.Any())
            return new List<RecipeMatchScore>();

        var inventoryFoodNames = inventoryItems
            .Select(i => i.ItemName.ToLower())
            .ToList();

        // Find recipes that use these ingredients
        var recipes = await _db.Recipes
            .Include(r => r.Ingredients)
            .ToListAsync();

        var matches = new List<RecipeMatchScore>();

        foreach (var recipe in recipes)
        {
            var recipeIngredientNames = recipe.Ingredients
                .Select(i => NormalizeIngredientName(i.Name))
                .ToList();

            // Calculate how many inventory items this recipe uses
            var matchingIngredients = inventoryFoodNames
                .Where(inv => recipeIngredientNames.Any(rec => rec.Contains(inv) || inv.Contains(rec)))
                .ToList();

            if (matchingIngredients.Any())
            {
                matches.Add(new RecipeMatchScore
                {
                    RecipeId = recipe.Id,
                    RecipeName = recipe.Name,
                    ImageUrl = recipe.ImageUrl,
                    TotalTime = recipe.TotalTime,
                    Difficulty = recipe.Difficulty,
                    MatchingIngredients = matchingIngredients,
                    MatchScore = matchingIngredients.Count,
                    TotalIngredients = recipe.Ingredients.Count,
                    MatchPercentage = (int)((matchingIngredients.Count / (double)recipe.Ingredients.Count) * 100)
                });
            }
        }

        return matches.OrderByDescending(m => m.MatchScore)
                      .ThenByDescending(m => m.MatchPercentage)
                      .ToList();
    }

    private string NormalizeIngredientName(string name)
    {
        return name.ToLowerInvariant()
            .Replace("boneless", "")
            .Replace("skinless", "")
            .Replace("fresh", "")
            .Replace("organic", "")
            .Replace("chopped", "")
            .Replace("diced", "")
            .Trim();
    }

    private async Task<Food?> FindFoodByName(string ingredientName)
    {
        var exactMatch = await _db.Foods
            .FirstOrDefaultAsync(f => f.Name.ToLower() == ingredientName.ToLower());

        if (exactMatch != null)
            return exactMatch;

        var containsMatch = await _db.Foods
            .FirstOrDefaultAsync(f => ingredientName.ToLower().Contains(f.Name.ToLower()));

        return containsMatch;
    }
}

// Response models
public class MealPlanAnalysis
{
    public int MealPlanId { get; set; }
    public string MealPlanName { get; set; } = string.Empty;
    public int TotalRecipes { get; set; }
    public List<BulkItemWarning> BulkItemWarnings { get; set; } = new();
    public List<OptimizationTip> OptimizationTips { get; set; } = new();
}

public class BulkItemWarning
{
    public string FoodName { get; set; } = string.Empty;
    public int TimesUsed { get; set; }
    public List<string> UsedInRecipes { get; set; } = new();
    public string? TypicalPackageSize { get; set; }
    public string Recommendation { get; set; } = string.Empty;
}

public class OptimizationTip
{
    public string Category { get; set; } = string.Empty;
    public string Message { get; set; } = string.Empty;
    public string? Savings { get; set; }
}

public class RecipeMatchScore
{
    public long RecipeId { get; set; }
    public string RecipeName { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }
    public int? TotalTime { get; set; }
    public string? Difficulty { get; set; }
    public List<string> MatchingIngredients { get; set; } = new();
    public int MatchScore { get; set; }
    public int TotalIngredients { get; set; }
    public int MatchPercentage { get; set; }
}

class IngredientUsageInfo
{
    public string IngredientName { get; set; } = string.Empty;
    public int TimesUsed { get; set; }
    public List<string> UsedInRecipes { get; set; } = new();
}
