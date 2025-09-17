"""
Firehose client wrapper for DataMCP

Purpose:
- Focused wrapper for AWS Kinesis Firehose delivery streams used by MCP tools.
- Provide simple methods: put_record and put_record_batch.
- Keep module small and documented so AI-driven MCP tools can call it directly.

Usage:
    from aws.firehose_client import FirehoseClient
    fh = FirehoseClient(delivery_stream_name="my-delivery-stream")
    fh.put_record(b"payload")
    fh.put_record_batch([{"Data": b"r1"}, {"Data": b"r2"}])

Design notes:
- Methods return boto3 response dicts.
- Exceptions propagate (botocore) — calling tools should catch and record audit logs.
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
    return boto3.client("firehose", **{k: v for k, v in init_kwargs.items() if v is not None})


class FirehoseClient:
    """
    FirehoseClient - minimal wrapper for AWS Firehose.

    Methods:
    - put_record(data: bytes, delivery_stream_name: Optional[str] = None) -> Dict[str, Any]
    - put_record_batch(records: List[Dict[str, Any]], delivery_stream_name: Optional[str] = None) -> Dict[str, Any]
    """

    def __init__(self, delivery_stream_name: Optional[str] = None, **client_kwargs: Any):
        self.client = _client(**client_kwargs)
        self.delivery_stream_name = delivery_stream_name

    def put_record(self, data: bytes, delivery_stream_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Put a single record into a Firehose delivery stream.

        Args:
            data: raw bytes payload
            delivery_stream_name: optional delivery stream name (falls back to instance default)

        Returns:
            boto3 response dict
        """
        name = delivery_stream_name or self.delivery_stream_name
        if not name:
            raise ValueError("No Firehose delivery stream specified")
        try:
            return self.client.put_record(DeliveryStreamName=name, Record={"Data": data})
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Firehose put_record failed")
            raise

    def put_record_batch(self, records: List[Dict[str, Any]], delivery_stream_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Put a batch of records into Firehose.

        Args:
            records: list of {"Data": b"..."} dicts
            delivery_stream_name: optional stream name

        Returns:
            boto3 response dict
        """
        name = delivery_stream_name or self.delivery_stream_name
        if not name:
            raise ValueError("No Firehose delivery stream specified")
        try:
            return self.client.put_record_batch(DeliveryStreamName=name, Records=records)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Firehose put_record_batch failed")
            raise
