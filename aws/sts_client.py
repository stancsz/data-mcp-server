"""
STS helper for DataMCP

Purpose:
- Provide a minimal, single-purpose STS client wrapper used by MCP tools.
- Export clear, well-documented functions the AI or MCP tool code can call.
- Keep implementation focused (get_caller_identity, assume_role) and return simple dicts.

Usage:
- Import STSClient and call methods from mcp_server tool wrappers.
- Example:
    from aws.sts_client import STSClient
    sts = STSClient()
    identity = sts.get_caller_identity()
    creds = sts.assume_role(role_arn="arn:aws:iam::123:role/role-name")

Design notes for AI/MCP tools:
- Methods raise on boto3 errors. Caller should handle exceptions and record audit logs.
- Returned credentials from assume_role are the temporary credentials dict matching boto3 shape:
  { "AccessKeyId": "...", "SecretAccessKey": "...", "SessionToken": "...", "Expiration": "..." }
"""

from __future__ import annotations
import logging
from typing import Dict, Any, Optional

import boto3
import botocore

from config import aws_credentials_dict

LOG = logging.getLogger(__name__)


def _client(**kwargs: Any):
    """
    Internal helper to build a boto3 STS client using credentials from config.aws_credentials_dict().
    """
    creds = aws_credentials_dict()
    init_kwargs = {**creds, **(kwargs or {})}
    return boto3.client("sts", **{k: v for k, v in init_kwargs.items() if v is not None})


class STSClient:
    """
    STSClient - focused wrapper around boto3 sts client.

    Methods:
    - get_caller_identity() -> Dict[str, Any]
        Returns the caller identity dict returned by STS.

    - assume_role(role_arn: str, session_name: str = "data-mcp-session", duration_seconds: int = 3600) -> Dict[str, Any]
        Returns temporary credentials dict for the assumed role (AccessKeyId, SecretAccessKey, SessionToken, Expiration).
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def get_caller_identity(self) -> Dict[str, Any]:
        """
        Return the result of sts.get_caller_identity().

        Returns:
            Dict[str, Any]: { 'Account': ..., 'UserId': ..., 'Arn': ... }
        Raises:
            botocore.exceptions.BotoCoreError on failure.
        """
        try:
            return self.client.get_caller_identity()
        except botocore.exceptions.BotoCoreError:
            LOG.exception("STS get_caller_identity failed")
            raise

    def assume_role(self, role_arn: str, session_name: str = "data-mcp-session", duration_seconds: int = 3600) -> Dict[str, Any]:
        """
        Assume an IAM role and return temporary credentials.

        Args:
            role_arn (str): ARN of the role to assume.
            session_name (str): Session name for the assumed role.
            duration_seconds (int): Duration for the credentials.

        Returns:
            Dict[str, Any]: Credentials dict (AccessKeyId, SecretAccessKey, SessionToken, Expiration).

        Raises:
            botocore.exceptions.BotoCoreError on failure.
        """
        try:
            resp = self.client.assume_role(RoleArn=role_arn, RoleSessionName=session_name, DurationSeconds=duration_seconds)
            return resp.get("Credentials", {})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("STS assume_role failed")
            raise
