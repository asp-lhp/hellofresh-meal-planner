"""
Flask web app route tests for Meal Planner.
"""

import pytest


class TestPublicRoutes:
    """Test public-facing routes."""

    def test_homepage_loads(self, flask_app):
        """Test homepage returns 200."""
        response = flask_app.get('/')
        assert response.status_code == 200
        assert b'Meal Planner' in response.data

    def test_search_page_loads(self, flask_app):
        """Test search page returns 200."""
        response = flask_app.get('/search')
        assert response.status_code == 200

    def test_search_with_query(self, flask_app):
        """Test search with query parameter."""
        response = flask_app.get('/search?q=chicken')
        assert response.status_code == 200

    def test_advanced_search_loads(self, flask_app):
        """Test advanced search page returns 200."""
        response = flask_app.get('/search/advanced')
        assert response.status_code == 200

    def test_meal_plans_list(self, flask_app):
        """Test meal plans list page."""
        response = flask_app.get('/meal-plans')
        assert response.status_code == 200

    def test_create_meal_plan_page(self, flask_app):
        """Test create meal plan page loads."""
        response = flask_app.get('/meal-plans/create')
        assert response.status_code == 200


class TestRecipeRoutes:
    """Test recipe-related routes."""

    def test_recipe_detail_exists(self, flask_app):
        """Test recipe detail page for existing recipe."""
        response = flask_app.get('/recipe/1')
        assert response.status_code == 200
        assert b'Test Recipe' in response.data

    def test_recipe_detail_not_found(self, flask_app):
        """Test recipe detail page returns 404 for non-existent recipe."""
        response = flask_app.get('/recipe/99999')
        assert response.status_code == 404


class TestAdminRoutes:
    """Test admin routes."""

    def test_pending_deletions_page(self, flask_app):
        """Test pending deletions admin page."""
        response = flask_app.get('/admin/pending-deletions')
        assert response.status_code == 200

    def test_ai_tagging_dashboard(self, flask_app):
        """Test AI tagging dashboard."""
        response = flask_app.get('/admin/ai-tagging')
        assert response.status_code == 200

    def test_import_recipe_page(self, flask_app):
        """Test import recipe page."""
        response = flask_app.get('/admin/import-recipe')
        assert response.status_code == 200

    def test_mark_for_deletion(self, flask_app):
        """Test marking recipe for deletion."""
        response = flask_app.post('/recipe/1/mark-delete')
        assert response.status_code == 200
        assert b'Marked for Deletion' in response.data
