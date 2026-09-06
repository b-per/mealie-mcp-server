import logging
from typing import Any, Dict, List, Optional

from utils import format_api_params

logger = logging.getLogger("mealie-mcp")


class FoodsMixin:
    """Mixin class for food-related API endpoints (/api/foods)."""

    def get_foods(
        self,
        search: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
        query_filter: Optional[str] = None,
        order_by: Optional[str] = None,
        order_direction: Optional[str] = None,
    ) -> Dict[str, Any]:
        """List the household's foods (optionally filtered by search term).

        Args:
            search: Search term to filter foods by name/alias
            page: Page number to retrieve
            per_page: Number of items per page
            query_filter: Advanced query filter
            order_by: Field to sort by
            order_direction: Sort direction (asc or desc)

        Returns:
            JSON response containing food items and pagination information
        """
        param_dict = {
            "search": search,
            "page": page,
            "perPage": per_page,
            "queryFilter": query_filter,
            "orderBy": order_by,
            "orderDirection": order_direction,
        }
        params = format_api_params(param_dict)

        logger.info({"message": "Retrieving foods", "parameters": params})
        return self._handle_request("GET", "/api/foods", params=params)

    def get_unlabeled_foods(self, limit: int = 25) -> Dict[str, Any]:
        """Get the newest foods that have no multi-purpose label assigned."""
        if not 1 <= limit <= 100:
            raise ValueError("Limit must be between 1 and 100")

        return self.get_foods(
            page=1,
            per_page=limit,
            query_filter="label_id IS NULL",
            order_by="created_at",
            order_direction="desc",
        )

    def get_food_labels(
        self,
        search: Optional[str] = None,
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """List the group's multi-purpose labels used to categorize foods."""
        params = format_api_params(
            {"search": search, "page": page, "perPage": per_page}
        )
        logger.info({"message": "Retrieving food labels", "parameters": params})
        return self._handle_request("GET", "/api/groups/labels", params=params)

    def create_food(
        self,
        name: str,
        plural_name: Optional[str] = None,
        description: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Create a new food.

        Args:
            name: Name of the food
            plural_name: Optional plural name
            description: Optional description

        Returns:
            JSON response containing the created food
        """
        if not name:
            raise ValueError("Food name cannot be empty")

        payload: Dict[str, Any] = {"name": name}
        if plural_name is not None:
            payload["pluralName"] = plural_name
        if description is not None:
            payload["description"] = description

        logger.info({"message": "Creating food", "name": name})
        return self._handle_request("POST", "/api/foods", json=payload)

    def get_food(self, food_id: str) -> Dict[str, Any]:
        """Get a specific food by ID.

        Args:
            food_id: The UUID of the food

        Returns:
            JSON response containing the food details
        """
        if not food_id:
            raise ValueError("Food ID cannot be empty")

        logger.info({"message": "Retrieving food", "food_id": food_id})
        return self._handle_request("GET", f"/api/foods/{food_id}")

    def update_food(self, food_id: str, food_data: Dict[str, Any]) -> Dict[str, Any]:
        """Update a specific food.

        Mealie's PUT replaces the whole record, so we fetch the existing food
        and merge the provided fields over it. This both preserves fields the
        caller did not set and keeps the required ``id``/``name`` in the body
        (a partial body would null them and fail).

        Args:
            food_id: The UUID of the food to update
            food_data: Dictionary containing the food properties to update

        Returns:
            JSON response containing the updated food
        """
        if not food_id:
            raise ValueError("Food ID cannot be empty")
        if not food_data:
            raise ValueError("Food data cannot be empty")

        existing = self.get_food(food_id)
        merged = {**existing, **food_data} if isinstance(existing, dict) else food_data

        logger.info({"message": "Updating food", "food_id": food_id})
        return self._handle_request("PUT", f"/api/foods/{food_id}", json=merged)

    def set_food_label(self, food_id: str, label_id: str) -> Dict[str, Any]:
        """Assign an existing multi-purpose label to a food."""
        if not label_id:
            raise ValueError("Label ID cannot be empty")
        return self.update_food(food_id, {"labelId": label_id})

    def set_food_labels_bulk(
        self, assignments: List[Dict[str, str]]
    ) -> Dict[str, Any]:
        """Assign labels to multiple foods using Mealie's per-food endpoint."""
        if not assignments:
            raise ValueError("At least one food-label assignment is required")

        seen_food_ids = set()
        normalized = []
        for assignment in assignments:
            food_id = assignment.get("food_id")
            label_id = assignment.get("label_id")
            if not food_id or not label_id:
                raise ValueError("Each assignment requires food_id and label_id")
            if food_id in seen_food_ids:
                raise ValueError(f"Duplicate food_id in assignments: {food_id}")
            seen_food_ids.add(food_id)
            normalized.append((food_id, label_id))

        updated = [
            self.set_food_label(food_id, label_id)
            for food_id, label_id in normalized
        ]
        return {"count": len(updated), "updated": updated}

    def delete_food(self, food_id: str) -> Dict[str, Any]:
        """Delete a specific food.

        Args:
            food_id: The UUID of the food to delete

        Returns:
            JSON response confirming deletion
        """
        if not food_id:
            raise ValueError("Food ID cannot be empty")

        logger.info({"message": "Deleting food", "food_id": food_id})
        return self._handle_request("DELETE", f"/api/foods/{food_id}")
