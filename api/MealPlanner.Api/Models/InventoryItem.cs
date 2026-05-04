namespace MealPlanner.Api.Models;

/// <summary>
/// Item in inventory (freezer, fridge, pantry)
/// </summary>
public class InventoryItem
{
    public int Id { get; set; }

    // Location
    public int LocationId { get; set; }
    public InventoryLocation Location { get; set; } = null!;

    // Food reference (optional - for normalization)
    public int? FoodId { get; set; }
    public Food? Food { get; set; }

    // Item details
    public string ItemName { get; set; } = string.Empty;
    public decimal Quantity { get; set; }
    public string Unit { get; set; } = string.Empty; // "lbs", "oz", "cups", "whole"

    // Dates
    public DateTime AddedDate { get; set; } = DateTime.UtcNow;
    public DateTime? ExpiresAt { get; set; } // When it goes bad
    public DateTime? UsedDate { get; set; } // When you used it up

    // Notes
    public string? Notes { get; set; } // "From Costco bulk buy", "Half used", etc.

    // Status
    public bool IsUsedUp { get; set; } = false;
}
