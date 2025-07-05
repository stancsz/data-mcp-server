import pytest
import subprocess
import sys
import time
import requests
from coding_agent import mcp

PLAYWRIGHT_MCP_PORT = 8931
PLAYWRIGHT_MCP_URL = f"http://localhost:{PLAYWRIGHT_MCP_PORT}"

@pytest.fixture(scope="module", autouse=True)
def playwright_mcp_server():
    # Start the Playwright MCP server
    proc = subprocess.Popen(
        [
            "npx",
            "@playwright/mcp@latest",
            "--port",
            str(PLAYWRIGHT_MCP_PORT)
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=(sys.platform == "win32")
    )
    # Wait for the server to be ready
    for _ in range(30):
        try:
            r = requests.get(f"{PLAYWRIGHT_MCP_URL}/health")
            if r.status_code == 200:
                break
        except Exception:
            pass
        time.sleep(1)
    else:
        proc.terminate()
        raise RuntimeError("Playwright MCP server did not start in time")

    yield

    # Teardown: terminate the server
    proc.terminate()
    try:
        proc.wait(timeout=10)
    except Exception:
        proc.kill()

def test_playwright_mcp_basic():
    """
    Test the playwright-mcp server by running a simple Playwright script via MCP.
    This requires the playwright-mcp server to be running at the configured endpoint.
    """
    servers = mcp.load_mcp_config()
    assert "playwright" in servers, "playwright server not found in MCP config"
    playwright_server = servers["playwright"]

    # Example: script to open example.com and return the page title
    script = '''
const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.goto('https://example.com');
  const title = await page.title();
  await browser.close();
  return { title };
})();
    '''.strip()

    # Call the tool
    result = playwright_server.call_tool("run_playwright_script", {"script": script})

    # Check result structure and content
    assert isinstance(result, dict), "Result should be a dict"
    assert "title" in result or "result" in result, "Expected 'title' or 'result' in response"
    # Accept either direct title or nested result
    if "title" in result:
        assert "Example Domain" in result["title"]
    elif "result" in result and isinstance(result["result"], dict):
        assert "Example Domain" in result["result"].get("title", "")
