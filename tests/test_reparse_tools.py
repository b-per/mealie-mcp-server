from copy import deepcopy

import pytest
from fastmcp.exceptions import ToolError

SLUG = "test-recipe"
REFERENCE = "58e6a020-1be3-4894-b84d-a29108674b66"


@pytest.mark.parametrize("language", [None, "fr-FR"])
async def test_batch_parser_forwards_language(invoke, fetcher, language):
    lines = ["300 g de farine", "60 cl de lait"]
    result = await invoke("parse_ingredients", ingredients=lines, accept_language=language)
    request = fetcher.last()
    assert (request["method"], request["url"]) == ("POST", "/api/parser/ingredients")
    assert request["json"] == {"ingredients": lines, "parser": "nlp"}
    assert request["headers"] == ({"Accept-Language": language} if language else None)
    assert [item["input"] for item in result] == lines


def test_single_parser_api_supports_language(fetcher):
    fetcher.parse_ingredient("60 cl de lait", accept_language="fr")
    request = fetcher.last()
    assert request["method"] == "POST"
    assert request["url"] == "/api/parser/ingredient"
    assert request["json"] == {"ingredient": "60 cl de lait", "parser": "nlp"}
    assert request["headers"] == {"Accept-Language": "fr"}


@pytest.mark.parametrize("text_field", ["originalText", "display", "note"])
async def test_reparse_patches_only_ingredients_and_preserves_references(invoke, fetcher, text_field):
    fetcher.recipe.update({
        "recipeIngredient": [{
            text_field: "60 cl de lait", "referenceId": REFERENCE, "title": "Sauce",
        }],
        "recipeInstructions": [{
            "text": "Mix", "ingredientReferences": [{"referenceId": REFERENCE}],
        }],
        "futureField": {"preserve": True},
    })
    original = deepcopy(fetcher.recipe)
    await invoke("reparse_recipe_ingredients", slug=SLUG, parser="brute", accept_language="fr")
    assert [(r["method"], r["url"]) for r in fetcher.requests] == [
        ("GET", f"/api/recipes/{SLUG}"),
        ("POST", "/api/parser/ingredients"),
        ("PATCH", f"/api/recipes/{SLUG}"),
    ]
    assert fetcher.requests[1]["json"] == {"ingredients": ["60 cl de lait"], "parser": "brute"}
    assert fetcher.requests[1]["headers"] == {"Accept-Language": "fr"}
    saved = fetcher.last()["json"]
    assert set(saved) == {"recipeIngredient"}
    ingredient = saved["recipeIngredient"][0]
    assert ingredient["quantity"] == 0.25
    assert ingredient["food"]["name"] == "onion"
    assert ingredient["originalText"] == "60 cl de lait"
    assert ingredient["referenceId"] == REFERENCE
    assert ingredient["title"] == "Sauce"
    assert fetcher.recipe == original


async def test_reparse_prefers_original_text_to_display_or_note(invoke, fetcher):
    fetcher.recipe["recipeIngredient"] = [{"originalText": "original", "display": "display", "note": "note"}]
    await invoke("reparse_recipe_ingredients", slug=SLUG)
    assert fetcher.requests[1]["json"]["ingredients"] == ["original"]


@pytest.mark.parametrize("ingredients", [None, [], [{}], [{"note": " "}], ["invalid"]])
async def test_reparse_rejects_missing_text_before_parsing_or_writing(invoke, fetcher, ingredients):
    fetcher.recipe["recipeIngredient"] = ingredients
    with pytest.raises(ToolError):
        await invoke("reparse_recipe_ingredients", slug=SLUG)
    assert len(fetcher.requests) == 1
    assert fetcher.last()["method"] == "GET"


@pytest.mark.parametrize("arguments", [{"slug": " "}, {"slug": SLUG, "parser": "magic"}])
async def test_reparse_preflights_arguments(invoke, fetcher, arguments):
    with pytest.raises(ToolError):
        await invoke("reparse_recipe_ingredients", **arguments)
    assert fetcher.requests == []


@pytest.mark.parametrize("parsed", [
    [], {}, [None], [{}], [{"ingredient": []}],
    [{"ingredient": {"quantity": "invalid"}}],
])
async def test_reparse_rejects_invalid_parser_results_without_writing(invoke, fetcher, parsed):
    fetcher.recipe["recipeIngredient"] = [{"note": "2 eggs"}]
    fetcher.responses["POST", "/api/parser/ingredients"] = parsed
    with pytest.raises(ToolError):
        await invoke("reparse_recipe_ingredients", slug=SLUG)
    assert not any(r["method"] in ("PUT", "PATCH") for r in fetcher.requests)


@pytest.mark.parametrize("stage", ["fetch", "parse", "save"])
async def test_reparse_surfaces_failure_without_logging_recipe_content(
    invoke, fetcher, stage, monkeypatch, caplog,
):
    fetcher.recipe["recipeIngredient"] = [{"note": "private-ingredient"}]
    original = fetcher._handle_request
    calls = {"fetch": "GET", "parse": "POST", "save": "PATCH"}

    def fail(method, url, **kwargs):
        result = original(method, url, **kwargs)
        if method == calls[stage]:
            raise TimeoutError("private-error")
        return result

    monkeypatch.setattr(fetcher, "_handle_request", fail)
    with pytest.raises(ToolError, match="timed out"):
        await invoke("reparse_recipe_ingredients", slug=SLUG)
    assert "private-" not in caplog.text
    assert len(fetcher.requests) == {"fetch": 1, "parse": 2, "save": 3}[stage]
