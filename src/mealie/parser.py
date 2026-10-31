import logging
from typing import Any, Dict, List

logger = logging.getLogger("mealie-mcp")


class ParserMixin:
    """Mixin class for Mealie's ingredient parser endpoints"""

    def parse_ingredient(
        self, ingredient: str, parser: str = "nlp", accept_language: str | None = None,
    ) -> Dict[str, Any]:
        """Parse a single ingredient string into structured components

        Args:
            ingredient: Free-text ingredient line, e.g. "1/4 cup chopped onion"
            parser: Parser backend: 'nlp', 'brute', or 'openai'
            accept_language: Optional locale sent as Mealie's Accept-Language header

        Returns:
            JSON response with the input, per-field confidences, and the
            resolved ingredient
        """
        if not ingredient or not ingredient.strip():
            raise ValueError("Ingredient cannot be empty")

        logger.info({"message": "Parsing ingredient"})
        return self._handle_request(
            "POST",
            "/api/parser/ingredient",
            json={"ingredient": ingredient, "parser": parser},
            headers={"Accept-Language": accept_language} if accept_language else None,
        )

    def parse_ingredients(
        self, ingredients: List[str], parser: str = "nlp", accept_language: str | None = None,
    ) -> List[Dict[str, Any]]:
        """Parse several ingredient strings in a single request

        Args:
            ingredients: Free-text ingredient lines
            parser: Parser backend: 'nlp', 'brute', or 'openai'
            accept_language: Optional locale sent as Mealie's Accept-Language header

        Returns:
            JSON response with one parse result per input, in the same order
        """
        if not ingredients:
            raise ValueError("Ingredients cannot be empty")
        if any(not ingredient.strip() for ingredient in ingredients):
            raise ValueError("Ingredient cannot be empty")

        logger.info(
            {
                "message": "Parsing ingredients",
                "count": len(ingredients),
            }
        )
        return self._handle_request(
            "POST",
            "/api/parser/ingredients",
            json={"ingredients": ingredients, "parser": parser},
            headers={"Accept-Language": accept_language} if accept_language else None,
        )
