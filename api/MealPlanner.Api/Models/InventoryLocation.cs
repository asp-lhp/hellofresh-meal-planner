namespace MealPlanner.Api.Models;

/// <summary>
/// Storage location for inventory items (freezer, fridge, pantry)
/// </summary>
public class InventoryLocation
{
    public int Id { get; set; }
    public string Name { get; set; } = string.Empty; // "freezer", "fridge", "pantry"
    public string? Description { get; set; }
    public bool IsFreezer { get; set; } // Special flag for frozen storage
    public int DisplayOrder { get; set; }

    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;

    // Navigation property
    public ICollection<InventoryItem> Items { get; set; } = new List<InventoryItem>();
}
