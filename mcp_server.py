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
from typing import Optional, Dict, Any, List

from fastmcp import FastMCP

from config import aws_credentials_dict
from aws.s3_client import S3Client
from aws.dynamo_client import DynamoClient
from boto3.dynamodb.conditions import Key  # type: ignore

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
