#!/usr/bin/env python3
"""
Recipe Validation System
Validates recipes against completeness requirements defined in STR-30.
"""

import os
import sys
import sqlite3
import argparse
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import List, Optional
from enum import Enum

# Database path
DB_PATH = Path(__file__).parent.parent / "database" / "recipes.db"


class ValidationLevel(Enum):
    ERROR = "error"      # Recipe unusable
    WARNING = "warning"  # Degraded experience
    INFO = "info"        # Nice to have


@dataclass
class ValidationIssue:
    level: ValidationLevel
    field: str
    message: str


@dataclass
class ValidationResult:
    recipe_id: int
    recipe_name: str
    is_valid: bool  # True if no errors (warnings allowed)
    errors: List[ValidationIssue] = field(default_factory=list)
    warnings: List[ValidationIssue] = field(default_factory=list)
    info: List[ValidationIssue] = field(default_factory=list)
    score: int = 100  # 0-100 completeness score

    def add_issue(self, level: ValidationLevel, field: str, message: str):
        issue = ValidationIssue(level=level, field=field, message=message)
        if level == ValidationLevel.ERROR:
            self.errors.append(issue)
            self.is_valid = False
        elif level == ValidationLevel.WARNING:
            self.warnings.append(issue)
        else:
            self.info.append(issue)

    def calculate_score(self):
        """Calculate completeness score (0-100)"""
        # Start at 100, deduct for issues
        score = 100
        score -= len(self.errors) * 25      # Major issues
        score -= len(self.warnings) * 10    # Important gaps
        score -= len(self.info) * 2         # Minor gaps
        self.score = max(0, score)


class RecipeValidator:
    """Validates recipes against completeness requirements"""

    # Minimum instruction length to be considered valid
    MIN_INSTRUCTION_LENGTH = 20

    # Placeholder patterns to detect
    PLACEHOLDER_PATTERNS = [
        "step 1", "step 2", "step 3", "step 4", "step 5",
        "todo", "tbd", "placeholder", "coming soon"
    ]

    def __init__(self, db_path: str = None):
        self.db_path = db_path or DB_PATH
        self.db_conn = None

    def connect_db(self):
        self.db_conn = sqlite3.connect(self.db_path)
        self.db_conn.row_factory = sqlite3.Row

    def close_db(self):
        if self.db_conn:
            self.db_conn.close()

    def validate_recipe(self, recipe_id: int) -> ValidationResult:
        """Validate a single recipe against all requirements"""
        cursor = self.db_conn.cursor()

        # Get recipe
        recipe = cursor.execute("""
            SELECT id, name, description, servings, total_time, prep_time, cook_time,
                   calories, protein, carbs, fat, difficulty, image_url
            FROM recipes WHERE id = ?
        """, (recipe_id,)).fetchone()

        if not recipe:
            result = ValidationResult(
                recipe_id=recipe_id,
                recipe_name="Unknown",
                is_valid=False
            )
            result.add_issue(ValidationLevel.ERROR, "recipe", "Recipe not found")
            return result

        result = ValidationResult(
            recipe_id=recipe_id,
            recipe_name=recipe["name"] or "Unnamed",
            is_valid=True
        )

        # === REQUIRED FIELDS (errors) ===

        # Name
        if not recipe["name"] or not recipe["name"].strip():
            result.add_issue(ValidationLevel.ERROR, "name", "Missing recipe name")

        # Servings
        if not recipe["servings"] or recipe["servings"] <= 0:
            result.add_issue(ValidationLevel.ERROR, "servings", "Missing or invalid servings")

        # Ingredients
        ingredients = cursor.execute("""
            SELECT id, name, quantity FROM ingredients WHERE recipe_id = ?
        """, (recipe_id,)).fetchall()

        if not ingredients:
            result.add_issue(ValidationLevel.ERROR, "ingredients", "No ingredients found")
        else:
            # Check ingredient quality
            empty_ingredients = [i for i in ingredients if not i["name"] or not i["name"].strip()]
            if empty_ingredients:
                result.add_issue(ValidationLevel.WARNING, "ingredients",
                                f"{len(empty_ingredients)} ingredient(s) missing name")

        # Instructions
        instructions = cursor.execute("""
            SELECT id, step_number, description FROM instructions
            WHERE recipe_id = ? ORDER BY step_number
        """, (recipe_id,)).fetchall()

        if not instructions:
            result.add_issue(ValidationLevel.ERROR, "instructions", "No instructions found")
        else:
            # Check instruction quality
            self._validate_instructions(instructions, result)

        # === IMPORTANT FIELDS (warnings) ===

        if not recipe["total_time"] or recipe["total_time"] <= 0:
            result.add_issue(ValidationLevel.WARNING, "total_time", "Missing total time")

        if not recipe["image_url"]:
            result.add_issue(ValidationLevel.WARNING, "image_url", "Missing image URL")

        if not recipe["description"] or not recipe["description"].strip():
            result.add_issue(ValidationLevel.WARNING, "description", "Missing description")

        # === OPTIONAL FIELDS (info) ===

        if not recipe["calories"] or recipe["calories"] <= 0:
            result.add_issue(ValidationLevel.INFO, "calories", "Missing calorie info")

        if not recipe["difficulty"]:
            result.add_issue(ValidationLevel.INFO, "difficulty", "Missing difficulty level")

        # Check for tags
        tags = cursor.execute("""
            SELECT id FROM tags WHERE recipe_id = ?
        """, (recipe_id,)).fetchall()

        if not tags:
            result.add_issue(ValidationLevel.INFO, "tags", "No tags assigned")

        # Calculate final score
        result.calculate_score()

        return result

    def _validate_instructions(self, instructions: list, result: ValidationResult):
        """Validate instruction quality"""
        short_steps = []
        placeholder_steps = []

        for inst in instructions:
            desc = inst["description"] or ""
            step_num = inst["step_number"]

            # Check for short/empty instructions
            if len(desc.strip()) < self.MIN_INSTRUCTION_LENGTH:
                short_steps.append(step_num)

            # Check for placeholder text
            desc_lower = desc.lower()
            for pattern in self.PLACEHOLDER_PATTERNS:
                if pattern in desc_lower and len(desc) < 50:
                    placeholder_steps.append(step_num)
                    break

        if short_steps:
            result.add_issue(ValidationLevel.WARNING, "instructions",
                           f"Step(s) {short_steps} have less than {self.MIN_INSTRUCTION_LENGTH} characters")

        if placeholder_steps:
            result.add_issue(ValidationLevel.ERROR, "instructions",
                           f"Step(s) {placeholder_steps} contain placeholder text")

    def validate_all(self, include_valid: bool = False) -> List[ValidationResult]:
        """Validate all recipes in database"""
        cursor = self.db_conn.cursor()
        recipe_ids = cursor.execute("SELECT id FROM recipes ORDER BY id").fetchall()

        results = []
        for row in recipe_ids:
            result = self.validate_recipe(row["id"])
            if include_valid or not result.is_valid or result.warnings:
                results.append(result)

        return results

    def get_broken_recipes(self) -> List[ValidationResult]:
        """Get only recipes with errors (unusable)"""
        return [r for r in self.validate_all(include_valid=False) if not r.is_valid]

    def get_summary(self) -> dict:
        """Get validation summary statistics"""
        cursor = self.db_conn.cursor()
        total = cursor.execute("SELECT COUNT(*) FROM recipes").fetchone()[0]

        all_results = self.validate_all(include_valid=True)

        broken = len([r for r in all_results if not r.is_valid])
        with_warnings = len([r for r in all_results if r.is_valid and r.warnings])
        complete = len([r for r in all_results if r.is_valid and not r.warnings])

        avg_score = sum(r.score for r in all_results) / len(all_results) if all_results else 0

        return {
            "total_recipes": total,
            "broken": broken,
            "with_warnings": with_warnings,
            "complete": complete,
            "average_score": round(avg_score, 1),
            "broken_percentage": round(broken / total * 100, 1) if total else 0,
            "complete_percentage": round(complete / total * 100, 1) if total else 0
        }

    def mark_status(self, recipe_id: int, result: ValidationResult = None) -> str:
        """
        Mark a recipe's validation status based on validation result.

        Returns: 'verified', 'needs_review', or 'broken'
        """
        if result is None:
            result = self.validate_recipe(recipe_id)

        if not result.is_valid:
            status = "broken"
        elif result.warnings:
            status = "needs_review"
        else:
            status = "verified"

        cursor = self.db_conn.cursor()
        cursor.execute(
            "UPDATE recipes SET validation_status = ? WHERE id = ?",
            (status, recipe_id)
        )
        self.db_conn.commit()
        return status

    def mark_all_statuses(self) -> dict:
        """
        Validate all recipes and update their validation_status column.

        Returns: counts of each status
        """
        cursor = self.db_conn.cursor()
        recipe_ids = cursor.execute("SELECT id FROM recipes ORDER BY id").fetchall()

        counts = {"verified": 0, "needs_review": 0, "broken": 0}

        for row in recipe_ids:
            result = self.validate_recipe(row["id"])
            status = self.mark_status(row["id"], result)
            counts[status] += 1

        return counts


def print_result(result: ValidationResult, verbose: bool = False):
    """Pretty print a validation result"""
    status = "❌ BROKEN" if not result.is_valid else "⚠️  WARNINGS" if result.warnings else "✅ OK"
    print(f"\n{status} [{result.score:3d}] {result.recipe_name} (ID: {result.recipe_id})")

    if verbose or not result.is_valid or result.warnings:
        for error in result.errors:
            print(f"      🔴 {error.field}: {error.message}")
        for warning in result.warnings:
            print(f"      🟡 {warning.field}: {warning.message}")
        if verbose:
            for info in result.info:
                print(f"      🔵 {info.field}: {info.message}")


def print_summary(summary: dict):
    """Print validation summary"""
    print("\n" + "=" * 60)
    print("📊 RECIPE VALIDATION SUMMARY")
    print("=" * 60)
    print(f"  Total recipes:    {summary['total_recipes']}")
    print(f"  ✅ Complete:      {summary['complete']} ({summary['complete_percentage']}%)")
    print(f"  ⚠️  With warnings: {summary['with_warnings']}")
    print(f"  ❌ Broken:        {summary['broken']} ({summary['broken_percentage']}%)")
    print(f"  📈 Average score: {summary['average_score']}/100")
    print("=" * 60)


def main():
    parser = argparse.ArgumentParser(description="Validate recipes against completeness requirements")
    parser.add_argument("--all", action="store_true", help="Validate all recipes")
    parser.add_argument("--id", type=int, help="Validate specific recipe by ID")
    parser.add_argument("--broken", action="store_true", help="Show only broken recipes")
    parser.add_argument("--summary", action="store_true", help="Show summary statistics only")
    parser.add_argument("--mark", action="store_true", help="Update validation_status column for all recipes")
    parser.add_argument("--verbose", "-v", action="store_true", help="Show all issues including info")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    parser.add_argument("--db", type=str, help="Path to database file")

    args = parser.parse_args()

    # Default to summary if no specific action
    if not any([args.all, args.id, args.broken, args.summary, args.mark]):
        args.summary = True
        args.broken = True

    validator = RecipeValidator(args.db)
    validator.connect_db()

    try:
        if args.mark:
            print("🔄 Marking validation status for all recipes...")
            counts = validator.mark_all_statuses()
            print(f"✅ Verified:     {counts['verified']}")
            print(f"🟡 Needs review: {counts['needs_review']}")
            print(f"🔴 Broken:       {counts['broken']}")
            return

        if args.id:
            result = validator.validate_recipe(args.id)
            if args.json:
                print(json.dumps(asdict(result), default=str, indent=2))
            else:
                print_result(result, verbose=args.verbose)

        elif args.broken:
            results = validator.get_broken_recipes()
            if args.json:
                print(json.dumps([asdict(r) for r in results], default=str, indent=2))
            else:
                for result in results:
                    print_result(result, verbose=args.verbose)
                print(f"\n📋 Found {len(results)} broken recipe(s)")

        elif args.all:
            results = validator.validate_all(include_valid=True)
            if args.json:
                print(json.dumps([asdict(r) for r in results], default=str, indent=2))
            else:
                for result in results:
                    print_result(result, verbose=args.verbose)

        if args.summary or (not args.id and not args.json):
            summary = validator.get_summary()
            if args.json and args.summary:
                print(json.dumps(summary, indent=2))
            elif not args.json:
                print_summary(summary)

    finally:
        validator.close_db()


if __name__ == "__main__":
    main()
