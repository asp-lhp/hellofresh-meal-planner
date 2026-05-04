# Meal Planner .NET API

C# implementation of the meal planner API using .NET 10 Minimal API and Entity Framework Core.

## Quick Start

```bash
# Build the project
dotnet build

# Run the API
dotnet run
```

The API will be available at: **http://localhost:5098**

## Tech Stack

- **.NET 10** - Latest .NET framework
- **Minimal API** - Lightweight, performant API architecture
- **Entity Framework Core** - ORM for SQLite database access
- **SQLite** - Shared database with Python scraper (40 recipes)
- **OpenAPI/Swagger** - Auto-generated API documentation

## API Endpoints

### Recipes

**GET /api/recipes**
- Returns all recipes (40 total)
- Response: Array of recipe summaries

**GET /api/recipes/{id}**
- Returns full recipe details including ingredients, instructions, tags, allergens
- Example: `/api/recipes/692`
- Response: Complete recipe object

**GET /api/recipes/search?q={query}**
- Search recipes by name or description
- Example: `/api/recipes/search?q=chicken`
- Response: Matching recipes

**GET /api/recipes/ingredient/{ingredient}**
- Find recipes containing a specific ingredient
- Example: `/api/recipes/ingredient/chicken`
- Response: Recipes with that ingredient

### Statistics

**GET /api/stats**
- Returns database statistics

## Key C# / .NET Learnings

### 1. Minimal API Pattern
Lightweight routing without controllers

### 2. Entity Framework Core
Type-safe ORM with LINQ queries

### 3. Dependency Injection
Automatic service injection into endpoints

### 4. Navigation Properties
Automatic relationship loading

## Testing

```bash
# Get all recipes
curl http://localhost:5098/api/recipes

# Search
curl "http://localhost:5098/api/recipes/search?q=chicken"

# Get stats
curl http://localhost:5098/api/stats
```

## Development

```bash
dotnet watch run  # Auto-reload on changes
```
