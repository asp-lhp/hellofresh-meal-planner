namespace MealPlanner.Api.Models;

public class Ingredient
{
    public int Id { get; set; }
    public long RecipeId { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? Quantity { get; set; }
    public string? ImageUrl { get; set; }

    // Navigation property
    public Recipe Recipe { get; set; } = null!;
}
