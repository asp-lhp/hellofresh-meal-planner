namespace MealPlanner.Api.Models;

/// <summary>
/// Normalized food item for ingredient consolidation.
/// Supports hierarchical relationships (e.g., "chicken breast" -> "chicken")
/// </summary>
public class Food
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty;
    public string? PluralName { get; set; }

    // Hierarchy - allows "boneless chicken thighs" -> "chicken thighs" -> "chicken"
    public int? ParentFoodId { get; set; }
    public Food? ParentFood { get; set; }
    public ICollection<Food> ChildFoods { get; set; } = new List<Food>();

    // Shopping list organization
    public string? Aisle { get; set; } // "meat", "produce", "dairy", "pantry", "frozen"
    public int? AisleOrder { get; set; } // Order within aisle for shopping

    // Unit preferences
    public string? PreferredUnit { get; set; } // "lbs", "oz", "cups", "whole"

    // Bulk item handling
    public bool IsBulkItem { get; set; } // pork shoulder, whole chicken
    public string? TypicalPackageSize { get; set; } // "3-5 lbs", "1 whole"
    public string? BulkItemNote { get; set; } // "Plan to freeze excess"

    // Freezer suitability
    public bool FreezesWell { get; set; }
    public int? ShelfLifeDays { get; set; } // How long it lasts in fridge

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
}
