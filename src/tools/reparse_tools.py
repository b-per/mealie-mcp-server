from typing import Any

from fastmcp import FastMCP

from mealie import MealieFetcher
from tools.errors import tool_error_boundary


def register_reparse_tools(mcp: FastMCP, mealie: MealieFetcher) -> None:
    @mcp.tool()
    def reparse_recipe_ingredients(
        slug: str, parser: str = "nlp", accept_language: str | None = None,
    ) -> dict[str, Any]:
        """Parse and save all ingredients on an existing recipe, as in Mealie's UI.

        Uses each ingredient's originalText, display, or note, in that order.
        Preserves reference IDs and section titles. Only ingredients are patched;
        instructions, metadata, nutrition, and display settings stay unchanged.
        Use accept_language (for example fr-FR) for localized input. Parser must
        be nlp, brute, or openai. Inspect parser matches before relying on them.
        """
        with tool_error_boundary("Error reparsing recipe ingredients"):
            return mealie.reparse_recipe_ingredients(slug, parser, accept_language)
