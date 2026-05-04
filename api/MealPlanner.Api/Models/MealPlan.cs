namespace MealPlanner.Api.Models;

public class MealPlan
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty; // "Week of March 24"
    public DateTime StartDate { get; set; }
    public DateTime EndDate { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public int? UserId { get; set; } // Flask user ID for multi-user support

    // Navigation property
    public ICollection<MealPlanRecipe> Recipes { get; set; } = new List<MealPlanRecipe>();
}
