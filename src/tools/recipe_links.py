"""Enrich recipe responses without changing upstream's recipe implementations."""

from typing import Any
from urllib.parse import quote

from fastmcp.server.middleware import Middleware
from fastmcp.tools import ToolResult

RECIPE_TOOLS = frozenset({
    "get_recipes", "get_recipe", "create_recipe", "update_recipe",
    "import_recipe_from_url", "import_recipe_with_ai", "duplicate_recipe",
    "mark_recipe_last_made", "update_recipe_categories_and_tags",
    "reparse_recipe_ingredients",
})


def add_recipe_urls(response: dict[str, Any], base_url: str) -> dict[str, Any]:
    result = dict(response)
    slug = result.get("slug")
    if isinstance(slug, str) and slug:
        result["recipeUrl"] = f"{base_url.rstrip('/')}/g/home/r/{quote(slug, safe='')}"
    if isinstance(result.get("items"), list):
        result["items"] = [
            add_recipe_urls(item, base_url) if isinstance(item, dict) else item
            for item in result["items"]
        ]
    return result


class RecipeLinks(Middleware):
    def __init__(self, mealie):
        self.mealie = mealie

    async def on_call_tool(self, context, call_next):
        result = await call_next(context)
        if context.message.name not in RECIPE_TOOLS or result.is_error:
            return result
        if not isinstance(result.structured_content, dict):
            return result
        response = add_recipe_urls(result.structured_content, self.mealie.base_url)
        return ToolResult(content=response, structured_content=response, meta=result.meta)
