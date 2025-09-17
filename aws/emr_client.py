"""
EMR client wrapper for DataMCP

Purpose:
- Focused wrapper for AWS EMR operations used by MCP tools.
- Expose run_job_flow, add_steps, list_clusters, describe_cluster, terminate_job_flows with clear docs.

Usage:
    from aws.emr_client import EMRClient
    emr = EMRClient()
    jid = emr.run_job_flow("my-cluster", instances={"InstanceGroups": []})
    emr.add_steps(jid, steps=[...])

Design notes:
- Methods return boto3 response dicts or values and raise on botocore errors.
- Caller should handle more advanced EMR usage (bootstrap actions, step configs) and audit logs.
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
    return boto3.client("emr", **{k: v for k, v in init_kwargs.items() if v is not None})


class EMRClient:
    """
    EMRClient - wrapper around boto3 emr client.

    Methods:
    - run_job_flow(name: str, instances: Dict[str, Any], steps: Optional[List[Dict[str, Any]]] = None, bootstrap_actions: Optional[List[Dict[str, Any]]] = None, **kwargs) -> str
    - add_steps(cluster_id: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]
    - list_clusters(**kwargs) -> List[Dict[str, Any]]
    - describe_cluster(cluster_id: str) -> Dict[str, Any]
    - terminate_job_flows(cluster_ids: List[str]) -> None
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def run_job_flow(self, name: str, instances: Dict[str, Any], steps: Optional[List[Dict[str, Any]]] = None, bootstrap_actions: Optional[List[Dict[str, Any]]] = None, **kwargs: Any) -> str:
        try:
            params: Dict[str, Any] = {"Name": name, "Instances": instances}
            if steps:
                params["Steps"] = steps
            if bootstrap_actions:
                params["BootstrapActions"] = bootstrap_actions
            params.update(kwargs)
            resp = self.client.run_job_flow(**params)
            return resp.get("JobFlowId", "")
        except botocore.exceptions.BotoCoreError:
            LOG.exception("EMR run_job_flow failed")
            raise

    def add_steps(self, cluster_id: str, steps: List[Dict[str, Any]]) -> Dict[str, Any]:
        try:
            return self.client.add_job_flow_steps(JobFlowId=cluster_id, Steps=steps)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("EMR add_job_flow_steps failed")
            raise

    def list_clusters(self, **kwargs: Any) -> List[Dict[str, Any]]:
        try:
            resp = self.client.list_clusters(**kwargs)
            return resp.get("Clusters", [])
        except botocore.exceptions.BotoCoreError:
            LOG.exception("EMR list_clusters failed")
            raise

    def describe_cluster(self, cluster_id: str) -> Dict[str, Any]:
        try:
            resp = self.client.describe_cluster(ClusterId=cluster_id)
            return resp.get("Cluster", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("EMR describe_cluster failed")
            raise

    def terminate_job_flows(self, cluster_ids: List[str]) -> None:
        try:
            self.client.terminate_job_flows(JobFlowIds=cluster_ids)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("EMR terminate_job_flows failed")
            raise
