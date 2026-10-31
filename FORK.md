# Maintaining this fork

This fork follows `rldiao/mealie-mcp-server`'s `main` branch. Adopt upstream tool
names and schemas rather than keeping aliases for removed tools. Custom commits
on top retain the following capabilities:

| Capability | Implementation |
| --- | --- |
| Standalone FastMCP for Horizon, stdio, SSE, and streamable HTTP | `pyproject.toml`, `src/server.py` |
| Custom HTTP path, stateless mode, JSON responses, HOST/PORT fallbacks | `src/server.py` |
| Label discovery/creation, newest unlabeled foods, bulk assignment | `src/mealie/labels.py`, `src/tools/label_tools.py` |
| Assign or clear one food's label | Upstream `update_food(label_id=...)` |
| Assign or clear a shopping item's label | `update_shopping_list_item(label_id=...)` |
| Language-aware ingredient parsing | `parse_ingredients(accept_language=...)` |
| Parse and save an existing recipe's ingredients | `src/mealie/reparse.py`, `src/tools/reparse_tools.py` |
| Browser links in recipe responses | `src/tools/recipe_links.py` middleware |

An empty string clears a label through `update_food` or
`update_shopping_list_item`. To parse one ingredient, pass a one-element list to
`parse_ingredients`. Recipe responses with a slug include `recipeUrl`;
non-recipe resources are left unchanged. Reparsing patches only ingredients,
preserving unrelated fields, ingredient reference IDs, and section titles.

Streamable HTTP uses `MCP_TRANSPORT=streamable-http` and defaults to port `8765`
and path `/mcp`. Optional settings are `MCP_HTTP_PATH`, `MCP_STATELESS_HTTP`, and
`MCP_JSON_RESPONSE`. Mealie credentials are required at startup. Importing the
server for discovery needs no credentials or network connection.

From a clean working tree, update with:

```sh
git fetch upstream
git rebase upstream/main
uv sync --locked --extra dev
uv run ruff check src tests
uv run pytest -q
```

Preserve the standalone `fastmcp` dependency/imports when resolving conflicts.
Keep extensions in their own modules where possible. Run HTTP protocol tests in
`tests/test_server.py` after any server or dependency changes. The privacy checks
also cover FastMCP's argument-validation logs.

Rebasing published commits changes their IDs. Before updating the GitHub fork,
fetch `origin`, inspect any new remote changes, and push with
`--force-with-lease` only when the rewrite is intentional.
