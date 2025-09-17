"""
Athena client wrapper for DataMCP

Purpose:
- Focused wrapper for AWS Athena operations used by MCP tools.
- Provide clear, single-purpose methods: start_query_execution, get_query_status, get_query_results, wait_query.
- Return values and errors are explicit for AI/tool consumption.

Usage (example):
    from aws.athena_client import AthenaClient
    a = AthenaClient(output_bucket="s3://my-athena-results/")
    qid = a.start_query_execution("SELECT * FROM table", database="my_db")
    status = a.wait_query(qid)
    results = a.get_query_results(qid)

Design notes for AI/MCP tools:
- start_query_execution requires an output_location (S3 path) either at initialization or per-call.
- wait_query polls until completion; callers should set a reasonable timeout.
- Methods raise on boto3/botocore errors. Tool wrappers should catch and log/audit failures.
"""

from __future__ import annotations
import time
import logging
from typing import Optional, Dict, Any

import boto3
import botocore

from config import aws_credentials_dict

LOG = logging.getLogger(__name__)


def _client(**kwargs: Any):
    creds = aws_credentials_dict()
    init_kwargs = {**creds, **(kwargs or {})}
    return boto3.client("athena", **{k: v for k, v in init_kwargs.items() if v is not None})


class AthenaClient:
    """
    AthenaClient - lightweight Athena wrapper.

    Methods:
    - start_query_execution(query: str, database: str, output_location: Optional[str] = None, work_group: Optional[str] = None) -> str
      Start a query; returns QueryExecutionId.

    - get_query_status(query_execution_id: str) -> Dict[str, Any]
      Return the status dict for the query execution.

    - get_query_results(query_execution_id: str, max_results: int = 1000) -> Dict[str, Any]
      Fetch results (may be paginated depending on size).

    - wait_query(query_execution_id: str, timeout: int = 300, poll_interval: int = 3) -> Dict[str, Any]
      Poll the query until completion or timeout; returns final status dict.
    """

    def __init__(self, output_bucket: Optional[str] = None, **client_kwargs: Any):
        """
        Args:
            output_bucket: Optional default S3 output location (e.g. "s3://my-bucket/path/"). If not provided,
                           callers must provide output_location to start_query_execution.
        """
        self.client = _client(**client_kwargs)
        self.output_bucket = output_bucket

    def start_query_execution(
        self,
        query: str,
        database: str,
        output_location: Optional[str] = None,
        work_group: Optional[str] = None,
    ) -> str:
        """
        Start an Athena query execution. Returns the QueryExecutionId.

        Raises botocore.exceptions.BotoCoreError on failure.
        """
        out = output_location or self.output_bucket
        if not out:
            raise ValueError("No output_location specified for Athena query results (S3 path required)")
        params: Dict[str, Any] = {
            "QueryString": query,
            "QueryExecutionContext": {"Database": database},
            "ResultConfiguration": {"OutputLocation": out},
        }
        if work_group:
            params["WorkGroup"] = work_group
        try:
            resp = self.client.start_query_execution(**params)
            return resp["QueryExecutionId"]
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Athena start_query_execution failed")
            raise

    def get_query_status(self, query_execution_id: str) -> Dict[str, Any]:
        """
        Retrieve the status dict for a query execution.
        """
        try:
            resp = self.client.get_query_execution(QueryExecutionId=query_execution_id)
            return resp.get("QueryExecution", {}).get("Status", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Athena get_query_status failed")
            raise

    def get_query_results(self, query_execution_id: str, max_results: int = 1000) -> Dict[str, Any]:
        """
        Retrieve query results. For large results, callers may need to page.
        """
        try:
            resp = self.client.get_query_results(QueryExecutionId=query_execution_id, MaxResults=max_results)
            return resp
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Athena get_query_results failed")
            raise

    def wait_query(self, query_execution_id: str, timeout: int = 300, poll_interval: int = 3) -> Dict[str, Any]:
        """
        Poll until the query reaches a terminal state (SUCCEEDED, FAILED, CANCELLED, TIMED_OUT)
        or until timeout (in seconds) is reached. Returns the final status dict.
        """
        start = time.time()
        while True:
            status = self.get_query_status(query_execution_id)
            state = status.get("State")
            if state in ("SUCCEEDED", "FAILED", "CANCELLED", "TIMED_OUT"):
                return status
            if time.time() - start > timeout:
                raise TimeoutError(f"Athena query {query_execution_id} did not complete within {timeout}s")
            time.sleep(poll_interval)
