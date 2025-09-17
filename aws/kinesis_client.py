"""
Kinesis client wrapper for DataMCP

Purpose:
- Focused wrapper for AWS Kinesis (Data Streams) used by MCP tools.
- Provide put_record, put_records, get_shard_iterator, get_records helpers.
- Clear docs and predictable return types for AI tooling.

Usage:
    from aws.kinesis_client import KinesisClient
    k = KinesisClient(stream_name="my-stream")
    k.put_record(b"payload", "key1")
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
    return boto3.client("kinesis", **{k: v for k, v in init_kwargs.items() if v is not None})


class KinesisClient:
    def __init__(self, stream_name: Optional[str] = None, **client_kwargs: Any):
        self.client = _client(**client_kwargs)
        self.stream_name = stream_name

    def put_record(self, data: bytes, partition_key: str, stream_name: Optional[str] = None) -> Dict[str, Any]:
        name = stream_name or self.stream_name
        if not name:
            raise ValueError("No Kinesis stream specified")
        try:
            return self.client.put_record(StreamName=name, Data=data, PartitionKey=partition_key)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Kinesis put_record failed")
            raise

    def put_records(self, records: List[Dict[str, Any]], stream_name: Optional[str] = None) -> Dict[str, Any]:
        name = stream_name or self.stream_name
        if not name:
            raise ValueError("No Kinesis stream specified")
        try:
            return self.client.put_records(Records=records, StreamName=name)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Kinesis put_records failed")
            raise

    def get_shard_iterator(self, stream_name: str, shard_id: str, iterator_type: str = "TRIM_HORIZON", sequence_number: Optional[str] = None) -> str:
        try:
            kwargs: Dict[str, Any] = {"StreamName": stream_name, "ShardId": shard_id, "ShardIteratorType": iterator_type}
            if sequence_number:
                kwargs["StartingSequenceNumber"] = sequence_number
            resp = self.client.get_shard_iterator(**kwargs)
            return resp.get("ShardIterator", "")
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Kinesis get_shard_iterator failed")
            raise

    def get_records(self, shard_iterator: str, limit: Optional[int] = None) -> Dict[str, Any]:
        try:
            if limit:
                return self.client.get_records(ShardIterator=shard_iterator, Limit=limit)
            return self.client.get_records(ShardIterator=shard_iterator)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Kinesis get_records failed")
            raise
