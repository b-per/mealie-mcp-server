import importlib
import sys
from unittest.mock import Mock

import mealie


class _FakeMealieFetcher:
    def __init__(self, base_url, api_key):
        self.base_url = base_url

    def close(self):
        pass


def test_main_runs_streamable_http_when_configured(monkeypatch):
    monkeypatch.setattr(mealie, "MealieFetcher", _FakeMealieFetcher)
    monkeypatch.setenv("MEALIE_BASE_URL", "https://mealie.example")
    monkeypatch.setenv("MEALIE_API_KEY", "test-key")
    monkeypatch.setenv("MCP_TRANSPORT", "streamable-http")
    monkeypatch.setenv("MCP_HOST", "0.0.0.0")
    monkeypatch.setenv("MCP_PORT", "9001")
    monkeypatch.setenv("MCP_HTTP_PATH", "/recipes-mcp")
    sys.modules.pop("server", None)

    server_module = importlib.import_module("server")
    server_module.mcp.run = Mock()
    server_module.main()

    server_module.mcp.run.assert_called_once_with(transport="streamable-http")
    assert server_module.mcp.settings.host == "0.0.0.0"
    assert server_module.mcp.settings.port == 9001
    assert server_module.mcp.settings.streamable_http_path == "/recipes-mcp"
