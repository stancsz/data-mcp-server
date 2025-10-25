#!/usr/bin/env python3
"""
tools/run_local.py

Simple helper to run the MCP server locally with optional environment overrides.
Usage:
    python tools/run_local.py --env-file .env.dev
"""

import argparse
import os
import subprocess
from pathlib import Path

def load_env_file(path: Path):
    if not path.exists():
        return
    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--env-file", type=str, default=".env", help="Path to env file")
    parser.add_argument("--python", type=str, default="python", help="Python executable")
    args = parser.parse_args()

    env_path = Path(args.env_file)
    load_env_file(env_path)

    # Run the MCP server module in a subprocess forwarding env
    cmd = [args.python, "mcp_server.py"]
    print("Running:", " ".join(cmd))
    subprocess.run(cmd, check=True, env=os.environ.copy())

if __name__ == "__main__":
    main()
