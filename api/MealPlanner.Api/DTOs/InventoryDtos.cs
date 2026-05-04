namespace MealPlanner.Api.DTOs;

// Request to add item to inventory
public class AddInventoryItemRequest
{
    public string LocationName { get; set; } = string.Empty; // "freezer", "fridge", "pantry"
    public string ItemName { get; set; } = string.Empty;
    public decimal Quantity { get; set; }
    public string Unit { get; set; } = string.Empty;
    public DateTime? ExpiresAt { get; set; }
    public string? Notes { get; set; }
}

// Response for inventory item
public class InventoryItemDto
{
    public int Id { get; set; }
    public string LocationName { get; set; } = string.Empty;
    public string ItemName { get; set; } = string.Empty;
    public decimal Quantity { get; set; }
    public string Unit { get; set; } = string.Empty;
    public DateTime AddedDate { get; set; }
    public DateTime? ExpiresAt { get; set; }
    public int? DaysUntilExpires { get; set; }
    public bool IsExpiringSoon { get; set; } // Within 7 days
    public bool IsExpired { get; set; }
    public string? Notes { get; set; }
}

// Response for inventory summary by location
public class InventorySummaryDto
{
    public int TotalItems { get; set; }
    public int ExpiringSoon { get; set; } // Within 7 days
    public int Expired { get; set; }
    public List<LocationInventoryDto> Locations { get; set; } = new();
}

public class LocationInventoryDto
{
    public string LocationName { get; set; } = string.Empty;
    public bool IsFreezer { get; set; }
    public int ItemCount { get; set; }
    public List<InventoryItemDto> Items { get; set; } = new();
}

// Smart suggestions for using inventory
public class InventorySuggestionsDto
{
    public List<InventoryItemDto> UseFirst { get; set; } = new(); // Expiring soon
    public List<RecipeSuggestion> RecipesUsingInventory { get; set; } = new();
}

public class RecipeSuggestion
{
    public long RecipeId { get; set; }
    public string RecipeName { get; set; } = string.Empty;
    public string? ImageUrl { get; set; }
    public List<string> InventoryItemsUsed { get; set; } = new(); // Which inventory items it uses
    public int InventoryItemCount { get; set; } // How many inventory items it uses
}

// Request to get recipe suggestions based on inventory
public class SuggestRecipesRequest
{
    public List<int> InventoryItemIds { get; set; } = new();
}
