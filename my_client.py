"""
Example FastMCP client to call the example tools in my_server.py.

Usage:
1. Start the server (HTTP transport):
    python my_server.py --transport http --port 8000
   or (stdio transport - advanced/for CLI-based clients)
    python my_server.py

2. Run this client (for HTTP server):
    python my_client.py http://localhost:8000/mcp

If you run the server via the FastMCP CLI that imports the `mcp` object, the entrypoint would be:
    fastmcp run my_server.py:mcp --transport http --port 8000
"""

import sys
import asyncio
from fastmcp import Client


async def call_tools(base_url: str):
    # Create a client that points at the HTTP MCP endpoint
    client = Client(base_url)
    async with client:
        # call greeting tool
        greet_res = await client.call_tool("greet", {"name": "Alice"})
        print("greet ->", greet_res)

        # call add tool
        add_res = await client.call_tool("add", {"a": 2.5, "b": 4.0})
        print("add ->", add_res)


def main():
    if len(sys.argv) < 2:
        print("Usage: python my_client.py <mcp_base_url>")
        print("Example: python my_client.py http://localhost:8000/mcp")
        sys.exit(1)

    base_url = sys.argv[1]
    asyncio.run(call_tools(base_url))


if __name__ == "__main__":
    main()
