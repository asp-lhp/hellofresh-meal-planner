# Meal Planner .NET API
# Build from api directory: docker build -t meal-planner-api .

FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project file and restore
COPY MealPlanner.Api/MealPlanner.Api.csproj ./MealPlanner.Api/
RUN dotnet restore MealPlanner.Api/MealPlanner.Api.csproj

# Copy source and build
COPY MealPlanner.Api/ ./MealPlanner.Api/
RUN dotnet publish MealPlanner.Api/MealPlanner.Api.csproj -c Release -o /app/publish

# Runtime image
FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS runtime
WORKDIR /app

# Create non-root user
RUN useradd -m appuser

# Copy published app
COPY --from=build /app/publish .

# Create data directory for SQLite
RUN mkdir -p /app/data && chown -R appuser:appuser /app

USER appuser

EXPOSE 8080

ENV ASPNETCORE_URLS=http://+:8080
ENV ASPNETCORE_ENVIRONMENT=Production

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8080/health || exit 1

ENTRYPOINT ["dotnet", "MealPlanner.Api.dll"]
