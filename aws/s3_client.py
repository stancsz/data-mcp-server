"""
AWS S3 helper wrappers for DataMCP.

Provides a small convenience class around boto3 to be used by the MCP server.
"""

from __future__ import annotations
import io
from typing import Optional, List, Dict, Any
import logging

import boto3
import botocore

from config import aws_credentials_dict, default_s3_bucket

LOG = logging.getLogger(__name__)


class S3Client:
    def __init__(self, bucket: Optional[str] = None, **client_kwargs: Any):
        """
        Initialize the S3 client.

        If AWS credentials are provided via env vars, aws_credentials_dict() will
        include them. Otherwise boto3's normal resolution chain applies.
        """
        creds = aws_credentials_dict()
        # allow caller to override region etc via client_kwargs
        init_kwargs = {**creds, **client_kwargs}
        self.s3 = boto3.client("s3", **{k: v for k, v in init_kwargs.items() if v is not None})
        self.bucket = bucket or default_s3_bucket()
        if not self.bucket:
            LOG.warning("No default S3 bucket configured (DEFAULT_S3_BUCKET)")

    def upload_bytes(self, data: bytes, key: str, bucket: Optional[str] = None, extra_args: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Upload raw bytes to S3 using PutObject. Returns the boto3 response dict.
        """
        target_bucket = bucket or self.bucket
        if not target_bucket:
            raise ValueError("No target S3 bucket specified")
        try:
            resp = self.s3.put_object(Bucket=target_bucket, Key=key, Body=data, **(extra_args or {}))
            return resp
        except botocore.exceptions.BotoCoreError as e:
            LOG.exception("S3 put_object failed")
            raise

    def upload_fileobj(self, fileobj: io.BytesIO, key: str, bucket: Optional[str] = None, extra_args: Optional[Dict[str, Any]] = None) -> None:
        """
        Upload a file-like object to S3. Uses upload_fileobj which streams the file.
        Returns None on success; exceptions propagate on failure.
        """
        target_bucket = bucket or self.bucket
        if not target_bucket:
            raise ValueError("No target S3 bucket specified")
        # Ensure fileobj is at start
        try:
            fileobj.seek(0)
        except Exception:
            pass
        try:
            # upload_fileobj does not return a value; exceptions indicate errors
            self.s3.upload_fileobj(Fileobj=fileobj, Bucket=target_bucket, Key=key, ExtraArgs=extra_args or {})
        except botocore.exceptions.BotoCoreError as e:
            LOG.exception("S3 upload_fileobj failed")
            raise

    def download_to_bytesio(self, key: str, bucket: Optional[str] = None) -> io.BytesIO:
        """
        Download object from S3 and return a BytesIO containing its contents.
        """
        target_bucket = bucket or self.bucket
        if not target_bucket:
            raise ValueError("No target S3 bucket specified")
        try:
            resp = self.s3.get_object(Bucket=target_bucket, Key=key)
            data = resp["Body"].read()
            return io.BytesIO(data)
        except self.s3.exceptions.NoSuchKey:
            raise
        except botocore.exceptions.BotoCoreError:
            LOG.exception("S3 get_object failed")
            raise

    def list_objects(self, prefix: Optional[str] = None, bucket: Optional[str] = None, max_keys: int = 1000) -> List[Dict[str, Any]]:
        """
        List objects in a bucket optionally filtering by prefix. Returns a list
        of object metadata dicts as returned by S3.
        """
        target_bucket = bucket or self.bucket
        if not target_bucket:
            raise ValueError("No target S3 bucket specified")
        paginator = self.s3.get_paginator("list_objects_v2")
        page_iter = paginator.paginate(Bucket=target_bucket, Prefix=prefix or "", PaginationConfig={"MaxItems": max_keys})
        results: List[Dict[str, Any]] = []
        try:
            for page in page_iter:
                contents = page.get("Contents", [])
                results.extend(contents)
            return results
        except botocore.exceptions.BotoCoreError:
            LOG.exception("S3 list_objects_v2 failed")
            raise

    def delete_object(self, key: str, bucket: Optional[str] = None) -> Dict[str, Any]:
        """
        Delete a single object from S3. Returns the delete_object response.
        """
        target_bucket = bucket or self.bucket
        if not target_bucket:
            raise ValueError("No target S3 bucket specified")
        try:
            resp = self.s3.delete_object(Bucket=target_bucket, Key=key)
            return resp
        except botocore.exceptions.BotoCoreError:
            LOG.exception("S3 delete_object failed")
            raise

    def generate_presigned_url(self, key: str, bucket: Optional[str] = None, expires_in: int = 3600, http_method: str = "GET") -> str:
        """
        Generate a presigned URL for GET/PUT operations on an object.
        """
        target_bucket = bucket or self.bucket
        if not target_bucket:
            raise ValueError("No target S3 bucket specified")
        try:
            url = self.s3.generate_presigned_url(
                ClientMethod="get_object" if http_method.upper() == "GET" else "put_object",
                Params={"Bucket": target_bucket, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except botocore.exceptions.BotoCoreError:
            LOG.exception("S3 generate_presigned_url failed")
            raise
