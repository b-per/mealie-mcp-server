import os
from dataclasses import dataclass
from typing import Literal, Mapping, cast

Transport = Literal["stdio", "sse", "streamable-http"]


def _as_bool(value: str, name: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


@dataclass(frozen=True)
class ServerSettings:
    transport: Transport
    host: str
    port: int
    streamable_http_path: str
    stateless_http: bool
    json_response: bool


def load_server_settings(
    environ: Mapping[str, str] | None = None,
) -> ServerSettings:
    """Load MCP transport settings while preserving stdio compatibility."""
    env = os.environ if environ is None else environ
    transport_value = env.get("MCP_TRANSPORT", "stdio").strip().lower()
    valid_transports = {"stdio", "sse", "streamable-http"}
    if transport_value not in valid_transports:
        raise ValueError(
            "MCP_TRANSPORT must be one of stdio, sse, or streamable-http"
        )

    port_value = env.get("MCP_PORT", env.get("PORT", "8000"))
    try:
        port = int(port_value)
    except ValueError as exc:
        raise ValueError("MCP_PORT (or PORT) must be an integer") from exc
    if not 1 <= port <= 65535:
        raise ValueError("MCP_PORT (or PORT) must be between 1 and 65535")

    path = env.get("MCP_HTTP_PATH", "/mcp").strip()
    if not path.startswith("/"):
        path = f"/{path}"

    return ServerSettings(
        transport=cast(Transport, transport_value),
        host=env.get("MCP_HOST", env.get("HOST", "127.0.0.1")),
        port=port,
        streamable_http_path=path,
        stateless_http=_as_bool(env.get("MCP_STATELESS_HTTP", "false"), "MCP_STATELESS_HTTP"),
        json_response=_as_bool(env.get("MCP_JSON_RESPONSE", "false"), "MCP_JSON_RESPONSE"),
    )
