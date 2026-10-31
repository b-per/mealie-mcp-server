"""Reparse stored ingredient text without replacing unrelated recipe fields."""

from typing import Any

from models.recipe import RecipeIngredient


class ReparseMixin:
    def reparse_recipe_ingredients(
        self, slug: str, parser: str = "nlp", accept_language: str | None = None,
    ) -> dict[str, Any]:
        if not slug.strip():
            raise ValueError("Recipe slug cannot be empty")
        if parser not in ("nlp", "brute", "openai"):
            raise ValueError("parser must be one of nlp, brute, openai")
        recipe = self.get_recipe(slug)
        ingredients = recipe.get("recipeIngredient")
        if not isinstance(ingredients, list) or not ingredients:
            raise ValueError("Recipe has no ingredients to parse")
        lines = []
        for ingredient in ingredients:
            if not isinstance(ingredient, dict):
                raise ValueError("Recipe contains an invalid ingredient")
            line = ingredient.get("originalText") or ingredient.get("display") or ingredient.get("note")
            if not isinstance(line, str) or not line.strip():
                raise ValueError("Recipe contains an ingredient with no text to parse")
            lines.append(line)
        parsed = self.parse_ingredients(lines, parser=parser, accept_language=accept_language)
        if not isinstance(parsed, list) or len(parsed) != len(ingredients):
            raise ValueError("Mealie returned a different number of ingredients")
        reparsed = []
        for old, line, result in zip(ingredients, lines, parsed, strict=True):
            if not isinstance(result, dict) or not isinstance(result.get("ingredient"), dict):
                raise ValueError("Mealie returned an invalid parsed ingredient")
            data = dict(result["ingredient"])
            data["originalText"] = data.get("originalText") or line
            if old.get("referenceId"):
                data["referenceId"] = old["referenceId"]
            if old.get("title") and not data.get("title"):
                data["title"] = old["title"]
            reparsed.append(RecipeIngredient.model_validate(data).model_dump(exclude_none=True))
        return self.patch_recipe(slug, {"recipeIngredient": reparsed})
