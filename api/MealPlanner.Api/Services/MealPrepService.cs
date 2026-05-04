using Microsoft.EntityFrameworkCore;
using MealPlanner.Api.Data;
using MealPlanner.Api.Models;
using MealPlanner.Api.DTOs;

namespace MealPlanner.Api.Services;

public class MealPrepService
{
    private readonly MealPlannerContext _db;

    private static readonly Dictionary<string, PrepType> AisleToPrepType = new()
    {
        { "meat", PrepType.Marinate },
        { "produce", PrepType.Chop },
        { "pantry", PrepType.PrepOnly },
        { "dairy", PrepType.PrepOnly },
        { "frozen", PrepType.PrepOnly }
    };

    private static readonly string[] BatchCookKeywords =
        { "rice", "quinoa", "pasta", "grain", "lentil", "bean", "chickpea", "farro", "barley", "couscous" };

    private static readonly string[] SauceKeywords =
        { "sauce", "dressing", "marinade", "glaze", "vinaigrette", "pesto", "aioli", "salsa" };

    private static readonly Dictionary<PrepType, int> PrepTimeEstimates = new()
    {
        { PrepType.Marinate, 10 },
        { PrepType.BatchCook, 25 },
        { PrepType.Chop, 8 },
        { PrepType.MakeSauce, 15 },
        { PrepType.PrepOnly, 5 }
    };

    private static readonly Dictionary<PrepType, string> PrepTypeDisplayNames = new()
    {
        { PrepType.Marinate, "Proteins to Marinate" },
        { PrepType.BatchCook, "Grains & Starches to Batch Cook" },
        { PrepType.Chop, "Vegetables to Chop" },
        { PrepType.MakeSauce, "Sauces & Dressings to Make" },
        { PrepType.PrepOnly, "Other Items to Prep" }
    };

    private static readonly Dictionary<PrepType, string> PrepTypeIcons = new()
    {
        { PrepType.Marinate, "🥩" },
        { PrepType.BatchCook, "🍚" },
        { PrepType.Chop, "🥕" },
        { PrepType.MakeSauce, "🫗" },
        { PrepType.PrepOnly, "📦" }
    };

    public MealPrepService(MealPlannerContext db)
    {
        _db = db;
    }

    public async Task<MealPrepGuideDto> GenerateMealPrepGuide(int mealPlanId, int servingsPerMeal = 3)
    {
        var mealPlan = await _db.MealPlans
            .Include(m => m.Recipes)
                .ThenInclude(mr => mr.Recipe)
                    .ThenInclude(r => r.Ingredients)
            .Include(m => m.Recipes)
                .ThenInclude(mr => mr.Recipe)
                    .ThenInclude(r => r.Instructions)
            .FirstOrDefaultAsync(m => m.Id == mealPlanId);

        if (mealPlan == null)
            throw new InvalidOperationException($"Meal plan {mealPlanId} not found");

        var prepDate = GetPrepDate(mealPlan.StartDate);
        var categorizedItems = await CategorizeIngredients(mealPlan, servingsPerMeal);
        var categories = BuildCategories(categorizedItems);
        var steps = GeneratePrepSteps(categories);
        var containerLabels = GenerateContainerLabels(mealPlan, servingsPerMeal);

        var totalPrepTime = CalculateTotalPrepTime(categories);

        return new MealPrepGuideDto(
            MealPlanId: mealPlanId,
            MealPlanName: mealPlan.Name,
            PrepDate: prepDate,
            TotalPrepTimeMinutes: totalPrepTime,
            TotalMeals: mealPlan.Recipes.Count,
            ServingsPerMeal: servingsPerMeal,
            Categories: categories,
            Steps: steps,
            ContainerLabels: containerLabels
        );
    }

    private DateTime GetPrepDate(DateTime startDate)
    {
        var daysUntilSunday = ((int)startDate.DayOfWeek - (int)DayOfWeek.Sunday + 7) % 7;
        if (daysUntilSunday == 0) daysUntilSunday = 7;
        return startDate.AddDays(-daysUntilSunday);
    }

    private async Task<Dictionary<PrepType, List<PrepItemDto>>> CategorizeIngredients(
        MealPlan mealPlan, int servingsPerMeal)
    {
        var categorized = new Dictionary<PrepType, List<PrepItemDto>>();
        foreach (PrepType type in Enum.GetValues<PrepType>())
        {
            categorized[type] = new List<PrepItemDto>();
        }

        var ingredientsByName = new Dictionary<string, (List<string> Recipes, List<string> Quantities)>();

        foreach (var mealPlanRecipe in mealPlan.Recipes)
        {
            var recipe = mealPlanRecipe.Recipe;
            var scaleFactor = (double)servingsPerMeal / (recipe.Servings > 0 ? recipe.Servings : 2);

            foreach (var ingredient in recipe.Ingredients)
            {
                var normalizedName = NormalizeIngredientName(ingredient.Name);

                if (!ingredientsByName.ContainsKey(normalizedName))
                {
                    ingredientsByName[normalizedName] = (new List<string>(), new List<string>());
                }

                ingredientsByName[normalizedName].Recipes.Add(recipe.Name);

                var scaledQty = ScaleQuantity(ingredient.Quantity, scaleFactor);
                ingredientsByName[normalizedName].Quantities.Add(scaledQty);
            }
        }

        foreach (var (ingredientName, data) in ingredientsByName)
        {
            var food = await FindFoodByName(ingredientName);
            var prepType = DeterminePrepType(ingredientName, food?.Aisle);
            var daysUntilUse = GetMinDaysUntilUse(mealPlan, data.Recipes);

            var item = new PrepItemDto(
                Name: food?.Name ?? ingredientName,
                ScaledQuantity: ConsolidateQuantities(data.Quantities),
                PrepInstructions: GetPrepInstructions(prepType, ingredientName),
                StorageLocation: daysUntilUse > 3 ? "Freezer" : "Fridge",
                UsedInRecipes: data.Recipes.Distinct().ToList()
            );

            categorized[prepType].Add(item);
        }

        return categorized;
    }

    private List<PrepCategoryDto> BuildCategories(Dictionary<PrepType, List<PrepItemDto>> categorized)
    {
        var categories = new List<PrepCategoryDto>();

        var orderedTypes = new[] { PrepType.BatchCook, PrepType.Marinate, PrepType.MakeSauce, PrepType.Chop, PrepType.PrepOnly };

        foreach (var type in orderedTypes)
        {
            if (categorized[type].Count > 0)
            {
                var estimatedMinutes = categorized[type].Count * PrepTimeEstimates[type];
                categories.Add(new PrepCategoryDto(
                    Type: type,
                    DisplayName: PrepTypeDisplayNames[type],
                    Icon: PrepTypeIcons[type],
                    EstimatedMinutes: estimatedMinutes,
                    Items: categorized[type].OrderBy(i => i.Name).ToList()
                ));
            }
        }

        return categories;
    }

    private List<PrepStepDto> GeneratePrepSteps(List<PrepCategoryDto> categories)
    {
        var steps = new List<PrepStepDto>();
        var stepNumber = 1;

        var batchCook = categories.FirstOrDefault(c => c.Type == PrepType.BatchCook);
        if (batchCook != null)
        {
            steps.Add(new PrepStepDto(
                StepNumber: stepNumber++,
                Description: $"Start batch cooking: {string.Join(", ", batchCook.Items.Select(i => i.Name))}",
                EstimatedMinutes: batchCook.EstimatedMinutes,
                IsPassive: true,
                ParallelSuggestion: "While grains cook, prepare proteins and vegetables"
            ));
        }

        var marinate = categories.FirstOrDefault(c => c.Type == PrepType.Marinate);
        if (marinate != null)
        {
            steps.Add(new PrepStepDto(
                StepNumber: stepNumber++,
                Description: $"Prep and marinate proteins: {string.Join(", ", marinate.Items.Select(i => i.Name))}",
                EstimatedMinutes: marinate.EstimatedMinutes,
                IsPassive: false,
                ParallelSuggestion: null
            ));
        }

        var sauces = categories.FirstOrDefault(c => c.Type == PrepType.MakeSauce);
        if (sauces != null)
        {
            steps.Add(new PrepStepDto(
                StepNumber: stepNumber++,
                Description: $"Make sauces and dressings: {string.Join(", ", sauces.Items.Select(i => i.Name))}",
                EstimatedMinutes: sauces.EstimatedMinutes,
                IsPassive: false,
                ParallelSuggestion: null
            ));
        }

        var chop = categories.FirstOrDefault(c => c.Type == PrepType.Chop);
        if (chop != null)
        {
            steps.Add(new PrepStepDto(
                StepNumber: stepNumber++,
                Description: $"Chop and prep vegetables: {string.Join(", ", chop.Items.Select(i => i.Name))}",
                EstimatedMinutes: chop.EstimatedMinutes,
                IsPassive: false,
                ParallelSuggestion: null
            ));
        }

        var prepOnly = categories.FirstOrDefault(c => c.Type == PrepType.PrepOnly);
        if (prepOnly != null)
        {
            steps.Add(new PrepStepDto(
                StepNumber: stepNumber++,
                Description: $"Prep remaining items: {string.Join(", ", prepOnly.Items.Select(i => i.Name))}",
                EstimatedMinutes: prepOnly.EstimatedMinutes,
                IsPassive: false,
                ParallelSuggestion: null
            ));
        }

        steps.Add(new PrepStepDto(
            StepNumber: stepNumber++,
            Description: "Portion all prepped ingredients into labeled containers",
            EstimatedMinutes: 15,
            IsPassive: false,
            ParallelSuggestion: null
        ));

        return steps;
    }

    private List<ContainerLabelDto> GenerateContainerLabels(MealPlan mealPlan, int servingsPerMeal)
    {
        var labels = new List<ContainerLabelDto>();
        var dayNumber = 1;

        var orderedRecipes = mealPlan.Recipes
            .OrderBy(r => r.ScheduledDate)
            .ThenBy(r => GetMealTypeOrder(r.MealType))
            .ToList();

        foreach (var mpr in orderedRecipes)
        {
            var dayOfWeek = mpr.ScheduledDate.DayOfWeek.ToString();
            var mealSuffix = GetMealTypeSuffix(mpr.MealType);
            var daysUntilMeal = (mpr.ScheduledDate - mealPlan.StartDate).Days;

            labels.Add(new ContainerLabelDto(
                LabelCode: $"{dayNumber}{mealSuffix}",
                DayOfWeek: dayOfWeek,
                MealType: mpr.MealType ?? "Dinner",
                RecipeName: mpr.Recipe.Name,
                Servings: servingsPerMeal,
                StorageLocation: daysUntilMeal > 3 ? "Freezer" : "Fridge",
                ReheatingInstructions: GetReheatingInstructions(daysUntilMeal > 3)
            ));

            if (mpr.MealType?.ToLower() == "dinner" || string.IsNullOrEmpty(mpr.MealType))
            {
                dayNumber++;
            }
        }

        return labels;
    }

    private int CalculateTotalPrepTime(List<PrepCategoryDto> categories)
    {
        var passiveTime = categories
            .Where(c => c.Type == PrepType.BatchCook)
            .Sum(c => c.EstimatedMinutes);

        var activeTime = categories
            .Where(c => c.Type != PrepType.BatchCook)
            .Sum(c => c.EstimatedMinutes);

        activeTime += 15;

        return Math.Max(passiveTime, activeTime);
    }

    private PrepType DeterminePrepType(string ingredientName, string? aisle)
    {
        var lowerName = ingredientName.ToLowerInvariant();

        if (BatchCookKeywords.Any(kw => lowerName.Contains(kw)))
            return PrepType.BatchCook;

        if (SauceKeywords.Any(kw => lowerName.Contains(kw)))
            return PrepType.MakeSauce;

        if (aisle != null && AisleToPrepType.TryGetValue(aisle.ToLowerInvariant(), out var prepType))
            return prepType;

        return PrepType.PrepOnly;
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
            .Replace("minced", "")
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

    private string ScaleQuantity(string? quantity, double scaleFactor)
    {
        if (string.IsNullOrWhiteSpace(quantity))
            return "as needed";

        return quantity;
    }

    private string ConsolidateQuantities(List<string> quantities)
    {
        var unique = quantities.Distinct().ToList();
        if (unique.Count == 1)
            return unique[0];

        return string.Join(" + ", unique);
    }

    private string GetPrepInstructions(PrepType type, string ingredientName)
    {
        return type switch
        {
            PrepType.Marinate => "Season and marinate overnight",
            PrepType.BatchCook => "Cook according to package directions, let cool before storing",
            PrepType.Chop => "Wash, dry, and chop; store in airtight container",
            PrepType.MakeSauce => "Blend or whisk ingredients; refrigerate",
            PrepType.PrepOnly => "Measure and store for easy access",
            _ => "Prep as directed"
        };
    }

    private int GetMinDaysUntilUse(MealPlan mealPlan, List<string> recipeNames)
    {
        var minDate = mealPlan.Recipes
            .Where(r => recipeNames.Contains(r.Recipe.Name))
            .Min(r => r.ScheduledDate);

        return (minDate - mealPlan.StartDate).Days;
    }

    private string GetMealTypeSuffix(string? mealType)
    {
        return (mealType?.ToLower()) switch
        {
            "breakfast" => "A",
            "lunch" => "B",
            "dinner" => "C",
            _ => "C"
        };
    }

    private int GetMealTypeOrder(string? mealType)
    {
        return (mealType?.ToLower()) switch
        {
            "breakfast" => 1,
            "lunch" => 2,
            "dinner" => 3,
            _ => 3
        };
    }

    private string GetReheatingInstructions(bool fromFreezer)
    {
        if (fromFreezer)
            return "Thaw overnight in fridge, then reheat at 350°F for 15-20 min or microwave 3-4 min";

        return "Microwave 2-3 min or reheat at 350°F for 10-15 min";
    }
}
