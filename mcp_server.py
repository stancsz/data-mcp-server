"""
DataMCP FastMCP server — entrypoint with AWS S3 and Dynamo integrations.

Usage:
- Ensure dependencies are installed (boto3, python-dotenv, fastmcp, httpx).
- Configure AWS credentials via environment variables or profile, or put a .env at repo root.
- Run the server (HTTP transport on port 8000):
    python mcp_server.py --transport http --port 8000

Tools provided:
- say_hello(name: str) -> str
- add_numbers(a: float, b: float) -> float
- s3_generate_presigned_put(bucket, key, expires_in) -> str
- s3_generate_presigned_get(bucket, key, expires_in) -> str
- s3_list_objects(prefix=None, bucket=None) -> list
- s3_delete_object(key, bucket=None) -> dict
- dynamo_put_item(table, item) -> dict
- dynamo_get_item(table, key) -> dict | None
- dynamo_delete_item(table, key) -> dict
- dynamo_query(table, key_name, key_value, limit=None) -> list
"""

from __future__ import annotations
import argparse
import logging
import shlex
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP

from config import aws_credentials_dict
from aws.s3_client import S3Client
from aws.dynamo_client import DynamoClient
from boto3.dynamodb.conditions import Key  # type: ignore
from tools.runner import run_cmd, CommandResult

LOG = logging.getLogger(__name__)

mcp = FastMCP("DataMCP — FastMCP Server (AWS Integrations)")

# initialize clients lazily (use defaults from config if available)
_s3_client: Optional[S3Client] = None
_dynamo_client: Optional[DynamoClient] = None


def get_s3(bucket: Optional[str] = None) -> S3Client:
    global _s3_client
    if _s3_client is None:
        # credentials handled inside S3Client via config.aws_credentials_dict()
        _s3_client = S3Client(bucket=bucket)
    return _s3_client


def get_dynamo(table: Optional[str] = None) -> DynamoClient:
    global _dynamo_client
    if _dynamo_client is None:
        _dynamo_client = DynamoClient(table_name=table)
    return _dynamo_client


#
# Basic example tools
#
@mcp.tool
def say_hello(name: str) -> str:
    """Return a simple greeting."""
    return f"Hello, {name}!"


@mcp.tool
def add_numbers(a: float, b: float) -> float:
    """Return the sum of two numbers."""
    return a + b


#
# S3 tools
#
@mcp.tool
def s3_generate_presigned_put(key: str, bucket: Optional[str] = None, expires_in: int = 3600) -> str:
    """
    Generate a presigned PUT URL so a client can upload directly to S3.
    Returns the presigned URL string.
    """
    s3 = get_s3(bucket=bucket)
    return s3.generate_presigned_url(key=key, bucket=bucket, expires_in=expires_in, http_method="PUT")


@mcp.tool
def s3_generate_presigned_get(key: str, bucket: Optional[str] = None, expires_in: int = 3600) -> str:
    """
    Generate a presigned GET URL for downloading an object.
    """
    s3 = get_s3(bucket=bucket)
    return s3.generate_presigned_url(key=key, bucket=bucket, expires_in=expires_in, http_method="GET")


@mcp.tool
def s3_list_objects(prefix: Optional[str] = None, bucket: Optional[str] = None, max_keys: int = 1000) -> List[Dict[str, Any]]:
    """
    List objects in the target bucket under the given prefix.
    Returns list of object metadata dicts.
    """
    s3 = get_s3(bucket=bucket)
    return s3.list_objects(prefix=prefix, bucket=bucket, max_keys=max_keys)


@mcp.tool
def s3_delete_object(key: str, bucket: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete an object from S3. Returns the delete_object response dict.
    """
    s3 = get_s3(bucket=bucket)
    return s3.delete_object(key=key, bucket=bucket)


#
# DynamoDB tools
#
@mcp.tool
def dynamo_put_item(item: Dict[str, Any], table: Optional[str] = None) -> Dict[str, Any]:
    """
    Put an item into a DynamoDB table. 'item' must be a JSON-serializable dict.
    """
    dyn = get_dynamo(table=table)
    return dyn.put_item(item=item, table_name=table)


@mcp.tool
def dynamo_get_item(key: Dict[str, Any], table: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """
    Get an item from DynamoDB by primary key dict (e.g. {'pk': 'value', 'sk': 'value'}).
    """
    dyn = get_dynamo(table=table)
    return dyn.get_item(key=key, table_name=table)


@mcp.tool
def dynamo_delete_item(key: Dict[str, Any], table: Optional[str] = None) -> Dict[str, Any]:
    """
    Delete an item by primary key. Returns the delete response.
    """
    dyn = get_dynamo(table=table)
    return dyn.delete_item(key=key, table_name=table)


@mcp.tool
def dynamo_query(table: str, key_name: str, key_value: Any, limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Simple helper to query a table by equality on a partition key.
    Returns list of matching items.
    """
    dyn = get_dynamo(table=table)
    key_expr = Key(key_name).eq(key_value)
    return dyn.query(key_condition=key_expr, table_name=table, limit=limit)


def parse_args():
    parser = argparse.ArgumentParser(description="Run the DataMCP FastMCP server.")
    parser.add_argument("--transport", default=None, help="Transport to use (e.g. http, stdio).")
    parser.add_argument("--port", type=int, default=None, help="Port for HTTP transport.")
    return parser.parse_args()


@mcp.tool
def apply_terraform(cloud: str, env: str, workspace: Optional[str] = None, vars: Optional[Dict[str, Any]] = None, dry_run: bool = True, auto_approve: bool = False) -> Dict[str, Any]:
    """
    MCP tool skeleton to run terraform operations for a given cloud and environment.
    This function runs in dry_run mode by default. It locates infra/{cloud}/envs/{env}
    and runs terraform init/plan (and apply if auto_approve is True).
    Returns a structured dict with command outputs and status.
    """
    # locate directory
    tf_dir = f"infra/{cloud}/envs/{env}"
    if vars:
        # For a real implementation, write vars to a temporary tfvars file and pass via -var-file
        var_args = " ".join(f"-var '{k}={v}'" for k, v in (vars or {}).items())
    else:
        var_args = ""

    init_cmd = ["terraform", "init", "-input=false"]
    plan_cmd = ["terraform", "plan", "-input=false", "-no-color"] + (shlex.split(var_args) if var_args else [])
    result_init = run_cmd(init_cmd, cwd=tf_dir, dry_run=dry_run)
    result_plan = run_cmd(plan_cmd, cwd=tf_dir, dry_run=dry_run)

    apply_result = None
    if auto_approve:
        apply_cmd = ["terraform", "apply", "-auto-approve", "-input=false"] + (shlex.split(var_args) if var_args else [])
        apply_result = run_cmd(apply_cmd, cwd=tf_dir, dry_run=dry_run)

    return {
        "init": {"rc": result_init.returncode, "stdout": result_init.stdout, "stderr": result_init.stderr},
        "plan": {"rc": result_plan.returncode, "stdout": result_plan.stdout, "stderr": result_plan.stderr},
        "apply": ({"rc": apply_result.returncode, "stdout": apply_result.stdout, "stderr": apply_result.stderr} if apply_result else None),
        "succeeded": (result_init.returncode == 0 and result_plan.returncode == 0 and (apply_result.returncode == 0 if apply_result else True))
    }


@mcp.tool
def destroy_terraform(cloud: str, env: str, dry_run: bool = True, auto_approve: bool = False) -> Dict[str, Any]:
    """
    MCP tool skeleton to destroy terraform-managed infra.
    """
    tf_dir = f"infra/{cloud}/envs/{env}"
    plan_cmd = ["terraform", "plan", "-destroy", "-input=false", "-no-color"]
    result_plan = run_cmd(plan_cmd, cwd=tf_dir, dry_run=dry_run)
    destroy_result = None
    if auto_approve:
        destroy_cmd = ["terraform", "destroy", "-auto-approve", "-input=false"]
        destroy_result = run_cmd(destroy_cmd, cwd=tf_dir, dry_run=dry_run)
    return {
        "plan": {"rc": result_plan.returncode, "stdout": result_plan.stdout, "stderr": result_plan.stderr},
        "destroy": ({"rc": destroy_result.returncode, "stdout": destroy_result.stdout, "stderr": destroy_result.stderr} if destroy_result else None),
        "succeeded": (result_plan.returncode == 0 and (destroy_result.returncode == 0 if destroy_result else True))
    }


@mcp.tool
def helm_deploy(kube_context: Optional[str], chart_path: str, release_name: str, namespace: str, values: Optional[Dict[str, Any]] = None, dry_run: bool = True) -> Dict[str, Any]:
    """
    MCP tool skeleton to install/upgrade a Helm chart.
    """
    kube_ctx_args = ["--kube-context", kube_context] if kube_context else []
    values_args = []
    if values:
        # In a production implementation we'd write values to a temp file and pass -f <file>
        for k, v in (values or {}).items():
            values_args += ["--set", f"{k}={v}"]

    cmd = ["helm", "upgrade", "--install", release_name, chart_path, "--namespace", namespace, "--create-namespace"] + kube_ctx_args + values_args
    result = run_cmd(cmd, dry_run=dry_run)
    return {"rc": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "succeeded": result.returncode == 0}


@mcp.tool
def argo_sync(app_name: str, argocd_ctx: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
    """
    MCP tool skeleton to sync an ArgoCD application by name using the argocd CLI.
    """
    ctx_args = ["--grpc-web", "--server", argocd_ctx] if argocd_ctx else []
    cmd = ["argocd", "app", "sync", app_name] + ctx_args
    result = run_cmd(cmd, dry_run=dry_run)
    return {"rc": result.returncode, "stdout": result.stdout, "stderr": result.stderr, "succeeded": result.returncode == 0}


@mcp.tool
def gcp_create_project(project_id: str, billing_account: str, org_id: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
    """
    MCP tool skeleton to create a GCP project using gcloud CLI. Requires organization permissions.
    """
    cmd = ["gcloud", "projects", "create", project_id, "--name", project_id]
    if org_id:
        cmd += ["--organization", org_id]
    # billing
    billing_cmd = ["gcloud", "beta", "billing", "projects", "link", project_id, "--billing-account", billing_account]
    create_result = run_cmd(cmd, dry_run=dry_run)
    billing_result = run_cmd(billing_cmd, dry_run=dry_run)
    return {
        "create": {"rc": create_result.returncode, "stdout": create_result.stdout, "stderr": create_result.stderr},
        "billing": {"rc": billing_result.returncode, "stdout": billing_result.stdout, "stderr": billing_result.stderr},
        "succeeded": create_result.returncode == 0 and billing_result.returncode == 0
    }


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
