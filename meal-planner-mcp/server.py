#!/usr/bin/env python3
"""
Meal Planner MCP Server

Exposes the Meal Planner C# API as MCP tools for OpenClaw and Claude Code.
"""

from fastmcp import FastMCP
import httpx
import os
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta

# Configuration
API_BASE_URL = os.getenv("MEAL_PLANNER_API_URL", "http://localhost:5000/api")

# Initialize FastMCP server
mcp = FastMCP("Meal Planner")

# HTTP client for API calls
http_client = httpx.AsyncClient(base_url=API_BASE_URL, timeout=30.0)


# ============================================================================
# MEAL PLANS
# ============================================================================

@mcp.tool()
async def list_meal_plans() -> Dict[str, Any]:
    """
    List all meal plans.

    Returns a list of meal plans with id, name, date range, and recipe count.
    """
    try:
        response = await http_client.get("/meal-plans")
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "count": len(data),
            "mealPlans": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_meal_plan(meal_plan_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific meal plan.

    Args:
        meal_plan_id: The ID of the meal plan to retrieve

    Returns meal plan with all recipes, dates, and servings.
    """
    try:
        response = await http_client.get(f"/meal-plans/{meal_plan_id}")
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "mealPlan": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def create_meal_plan(
    name: str,
    start_date: str,
    end_date: str
) -> Dict[str, Any]:
    """
    Create a new meal plan.

    Args:
        name: Name for the meal plan (e.g., "Week of March 24")
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns the newly created meal plan.
    """
    try:
        response = await http_client.post("/meal-plans", json={
            "name": name,
            "startDate": start_date,
            "endDate": end_date
        })
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "mealPlan": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def add_recipe_to_meal_plan(
    meal_plan_id: int,
    recipe_id: int,
    scheduled_date: str,
    meal_type: str = "dinner",
    servings: int = 2
) -> Dict[str, Any]:
    """
    Add a recipe to a meal plan.

    Args:
        meal_plan_id: ID of the meal plan
        recipe_id: ID of the recipe to add
        scheduled_date: Date to schedule the meal (YYYY-MM-DD)
        meal_type: Type of meal (breakfast, lunch, dinner)
        servings: Number of servings

    Returns the updated meal plan.
    """
    try:
        response = await http_client.post(
            f"/meal-plans/{meal_plan_id}/recipes",
            json={
                "recipeId": recipe_id,
                "scheduledDate": scheduled_date,
                "mealType": meal_type,
                "servings": servings
            }
        )
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "mealPlan": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def analyze_meal_plan(meal_plan_id: int) -> Dict[str, Any]:
    """
    Analyze a meal plan for bulk items and optimization opportunities.

    Args:
        meal_plan_id: ID of the meal plan to analyze

    Returns warnings about bulk items used only once and optimization tips.
    """
    try:
        response = await http_client.get(f"/meal-plans/{meal_plan_id}/analyze")
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "analysis": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# RECIPES
# ============================================================================

@mcp.tool()
async def search_recipes(
    query: Optional[str] = None,
    difficulty: Optional[str] = None,
    max_time: Optional[int] = None,
    limit: int = 20
) -> Dict[str, Any]:
    """
    Search for recipes.

    Args:
        query: Search term (searches name, description, ingredients)
        difficulty: Filter by difficulty (easy, medium, hard)
        max_time: Maximum total time in minutes
        limit: Maximum number of results (default 20)

    Returns list of matching recipes.
    """
    try:
        params = {"limit": limit}
        if query:
            params["q"] = query
        if difficulty:
            params["difficulty"] = difficulty
        if max_time:
            params["maxTime"] = max_time

        response = await http_client.get("/recipes", params=params)
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "count": len(data),
            "recipes": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def get_recipe(recipe_id: int) -> Dict[str, Any]:
    """
    Get detailed information about a specific recipe.

    Args:
        recipe_id: The ID of the recipe

    Returns full recipe details including ingredients and instructions.
    """
    try:
        response = await http_client.get(f"/recipes/{recipe_id}")
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "recipe": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def suggest_recipes_from_inventory(
    inventory_item_ids: List[int]
) -> Dict[str, Any]:
    """
    Suggest recipes based on inventory items (e.g., from farmers market).

    Args:
        inventory_item_ids: List of inventory item IDs you have available

    Returns recipes sorted by match score (how many ingredients match).
    """
    try:
        response = await http_client.post(
            "/recipes/suggest-from-inventory",
            json={"inventoryItemIds": inventory_item_ids}
        )
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "recipesFound": data.get("recipesFound", 0),
            "recipes": data.get("recipes", [])
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# SHOPPING
# ============================================================================

@mcp.tool()
async def generate_shopping_list(meal_plan_id: int) -> Dict[str, Any]:
    """
    Generate a shopping list from a meal plan.

    Args:
        meal_plan_id: ID of the meal plan

    Returns consolidated shopping list with all ingredients.
    """
    try:
        response = await http_client.get(f"/meal-plans/{meal_plan_id}/shopping-list")
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "shoppingList": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# INVENTORY
# ============================================================================

@mcp.tool()
async def get_inventory() -> Dict[str, Any]:
    """
    Get current inventory items.

    Returns list of items in inventory (e.g., from farmers market).
    """
    try:
        response = await http_client.get("/inventory")
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "count": len(data),
            "items": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


@mcp.tool()
async def add_to_inventory(
    name: str,
    quantity: Optional[float] = None,
    unit: Optional[str] = None,
    source: str = "farmers_market"
) -> Dict[str, Any]:
    """
    Add an item to inventory.

    Args:
        name: Item name (e.g., "tomatoes", "fresh basil")
        quantity: Optional quantity
        unit: Optional unit (lbs, oz, count)
        source: Source of the item (farmers_market, pantry, etc)

    Returns the created inventory item.
    """
    try:
        response = await http_client.post("/inventory", json={
            "name": name,
            "quantity": quantity,
            "unit": unit,
            "source": source
        })
        response.raise_for_status()
        data = response.json()

        return {
            "success": True,
            "item": data
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e)
        }


# ============================================================================
# HELPER TOOLS
# ============================================================================

@mcp.tool()
async def get_current_week_dates() -> Dict[str, Any]:
    """
    Get start and end dates for the current week (Monday-Sunday).

    Useful when creating a new meal plan for the current week.
    """
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday())
    sunday = monday + timedelta(days=6)

    return {
        "success": True,
        "startDate": monday.strftime("%Y-%m-%d"),
        "endDate": sunday.strftime("%Y-%m-%d"),
        "weekName": f"Week of {monday.strftime('%B %d')}"
    }


@mcp.tool()
async def get_next_week_dates() -> Dict[str, Any]:
    """
    Get start and end dates for next week (Monday-Sunday).

    Useful when planning ahead.
    """
    today = datetime.now().date()
    monday = today - timedelta(days=today.weekday()) + timedelta(days=7)
    sunday = monday + timedelta(days=6)

    return {
        "success": True,
        "startDate": monday.strftime("%Y-%m-%d"),
        "endDate": sunday.strftime("%Y-%m-%d"),
        "weekName": f"Week of {monday.strftime('%B %d')}"
    }


# ============================================================================
# SERVER INFO
# ============================================================================

@mcp.tool()
async def meal_planner_status() -> Dict[str, Any]:
    """
    Check if the Meal Planner API is running and accessible.

    Returns API status and connection info.
    """
    try:
        response = await http_client.get("/health", timeout=5.0)

        return {
            "success": True,
            "status": "running",
            "apiUrl": API_BASE_URL,
            "message": "Meal Planner API is accessible"
        }
    except Exception as e:
        return {
            "success": False,
            "status": "unreachable",
            "apiUrl": API_BASE_URL,
            "error": str(e),
            "message": "Could not connect to Meal Planner API. Make sure it's running on localhost:5000"
        }


if __name__ == "__main__":
    # Run the MCP server
    mcp.run()
