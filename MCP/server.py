"""
TestHelper MCP 服务 — 主入口。

通过 stdio 与 AI 助手通信，提供识图、浏览器控制等工具。
新增工具模块无需修改本文件，只需在 tools/__init__.py 中注册。

启动方式：
    python server.py
"""

import sys
import os

# 确保 MCP 目录在 sys.path 中，方便工具模块 import config
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mcp.server import Server, InitializationOptions
from mcp.server.stdio import stdio_server
from mcp.types import ServerCapabilities, ToolsCapability

from tools import get_all_tools, handle_tool

# ==================== 创建 MCP Server ====================

server = Server("testhelper-mcp")

# ==================== 工具注册 ====================


@server.list_tools()
async def list_tools() -> list:
    """返回所有注册的工具定义"""
    return get_all_tools()


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list:
    """分发工具调用到对应模块"""
    return await handle_tool(name, arguments)

# ==================== 启动 ====================


async def main():
    capabilities = ServerCapabilities(
        tools=ToolsCapability(listChanged=False),
    )
    init_options = InitializationOptions(
        server_name="testhelper-mcp",
        server_version="1.0.0",
        capabilities=capabilities,
    )
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, init_options)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
