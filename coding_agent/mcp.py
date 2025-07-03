import yaml
import requests
import os

class MCPServer:
    def __init__(self, name, endpoint, tools, resources):
        self.name = name
        self.endpoint = endpoint
        self.tools = {tool['name']: tool for tool in tools}
        self.resources = {res['name']: res for res in resources}

    def call_tool(self, tool_name, params):
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found in server '{self.name}'")
        url = f"{self.endpoint}/tools/{tool_name}"
        response = requests.post(url, json=params)
        response.raise_for_status()
        return response.json()

    def get_resource(self, resource_name):
        if resource_name not in self.resources:
            raise ValueError(f"Resource '{resource_name}' not found in server '{self.name}'")
        url = f"{self.endpoint}/resources/{resource_name}"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

def load_mcp_config(config_path="mcp.yml"):
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Could not find MCP config file: {config_path}")
    with open(config_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    servers = {}
    for server in data.get("servers", []):
        name = server["name"]
        endpoint = server["endpoint"]
        tools = server.get("tools", [])
        resources = server.get("resources", [])
        servers[name] = MCPServer(name, endpoint, tools, resources)
    return servers

# Example usage:
# mcp_servers = load_mcp_config()
# result = mcp_servers["example-mcp-server"].call_tool("get_weather", {"city": "Denver"})
