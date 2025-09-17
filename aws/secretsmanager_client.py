"""
Secrets Manager client for DataMCP

Purpose:
- Single-purpose wrapper for AWS Secrets Manager used by MCP tools.
- Provide clear, well-documented methods that return simple values or boto3 response dicts.
- Keep behavior predictable for AI-driven tools: get_secret returns the secret string or None; put_secret creates or updates.

Usage (example):
    from aws.secretsmanager_client import SecretsManagerClient
    sm = SecretsManagerClient()
    secret = sm.get_secret("projects/my-project/secrets/sa-key")
    sm.put_secret("my/secret/name", '{"user":"..."}')

Design notes for AI/MCP tools:
- Methods raise on boto3 errors. Tools should catch exceptions and record audit logs.
- get_secret returns a plain string (SecretString) or None if not found.
- put_secret attempts create and falls back to update.
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
    return boto3.client("secretsmanager", **{k: v for k, v in init_kwargs.items() if v is not None})


class SecretsManagerClient:
    """
    Wrapper around AWS Secrets Manager.

    Methods:
    - get_secret(name: str) -> Optional[str]
      Returns the secret string or None if not found.

    - put_secret(name: str, secret_string: str) -> Dict[str, Any]
      Creates or updates a secret and returns the boto3 response dict.
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def get_secret(self, name: str) -> Optional[str]:
        """
        Retrieve a secret value by name.

        Args:
            name: Secret id or ARN.

        Returns:
            Secret string or None if not found.

        Raises:
            botocore.exceptions.BotoCoreError on failure.
        """
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
        """
        Create or update a secret.

        Args:
            name: Secret name or ARN.
            secret_string: The secret payload as a JSON string or plain text.

        Returns:
            boto3 response dict for create_secret or update_secret.
        """
        try:
            try:
                return self.client.create_secret(Name=name, SecretString=secret_string)
            except self.client.exceptions.ResourceExistsException:
                return self.client.update_secret(SecretId=name, SecretString=secret_string)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("SecretsManager put_secret failed")
            raise
