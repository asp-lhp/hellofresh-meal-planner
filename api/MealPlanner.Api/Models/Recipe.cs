namespace MealPlanner.Api.Models;

public class Recipe
{
    public long Id { get; set; }
    public string Slug { get; set; } = string.Empty;
    public string Name { get; set; } = string.Empty;
    public string? Description { get; set; }
    public string? Difficulty { get; set; }

    public int? PrepTime { get; set; }
    public int? CookTime { get; set; }
    public int? TotalTime { get; set; }
    public int Servings { get; set; } = 2;

    public int? Calories { get; set; }
    public int? Protein { get; set; }
    public int? Carbs { get; set; }
    public int? Fat { get; set; }

    public string? ImageUrl { get; set; }
    public string? HellofreshUrl { get; set; }
    public string? PdfUrl { get; set; }
    public string Region { get; set; } = "en-US";

    public DateTime ScrapedAt { get; set; } = DateTime.UtcNow;

    // Navigation properties
    public ICollection<Ingredient> Ingredients { get; set; } = new List<Ingredient>();
    public ICollection<Instruction> Instructions { get; set; } = new List<Instruction>();
    public ICollection<Tag> Tags { get; set; } = new List<Tag>();
    public ICollection<Allergen> Allergens { get; set; } = new List<Allergen>();
}
