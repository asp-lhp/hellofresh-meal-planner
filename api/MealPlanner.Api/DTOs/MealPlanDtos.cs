namespace MealPlanner.Api.DTOs;

// Request to create a new meal plan
public class CreateMealPlanRequest
{
    public string Name { get; set; } = string.Empty;
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public int? UserId { get; set; } // Flask user ID for multi-user support
}

// Request to update an existing meal plan
public class UpdateMealPlanRequest
{
    public string? Name { get; set; }
    public DateTime? StartDate { get; set; }
    public DateTime? EndDate { get; set; }
}

// Request to add a recipe to a meal plan
public class AddRecipeToMealPlanRequest
{
    public long RecipeId { get; set; }
    public DateTime ScheduledDate { get; set; }
    public string MealType { get; set; } = "dinner";
    public int Servings { get; set; } = 2;
}

// Response for meal plan summary (list view)
public class MealPlanSummary
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public int RecipeCount { get; set; }
    public DateTime CreatedAt { get; set; }
    public int? UserId { get; set; }
}

// Response for meal plan details (full view)
public class MealPlanDetails
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public DateTime CreatedAt { get; set; }
    public int? UserId { get; set; }
    public List<MealPlanRecipeDetails> Recipes { get; set; } = new();
}

// Recipe details within a meal plan
public class MealPlanRecipeDetails
{
    public int Id { get; set; }
    public long RecipeId { get; set; }
    public string RecipeName { get; set; } = string.Empty;
    public string? RecipeImageUrl { get; set; }
    public int? TotalTime { get; set; }
    public int? Calories { get; set; }
    public DateTime ScheduledDate { get; set; }
    public string MealType { get; set; } = string.Empty;
    public int Servings { get; set; }
}
