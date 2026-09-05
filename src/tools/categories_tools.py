import logging
import traceback
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from mealie import MealieFetcher

logger = logging.getLogger("mealie-mcp")


def register_categories_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    """Register all category-related tools with the MCP server."""

    @mcp.tool()
    def get_categories(
        page: Optional[int] = None,
        per_page: Optional[int] = None,
    ) -> Dict[str, Any]:
        """Get all recipe categories with pagination.

        Args:
            page: Page number to retrieve
            per_page: Number of items per page

        Returns:
            Dict[str, Any]: Categories with pagination information
        """
        try:
            logger.info({"message": "Fetching categories", "page": page, "per_page": per_page})
            return mealie.get_categories(page=page, per_page=per_page)
        except Exception as e:
            error_msg = f"Error fetching categories: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def get_empty_categories() -> List[Dict[str, Any]]:
        """Get all categories that have no recipes assigned.

        Returns:
            List[Dict[str, Any]]: List of empty categories
        """
        try:
            logger.info({"message": "Fetching empty categories"})
            return mealie.get_empty_categories()
        except Exception as e:
            error_msg = f"Error fetching empty categories: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def create_category(name: str) -> Dict[str, Any]:
        """Create a new recipe category.

        Args:
            name: Name of the category (e.g., "Breakfast", "Desserts", "Vegetarian")

        Returns:
            Dict[str, Any]: The created category details
        """
        try:
            logger.info({"message": "Creating category", "name": name})
            return mealie.create_category(name)
        except Exception as e:
            error_msg = f"Error creating category '{name}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def get_category(category_id: str) -> Dict[str, Any]:
        """Get a specific category by ID.

        Args:
            category_id: The UUID of the category

        Returns:
            Dict[str, Any]: The category details including associated recipes
        """
        try:
            logger.info({"message": "Fetching category", "category_id": category_id})
            return mealie.get_category(category_id)
        except Exception as e:
            error_msg = f"Error fetching category '{category_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def get_category_by_slug(category_slug: str) -> Dict[str, Any]:
        """Get a specific category by its slug.

        Args:
            category_slug: The slug of the category (e.g., "breakfast", "desserts")

        Returns:
            Dict[str, Any]: The category details including associated recipes
        """
        try:
            logger.info({"message": "Fetching category by slug", "category_slug": category_slug})
            return mealie.get_category_by_slug(category_slug)
        except Exception as e:
            error_msg = f"Error fetching category by slug '{category_slug}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def update_category(
        category_id: str,
        name: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Update a category's details.

        Args:
            category_id: The UUID of the category to update
            name: New name for the category

        Returns:
            Dict[str, Any]: The updated category details
        """
        try:
            logger.info({"message": "Updating category", "category_id": category_id})

            category_data = {}
            if name is not None:
                category_data["name"] = name

            if not category_data:
                raise ValueError("At least one field must be provided to update")

            return mealie.update_category(category_id, category_data)
        except Exception as e:
            error_msg = f"Error updating category '{category_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)

    @mcp.tool()
    def delete_category(category_id: str) -> Dict[str, Any]:
        """Delete a specific category.

        Args:
            category_id: The UUID of the category to delete

        Returns:
            Dict[str, Any]: Confirmation of deletion
        """
        try:
            logger.info({"message": "Deleting category", "category_id": category_id})
            return mealie.delete_category(category_id)
        except Exception as e:
            error_msg = f"Error deleting category '{category_id}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug({"message": "Error traceback", "traceback": traceback.format_exc()})
            raise ToolError(error_msg)
