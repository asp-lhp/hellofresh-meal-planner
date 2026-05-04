namespace MealPlanner.Api.Models;

public class Instruction
{
    public int Id { get; set; }
    public long RecipeId { get; set; }
    public int StepNumber { get; set; }
    public string Description { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }

    // Navigation property
    public Recipe Recipe { get; set; } = null!;
}
