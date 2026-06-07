FROM ghcr.io/astral-sh/uv:python3.13-bookworm-slim

ENV UV_TOOL_BIN_DIR=/usr/local/bin

RUN uv tool install mcp-server-time

ENTRYPOINT ["mcp-server-time"]
