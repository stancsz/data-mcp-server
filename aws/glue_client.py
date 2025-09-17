"""
Glue client wrapper for DataMCP

Purpose:
- Provide a focused wrapper for AWS Glue operations used by MCP tools and AI agents.
- Expose simple methods with clear semantics: start_job, get_job_run, list_jobs.
- Keep behavior predictable: return boto3 response dicts or simplified structures and raise on boto3 errors.

Usage:
    from aws.glue_client import GlueClient
    g = GlueClient()
    run_id = g.start_job("my-glue-job", {"--arg":"value"})
    status = g.get_job_run("my-glue-job", run_id)
    jobs = g.list_jobs()

Design notes:
- Methods are intentionally small and documented so the AI can call them directly as MCP tools.
- Callers should handle exceptions and record audit logs.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List

import boto3
import botocore

from config import aws_credentials_dict

LOG = logging.getLogger(__name__)


def _client(**kwargs: Any):
    creds = aws_credentials_dict()
    init_kwargs = {**creds, **(kwargs or {})}
    return boto3.client("glue", **{k: v for k, v in init_kwargs.items() if v is not None})


class GlueClient:
    """
    GlueClient - focused wrapper around boto3 glue client.

    Methods:
    - start_job(job_name: str, arguments: Optional[Dict[str,str]] = None) -> str
      Starts a Glue job and returns the JobRunId.

    - get_job_run(job_name: str, run_id: str) -> Dict[str, Any]
      Returns job run metadata and status.

    - list_jobs() -> List[Dict[str, Any]]
      Returns a list of jobs (simplified).
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def start_job(self, job_name: str, arguments: Optional[Dict[str, str]] = None) -> str:
        """
        Start a Glue job run.

        Returns:
            JobRunId (str)
        """
        try:
            resp = self.client.start_job_run(JobName=job_name, Arguments=arguments or {})
            return resp.get("JobRunId", "")
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Glue start_job_run failed")
            raise

    def get_job_run(self, job_name: str, run_id: str) -> Dict[str, Any]:
        """
        Retrieve details for a specific job run.
        """
        try:
            resp = self.client.get_job_run(JobName=job_name, RunId=run_id)
            return resp.get("JobRun", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Glue get_job_run failed")
            raise

    def list_jobs(self) -> List[Dict[str, Any]]:
        """
        List Glue jobs (returns simplified list). Pagination not implemented for brevity.
        """
        try:
            resp = self.client.get_jobs()
            return resp.get("Jobs", [])
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Glue get_jobs failed")
            raise
