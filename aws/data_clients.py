"""
Collection of common AWS data-related wrappers used by DataMCP.

Includes lightweight helpers for:
- STS (assume role / caller identity)
- Secrets Manager
- SSM Parameter Store
- Athena (start query, poll status, fetch results)
- Glue (start job, get job run, list jobs)

All wrappers use boto3 clients created with credentials from config.aws_credentials_dict().
They return raw boto3 response dicts (or simplified structured results) and raise on boto3 errors.
"""

from __future__ import annotations
import time
import logging
from typing import Optional, Dict, Any, List

import boto3
import botocore

from config import aws_credentials_dict

LOG = logging.getLogger(__name__)


def _client(service_name: str, **kwargs: Any):
    creds = aws_credentials_dict()
    init_kwargs = {**creds, **(kwargs or {})}
    return boto3.client(service_name, **{k: v for k, v in init_kwargs.items() if v is not None})


class STSClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("sts", **client_kwargs)

    def get_caller_identity(self) -> Dict[str, Any]:
        try:
            return self.client.get_caller_identity()
        except botocore.exceptions.BotoCoreError:
            LOG.exception("STS get_caller_identity failed")
            raise

    def assume_role(self, role_arn: str, session_name: str = "data-mcp-session", duration_seconds: int = 3600) -> Dict[str, Any]:
        """
        Assume the given role and return the temporary credentials structure.
        """
        try:
            resp = self.client.assume_role(RoleArn=role_arn, RoleSessionName=session_name, DurationSeconds=duration_seconds)
            return resp.get("Credentials", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("STS assume_role failed")
            raise


class SecretsManagerClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("secretsmanager", **client_kwargs)

    def get_secret(self, name: str) -> Optional[str]:
        try:
            resp = self.client.get_secret_value(SecretId=name)
            return resp.get("SecretString") or None
        except self.client.exceptions.ResourceNotFoundException:
            LOG.debug("Secret %s not found", name)
            return None
        except botocore.exceptions.BotoCoreError:
            LOG.exception("SecretsManager get_secret failed")
            raise

    def put_secret(self, name: str, secret_string: str) -> Dict[str, Any]:
        try:
            # Try create first; if exists, update
            try:
                return self.client.create_secret(Name=name, SecretString=secret_string)
            except self.client.exceptions.ResourceExistsException:
                return self.client.update_secret(SecretId=name, SecretString=secret_string)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("SecretsManager put_secret failed")
            raise


class SSMClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("ssm", **client_kwargs)

    def get_parameter(self, name: str, with_decryption: bool = True) -> Optional[str]:
        try:
            resp = self.client.get_parameter(Name=name, WithDecryption=with_decryption)
            return resp["Parameter"]["Value"]
        except self.client.exceptions.ParameterNotFound:
            LOG.debug("SSM parameter %s not found", name)
            return None
        except botocore.exceptions.BotoCoreError:
            LOG.exception("SSM get_parameter failed")
            raise

    def put_parameter(self, name: str, value: str, type: str = "String", overwrite: bool = True) -> Dict[str, Any]:
        try:
            return self.client.put_parameter(Name=name, Value=value, Type=type, Overwrite=overwrite)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("SSM put_parameter failed")
            raise


class AthenaClient:
    def __init__(self, output_bucket: Optional[str] = None, **client_kwargs: Any):
        self.client = _client("athena", **client_kwargs)
        self.output_bucket = output_bucket

    def start_query_execution(self, query: str, database: str, output_location: Optional[str] = None, work_group: Optional[str] = None) -> str:
        """
        Start an Athena query execution. Returns the QueryExecutionId.
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
        try:
            resp = self.client.get_query_execution(QueryExecutionId=query_execution_id)
            return resp.get("QueryExecution", {}).get("Status", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Athena get_query_status failed")
            raise

    def get_query_results(self, query_execution_id: str, max_results: int = 1000) -> Dict[str, Any]:
        try:
            resp = self.client.get_query_results(QueryExecutionId=query_execution_id, MaxResults=max_results)
            return resp
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Athena get_query_results failed")
            raise

    def wait_query(self, query_execution_id: str, timeout: int = 300, poll_interval: int = 3) -> Dict[str, Any]:
        """
        Poll until query completes or timeout (seconds) is reached. Returns final status dict.
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


class GlueClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("glue", **client_kwargs)

    def start_job(self, job_name: str, arguments: Optional[Dict[str, str]] = None) -> str:
        try:
            resp = self.client.start_job_run(JobName=job_name, Arguments=arguments or {})
            return resp["JobRunId"]
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Glue start_job_run failed")
            raise

    def get_job_run(self, job_name: str, run_id: str) -> Dict[str, Any]:
        try:
            resp = self.client.get_job_run(JobName=job_name, RunId=run_id)
            return resp.get("JobRun", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Glue get_job_run failed")
            raise

    def list_jobs(self) -> List[Dict[str, Any]]:
        try:
            resp = self.client.get_jobs()
            return resp.get("Jobs", [])
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Glue get_jobs failed")
            raise
