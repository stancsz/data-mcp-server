import json
import requests
import os

class MCPServer:
    def __init__(self, name, config):
        self.name = name
        self.config = config
        self.endpoint = config.get("url")
        self.command = config.get("command")
        self.args = config.get("args", [])
        # For direct HTTP servers, endpoint is required
        # For command-based servers, endpoint may be set after launch (not handled here)

    def call_tool(self, tool_name, params):
        if not self.endpoint:
            raise ValueError(f"Server '{self.name}' does not have a 'url' endpoint configured.")
        url = f"{self.endpoint}/tools/{tool_name}"
        response = requests.post(url, json=params)
        response.raise_for_status()
        return response.json()

    # Optionally, implement resource access if needed
    def get_resource(self, resource_name):
        if not self.endpoint:
            raise ValueError(f"Server '{self.name}' does not have a 'url' endpoint configured.")
        url = f"{self.endpoint}/resources/{resource_name}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

def load_mcp_config(config_path=".vscode/settings.json"):
    """
    Loads MCP server configurations from the standard MCP config location.
    Expects a JSON file with an 'mcpServers' key.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Could not find MCP config file: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    mcp_servers = data.get("mcpServers", {})
    servers = {}
    for name, config in mcp_servers.items():
        servers[name] = MCPServer(name, config)
    return servers

# Example usage:
# mcp_servers = load_mcp_config()
# result = mcp_servers["playwright"].call_tool("browser_navigate", {"url": "https://example.com"})
