import pytest

from settings import load_server_settings


def test_stdio_is_default():
    settings = load_server_settings({})
    assert settings.transport == "stdio"
    assert settings.host == "127.0.0.1"
    assert settings.port == 8000


def test_streamable_http_settings():
    settings = load_server_settings(
        {
            "MCP_TRANSPORT": "streamable-http",
            "MCP_HOST": "0.0.0.0",
            "MCP_PORT": "9001",
            "MCP_HTTP_PATH": "mealie",
            "MCP_STATELESS_HTTP": "true",
        }
    )
    assert settings.transport == "streamable-http"
    assert settings.host == "0.0.0.0"
    assert settings.port == 9001
    assert settings.streamable_http_path == "/mealie"
    assert settings.stateless_http is True


def test_invalid_transport_is_rejected():
    with pytest.raises(ValueError, match="MCP_TRANSPORT"):
        load_server_settings({"MCP_TRANSPORT": "http"})
