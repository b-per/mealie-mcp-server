import json
from copy import deepcopy

import pytest
from fastmcp.exceptions import ToolError

from tools.recipe_links import add_recipe_urls


def test_recipe_urls_escape_slugs_and_preserve_original_response():
    original = {"items": [{"slug": "one/two"}, {"id": "no-slug"}, None]}
    before = deepcopy(original)
    result = add_recipe_urls(original, "https://mealie.example/prefix/")
    assert result["items"][0]["recipeUrl"] == "https://mealie.example/prefix/g/home/r/one%2Ftwo"
    assert result["items"][1:] == original["items"][1:]
    assert original == before


async def test_list_recipe_links(invoke, fetcher):
    fetcher.responses["GET", "/api/recipes"] = {"items": [{"slug": "my-recipe"}]}
    result = await invoke("get_recipes")
    assert result["items"][0]["recipeUrl"] == "https://mealie.example/g/home/r/my-recipe"
    assert len(fetcher.requests) == 1


@pytest.mark.parametrize("concise", [False, True])
async def test_recipe_links_match_text_and_structured_content(server, concise):
    mcp, fetcher = server
    original = deepcopy(fetcher.recipe)
    result = await mcp.call_tool("get_recipe", {"slug": "test-recipe", "concise": concise})
    assert result.structured_content["recipeUrl"] == "https://mealie.example/g/home/r/test-recipe"
    assert json.loads(result.content[0].text) == result.structured_content
    assert fetcher.recipe == original


async def test_created_recipe_has_link(invoke):
    result = await invoke("create_recipe", name="New recipe")
    assert result["recipeUrl"] == "https://mealie.example/g/home/r/test-recipe"


async def test_non_recipe_organizer_has_no_recipe_link(invoke):
    result = await invoke("get_category", category_id="category-1")
    assert "slug" in result
    assert "recipeUrl" not in result


async def test_link_enrichment_does_not_hide_tool_failures(invoke, fetcher):
    fetcher.fail_on("/api/recipes/", 503)
    with pytest.raises(ToolError, match="HTTP 503"):
        await invoke("get_recipe", slug="test-recipe")
