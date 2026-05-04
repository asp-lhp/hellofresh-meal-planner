namespace MealPlanner.Api.DTOs;

// Response for shopping list item
public class ShoppingListItemDto
{
    public int Id { get; set; }
    public string ItemName { get; set; } = string.Empty;
    public string Quantity { get; set; } = string.Empty;
    public string? Unit { get; set; }
    public string? Aisle { get; set; }
    public bool IsBulkItem { get; set; }
    public string? BulkItemNote { get; set; }
    public bool Checked { get; set; }
    public List<string>? UsedInRecipes { get; set; }
}

// Response for full shopping list
public class ShoppingListDto
{
    public int Id { get; set; }
    public int MealPlanId { get; set; }
    public string MealPlanName { get; set; } = string.Empty;
    public DateTime GeneratedAt { get; set; }
    public int TotalItems { get; set; }
    public Dictionary<string, List<ShoppingListItemDto>> ItemsByAisle { get; set; } = new();
}

// Grouped shopping list for easy display
public class GroupedShoppingList
{
    public string MealPlanName { get; set; } = string.Empty;
    public DateTime GeneratedAt { get; set; }
    public int TotalItems { get; set; }
    public List<AisleGroup> Aisles { get; set; } = new();
}

public class AisleGroup
{
    public string AisleName { get; set; } = string.Empty;
    public List<ShoppingListItemDto> Items { get; set; } = new();
}
