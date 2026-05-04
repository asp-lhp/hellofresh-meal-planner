using Microsoft.EntityFrameworkCore;
using MealPlanner.Api.Data;
using MealPlanner.Api.Models;
using MealPlanner.Api.DTOs;
using MealPlanner.Api.Services;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container
builder.Services.AddOpenApi();

// Configure JSON serialization to handle circular references
builder.Services.ConfigureHttpJsonOptions(options =>
{
    options.SerializerOptions.ReferenceHandler = System.Text.Json.Serialization.ReferenceHandler.IgnoreCycles;
});

// Add CORS for development (allow Flask web app to call API)
builder.Services.AddCors(options =>
{
    options.AddPolicy("AllowAll", policy =>
    {
        policy.AllowAnyOrigin()
              .AllowAnyMethod()
              .AllowAnyHeader();
    });
});

// Configure Entity Framework Core with SQLite
// Use DATABASE_PATH env var in production, relative path in development
var dbPath = Environment.GetEnvironmentVariable("DATABASE_PATH")
    ?? Path.Combine(builder.Environment.ContentRootPath, "..", "..", "database", "recipes.db");
builder.Services.AddDbContext<MealPlannerContext>(options =>
    options.UseSqlite($"Data Source={dbPath}"));

// Register services
builder.Services.AddScoped<ShoppingListService>();
builder.Services.AddScoped<MealPlanValidationService>();
builder.Services.AddScoped<MealPrepService>();

var app = builder.Build();

// Configure the HTTP request pipeline
if (app.Environment.IsDevelopment())
{
    app.MapOpenApi();
}

app.UseCors("AllowAll");
app.UseHttpsRedirection();

// Health check endpoint for Fly.io
app.MapGet("/health", () => Results.Ok(new { status = "healthy", timestamp = DateTime.UtcNow }));

// ============================================================
// API Endpoints - Meal Planner
// ============================================================

// GET /api/recipes - List all recipes
app.MapGet("/api/recipes", async (MealPlannerContext db) =>
{
    var recipes = await db.Recipes
        .Select(r => new
        {
            r.Id,
            r.Slug,
            r.Name,
            r.Description,
            r.Difficulty,
            r.PrepTime,
            r.CookTime,
            r.TotalTime,
            r.Servings,
            r.Calories,
            r.Protein,
            r.Carbs,
            r.Fat,
            r.ImageUrl,
            r.Region
        })
        .ToListAsync();

    return Results.Ok(recipes);
})
.WithName("GetRecipes")
.WithTags("Recipes");

// GET /api/recipes/{id} - Get recipe details
app.MapGet("/api/recipes/{id}", async (long id, MealPlannerContext db) =>
{
    var recipe = await db.Recipes
        .Include(r => r.Ingredients)
        .Include(r => r.Instructions)
        .Include(r => r.Tags)
        .Include(r => r.Allergens)
        .FirstOrDefaultAsync(r => r.Id == id);

    if (recipe == null)
        return Results.NotFound(new { error = "Recipe not found" });

    return Results.Ok(recipe);
})
.WithName("GetRecipeById")
.WithTags("Recipes");

// GET /api/recipes/search - Search recipes with advanced filtering
// Query params: q (text), difficulty, maxTime, maxCalories, tags (comma-separated)
app.MapGet("/api/recipes/search", async (
    string? q,
    string? difficulty,
    int? maxTime,
    int? maxCalories,
    string? tags,
    MealPlannerContext db) =>
{
    var query = db.Recipes.AsQueryable();

    // Text search (optional with filters)
    if (!string.IsNullOrWhiteSpace(q))
    {
        query = query.Where(r => r.Name.Contains(q) || r.Description!.Contains(q));
    }

    // Filter by difficulty
    if (!string.IsNullOrWhiteSpace(difficulty))
    {
        query = query.Where(r => r.Difficulty != null && r.Difficulty.ToLower() == difficulty.ToLower());
    }

    // Filter by max total time
    if (maxTime.HasValue)
    {
        query = query.Where(r => r.TotalTime != null && r.TotalTime <= maxTime.Value);
    }

    // Filter by max calories
    if (maxCalories.HasValue)
    {
        query = query.Where(r => r.Calories != null && r.Calories <= maxCalories.Value);
    }

    // Filter by tags (comma-separated)
    if (!string.IsNullOrWhiteSpace(tags))
    {
        var tagList = tags.Split(',').Select(t => t.Trim().ToLower()).ToList();
        query = query.Where(r => r.Tags.Any(t => tagList.Contains(t.TagName.ToLower())));
    }

    var recipes = await query
        .Include(r => r.Tags)
        .Select(r => new
        {
            r.Id,
            r.Name,
            r.Description,
            r.ImageUrl,
            r.TotalTime,
            r.Calories,
            r.Difficulty,
            Tags = r.Tags.Select(t => t.TagName).ToList()
        })
        .ToListAsync();

    return Results.Ok(new
    {
        filters = new { q, difficulty, maxTime, maxCalories, tags },
        count = recipes.Count,
        recipes
    });
})
.WithName("SearchRecipes")
.WithTags("Recipes");

// GET /api/recipes/ingredient/{ingredient} - Find recipes by ingredient
app.MapGet("/api/recipes/ingredient/{ingredient}", async (string ingredient, MealPlannerContext db) =>
{
    var recipes = await db.Ingredients
        .Where(i => i.Name.Contains(ingredient))
        .Select(i => i.Recipe)
        .Distinct()
        .Select(r => new
        {
            r.Id,
            r.Name,
            r.Description,
            r.ImageUrl,
            r.TotalTime,
            r.Calories
        })
        .ToListAsync();

    return Results.Ok(new { ingredient, count = recipes.Count, recipes });
})
.WithName("GetRecipesByIngredient")
.WithTags("Recipes");

// GET /api/stats - Database statistics
app.MapGet("/api/stats", async (MealPlannerContext db) =>
{
    var stats = new
    {
        recipes = await db.Recipes.CountAsync(),
        ingredients = await db.Ingredients.CountAsync(),
        instructions = await db.Instructions.CountAsync(),
        tags = await db.Tags.CountAsync(),
        allergens = await db.Allergens.CountAsync(),
        mealPlans = await db.MealPlans.CountAsync()
    };

    return Results.Ok(stats);
})
.WithName("GetStats")
.WithTags("Statistics");

// ============================================================
// Meal Planning Endpoints
// ============================================================

// POST /api/meal-plans - Create new meal plan
app.MapPost("/api/meal-plans", async (CreateMealPlanRequest request, MealPlannerContext db) =>
{
    var mealPlan = new MealPlan
    {
        Name = request.Name,
        StartDate = request.StartDate,
        EndDate = request.EndDate,
        UserId = request.UserId
    };

    db.MealPlans.Add(mealPlan);
    await db.SaveChangesAsync();

    var response = new MealPlanSummary
    {
        Id = mealPlan.Id,
        Name = mealPlan.Name,
        StartDate = mealPlan.StartDate,
        EndDate = mealPlan.EndDate,
        RecipeCount = 0,
        CreatedAt = mealPlan.CreatedAt,
        UserId = mealPlan.UserId
    };

    return Results.Created($"/api/meal-plans/{mealPlan.Id}", response);
})
.WithName("CreateMealPlan")
.WithTags("Meal Planning");

// GET /api/meal-plans - List all meal plans (optionally filtered by userId)
app.MapGet("/api/meal-plans", async (int? userId, MealPlannerContext db) =>
{
    var query = db.MealPlans.AsQueryable();

    // Filter by userId if provided
    if (userId.HasValue)
    {
        query = query.Where(m => m.UserId == userId.Value);
    }

    var mealPlans = await query
        .Select(m => new MealPlanSummary
        {
            Id = m.Id,
            Name = m.Name,
            StartDate = m.StartDate,
            EndDate = m.EndDate,
            RecipeCount = m.Recipes.Count,
            CreatedAt = m.CreatedAt,
            UserId = m.UserId
        })
        .OrderByDescending(m => m.StartDate)
        .ToListAsync();

    return Results.Ok(mealPlans);
})
.WithName("GetMealPlans")
.WithTags("Meal Planning");

// GET /api/meal-plans/{id} - Get meal plan details
app.MapGet("/api/meal-plans/{id}", async (int id, MealPlannerContext db) =>
{
    var mealPlan = await db.MealPlans
        .Include(m => m.Recipes)
            .ThenInclude(mr => mr.Recipe)
        .FirstOrDefaultAsync(m => m.Id == id);

    if (mealPlan == null)
        return Results.NotFound(new { error = "Meal plan not found" });

    var response = new MealPlanDetails
    {
        Id = mealPlan.Id,
        Name = mealPlan.Name,
        StartDate = mealPlan.StartDate,
        EndDate = mealPlan.EndDate,
        CreatedAt = mealPlan.CreatedAt,
        UserId = mealPlan.UserId,
        Recipes = mealPlan.Recipes
            .OrderBy(mr => mr.ScheduledDate)
            .ThenBy(mr => mr.MealType)
            .Select(mr => new MealPlanRecipeDetails
            {
                Id = mr.Id,
                RecipeId = mr.RecipeId,
                RecipeName = mr.Recipe.Name,
                RecipeImageUrl = mr.Recipe.ImageUrl,
                TotalTime = mr.Recipe.TotalTime,
                Calories = mr.Recipe.Calories,
                ScheduledDate = mr.ScheduledDate,
                MealType = mr.MealType,
                Servings = mr.Servings
            })
            .ToList()
    };

    return Results.Ok(response);
})
.WithName("GetMealPlanById")
.WithTags("Meal Planning");

// POST /api/meal-plans/{id}/recipes - Add recipe to meal plan
app.MapPost("/api/meal-plans/{id}/recipes", async (int id, AddRecipeToMealPlanRequest request, MealPlannerContext db) =>
{
    // Verify meal plan exists
    var mealPlan = await db.MealPlans.FindAsync(id);
    if (mealPlan == null)
        return Results.NotFound(new { error = "Meal plan not found" });

    // Verify recipe exists
    var recipe = await db.Recipes.FindAsync(request.RecipeId);
    if (recipe == null)
        return Results.NotFound(new { error = "Recipe not found" });

    // Add recipe to meal plan
    var mealPlanRecipe = new MealPlanRecipe
    {
        MealPlanId = id,
        RecipeId = request.RecipeId,
        ScheduledDate = request.ScheduledDate,
        MealType = request.MealType,
        Servings = request.Servings
    };

    db.MealPlanRecipes.Add(mealPlanRecipe);
    await db.SaveChangesAsync();

    // Return the created entry
    var response = new MealPlanRecipeDetails
    {
        Id = mealPlanRecipe.Id,
        RecipeId = recipe.Id,
        RecipeName = recipe.Name,
        RecipeImageUrl = recipe.ImageUrl,
        TotalTime = recipe.TotalTime,
        Calories = recipe.Calories,
        ScheduledDate = mealPlanRecipe.ScheduledDate,
        MealType = mealPlanRecipe.MealType,
        Servings = mealPlanRecipe.Servings
    };

    return Results.Created($"/api/meal-plans/{id}/recipes/{mealPlanRecipe.Id}", response);
})
.WithName("AddRecipeToMealPlan")
.WithTags("Meal Planning");

// DELETE /api/meal-plans/{id}/recipes/{recipeId} - Remove recipe from meal plan
app.MapDelete("/api/meal-plans/{id}/recipes/{recipeId}", async (int id, int recipeId, MealPlannerContext db) =>
{
    var mealPlanRecipe = await db.MealPlanRecipes
        .FirstOrDefaultAsync(mr => mr.MealPlanId == id && mr.Id == recipeId);

    if (mealPlanRecipe == null)
        return Results.NotFound(new { error = "Recipe not found in meal plan" });

    db.MealPlanRecipes.Remove(mealPlanRecipe);
    await db.SaveChangesAsync();

    return Results.Ok(new { message = "Recipe removed from meal plan" });
})
.WithName("RemoveRecipeFromMealPlan")
.WithTags("Meal Planning");

// DELETE /api/meal-plans/{id} - Delete meal plan
app.MapDelete("/api/meal-plans/{id}", async (int id, MealPlannerContext db) =>
{
    var mealPlan = await db.MealPlans.FindAsync(id);
    if (mealPlan == null)
        return Results.NotFound(new { error = "Meal plan not found" });

    db.MealPlans.Remove(mealPlan);
    await db.SaveChangesAsync();

    return Results.Ok(new { message = "Meal plan deleted" });
})
.WithName("DeleteMealPlan")
.WithTags("Meal Planning");

// PUT /api/meal-plans/{id} - Update meal plan
app.MapPut("/api/meal-plans/{id}", async (int id, UpdateMealPlanRequest request, MealPlannerContext db) =>
{
    var mealPlan = await db.MealPlans.FindAsync(id);
    if (mealPlan == null)
        return Results.NotFound(new { error = "Meal plan not found" });

    // Update only provided fields
    if (request.Name != null)
        mealPlan.Name = request.Name;
    if (request.StartDate.HasValue)
        mealPlan.StartDate = request.StartDate.Value;
    if (request.EndDate.HasValue)
        mealPlan.EndDate = request.EndDate.Value;

    await db.SaveChangesAsync();

    var response = new MealPlanSummary
    {
        Id = mealPlan.Id,
        Name = mealPlan.Name,
        StartDate = mealPlan.StartDate,
        EndDate = mealPlan.EndDate,
        RecipeCount = await db.MealPlanRecipes.CountAsync(r => r.MealPlanId == id),
        CreatedAt = mealPlan.CreatedAt
    };

    return Results.Ok(response);
})
.WithName("UpdateMealPlan")
.WithTags("Meal Planning");

// POST /api/meal-plans/{id}/duplicate - Duplicate meal plan with all recipes
app.MapPost("/api/meal-plans/{id}/duplicate", async (int id, MealPlannerContext db) =>
{
    var original = await db.MealPlans
        .Include(m => m.Recipes)
        .FirstOrDefaultAsync(m => m.Id == id);

    if (original == null)
        return Results.NotFound(new { error = "Meal plan not found" });

    // Create duplicate meal plan
    var duplicate = new MealPlan
    {
        Name = $"{original.Name} (Copy)",
        StartDate = original.StartDate,
        EndDate = original.EndDate
    };

    db.MealPlans.Add(duplicate);
    await db.SaveChangesAsync();

    // Duplicate all recipes
    foreach (var recipe in original.Recipes)
    {
        var duplicateRecipe = new MealPlanRecipe
        {
            MealPlanId = duplicate.Id,
            RecipeId = recipe.RecipeId,
            ScheduledDate = recipe.ScheduledDate,
            MealType = recipe.MealType,
            Servings = recipe.Servings
        };
        db.MealPlanRecipes.Add(duplicateRecipe);
    }
    await db.SaveChangesAsync();

    var response = new MealPlanSummary
    {
        Id = duplicate.Id,
        Name = duplicate.Name,
        StartDate = duplicate.StartDate,
        EndDate = duplicate.EndDate,
        RecipeCount = original.Recipes.Count,
        CreatedAt = duplicate.CreatedAt
    };

    return Results.Created($"/api/meal-plans/{duplicate.Id}", response);
})
.WithName("DuplicateMealPlan")
.WithTags("Meal Planning");

// ============================================================
// Shopping List Endpoints
// ============================================================

// POST /api/shopping-lists/generate/{mealPlanId} - Generate shopping list from meal plan
app.MapPost("/api/shopping-lists/generate/{mealPlanId}", async (int mealPlanId, ShoppingListService service, MealPlannerContext db) =>
{
    try
    {
        var shoppingList = await service.GenerateShoppingList(mealPlanId);

        // Load the generated list with items
        var list = await db.ShoppingLists
            .Include(s => s.MealPlan)
            .Include(s => s.Items)
                .ThenInclude(i => i.Food)
            .FirstOrDefaultAsync(s => s.Id == shoppingList.Id);

        if (list == null)
            return Results.NotFound(new { error = "Shopping list not found" });

        // Group items by aisle
        var itemsByAisle = list.Items
            .GroupBy(i => i.Aisle ?? "Other")
            .OrderBy(g => g.Key)
            .ToDictionary(
                g => g.Key,
                g => g.OrderBy(i => i.DisplayOrder)
                      .Select(i => new ShoppingListItemDto
                      {
                          Id = i.Id,
                          ItemName = i.ItemName,
                          Quantity = i.Quantity,
                          Unit = i.Unit,
                          Aisle = i.Aisle,
                          IsBulkItem = i.IsBulkItem,
                          BulkItemNote = i.BulkItemNote,
                          Checked = i.Checked,
                          UsedInRecipes = System.Text.Json.JsonSerializer.Deserialize<List<string>>(i.UsedInRecipes ?? "[]")
                      })
                      .ToList()
            );

        var response = new ShoppingListDto
        {
            Id = list.Id,
            MealPlanId = list.MealPlanId,
            MealPlanName = list.MealPlan.Name,
            GeneratedAt = list.GeneratedAt,
            TotalItems = list.Items.Count,
            ItemsByAisle = itemsByAisle
        };

        return Results.Created($"/api/shopping-lists/{list.Id}", response);
    }
    catch (InvalidOperationException ex)
    {
        return Results.NotFound(new { error = ex.Message });
    }
})
.WithName("GenerateShoppingList")
.WithTags("Shopping Lists");

// GET /api/shopping-lists/{id} - Get shopping list details
app.MapGet("/api/shopping-lists/{id}", async (int id, MealPlannerContext db) =>
{
    var list = await db.ShoppingLists
        .Include(s => s.MealPlan)
        .Include(s => s.Items)
            .ThenInclude(i => i.Food)
        .FirstOrDefaultAsync(s => s.Id == id);

    if (list == null)
        return Results.NotFound(new { error = "Shopping list not found" });

    // Group items by aisle for easy display
    var aisles = list.Items
        .GroupBy(i => i.Aisle ?? "Other")
        .OrderBy(g => g.Key)
        .Select(g => new AisleGroup
        {
            AisleName = g.Key,
            Items = g.OrderBy(i => i.DisplayOrder)
                     .Select(i => new ShoppingListItemDto
                     {
                         Id = i.Id,
                         ItemName = i.ItemName,
                         Quantity = i.Quantity,
                         Unit = i.Unit,
                         Aisle = i.Aisle,
                         IsBulkItem = i.IsBulkItem,
                         BulkItemNote = i.BulkItemNote,
                         Checked = i.Checked,
                         UsedInRecipes = System.Text.Json.JsonSerializer.Deserialize<List<string>>(i.UsedInRecipes ?? "[]")
                     })
                     .ToList()
        })
        .ToList();

    var response = new GroupedShoppingList
    {
        MealPlanName = list.MealPlan.Name,
        GeneratedAt = list.GeneratedAt,
        TotalItems = list.Items.Count,
        Aisles = aisles
    };

    return Results.Ok(response);
})
.WithName("GetShoppingList")
.WithTags("Shopping Lists");

// PATCH /api/shopping-lists/{id}/items/{itemId}/check - Toggle item checked status
app.MapPatch("/api/shopping-lists/{id}/items/{itemId}/check", async (int id, int itemId, MealPlannerContext db) =>
{
    var item = await db.ShoppingListItems
        .FirstOrDefaultAsync(i => i.ShoppingListId == id && i.Id == itemId);

    if (item == null)
        return Results.NotFound(new { error = "Shopping list item not found" });

    item.Checked = !item.Checked;
    await db.SaveChangesAsync();

    return Results.Ok(new { itemId = item.Id, isChecked = item.Checked });
})
.WithName("ToggleShoppingListItemCheck")
.WithTags("Shopping Lists");

// GET /api/shopping-lists/{id}/export - Export shopping list for OpenClaw
app.MapGet("/api/shopping-lists/{id}/export", async (int id, MealPlannerContext db) =>
{
    var list = await db.ShoppingLists
        .Include(s => s.MealPlan)
        .Include(s => s.Items)
            .ThenInclude(i => i.Food)
        .FirstOrDefaultAsync(s => s.Id == id);

    if (list == null)
        return Results.NotFound(new { error = "Shopping list not found" });

    // Export format optimized for OpenClaw AI skills
    var export = new
    {
        version = "1.0",
        generatedAt = list.GeneratedAt,
        mealPlan = new
        {
            name = list.MealPlan.Name,
            startDate = list.MealPlan.StartDate,
            endDate = list.MealPlan.EndDate
        },
        totalItems = list.Items.Count,
        items = list.Items
            .OrderBy(i => i.Aisle)
            .ThenBy(i => i.DisplayOrder)
            .Select(i => new
            {
                name = i.ItemName,
                quantity = i.Quantity,
                unit = i.Unit,
                aisle = i.Aisle,
                isBulkItem = i.IsBulkItem,
                bulkNote = i.BulkItemNote,
                usedInRecipes = System.Text.Json.JsonSerializer.Deserialize<List<string>>(i.UsedInRecipes ?? "[]"),
                category = i.Food?.Aisle ?? i.Aisle
            })
            .ToList(),
        itemsByAisle = list.Items
            .GroupBy(i => i.Aisle ?? "Other")
            .OrderBy(g => g.Key)
            .ToDictionary(
                g => g.Key,
                g => g.OrderBy(i => i.DisplayOrder)
                      .Select(i => new {
                          name = i.ItemName,
                          quantity = i.Quantity,
                          unit = i.Unit,
                          isBulkItem = i.IsBulkItem
                      })
                      .ToList()
            ),
        instructions = new
        {
            totalRecipes = list.MealPlan.Recipes.Count,
            message = "Shopping list generated from meal plan. Items organized by aisle for efficient shopping.",
            regions = new[] { "en-US", "en-AU", "en-CA" }
        }
    };

    return Results.Ok(export);
})
.WithName("ExportShoppingListForOpenClaw")
.WithTags("Shopping Lists", "OpenClaw");

// ============================================================
// Meal Prep Guide Endpoints
// ============================================================

// POST /api/meal-prep/generate/{mealPlanId} - Generate meal prep guide
app.MapPost("/api/meal-prep/generate/{mealPlanId}", async (int mealPlanId, MealPrepService service, int? servings) =>
{
    try
    {
        var guide = await service.GenerateMealPrepGuide(mealPlanId, servings ?? 3);
        return Results.Ok(guide);
    }
    catch (InvalidOperationException ex)
    {
        return Results.NotFound(new { error = ex.Message });
    }
})
.WithName("GenerateMealPrepGuide")
.WithTags("Meal Prep");

// ============================================================
// Inventory Tracking Endpoints
// ============================================================

// POST /api/inventory - Add item to inventory
app.MapPost("/api/inventory", async (AddInventoryItemRequest request, MealPlannerContext db) =>
{
    // Find location
    var location = await db.InventoryLocations
        .FirstOrDefaultAsync(l => l.Name.ToLower() == request.LocationName.ToLower());

    if (location == null)
        return Results.NotFound(new { error = $"Location '{request.LocationName}' not found. Valid: freezer, fridge, pantry" });

    // Try to find matching food
    var food = await db.Foods
        .FirstOrDefaultAsync(f => f.Name.ToLower() == request.ItemName.ToLower());

    // Calculate expiration if not provided
    DateTime? expiresAt = request.ExpiresAt;
    if (expiresAt == null && food != null && food.ShelfLifeDays.HasValue)
    {
        expiresAt = DateTime.UtcNow.AddDays(food.ShelfLifeDays.Value);
    }

    var item = new InventoryItem
    {
        LocationId = location.Id,
        FoodId = food?.Id,
        ItemName = food?.Name ?? request.ItemName,
        Quantity = request.Quantity,
        Unit = request.Unit,
        ExpiresAt = expiresAt,
        Notes = request.Notes
    };

    db.InventoryItems.Add(item);
    await db.SaveChangesAsync();

    var response = new InventoryItemDto
    {
        Id = item.Id,
        LocationName = location.Name,
        ItemName = item.ItemName,
        Quantity = item.Quantity,
        Unit = item.Unit,
        AddedDate = item.AddedDate,
        ExpiresAt = item.ExpiresAt,
        DaysUntilExpires = item.ExpiresAt.HasValue
            ? (int)(item.ExpiresAt.Value - DateTime.UtcNow).TotalDays
            : null,
        Notes = item.Notes
    };

    return Results.Created($"/api/inventory/{item.Id}", response);
})
.WithName("AddInventoryItem")
.WithTags("Inventory");

// GET /api/inventory - Get all inventory grouped by location
app.MapGet("/api/inventory", async (MealPlannerContext db) =>
{
    var items = await db.InventoryItems
        .Include(i => i.Location)
        .Include(i => i.Food)
        .Where(i => !i.IsUsedUp)
        .OrderBy(i => i.ExpiresAt)
        .ToListAsync();

    var now = DateTime.UtcNow;
    var itemDtos = items.Select(i => new InventoryItemDto
    {
        Id = i.Id,
        LocationName = i.Location.Name,
        ItemName = i.ItemName,
        Quantity = i.Quantity,
        Unit = i.Unit,
        AddedDate = i.AddedDate,
        ExpiresAt = i.ExpiresAt,
        DaysUntilExpires = i.ExpiresAt.HasValue ? (int)(i.ExpiresAt.Value - now).TotalDays : null,
        IsExpiringSoon = i.ExpiresAt.HasValue && (i.ExpiresAt.Value - now).TotalDays <= 7 && (i.ExpiresAt.Value - now).TotalDays > 0,
        IsExpired = i.ExpiresAt.HasValue && i.ExpiresAt.Value < now,
        Notes = i.Notes
    }).ToList();

    var locations = await db.InventoryLocations
        .OrderBy(l => l.DisplayOrder)
        .ToListAsync();

    var locationInventory = locations.Select(l => new LocationInventoryDto
    {
        LocationName = l.Name,
        IsFreezer = l.IsFreezer,
        ItemCount = itemDtos.Count(i => i.LocationName == l.Name),
        Items = itemDtos.Where(i => i.LocationName == l.Name).ToList()
    }).ToList();

    var summary = new InventorySummaryDto
    {
        TotalItems = itemDtos.Count,
        ExpiringSoon = itemDtos.Count(i => i.IsExpiringSoon),
        Expired = itemDtos.Count(i => i.IsExpired),
        Locations = locationInventory
    };

    return Results.Ok(summary);
})
.WithName("GetInventory")
.WithTags("Inventory");

// GET /api/inventory/suggestions - Get smart recipe suggestions based on inventory
app.MapGet("/api/inventory/suggestions", async (MealPlannerContext db) =>
{
    var now = DateTime.UtcNow;

    // Get items expiring soon (within 7 days)
    var useFirst = await db.InventoryItems
        .Include(i => i.Location)
        .Where(i => !i.IsUsedUp && i.ExpiresAt.HasValue && i.ExpiresAt.Value >= now && i.ExpiresAt.Value <= now.AddDays(7))
        .OrderBy(i => i.ExpiresAt)
        .Select(i => new InventoryItemDto
        {
            Id = i.Id,
            LocationName = i.Location.Name,
            ItemName = i.ItemName,
            Quantity = i.Quantity,
            Unit = i.Unit,
            AddedDate = i.AddedDate,
            ExpiresAt = i.ExpiresAt,
            DaysUntilExpires = i.ExpiresAt.HasValue ? (int)(i.ExpiresAt.Value - now).TotalDays : null,
            IsExpiringSoon = true,
            Notes = i.Notes
        })
        .ToListAsync();

    // Find recipes that use inventory items
    var inventoryItemNames = await db.InventoryItems
        .Where(i => !i.IsUsedUp)
        .Select(i => i.ItemName.ToLower())
        .Distinct()
        .ToListAsync();

    var recipeSuggestions = await db.Recipes
        .Include(r => r.Ingredients)
        .Where(r => r.Ingredients.Any(ing => inventoryItemNames.Any(inv => ing.Name.ToLower().Contains(inv))))
        .Select(r => new
        {
            Recipe = r,
            MatchingIngredients = r.Ingredients
                .Where(ing => inventoryItemNames.Any(inv => ing.Name.ToLower().Contains(inv)))
                .Select(ing => ing.Name)
                .ToList()
        })
        .OrderByDescending(x => x.MatchingIngredients.Count)
        .Take(10)
        .ToListAsync();

    var suggestions = new InventorySuggestionsDto
    {
        UseFirst = useFirst,
        RecipesUsingInventory = recipeSuggestions.Select(rs => new RecipeSuggestion
        {
            RecipeId = rs.Recipe.Id,
            RecipeName = rs.Recipe.Name,
            ImageUrl = rs.Recipe.ImageUrl,
            InventoryItemsUsed = rs.MatchingIngredients,
            InventoryItemCount = rs.MatchingIngredients.Count
        }).ToList()
    };

    return Results.Ok(suggestions);
})
.WithName("GetInventorySuggestions")
.WithTags("Inventory");

// PATCH /api/inventory/{id}/use - Mark item as used
app.MapPatch("/api/inventory/{id}/use", async (int id, MealPlannerContext db) =>
{
    var item = await db.InventoryItems.FindAsync(id);
    if (item == null)
        return Results.NotFound(new { error = "Inventory item not found" });

    item.IsUsedUp = true;
    item.UsedDate = DateTime.UtcNow;
    await db.SaveChangesAsync();

    return Results.Ok(new { itemId = item.Id, isUsedUp = true, usedDate = item.UsedDate });
})
.WithName("MarkInventoryItemUsed")
.WithTags("Inventory");

// DELETE /api/inventory/{id} - Delete inventory item
app.MapDelete("/api/inventory/{id}", async (int id, MealPlannerContext db) =>
{
    var item = await db.InventoryItems.FindAsync(id);
    if (item == null)
        return Results.NotFound(new { error = "Inventory item not found" });

    db.InventoryItems.Remove(item);
    await db.SaveChangesAsync();

    return Results.Ok(new { message = "Inventory item deleted" });
})
.WithName("DeleteInventoryItem")
.WithTags("Inventory");

// ============================================================
// Meal Plan Analysis & Validation Endpoints
// ============================================================

// GET /api/meal-plans/{id}/nutrition - Get aggregated nutritional info for meal plan
app.MapGet("/api/meal-plans/{id}/nutrition", async (int id, MealPlannerContext db) =>
{
    var mealPlan = await db.MealPlans
        .Include(m => m.Recipes)
            .ThenInclude(mr => mr.Recipe)
        .FirstOrDefaultAsync(m => m.Id == id);

    if (mealPlan == null)
        return Results.NotFound(new { error = "Meal plan not found" });

    var recipes = mealPlan.Recipes.Select(mr => mr.Recipe).ToList();

    // Calculate totals
    var totalCalories = recipes.Sum(r => r.Calories ?? 0);
    var totalProtein = recipes.Sum(r => r.Protein ?? 0);
    var totalCarbs = recipes.Sum(r => r.Carbs ?? 0);
    var totalFat = recipes.Sum(r => r.Fat ?? 0);

    var recipeCount = recipes.Count;
    var daysInPlan = (mealPlan.EndDate - mealPlan.StartDate).Days + 1;

    // Per-day averages
    var dailyCalories = daysInPlan > 0 ? totalCalories / daysInPlan : 0;
    var dailyProtein = daysInPlan > 0 ? totalProtein / daysInPlan : 0;
    var dailyCarbs = daysInPlan > 0 ? totalCarbs / daysInPlan : 0;
    var dailyFat = daysInPlan > 0 ? totalFat / daysInPlan : 0;

    // Per-recipe averages
    var avgCaloriesPerRecipe = recipeCount > 0 ? totalCalories / recipeCount : 0;

    // Breakdown by day
    var nutritionByDay = mealPlan.Recipes
        .GroupBy(mr => mr.ScheduledDate.Date)
        .OrderBy(g => g.Key)
        .Select(g => new
        {
            date = g.Key,
            calories = g.Sum(mr => mr.Recipe.Calories ?? 0),
            protein = g.Sum(mr => mr.Recipe.Protein ?? 0),
            carbs = g.Sum(mr => mr.Recipe.Carbs ?? 0),
            fat = g.Sum(mr => mr.Recipe.Fat ?? 0),
            recipeCount = g.Count()
        })
        .ToList();

    return Results.Ok(new
    {
        mealPlanId = mealPlan.Id,
        mealPlanName = mealPlan.Name,
        startDate = mealPlan.StartDate,
        endDate = mealPlan.EndDate,
        daysInPlan,
        recipeCount,
        totals = new
        {
            calories = totalCalories,
            protein = totalProtein,
            carbs = totalCarbs,
            fat = totalFat
        },
        dailyAverages = new
        {
            calories = dailyCalories,
            protein = dailyProtein,
            carbs = dailyCarbs,
            fat = dailyFat
        },
        perRecipeAverage = new
        {
            calories = avgCaloriesPerRecipe
        },
        byDay = nutritionByDay
    });
})
.WithName("GetMealPlanNutrition")
.WithTags("Meal Planning", "Nutrition");

// GET /api/meal-plans/{id}/analyze - Analyze meal plan for bulk items and optimization
app.MapGet("/api/meal-plans/{id}/analyze", async (int id, MealPlanValidationService service) =>
{
    try
    {
        var analysis = await service.AnalyzeMealPlan(id);
        return Results.Ok(analysis);
    }
    catch (InvalidOperationException ex)
    {
        return Results.NotFound(new { error = ex.Message });
    }
})
.WithName("AnalyzeMealPlan")
.WithTags("Meal Planning");

// POST /api/recipes/suggest-from-inventory - Get recipes that use specific inventory items
app.MapPost("/api/recipes/suggest-from-inventory", async (SuggestRecipesRequest request, MealPlanValidationService service) =>
{
    if (request.InventoryItemIds == null || !request.InventoryItemIds.Any())
        return Results.BadRequest(new { error = "At least one inventory item ID is required" });

    var suggestions = await service.SuggestRecipesFromInventory(request.InventoryItemIds);

    return Results.Ok(new {
        requestedItems = request.InventoryItemIds.Count,
        recipesFound = suggestions.Count,
        recipes = suggestions
    });
})
.WithName("SuggestRecipesFromInventory")
.WithTags("Recipes", "Inventory");

app.Run();
