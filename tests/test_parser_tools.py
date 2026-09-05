"""Tests for Mealie's server-side ingredient parser tools."""

import pytest
from fastmcp.exceptions import ToolError, ValidationError


async def test_parse_ingredient_uses_ui_endpoint_and_language(invoke, fetcher):
    result = await invoke(
        "parse_ingredient", ingredient="60 cl de lait", accept_language="fr-FR"
    )

    request = fetcher.last("POST", "/api/parser/ingredient")
    assert request["json"] == {"ingredient": "60 cl de lait", "parser": "nlp"}
    assert request["headers"] == {"Accept-Language": "fr-FR"}
    assert result == {
        "input": "60 cl de lait",
        "confidence": 0.98,
        "quantity": 0.25,
        "unit": None,
        "food": {
            "id": "a0819c33-1a5e-4374-9151-ed85160c0049",
            "name": "onion",
        },
        "note": "chopped",
    }


async def test_parse_ingredients_batches_and_preserves_order(invoke, fetcher):
    lines = ["300 g de farine", "60 cl de lait"]
    result = await invoke("parse_ingredients", ingredients=lines, accept_language="fr")

    request = fetcher.last("POST", "/api/parser/ingredients")
    assert request["json"] == {"ingredients": lines, "parser": "nlp"}
    assert request["headers"] == {"Accept-Language": "fr"}
    assert [item["input"] for item in result] == lines


async def test_parse_ingredient_verbose_returns_mealie_response(invoke):
    result = await invoke("parse_ingredient", ingredient="2 eggs", verbose=True)
    assert result["confidence"]["quantity"] == 1.0
    assert "ingredient" in result


async def test_parse_ingredient_rejects_unknown_parser(invoke, fetcher):
    with pytest.raises(ValidationError):
        await invoke("parse_ingredient", ingredient="2 eggs", parser="magic")
    assert fetcher.last("POST", "/api/parser/ingredient") is None


async def test_parse_ingredients_rejects_empty_lines(invoke, fetcher):
    with pytest.raises(ToolError, match="empty lines"):
        await invoke("parse_ingredients", ingredients=["2 eggs", ""])
    assert fetcher.last("POST", "/api/parser/ingredients") is None


async def test_reparse_recipe_ingredients_uses_parser_and_saves(invoke, fetcher):
    fetcher.recipe = {
        **fetcher.recipe,
        "recipeIngredient": [
            {
                "note": "60 cl de lait",
                "referenceId": "58e6a020-1be3-4894-b84d-a29108674b66",
            }
        ],
    }

    await invoke(
        "reparse_recipe_ingredients", slug="test-recipe", accept_language="fr"
    )

    parse_request = fetcher.last("POST", "/api/parser/ingredients")
    assert parse_request["json"]["ingredients"] == ["60 cl de lait"]
    assert parse_request["headers"] == {"Accept-Language": "fr"}
    saved = fetcher.last("PUT", "/api/recipes/test-recipe")["json"]
    ingredient = saved["recipeIngredient"][0]
    assert ingredient["quantity"] == 0.25
    assert ingredient["food"]["name"] == "onion"
    assert ingredient["originalText"] == "60 cl de lait"
    assert ingredient["referenceId"] == "58e6a020-1be3-4894-b84d-a29108674b66"
