import asyncio
import json
import logging
from pathlib import Path

from collections.abc import Iterable
from typing import Any

from langchain_core.tools import BaseTool, StructuredTool

BASE_DIR = Path(__file__).resolve().parents[1]
MCP_CONFIG_FILE = BASE_DIR / "config" / "mcp.json"

logger = logging.getLogger(__name__)


def load_mcp_tools() -> list[BaseTool]:
    config = _load_config()
    if not config:
        return []
    return asyncio.run(_load_mcp_tools(config))


async def _load_mcp_tools(config: dict) -> list[BaseTool]:
    try:
        from langchain_mcp_adapters.client import MultiServerMCPClient
    except ImportError:
        logger.exception("langchain_mcp_adapters_not_installed")
        return []

    try:
        client = MultiServerMCPClient(config, tool_name_prefix=True)
        tools = await client.get_tools()
        return [_make_sync_compatible_tool(tool, mcp_server_names=config.keys()) for tool in tools]
    except Exception:
        logger.exception("mcp_tools_load_failed")
        return []


def _load_config() -> dict:
    if not MCP_CONFIG_FILE.exists():
        return {}

    try:
        raw = json.loads(MCP_CONFIG_FILE.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        logger.exception("mcp_config_invalid_json path=%s", MCP_CONFIG_FILE)
        return {}

    servers = raw.get("servers", {})
    if not isinstance(servers, dict):
        logger.warning("mcp_config_invalid_servers path=%s", MCP_CONFIG_FILE)
        return {}

    enabled_servers = {
        name: _to_langchain_connection(server_config)
        for name, server_config in servers.items()
        if isinstance(name, str)
        and isinstance(server_config, dict)
        and server_config.get("enabled", True)
    }
    return {
        name: config
        for name, config in enabled_servers.items()
        if config is not None
    }


def _to_langchain_connection(server_config: dict) -> dict | None:
    command = server_config.get("command")
    args = server_config.get("args", [])
    transport = server_config.get("transport", "stdio")

    if not isinstance(command, str) or not command:
        return None
    if not isinstance(args, list) or not all(isinstance(arg, str) for arg in args):
        return None
    if not isinstance(transport, str):
        return None

    connection = {
        "transport": transport,
        "command": command,
        "args": args,
    }

    env = server_config.get("env")
    if isinstance(env, dict) and all(isinstance(k, str) and isinstance(v, str) for k, v in env.items()):
        connection["env"] = env

    return connection


def _make_sync_compatible_tool(tool: BaseTool, mcp_server_names: Iterable[str]) -> BaseTool:
    if not isinstance(tool, StructuredTool) or tool.func is not None:
        return tool
    if tool.coroutine is None:
        return tool

    async_call = tool.coroutine
    tool_name = _mcp_tool_name(tool.name, mcp_server_names)

    def sync_call(**kwargs: Any) -> Any:
        return asyncio.run(async_call(**kwargs))

    async def wrapped_async_call(**kwargs: Any) -> Any:
        return await async_call(**kwargs)

    return StructuredTool(
        name=tool_name,
        description=tool.description,
        args_schema=tool.args_schema,
        return_direct=tool.return_direct,
        metadata=tool.metadata,
        response_format=tool.response_format,
        func=sync_call,
        coroutine=wrapped_async_call,
    )


def _mcp_tool_name(tool_name: str, mcp_server_names: Iterable[str]) -> str:
    if tool_name.startswith("mcp_"):
        return tool_name
    for server_name in mcp_server_names:
        prefix = f"{server_name}_"
        if tool_name.startswith(prefix):
            return f"mcp_{tool_name}"
    return f"mcp_{tool_name}"

if __name__ == '__main__':
    print(load_mcp_tools())
