"""Food-label workflows kept separate from upstream's food CRUD."""

import logging
from typing import Any

from models.food_label import FoodLabelAssignment
from utils import format_api_params

from .client import MealieApiError

logger = logging.getLogger("mealie-mcp")


class FoodLabelUpdateError(Exception):
    def __init__(self, completed: list[dict[str, Any]], failed_index: int):
        super().__init__("Food label update did not complete")
        self.completed = completed
        self.failed_index = failed_index


class LabelsMixin:
    def get_unlabeled_foods(self, limit: int = 25) -> dict[str, Any]:
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")
        logger.info({"operation": "Retrieving unlabeled foods"})
        return self._handle_request("GET", "/api/foods", params={
            "page": 1, "perPage": limit, "queryFilter": "label_id IS NULL",
            "orderBy": "created_at", "orderDirection": "desc",
        })

    def get_food_labels(
        self, search: str | None = None, page: int | None = None,
        per_page: int | None = None,
    ) -> dict[str, Any]:
        params = format_api_params({"search": search, "page": page, "perPage": per_page})
        logger.info({"operation": "Retrieving food labels"})
        return self._handle_request("GET", "/api/groups/labels", params=params)

    def create_food_label(self, name: str, color: str | None = None) -> dict[str, Any]:
        if not name.strip():
            raise ValueError("Food label name cannot be empty")
        payload = {"name": name}
        if color is not None:
            payload["color"] = color
        logger.info({"operation": "Creating food label"})
        return self._handle_request("POST", "/api/groups/labels", json=payload)

    def set_food_labels_bulk(
        self, assignments: list[FoodLabelAssignment | dict[str, Any]],
    ) -> dict[str, Any]:
        if not assignments:
            raise ValueError("At least one food-label assignment is required")
        entries = [FoodLabelAssignment.model_validate(a) for a in assignments]
        if len({entry.food_id for entry in entries}) != len(entries):
            raise ValueError("Duplicate food_id in assignments")
        updated = []
        completed = []
        for index, entry in enumerate(entries):
            try:
                result = self.update_food(entry.food_id, {"labelId": entry.label_id})
            except (MealieApiError, TimeoutError, ConnectionError, ValueError):
                raise FoodLabelUpdateError(completed, index) from None
            updated.append(result)
            completed.append({"index": index, "food_id": entry.food_id})
        return {"count": len(updated), "updated": updated}
