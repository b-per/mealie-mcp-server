import json
import logging

import pytest
from fastmcp.exceptions import ToolError


async def test_unlabeled_foods_use_one_sorted_filtered_request(invoke, fetcher):
    await invoke("get_unlabeled_foods", limit=12)
    assert len(fetcher.requests) == 1
    assert fetcher.last()["method"] == "GET"
    assert fetcher.last()["url"] == "/api/foods"
    assert fetcher.last()["params"] == {
        "page": 1, "perPage": 12, "queryFilter": "label_id IS NULL",
        "orderBy": "created_at", "orderDirection": "desc",
    }


@pytest.mark.parametrize("limit", [0, 101])
async def test_unlabeled_food_limit_is_validated(invoke, fetcher, limit):
    with pytest.raises(ToolError, match="between 1 and 100"):
        await invoke("get_unlabeled_foods", limit=limit)
    assert fetcher.requests == []


async def test_list_food_labels_preserves_api_casing(invoke, fetcher):
    await invoke("get_food_labels", search="Produce", page=2, per_page=20)
    request = fetcher.last()
    assert (request["method"], request["url"]) == ("GET", "/api/groups/labels")
    assert request["params"] == {"search": "Produce", "page": 2, "perPage": 20}


@pytest.mark.parametrize("color", [None, "#4A90E2"])
async def test_create_food_label(invoke, fetcher, color):
    result = await invoke("create_food_label", name="Cleaning Supplies", color=color)
    assert result["id"] == "generated-0001"
    request = fetcher.last()
    assert (request["method"], request["url"]) == ("POST", "/api/groups/labels")
    assert request["json"] == {
        "name": "Cleaning Supplies", **({"color": color} if color is not None else {}),
    }


@pytest.mark.parametrize("name", ["", " \t"])
async def test_create_food_label_rejects_blank_names(invoke, fetcher, name):
    with pytest.raises(ToolError, match="cannot be empty"):
        await invoke("create_food_label", name=name)
    assert fetcher.requests == []


async def test_bulk_labels_preserve_existing_food_fields(invoke, fetcher):
    result = await invoke("set_food_labels_bulk", assignments=[
        {"food_id": "f1", "label_id": "l1"}, {"food_id": "f2", "label_id": "l2"},
    ])
    assert result["count"] == 2
    assert [(r["method"], r["url"]) for r in fetcher.requests] == [
        ("GET", "/api/foods/f1"), ("PUT", "/api/foods/f1"),
        ("GET", "/api/foods/f2"), ("PUT", "/api/foods/f2"),
    ]
    for food, label in zip(result["updated"], ("l1", "l2"), strict=True):
        assert food["name"] == "Existing"
        assert food["description"] == "old"
        assert food["labelId"] == label


@pytest.mark.parametrize("assignments", [
    [], [{"food_id": "f1"}], [{"food_id": " ", "label_id": "l1"}],
    [{"food_id": "f1", "label_id": " "}],
    [{"food_id": "f1", "label_id": "l1"}, {"food_id": "f1", "label_id": "l2"}],
    [{"food_id": "f1", "label_id": "l1"}, {"food_id": "f2"}],
])
async def test_bulk_labels_validate_every_assignment_before_requests(invoke, fetcher, assignments):
    with pytest.raises(ToolError):
        await invoke("set_food_labels_bulk", assignments=assignments)
    assert fetcher.requests == []


async def test_bulk_labels_report_partial_progress_without_logging_it(invoke, fetcher, caplog):
    fetcher.fail_on("/api/foods/private-food-2", 503, "private-error")
    with caplog.at_level(logging.DEBUG):
        with pytest.raises(ToolError) as caught:
            await invoke("set_food_labels_bulk", assignments=[
                {"food_id": "private-food-1", "label_id": "private-label"},
                {"food_id": "private-food-2", "label_id": "private-label"},
                {"food_id": "private-food-3", "label_id": "private-label"},
            ])
    result = json.loads(str(caught.value))
    assert result["completed"] == [{"index": 0, "food_id": "private-food-1"}]
    assert result["failed_index"] == 1
    assert not any("private-food-3" in r["url"] for r in fetcher.requests)
    assert "private-" not in caplog.text


@pytest.mark.parametrize("label", ["cleaning-label", ""])
async def test_shopping_item_label_update_preserves_other_fields(invoke, fetcher, label):
    result = await invoke("update_shopping_list_item", item_id="item-1", label_id=label)
    assert result == {
        "id": "item-1", "shoppingListId": "list-1", "note": "Existing item",
        "quantity": 1, "checked": False, "labelId": label or None,
    }
    assert fetcher.last()["method"] == "PUT"
    assert fetcher.last()["url"] == "/api/households/shopping/items/item-1"
    assert fetcher.last()["json"] == result


@pytest.mark.parametrize("tool,arguments,path", [
    ("get_unlabeled_foods", {}, "/api/foods"),
    ("get_food_labels", {}, "/api/groups/labels"),
    ("create_food_label", {"name": "Produce"}, "/api/groups/labels"),
    ("update_shopping_list_item", {"item_id": "item-1", "label_id": "l1"}, "/shopping/items/"),
])
async def test_label_tools_surface_client_failures(invoke, fetcher, tool, arguments, path):
    fetcher.fail_on(path, 503)
    with pytest.raises(ToolError, match="HTTP 503"):
        await invoke(tool, **arguments)
