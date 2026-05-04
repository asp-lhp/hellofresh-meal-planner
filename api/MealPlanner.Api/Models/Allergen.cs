namespace MealPlanner.Api.Models;

public class Allergen
{
    public int Id { get; set; }
    public long RecipeId { get; set; }
    public string AllergenName { get; set; } = string.Empty;

    // Navigation property
    public Recipe Recipe { get; set; } = null!;
}
