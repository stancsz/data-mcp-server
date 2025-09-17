"""
SSM Parameter Store client for DataMCP

Purpose:
- Simple wrapper focused on Parameter Store usage for storing non-sensitive and secure parameters.
- Provide get_parameter and put_parameter methods with clear behavior for MCP tools.

Usage:
    from aws.ssm_client import SSMClient
    s = SSMClient()
    val = s.get_parameter("/my/app/config", with_decryption=True)
    s.put_parameter("/my/app/config", "value", type="String")

Design notes:
- get_parameter returns the parameter value or None if not found.
- put_parameter supports Overwrite and types (String, SecureString, StringList).
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
    return boto3.client("ssm", **{k: v for k, v in init_kwargs.items() if v is not None})


class SSMClient:
    """
    Wrapper for AWS SSM Parameter Store.
    """

    def __init__(self, **client_kwargs: Any):
        self.client = _client(**client_kwargs)

    def get_parameter(self, name: str, with_decryption: bool = True) -> Optional[str]:
        """
        Retrieve a parameter value.

        Returns:
            Parameter value string or None if not found.
        """
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
        """
        Put a parameter in SSM.

        Args:
            name: parameter name.
            value: parameter value.
            type: String | SecureString | StringList
            overwrite: whether to overwrite existing parameter.

        Returns:
            boto3 response dict.
        """
        try:
            return self.client.put_parameter(Name=name, Value=value, Type=type, Overwrite=overwrite)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("SSM put_parameter failed")
            raise
