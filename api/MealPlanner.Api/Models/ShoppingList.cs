namespace MealPlanner.Api.Models;

/// <summary>
/// Shopping list generated from a meal plan
/// </summary>
public class ShoppingList
{
    public int Id { get; set; }
    public int MealPlanId { get; set; }
    public MealPlan MealPlan { get; set; } = null!;

    public DateTime GeneratedAt { get; set; } = DateTime.UtcNow;

    // Shopping list items
    public ICollection<ShoppingListItem> Items { get; set; } = new List<ShoppingListItem>();
}
