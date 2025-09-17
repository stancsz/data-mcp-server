"""
Redshift Data API client for DataMCP

Purpose:
- Focused wrapper for the Redshift Data API (service name 'redshift-data').
- Provide execute_statement and get_statement_result helpers suitable for MCP tools and AI.
- Keep behavior explicit and documented so the AI can call the tool directly.

Usage:
    from aws.redshift_data_client import RedshiftDataClient
    r = RedshiftDataClient(cluster_identifier="my-cluster", database="dev", db_user="admin")
    resp = r.execute_statement("SELECT count(*) FROM table")
    results = r.get_statement_result(resp["Id"])

Design notes:
- This wrapper uses the Redshift Data API and is intended for interacting with Redshift Serverless or provisioned clusters via the Data API.
- Methods return boto3 response dicts and raise on botocore errors.
- Caller should handle pagination and result parsing as needed and log/audit the actions.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any

import boto3
import botocore

from config import aws_credentials_dict

LOG = logging.getLogger(__name__)


def _client(**kwargs: Any):
    creds = aws_credentials_dict()
    init_kwargs = {**creds, **(kwargs or {})}
    return boto3.client("redshift-data", **{k: v for k, v in init_kwargs.items() if v is not None})


class RedshiftDataClient:
    """
    Wrapper around AWS Redshift Data API.

    Methods:
    - execute_statement(sql: str, cluster_identifier: Optional[str] = None, database: Optional[str] = None, db_user: Optional[str] = None, with_event: bool = False) -> Dict[str, Any]
      Execute SQL and return the execute_statement response dict (contains an Id).

    - get_statement_result(id: str, max_results: int = 1000) -> Dict[str, Any]
      Retrieve the results for a previously executed statement.
    """

    def __init__(self, cluster_identifier: Optional[str] = None, database: Optional[str] = None, db_user: Optional[str] = None, **client_kwargs: Any):
        self.client = _client(**client_kwargs)
        self.cluster_identifier = cluster_identifier
        self.database = database
        self.db_user = db_user

    def execute_statement(
        self,
        sql: str,
        cluster_identifier: Optional[str] = None,
        database: Optional[str] = None,
        db_user: Optional[str] = None,
        with_event: bool = False,
    ) -> Dict[str, Any]:
        """
        Execute a SQL statement via Redshift Data API.

        Returns:
            boto3 response dict from execute_statement which includes an 'Id'.
        """
        try:
            params: Dict[str, Any] = {"Sql": sql}
            if cluster_identifier or self.cluster_identifier:
                params["ClusterIdentifier"] = cluster_identifier or self.cluster_identifier
            if database or self.database:
                params["Database"] = database or self.database
            if db_user or self.db_user:
                params["DbUser"] = db_user or self.db_user
            if with_event:
                params["WithEvent"] = True
            return self.client.execute_statement(**params)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Redshift Data execute_statement failed")
            raise

    def get_statement_result(self, id: str, max_results: int = 1000) -> Dict[str, Any]:
        """
        Retrieve results for a statement execution.

        Returns:
            boto3 response dict containing 'Records' and metadata.
        """
        try:
            return self.client.get_statement_result(Id=id, MaxResults=max_results)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Redshift Data get_statement_result failed")
            raise
