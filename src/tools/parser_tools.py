import logging
import traceback
from typing import Any, Dict, List, Literal, Optional

from fastmcp import FastMCP
from fastmcp.exceptions import ToolError

from mealie import MealieFetcher
from models.recipe import Recipe, RecipeIngredient

logger = logging.getLogger("mealie-mcp")
ParserName = Literal["nlp", "brute", "openai"]


def _organizer_ref(value: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not value:
        return None
    return {"id": value.get("id"), "name": value.get("name")}


def _flatten(parsed: Dict[str, Any]) -> Dict[str, Any]:
    """Return the fields accepted by the structured recipe ingredient input."""
    ingredient = parsed.get("ingredient") or {}
    return {
        "input": parsed.get("input"),
        "confidence": (parsed.get("confidence") or {}).get("average"),
        "quantity": ingredient.get("quantity"),
        "unit": _organizer_ref(ingredient.get("unit")),
        "food": _organizer_ref(ingredient.get("food")),
        "note": ingredient.get("note"),
    }


def register_parser_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    """Register ingredient parser tools backed by Mealie itself."""

    @mcp.tool()
    def parse_ingredient(
        ingredient: str,
        parser: ParserName = "nlp",
        accept_language: Optional[str] = None,
        verbose: bool = False,
    ) -> Dict[str, Any]:
        """Parse one free-text ingredient with the same parser as Mealie's UI.

        The compact result can be passed to a recipe creation/update tool after
        removing the informational ``input`` and ``confidence`` fields.

        Args:
            ingredient: Ingredient line, for example ``60 cl de lait``.
            parser: Mealie parser backend. ``nlp`` is the normal UI behavior.
            accept_language: Optional locale such as ``fr`` or ``fr-FR``. This
                is important when parsing non-English ingredient lines.
            verbose: Return Mealie's untouched response, including detailed
                confidence and complete food/unit records.
        """
        try:
            parsed = mealie.parse_ingredient(
                ingredient, parser=parser, accept_language=accept_language
            )
            return parsed if verbose else _flatten(parsed)
        except Exception as e:
            error_msg = f"Error parsing ingredient: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def parse_ingredients(
        ingredients: List[str],
        parser: ParserName = "nlp",
        accept_language: Optional[str] = None,
        verbose: bool = False,
    ) -> List[Dict[str, Any]]:
        """Parse a recipe's ingredient lines in one Mealie API request.

        Results retain input order. Use ``accept_language`` for localized input,
        for example ``fr`` for French. The default compact objects contain the
        quantity, food, unit, and note needed by recipe creation/update tools.

        Args:
            ingredients: Non-empty ingredient lines in recipe order.
            parser: Mealie parser backend. ``nlp`` is the normal UI behavior.
            accept_language: Optional locale such as ``fr`` or ``fr-FR``.
            verbose: Return Mealie's untouched parser responses.
        """
        try:
            parsed = mealie.parse_ingredients(
                ingredients, parser=parser, accept_language=accept_language
            )
            return parsed if verbose else [_flatten(item) for item in parsed]
        except Exception as e:
            error_msg = f"Error parsing ingredients: {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)

    @mcp.tool()
    def reparse_recipe_ingredients(
        slug: str,
        parser: ParserName = "nlp",
        accept_language: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Reparse and save every ingredient on an existing recipe.

        This is the MCP equivalent of using Mealie's Parse action after an
        import. Each line is sent through Mealie's own batch parser, then the
        complete recipe is saved while preserving ingredient reference IDs and
        section titles.

        Args:
            slug: Existing recipe slug.
            parser: Mealie parser backend. ``nlp`` is the normal UI behavior.
            accept_language: Optional locale such as ``fr`` or ``fr-FR``.
        """
        try:
            recipe = Recipe.model_validate(mealie.get_recipe(slug))
            if not recipe.recipeIngredient:
                raise ValueError("Recipe has no ingredients to parse")

            lines = []
            for ingredient in recipe.recipeIngredient:
                line = ingredient.originalText or ingredient.display or ingredient.note
                if not line or not line.strip():
                    raise ValueError("Recipe contains an ingredient with no text to parse")
                lines.append(line)

            parsed = mealie.parse_ingredients(
                lines, parser=parser, accept_language=accept_language
            )
            if len(parsed) != len(recipe.recipeIngredient):
                raise ValueError("Mealie returned a different number of ingredients")

            reparsed = []
            for old, line, result in zip(
                recipe.recipeIngredient, lines, parsed, strict=True
            ):
                ingredient_data = dict(result.get("ingredient") or {})
                ingredient_data.setdefault("originalText", line)
                if old.referenceId:
                    ingredient_data["referenceId"] = old.referenceId
                if old.title and not ingredient_data.get("title"):
                    ingredient_data["title"] = old.title
                reparsed.append(RecipeIngredient.model_validate(ingredient_data))

            recipe.recipeIngredient = reparsed
            updated = mealie.update_recipe(
                slug, recipe.model_dump(exclude_none=True)
            )
            return mealie.add_recipe_urls(updated)
        except Exception as e:
            error_msg = f"Error reparsing ingredients for recipe '{slug}': {str(e)}"
            logger.error({"message": error_msg})
            logger.debug(
                {"message": "Error traceback", "traceback": traceback.format_exc()}
            )
            raise ToolError(error_msg)
