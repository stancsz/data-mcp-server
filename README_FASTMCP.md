Data MCP Server — FastMCP scaffold
=================================

Project name: data-mcp
- This repository is a minimal scaffold for a FastMCP-based MCP server named "Data MCP Server".
- The server exposes tools that provide data-platform capabilities: retrieving & analyzing data, generating SQL files, scaffolding and running data pipelines (Airflow), producing ML notebooks, generating and deploying infrastructure, and creating boilerplate data applications that you can modify, develop, and test.

Key capabilities (intended)
- Data retrieval and analysis: connectors and tools that fetch data from sources and run exploratory analyses.
- SQL generation: create parameterized SQL files or queries programmatically from prompts or structured inputs.
- Data pipeline generation & orchestration: produce pipeline DAGs (e.g., Airflow), helper scripts, and deployment artifacts.
- ML notebook generation: create Jupyter/Colab notebooks with model training, evaluation, and data exploration code.
- Infrastructure generation & deployment: generate IaC (Terraform/CloudFormation) or deployment scripts and optionally invoke deployment workflows.
- Boilerplate data applications: scaffold a data app (APIs, ETL, ingestion jobs) and provide tools to iterate and test them.

What this repo contains
- Minimal FastMCP server scaffold: `my_server.py` (registers sample tools: `greet`, `add`)
- Example async client: `my_client.py` (calls the example tools over HTTP)
- Basic pyproject for packaging: `pyproject.toml`
- This workspace may contain a local FastMCP checkout at `~/fastmcp-main` — useful for development.

Quick start (recommended)
1. Create and activate a virtual environment
   - Windows (PowerShell):
       python -m venv .venv
       .\\.venv\\Scripts\\Activate.ps1
   - Windows (cmd):
       python -m venv .venv
       .\\.venv\\Scripts\\activate.bat
   - macOS / Linux:
       python -m venv .venv
       source .venv/bin/activate

2. Install FastMCP and client deps
   - From PyPI (recommended):
       .venv\Scripts\python -m pip install --upgrade pip
       .venv\Scripts\python -m pip install fastmcp httpx
   - Or use a local checkout (dev):
       pip install -e "/path/to/fastmcp-main"

3. Run the example server
   - HTTP transport (port 8000):
       .venv\Scripts\python my_server.py --transport http --port 8000
     Server URL: http://127.0.0.1:8000/mcp
   - stdio transport (for CLI-driven clients):
       .venv\Scripts\python my_server.py

4. Call the server (example client)
   - In a separate shell:
       .venv\Scripts\python my_client.py http://localhost:8000/mcp

How to extend for data-platform features
- Add tools to `my_server.py` (or import modules) and register them with `@mcp.tool`.
- Example tool ideas:
  - `@mcp.tool def fetch_table(conn_str: str, table: str) -> dict: ...`
  - `@mcp.tool def generate_sql(prompt: str, db_type: str = "postgres") -> str: ...`
  - `@mcp.tool def scaffold_airflow_dag(spec: dict) -> str: ...` (returns DAG file text + install instructions)
  - `@mcp.tool def create_notebook(spec: dict) -> bytes: ...` (returns notebook content)
  - `@mcp.tool def deploy_infra(spec: dict) -> dict: ...` (returns deployment plan or status)
- Use the FastMCP docs in `~/fastmcp-main/docs/` for middleware, authentication, HTTP options, and advanced tooling.

Security notes
- When adding tools that can execute or deploy code, ensure you add authentication and proper authorization (see `~/fastmcp-main/docs/python-sdk/fastmcp-server-auth-*.mdx`).
- Validate and sanitize user input to avoid injecting into shell/SQL executions.

Next recommended steps (I can do these for you)
- Add data-platform example tools (SQL generator, DAG scaffold, notebook generator).
- Add unit tests for new tools.
- Add an example pipeline that demonstrates end-to-end: generate SQL -> run query -> produce notebook.
- Add automation scripts (justfile / Makefile) to create venv, install deps, and run the server.
- Configure pre-commit and CI using the pre-commit config in the fastmcp source (if desired).

Current status
- Example server file (`my_server.py`) and client (`my_client.py`) are created.
- Virtual environment `.venv` created and `fastmcp`, `httpx` installed.
- Server can be started with the commands above; optionally I can start/stop and verify endpoints for you.

Contact me with which specific data-platform tools you'd like implemented first (e.g., SQL generator, Airflow DAG scaffolder, notebook generator) and I will add working tool implementations and tests.
