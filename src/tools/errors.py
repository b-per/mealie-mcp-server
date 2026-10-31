"""Safe error translation shared by explicitly registered MCP tools."""

import logging
from collections.abc import Iterator
from contextlib import contextmanager

import httpx
from fastmcp.exceptions import ToolError, ValidationError as ArgumentValidationError
from fastmcp.server.middleware import Middleware
from pydantic import ValidationError

from mealie.client import MealieApiError

logger = logging.getLogger("mealie-mcp")


class _SafeFrameworkLog(logging.Filter):
    """FastMCP's default validation/exception logs can contain private inputs."""

    def filter(self, record: logging.LogRecord) -> bool:
        error_type = record.exc_info[0].__name__ if record.exc_info else "MCPEvent"
        record.msg = {"operation": "Handling MCP request", "error_type": error_type}
        record.args = ()
        record.exc_info = record.exc_text = record.stack_info = None
        return True


class SafeToolErrors(Middleware):
    """Keep framework argument validation as private as in-tool validation."""

    def __init__(self):
        framework_logger = logging.getLogger("fastmcp.server.server")
        if not any(isinstance(f, _SafeFrameworkLog) for f in framework_logger.filters):
            framework_logger.addFilter(_SafeFrameworkLog())

    async def on_call_tool(self, context, call_next):
        try:
            return await call_next(context)
        except ArgumentValidationError as error:
            cause = error.__cause__
            kinds = sorted({
                item["type"] for item in cause.errors(
                    include_input=False, include_context=False, include_url=False
                )
            }) if isinstance(cause, ValidationError) else []
            detail = f" ({', '.join(kinds)})" if kinds else ""
            raise ToolError(f"Invalid input{detail}") from None


@contextmanager
def tool_error_boundary(operation: str) -> Iterator[None]:
    """Translate expected failures without logging exception text or tool input.

    ``operation`` must be a fixed description, never formatted with user data.
    Explicit ToolError messages, including partial-progress recovery, pass through.
    """
    try:
        yield
    except ToolError:
        raise
    except (
        MealieApiError,
        httpx.HTTPError,
        TimeoutError,
        ConnectionError,
        ValueError,
        FileNotFoundError,
        PermissionError,
        IsADirectoryError,
        NotADirectoryError,
    ) as error:
        metadata = {"operation": operation, "error_type": type(error).__name__}
        if isinstance(error, MealieApiError):
            metadata["status_code"] = error.status_code
            detail = f"Mealie API request failed (HTTP {error.status_code})"
        elif isinstance(error, httpx.HTTPStatusError):
            metadata["status_code"] = error.response.status_code
            detail = f"Mealie API request failed (HTTP {error.response.status_code})"
        elif isinstance(error, (TimeoutError, httpx.TimeoutException)):
            detail = "Mealie API request timed out"
        elif isinstance(error, (ConnectionError, httpx.RequestError)):
            detail = "Could not communicate with the Mealie API"
        elif isinstance(error, ValidationError):
            # Custom validator messages can embed input even when include_input=False.
            kinds = sorted({
                item["type"]
                for item in error.errors(
                    include_input=False, include_context=False, include_url=False
                )
            })
            detail = f"Invalid input ({', '.join(kinds)})"
        elif isinstance(error, ValueError):
            detail = str(error)
        else:
            detail = "Could not access the requested file"
        logger.error(metadata)
        raise ToolError(f"{operation}: {detail}") from None
