"""Tests for browser-friendly recipe URLs in MCP responses."""


async def test_recipe_list_items_include_full_url(invoke, fetcher):
    fetcher._handle_request = _list_response_recorder(fetcher)
    result = await invoke("get_recipes")
    assert result["items"][0]["recipeUrl"] == (
        "https://mealie.example/g/home/r/my-recipe"
    )


def _list_response_recorder(fetcher):
    original = fetcher._handle_request

    def handle(method, url, **kwargs):
        if method == "GET" and url == "/api/recipes":
            original(method, url, **kwargs)
            return {"items": [{"id": "recipe-id", "slug": "my-recipe"}]}
        return original(method, url, **kwargs)

    return handle


async def test_recipe_details_include_full_url(invoke):
    result = await invoke("get_recipe_detailed", slug="test-recipe")
    assert result["recipeUrl"] == (
        "https://mealie.example/g/home/r/test-recipe"
    )


def test_recipe_url_escapes_slug(fetcher):
    assert fetcher.recipe_url("one/two") == (
        "https://mealie.example/g/home/r/one%2Ftwo"
    )
