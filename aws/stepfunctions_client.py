"""
Step Functions client wrapper for DataMCP

Purpose:
- Focused wrapper for AWS Step Functions used by MCP tools.
- Provide start_execution, describe_execution, stop_execution helpers with clear docs.

Usage:
    from aws.stepfunctions_client import StepFunctionsClient
    sf = StepFunctionsClient()
    resp = sf.start_execution(state_machine_arn="arn:...", name="run1", input='{"k":"v"}')

Design notes:
- Methods return boto3 response dicts and raise on botocore errors.
- Caller should record audit logs and sanitize outputs for AI consumption.
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
    return boto3.client("stepfunctions", **{k: v for k, v in init_kwargs.items() if v is not None})


class StepFunctionsClient:
    """
    Wrapper around AWS Step Functions.

    Methods:
    - start_execution(state_machine_arn: str, name: Optional[str] = None, input: Optional[str] = None) -> Dict[str, Any]
    - describe_execution(execution_arn: str) -> Dict[str, Any]
    - stop_execution(execution_arn: str, error: Optional[str] = None, cause: Optional[str] = None) -> Dict[str, Any]
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def start_execution(self, state_machine_arn: str, name: Optional[str] = None, input: Optional[str] = None) -> Dict[str, Any]:
        """
        Start a state machine execution. Returns the start_execution response dict.
        """
        try:
            params: Dict[str, Any] = {"stateMachineArn": state_machine_arn}
            if name:
                params["name"] = name
            if input:
                params["input"] = input
            return self.client.start_execution(**params)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("StepFunctions start_execution failed")
            raise

    def describe_execution(self, execution_arn: str) -> Dict[str, Any]:
        """
        Describe an execution and return its metadata.
        """
        try:
            return self.client.describe_execution(executionArn=execution_arn)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("StepFunctions describe_execution failed")
            raise

    def stop_execution(self, execution_arn: str, error: Optional[str] = None, cause: Optional[str] = None) -> Dict[str, Any]:
        """
        Stop a running execution. Returns stop_execution response dict.
        """
        try:
            params: Dict[str, Any] = {"executionArn": execution_arn}
            if error:
                params["error"] = error
            if cause:
                params["cause"] = cause
            return self.client.stop_execution(**params)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("StepFunctions stop_execution failed")
            raise
