"""
Lambda client wrapper for DataMCP

Purpose:
- Focused wrapper for AWS Lambda invoke operations used by MCP tools.
- Provide a simple, well-documented `invoke` method suitable for AI-driven tooling.

Usage:
    from aws.lambda_client import LambdaClient
    lc = LambdaClient()
    resp = lc.invoke("my-func", payload=b'{"key":"value"}')

Design notes for AI/MCP tools:
- `invoke` returns the raw boto3 response dict. For RequestResponse invocations, the response contains a 'Payload' stream.
- Exceptions propagate (botocore). Callers should catch and record audit logs and sanitize outputs before exposing to agents.
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
    return boto3.client("lambda", **{k: v for k, v in init_kwargs.items() if v is not None})


class LambdaClient:
    """
    LambdaClient - minimal wrapper around boto3 lambda client.

    Methods:
    - invoke(function_name: str, payload: Optional[bytes] = None,
             invocation_type: str = "RequestResponse", log_type: Optional[str] = None,
             qualifier: Optional[str] = None) -> Dict[str, Any]
      Invoke a Lambda function and return the boto3 response dict.
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def invoke(
        self,
        function_name: str,
        payload: Optional[bytes] = None,
        invocation_type: str = "RequestResponse",
        log_type: Optional[str] = None,
        qualifier: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Invoke a Lambda function.

        Args:
            function_name: name or ARN of the Lambda function.
            payload: optional bytes payload to send.
            invocation_type: RequestResponse | Event | DryRun
            log_type: Tail to include execution log in the response (base64)
            qualifier: version or alias

        Returns:
            boto3 response dict as returned by lambda.invoke()
        """
        try:
            params: Dict[str, Any] = {"FunctionName": function_name, "InvocationType": invocation_type}
            if payload is not None:
                params["Payload"] = payload
            if log_type:
                params["LogType"] = log_type
            if qualifier:
                params["Qualifier"] = qualifier
            return self.client.invoke(**params)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Lambda invoke failed")
            raise
