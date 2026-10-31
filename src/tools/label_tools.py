import json
from typing import Any

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from mealie import MealieFetcher
from mealie.labels import FoodLabelUpdateError
from models.food_label import FoodLabelAssignment
from tools.errors import tool_error_boundary


def register_label_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    @mcp.tool()
    def get_unlabeled_foods(limit: int = 25) -> dict[str, Any]:
        """List the newest unlabeled foods in one filtered request (limit 1–100)."""
        with tool_error_boundary("Error fetching unlabeled foods"):
            return mealie.get_unlabeled_foods(limit)

    @mcp.tool()
    def get_food_labels(
        search: str | None = None, page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        """List labels for foods and shopping items; resolve IDs before assigning them."""
        with tool_error_boundary("Error fetching food labels"):
            return mealie.get_food_labels(search=search, page=page, per_page=per_page)

    @mcp.tool()
    def create_food_label(name: str, color: str | None = None) -> dict[str, Any]:
        """Create a food/shopping label with a name and optional hex color."""
        with tool_error_boundary("Error creating food label"):
            return mealie.create_food_label(name, color)

    @mcp.tool()
    def set_food_labels_bulk(assignments: list[FoodLabelAssignment]) -> dict[str, Any]:
        """Assign labels to foods, preserving existing fields.

        Each assignment needs food_id and label_id. All assignments are validated
        first. A later failure reports completed indexes/food IDs and the failed
        index; inspect that food before retrying. For one food, use update_food.
        """
        with tool_error_boundary("Error assigning food labels"):
            try:
                return mealie.set_food_labels_bulk(assignments)
            except FoodLabelUpdateError as error:
                raise ToolError(json.dumps({
                    "message": "Food label updates stopped; inspect the failed food before retrying",
                    "completed": error.completed,
                    "failed_index": error.failed_index,
                })) from None
