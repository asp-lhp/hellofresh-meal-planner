using Microsoft.EntityFrameworkCore;
using MealPlanner.Api.Models;

namespace MealPlanner.Api.Data;

public class MealPlannerContext : DbContext
{
    public MealPlannerContext(DbContextOptions<MealPlannerContext> options)
        : base(options)
    {
    }

    public DbSet<Recipe> Recipes => Set<Recipe>();
    public DbSet<Ingredient> Ingredients => Set<Ingredient>();
    public DbSet<Instruction> Instructions => Set<Instruction>();
    public DbSet<Tag> Tags => Set<Tag>();
    public DbSet<Allergen> Allergens => Set<Allergen>();
    public DbSet<MealPlan> MealPlans => Set<MealPlan>();
    public DbSet<MealPlanRecipe> MealPlanRecipes => Set<MealPlanRecipe>();
    public DbSet<Food> Foods => Set<Food>();
    public DbSet<ShoppingList> ShoppingLists => Set<ShoppingList>();
    public DbSet<ShoppingListItem> ShoppingListItems => Set<ShoppingListItem>();
    public DbSet<InventoryLocation> InventoryLocations => Set<InventoryLocation>();
    public DbSet<InventoryItem> InventoryItems => Set<InventoryItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        base.OnModelCreating(modelBuilder);

        // Configure Recipe
        modelBuilder.Entity<Recipe>(entity =>
        {
            entity.ToTable("recipes");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Slug).HasColumnName("slug").IsRequired();
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.Difficulty).HasColumnName("difficulty");
            entity.Property(e => e.PrepTime).HasColumnName("prep_time");
            entity.Property(e => e.CookTime).HasColumnName("cook_time");
            entity.Property(e => e.TotalTime).HasColumnName("total_time");
            entity.Property(e => e.Servings).HasColumnName("servings").HasDefaultValue(2);
            entity.Property(e => e.Calories).HasColumnName("calories");
            entity.Property(e => e.Protein).HasColumnName("protein");
            entity.Property(e => e.Carbs).HasColumnName("carbs");
            entity.Property(e => e.Fat).HasColumnName("fat");
            entity.Property(e => e.ImageUrl).HasColumnName("image_url");
            entity.Property(e => e.HellofreshUrl).HasColumnName("hellofresh_url");
            entity.Property(e => e.PdfUrl).HasColumnName("pdf_url");
            entity.Property(e => e.Region).HasColumnName("region").HasDefaultValue("en-US");
            entity.Property(e => e.ScrapedAt).HasColumnName("scraped_at")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");
        });

        // Configure Ingredient
        modelBuilder.Entity<Ingredient>(entity =>
        {
            entity.ToTable("ingredients");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.RecipeId).HasColumnName("recipe_id");
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.Property(e => e.Quantity).HasColumnName("quantity");
            entity.Property(e => e.ImageUrl).HasColumnName("image_url");

            entity.HasOne(e => e.Recipe)
                .WithMany(r => r.Ingredients)
                .HasForeignKey(e => e.RecipeId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure Instruction
        modelBuilder.Entity<Instruction>(entity =>
        {
            entity.ToTable("instructions");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.RecipeId).HasColumnName("recipe_id");
            entity.Property(e => e.StepNumber).HasColumnName("step_number");
            entity.Property(e => e.Description).HasColumnName("description").IsRequired();
            entity.Property(e => e.ImageUrl).HasColumnName("image_url");

            entity.HasOne(e => e.Recipe)
                .WithMany(r => r.Instructions)
                .HasForeignKey(e => e.RecipeId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure Tag
        modelBuilder.Entity<Tag>(entity =>
        {
            entity.ToTable("tags");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.RecipeId).HasColumnName("recipe_id");
            entity.Property(e => e.TagName).HasColumnName("tag").IsRequired();

            entity.HasOne(e => e.Recipe)
                .WithMany(r => r.Tags)
                .HasForeignKey(e => e.RecipeId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure Allergen
        modelBuilder.Entity<Allergen>(entity =>
        {
            entity.ToTable("allergens");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.RecipeId).HasColumnName("recipe_id");
            entity.Property(e => e.AllergenName).HasColumnName("allergen").IsRequired();

            entity.HasOne(e => e.Recipe)
                .WithMany(r => r.Allergens)
                .HasForeignKey(e => e.RecipeId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure MealPlan
        modelBuilder.Entity<MealPlan>(entity =>
        {
            entity.ToTable("meal_plans");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.Property(e => e.StartDate).HasColumnName("start_date");
            entity.Property(e => e.EndDate).HasColumnName("end_date");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");
        });

        // Configure MealPlanRecipe
        modelBuilder.Entity<MealPlanRecipe>(entity =>
        {
            entity.ToTable("meal_plan_recipes");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.MealPlanId).HasColumnName("meal_plan_id");
            entity.Property(e => e.RecipeId).HasColumnName("recipe_id");
            entity.Property(e => e.ScheduledDate).HasColumnName("scheduled_date");
            entity.Property(e => e.MealType).HasColumnName("meal_type").HasDefaultValue("dinner");
            entity.Property(e => e.Servings).HasColumnName("servings").HasDefaultValue(2);
            entity.Property(e => e.AddedAt).HasColumnName("added_at")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            entity.HasOne(e => e.MealPlan)
                .WithMany(m => m.Recipes)
                .HasForeignKey(e => e.MealPlanId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.Recipe)
                .WithMany()
                .HasForeignKey(e => e.RecipeId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure Food
        modelBuilder.Entity<Food>(entity =>
        {
            entity.ToTable("foods");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.Property(e => e.PluralName).HasColumnName("plural_name");
            entity.Property(e => e.ParentFoodId).HasColumnName("parent_food_id");
            entity.Property(e => e.Aisle).HasColumnName("aisle");
            entity.Property(e => e.AisleOrder).HasColumnName("aisle_order");
            entity.Property(e => e.PreferredUnit).HasColumnName("preferred_unit");
            entity.Property(e => e.IsBulkItem).HasColumnName("is_bulk_item");
            entity.Property(e => e.TypicalPackageSize).HasColumnName("typical_package_size");
            entity.Property(e => e.BulkItemNote).HasColumnName("bulk_item_note");
            entity.Property(e => e.FreezesWell).HasColumnName("freezes_well");
            entity.Property(e => e.ShelfLifeDays).HasColumnName("shelf_life_days");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            // Self-referencing relationship for hierarchy
            entity.HasOne(e => e.ParentFood)
                .WithMany(f => f.ChildFoods)
                .HasForeignKey(e => e.ParentFoodId)
                .OnDelete(DeleteBehavior.Restrict);
        });

        // Configure ShoppingList
        modelBuilder.Entity<ShoppingList>(entity =>
        {
            entity.ToTable("shopping_lists");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.MealPlanId).HasColumnName("meal_plan_id");
            entity.Property(e => e.GeneratedAt).HasColumnName("generated_at")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");

            entity.HasOne(e => e.MealPlan)
                .WithMany()
                .HasForeignKey(e => e.MealPlanId)
                .OnDelete(DeleteBehavior.Cascade);
        });

        // Configure ShoppingListItem
        modelBuilder.Entity<ShoppingListItem>(entity =>
        {
            entity.ToTable("shopping_list_items");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.ShoppingListId).HasColumnName("shopping_list_id");
            entity.Property(e => e.FoodId).HasColumnName("food_id");
            entity.Property(e => e.ItemName).HasColumnName("item_name").IsRequired();
            entity.Property(e => e.Quantity).HasColumnName("quantity");
            entity.Property(e => e.Unit).HasColumnName("unit");
            entity.Property(e => e.Aisle).HasColumnName("aisle");
            entity.Property(e => e.DisplayOrder).HasColumnName("display_order");
            entity.Property(e => e.IsBulkItem).HasColumnName("is_bulk_item");
            entity.Property(e => e.BulkItemNote).HasColumnName("bulk_item_note");
            entity.Property(e => e.Checked).HasColumnName("checked");
            entity.Property(e => e.UsedInRecipes).HasColumnName("used_in_recipes");

            entity.HasOne(e => e.ShoppingList)
                .WithMany(s => s.Items)
                .HasForeignKey(e => e.ShoppingListId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.Food)
                .WithMany()
                .HasForeignKey(e => e.FoodId)
                .OnDelete(DeleteBehavior.SetNull);
        });

        // Configure InventoryLocation
        modelBuilder.Entity<InventoryLocation>(entity =>
        {
            entity.ToTable("inventory_locations");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.Name).HasColumnName("name").IsRequired();
            entity.Property(e => e.Description).HasColumnName("description");
            entity.Property(e => e.IsFreezer).HasColumnName("is_freezer");
            entity.Property(e => e.DisplayOrder).HasColumnName("display_order");
            entity.Property(e => e.CreatedAt).HasColumnName("created_at")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");
        });

        // Configure InventoryItem
        modelBuilder.Entity<InventoryItem>(entity =>
        {
            entity.ToTable("inventory_items");
            entity.HasKey(e => e.Id);
            entity.Property(e => e.Id).HasColumnName("id");
            entity.Property(e => e.LocationId).HasColumnName("location_id");
            entity.Property(e => e.FoodId).HasColumnName("food_id");
            entity.Property(e => e.ItemName).HasColumnName("item_name").IsRequired();
            entity.Property(e => e.Quantity).HasColumnName("quantity");
            entity.Property(e => e.Unit).HasColumnName("unit").IsRequired();
            entity.Property(e => e.AddedDate).HasColumnName("added_date")
                .HasDefaultValueSql("CURRENT_TIMESTAMP");
            entity.Property(e => e.ExpiresAt).HasColumnName("expires_at");
            entity.Property(e => e.UsedDate).HasColumnName("used_date");
            entity.Property(e => e.Notes).HasColumnName("notes");
            entity.Property(e => e.IsUsedUp).HasColumnName("is_used_up");

            entity.HasOne(e => e.Location)
                .WithMany(l => l.Items)
                .HasForeignKey(e => e.LocationId)
                .OnDelete(DeleteBehavior.Cascade);

            entity.HasOne(e => e.Food)
                .WithMany()
                .HasForeignKey(e => e.FoodId)
                .OnDelete(DeleteBehavior.SetNull);
        });
    }
}
