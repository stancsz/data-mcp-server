"""
Minimal FastMCP server scaffold for this repository.

Usage:
- Create a virtualenv: python -m venv .venv
- Activate it:
    Windows (PowerShell): .venv\\Scripts\\Activate.ps1
    Windows (cmd): .venv\\Scripts\\activate.bat
    macOS / Linux: source .venv/bin/activate
- Install FastMCP:
    - If you want to use the local copy included in this environment:
        pip install -e "~\\fastmcp-main"
      (Adjust the path if your fastmcp-main directory is elsewhere.)
    - Or install from PyPI (if available):
        pip install fastmcp
- Run the server (stdio transport):
    python my_server.py
- Run the server (HTTP transport on port 8000):
    python my_server.py --transport http --port 8000
  or use the FastMCP CLI:
    fastmcp run my_server.py:mcp --transport http --port 8000

This file creates a single tool `greet` as an example. Add more tools by decorating functions with @mcp.tool.
"""

from fastmcp import FastMCP
import argparse

mcp = FastMCP("Data MCP Server")

@mcp.tool
def greet(name: str) -> str:
    """Simple example tool that returns a greeting."""
    return f"Hello, {name}!"

@mcp.tool
def add(a: float, b: float) -> float:
    """Example numeric tool (demonstrates typing)."""
    return a + b

def parse_args():
    parser = argparse.ArgumentParser(description="Run the FastMCP server.")
    parser.add_argument("--transport", default=None, help="Transport to use (e.g. http, stdio).")
    parser.add_argument("--port", type=int, default=None, help="Port for HTTP transport.")
    return parser.parse_args()

if __name__ == "__main__":
    args = parse_args()
    # If user passed explicit transport/port, forward them to mcp.run
    run_kwargs = {}
    if args.transport:
        run_kwargs["transport"] = args.transport
    if args.port:
        run_kwargs["port"] = args.port
    mcp.run(**run_kwargs)
