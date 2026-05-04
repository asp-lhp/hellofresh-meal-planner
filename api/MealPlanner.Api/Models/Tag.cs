namespace MealPlanner.Api.Models;

public class Tag
{
    public int Id { get; set; }
    public long RecipeId { get; set; }
    public string TagName { get; set; } = string.Empty;

    // Navigation property
    public Recipe Recipe { get; set; } = null!;
}
