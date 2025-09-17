"""
AWS DynamoDB helper wrappers for DataMCP.

Provides a convenience class around boto3.resource('dynamodb') for simple
put/get/delete/query operations used by the MCP server.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List

import boto3
import botocore
from boto3.dynamodb.conditions import Key, Attr  # type: ignore

from config import aws_credentials_dict, default_dynamo_table

LOG = logging.getLogger(__name__)


class DynamoClient:
    def __init__(self, table_name: Optional[str] = None, **resource_kwargs: Any):
        """
        Initialize the DynamoDB resource and optionally bind to a default table.
        """
        creds = aws_credentials_dict()
        init_kwargs = {**creds, **resource_kwargs}
        self.dynamo = boto3.resource("dynamodb", **{k: v for k, v in init_kwargs.items() if v is not None})
        self.table_name = table_name or default_dynamo_table()
        if not self.table_name:
            LOG.warning("No default DynamoDB table configured (DEFAULT_DYNAMO_TABLE)")

    def table(self, table_name: Optional[str] = None):
        tname = table_name or self.table_name
        if not tname:
            raise ValueError("No DynamoDB table specified")
        return self.dynamo.Table(tname)

    def put_item(self, item: Dict[str, Any], table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Put an item into the specified table. Returns the response dict.
        """
        tbl = self.table(table_name)
        try:
            resp = tbl.put_item(Item=item)
            return resp
        except botocore.exceptions.BotoCoreError:
            LOG.exception("DynamoDB put_item failed")
            raise

    def get_item(self, key: Dict[str, Any], table_name: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """
        Get an item by primary key. Returns the item dict or None if not found.
        """
        tbl = self.table(table_name)
        try:
            resp = tbl.get_item(Key=key)
            return resp.get("Item")
        except botocore.exceptions.BotoCoreError:
            LOG.exception("DynamoDB get_item failed")
            raise

    def delete_item(self, key: Dict[str, Any], table_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete an item by primary key. Returns the response dict.
        """
        tbl = self.table(table_name)
        try:
            resp = tbl.delete_item(Key=key)
            return resp
        except botocore.exceptions.BotoCoreError:
            LOG.exception("DynamoDB delete_item failed")
            raise

    def query(self, key_condition: Any, filter_expression: Optional[Any] = None, table_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Query the table using a Key condition expression. Returns list of items.

        Example key_condition: Key('pk').eq('value')
        Example filter_expression: Attr('status').eq('active')
        """
        tbl = self.table(table_name)
        try:
            kwargs: Dict[str, Any] = {"KeyConditionExpression": key_condition}
            if filter_expression is not None:
                kwargs["FilterExpression"] = filter_expression
            if limit is not None:
                kwargs["Limit"] = limit
            resp = tbl.query(**kwargs)
            return resp.get("Items", [])
        except botocore.exceptions.BotoCoreError:
            LOG.exception("DynamoDB query failed")
            raise

    def scan(self, filter_expression: Optional[Any] = None, table_name: Optional[str] = None, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Perform a scan (use carefully). Returns list of items.
        """
        tbl = self.table(table_name)
        try:
            kwargs: Dict[str, Any] = {}
            if filter_expression is not None:
                kwargs["FilterExpression"] = filter_expression
            if limit is not None:
                kwargs["Limit"] = limit
            resp = tbl.scan(**kwargs)
            return resp.get("Items", [])
        except botocore.exceptions.BotoCoreError:
            LOG.exception("DynamoDB scan failed")
            raise
