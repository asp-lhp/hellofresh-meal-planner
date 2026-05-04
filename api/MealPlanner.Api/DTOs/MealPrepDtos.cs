namespace MealPlanner.Api.DTOs;

public enum PrepType
{
    Marinate,
    BatchCook,
    Chop,
    MakeSauce,
    PrepOnly
}

public record MealPrepGuideDto(
    int MealPlanId,
    string MealPlanName,
    DateTime PrepDate,
    int TotalPrepTimeMinutes,
    int TotalMeals,
    int ServingsPerMeal,
    List<PrepCategoryDto> Categories,
    List<PrepStepDto> Steps,
    List<ContainerLabelDto> ContainerLabels
);

public record PrepCategoryDto(
    PrepType Type,
    string DisplayName,
    string Icon,
    int EstimatedMinutes,
    List<PrepItemDto> Items
);

public record PrepItemDto(
    string Name,
    string ScaledQuantity,
    string PrepInstructions,
    string StorageLocation,
    List<string> UsedInRecipes
);

public record PrepStepDto(
    int StepNumber,
    string Description,
    int EstimatedMinutes,
    bool IsPassive,
    string? ParallelSuggestion
);

public record ContainerLabelDto(
    string LabelCode,
    string DayOfWeek,
    string MealType,
    string RecipeName,
    int Servings,
    string StorageLocation,
    string ReheatingInstructions
);
