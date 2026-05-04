namespace MealPlanner.Api.Models;

/// <summary>
/// Individual item on a shopping list with consolidated quantities
/// </summary>
public class ShoppingListItem
{
    public int Id { get; set; }
    public int ShoppingListId { get; set; }
    public ShoppingList ShoppingList { get; set; } = null!;

    // Link to normalized food
    public int? FoodId { get; set; }
    public Food? Food { get; set; }

    // For items not yet mapped to Food
    public string ItemName { get; set; } = string.Empty;

    // Consolidated quantity across all recipes
    public string Quantity { get; set; } = string.Empty;
    public string? Unit { get; set; }

    // Organization
    public string? Aisle { get; set; }
    public int DisplayOrder { get; set; }

    // Smart features
    public bool IsBulkItem { get; set; }
    public string? BulkItemNote { get; set; } // "Pork shoulder: 4-6 lbs typical. Plan to freeze 2-3 lbs."
    public bool Checked { get; set; } // For marking as purchased

    // Traceability - which recipes need this ingredient
    public string? UsedInRecipes { get; set; } // JSON array of recipe IDs or names
}
