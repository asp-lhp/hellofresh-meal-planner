namespace MealPlanner.Api.Models;

public class MealPlanRecipe
{
    public int Id { get; set; }

    // Foreign keys
    public int MealPlanId { get; set; }
    public long RecipeId { get; set; }

    // Scheduling info
    public DateTime ScheduledDate { get; set; }
    public string MealType { get; set; } = "dinner"; // "breakfast", "lunch", "dinner"
    public int Servings { get; set; } = 2;

    public DateTime AddedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public MealPlan MealPlan { get; set; } = null!;
    public Recipe Recipe { get; set; } = null!;
}
