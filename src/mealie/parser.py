import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger("mealie-mcp")


class ParserMixin:
    """Mixin for Mealie's server-side ingredient parser endpoints."""

    def parse_ingredient(
        self,
        ingredient: str,
        parser: str = "nlp",
        accept_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        if not ingredient or not ingredient.strip():
            raise ValueError("Ingredient cannot be empty")

        headers = {"Accept-Language": accept_language} if accept_language else None
        logger.info({"message": "Parsing ingredient", "parser": parser})
        return self._handle_request(
            "POST",
            "/api/parser/ingredient",
            json={"ingredient": ingredient, "parser": parser},
            headers=headers,
        )

    def parse_ingredients(
        self,
        ingredients: List[str],
        parser: str = "nlp",
        accept_language: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        if not ingredients:
            raise ValueError("Ingredients cannot be empty")
        if any(not ingredient or not ingredient.strip() for ingredient in ingredients):
            raise ValueError("Ingredients cannot contain empty lines")

        headers = {"Accept-Language": accept_language} if accept_language else None
        logger.info(
            {
                "message": "Parsing ingredients",
                "parser": parser,
                "count": len(ingredients),
            }
        )
        return self._handle_request(
            "POST",
            "/api/parser/ingredients",
            json={"ingredients": ingredients, "parser": parser},
            headers=headers,
        )
