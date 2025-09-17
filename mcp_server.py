"""
MCP server (professional name) — entrypoint for the FastMCP server.

Usage:
- Create a virtualenv: python -m venv .venv
- Activate it:
    Windows (PowerShell): .venv\\Scripts\\Activate.ps1
    Windows (cmd): .venv\\Scripts\\activate.bat
    macOS / Linux: source .venv/bin/activate
- Install dependencies (will add boto3 later):
    pip install fastmcp httpx
- Run the server (stdio transport):
    python mcp_server.py
- Run the server (HTTP transport on port 8000):
    python mcp_server.py --transport http --port 8000
  or via FastMCP CLI (if available):
    fastmcp run mcp_server.py:mcp --transport http --port 8000

This file replaces the previous `my_server.py`. Tools exposed by this MCP server:
- say_hello(name: str) -> str
- add_numbers(a: float, b: float) -> float
"""

from fastmcp import FastMCP
import argparse

# Create the FastMCP instance with a clear, professional name
mcp = FastMCP("DataMCP — FastMCP Server")

@mcp.tool
def say_hello(name: str) -> str:
    """Return a simple greeting."""
    return f"Hello, {name}!"

@mcp.tool
def add_numbers(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b

def parse_args():
    parser = argparse.ArgumentParser(description="Run the DataMCP FastMCP server.")
    parser.add_argument("--transport", default=None, help="Transport to use (e.g. http, stdio).")
    parser.add_argument("--port", type=int, default=None, help="Port for HTTP transport.")
    return parser.parse_args()

def run():
    args = parse_args()
    run_kwargs = {}
    if args.transport:
        run_kwargs["transport"] = args.transport
    if args.port:
        run_kwargs["port"] = args.port
    mcp.run(**run_kwargs)

if __name__ == "__main__":
    run()
