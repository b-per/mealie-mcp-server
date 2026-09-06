"""Tests for the foods/units/tools lookup + CRUD tools.

These assert the REST method, path, and payload each tool builds.
"""

import pytest
from fastmcp.exceptions import ToolError

# --- Foods ---------------------------------------------------------------


async def test_get_foods_forwards_search_and_pagination(invoke, fetcher):
    await invoke("get_foods", search="Reis", per_page=10)
    req = fetcher.last("GET", "/api/foods")
    assert req["params"] == {"search": "Reis", "perPage": 10}


async def test_get_unlabeled_foods_is_filtered_and_bounded(invoke, fetcher):
    await invoke("get_unlabeled_foods", limit=12)
    req = fetcher.last("GET", "/api/foods")
    assert req["params"] == {
        "page": 1,
        "perPage": 12,
        "queryFilter": "label_id IS NULL",
        "orderBy": "created_at",
        "orderDirection": "desc",
    }


async def test_get_unlabeled_foods_rejects_excessive_limit(invoke):
    with pytest.raises(ToolError, match="Limit must be between 1 and 100"):
        await invoke("get_unlabeled_foods", limit=101)


async def test_get_food_labels(invoke, fetcher):
    await invoke("get_food_labels", search="Produce", per_page=20)
    req = fetcher.last("GET", "/api/groups/labels")
    assert req["params"] == {"search": "Produce", "perPage": 20}


async def test_create_food(invoke, fetcher):
    await invoke("create_food", name="Reis", plural_name="Reissorten")
    req = fetcher.last("POST", "/api/foods")
    assert req["json"] == {"name": "Reis", "pluralName": "Reissorten"}


async def test_get_food_by_id(invoke, fetcher):
    await invoke("get_food", food_id="f1")
    assert fetcher.last("GET", "/api/foods/f1") is not None


async def test_update_food(invoke, fetcher):
    await invoke("update_food", food_id="f1", description="grain")
    req = fetcher.last("PUT", "/api/foods/f1")
    # fetch-merge: id kept, change applied (see test_bugfixes for full merge)
    assert req["json"]["id"] == "f1"
    assert req["json"]["description"] == "grain"


async def test_set_food_label_preserves_food_and_sets_label(invoke, fetcher):
    await invoke("set_food_label", food_id="f1", label_id="label-1")
    req = fetcher.last("PUT", "/api/foods/f1")
    assert req["json"]["id"] == "f1"
    assert req["json"]["name"] == "Existing"
    assert req["json"]["labelId"] == "label-1"


async def test_set_food_labels_bulk_updates_each_food(invoke, fetcher):
    result = await invoke(
        "set_food_labels_bulk",
        assignments=[
            {"food_id": "f1", "label_id": "label-1"},
            {"food_id": "f2", "label_id": "label-2"},
        ],
    )
    assert result["count"] == 2
    puts = [
        request
        for request in fetcher.requests
        if request["method"] == "PUT" and request["url"].startswith("/api/foods/")
    ]
    assert [request["url"] for request in puts] == [
        "/api/foods/f1",
        "/api/foods/f2",
    ]
    assert [request["json"]["labelId"] for request in puts] == [
        "label-1",
        "label-2",
    ]


async def test_set_food_labels_bulk_rejects_duplicate_foods(invoke):
    with pytest.raises(ToolError, match="Duplicate food_id"):
        await invoke(
            "set_food_labels_bulk",
            assignments=[
                {"food_id": "f1", "label_id": "label-1"},
                {"food_id": "f1", "label_id": "label-2"},
            ],
        )


async def test_delete_food(invoke, fetcher):
    await invoke("delete_food", food_id="f1")
    assert fetcher.last("DELETE", "/api/foods/f1") is not None


# --- Units ---------------------------------------------------------------


async def test_get_units(invoke, fetcher):
    await invoke("get_units", search="Gramm")
    req = fetcher.last("GET", "/api/units")
    assert req["params"] == {"search": "Gramm"}


async def test_create_unit(invoke, fetcher):
    await invoke("create_unit", name="Gramm", abbreviation="g")
    req = fetcher.last("POST", "/api/units")
    assert req["json"] == {"name": "Gramm", "abbreviation": "g"}


async def test_update_unit(invoke, fetcher):
    await invoke("update_unit", unit_id="u1", abbreviation="ml")
    req = fetcher.last("PUT", "/api/units/u1")
    assert req["json"]["id"] == "u1"
    assert req["json"]["abbreviation"] == "ml"


async def test_delete_unit(invoke, fetcher):
    await invoke("delete_unit", unit_id="u1")
    assert fetcher.last("DELETE", "/api/units/u1") is not None


# --- Tools ---------------------------------------------------------------


async def test_get_tools(invoke, fetcher):
    await invoke("get_tools", search="Pfanne")
    req = fetcher.last("GET", "/api/organizers/tools")
    assert req["params"] == {"search": "Pfanne"}


async def test_create_tool(invoke, fetcher):
    await invoke("create_tool", name="Kochtopf")
    req = fetcher.last("POST", "/api/organizers/tools")
    assert req["json"] == {"name": "Kochtopf"}


async def test_get_tool_by_id_and_slug(invoke, fetcher):
    await invoke("get_tool", tool_id="k1")
    assert fetcher.last("GET", "/api/organizers/tools/k1") is not None
    await invoke("get_tool_by_slug", tool_slug="kochtopf")
    assert fetcher.last("GET", "/api/organizers/tools/slug/kochtopf") is not None


async def test_update_tool(invoke, fetcher):
    await invoke("update_tool", tool_id="k1", name="Topf")
    req = fetcher.last("PUT", "/api/organizers/tools/k1")
    assert req["json"]["id"] == "k1"
    assert req["json"]["name"] == "Topf"


async def test_delete_tool(invoke, fetcher):
    await invoke("delete_tool", tool_id="k1")
    assert fetcher.last("DELETE", "/api/organizers/tools/k1") is not None


@pytest.mark.parametrize(
    "tool_name",
    [
        "get_foods",
        "get_unlabeled_foods",
        "get_food_labels",
        "create_food",
        "get_food",
        "update_food",
        "set_food_label",
        "set_food_labels_bulk",
        "delete_food",
        "get_units",
        "create_unit",
        "get_unit",
        "update_unit",
        "delete_unit",
        "get_tools",
        "create_tool",
        "get_tool",
        "get_tool_by_slug",
        "update_tool",
        "delete_tool",
    ],
)
async def test_tool_is_registered(server, tool_name):
    mcp, _ = server
    names = {t.name for t in await mcp.list_tools()}
    assert tool_name in names
