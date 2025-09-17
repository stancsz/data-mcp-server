"""
Unit tests for aws.s3_client.S3Client and aws.dynamo_client.DynamoClient.

These tests mock boto3 to assert our wrappers call the expected boto3 methods
and propagate responses/errors correctly.
"""

from __future__ import annotations
import io
from unittest.mock import MagicMock, patch

import pytest

from aws.s3_client import S3Client
from aws.dynamo_client import DynamoClient


def test_s3_upload_bytes_calls_put_object():
    fake_resp = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_s3 = MagicMock()
    mock_s3.put_object.return_value = fake_resp

    with patch("boto3.client", return_value=mock_s3) as mock_client:
        s3 = S3Client(bucket="test-bucket")
        resp = s3.upload_bytes(b"hello", key="path/to/key")
        assert resp == fake_resp
        mock_s3.put_object.assert_called_once_with(Bucket="test-bucket", Key="path/to/key", Body=b"hello")


def test_s3_upload_fileobj_streams_fileobj():
    mock_s3 = MagicMock()
    # upload_fileobj doesn't return a value
    mock_s3.upload_fileobj.return_value = None

    with patch("boto3.client", return_value=mock_s3):
        s3 = S3Client(bucket="test-bucket")
        fileobj = io.BytesIO(b"data")
        s3.upload_fileobj(fileobj=fileobj, key="obj.bin")
        mock_s3.upload_fileobj.assert_called_once()
        call_args = mock_s3.upload_fileobj.call_args[1]
        assert call_args["Bucket"] == "test-bucket"
        assert call_args["Key"] == "obj.bin"


def test_s3_download_to_bytesio_reads_object():
    body_bytes = b"file-bytes"
    mock_body = MagicMock()
    mock_body.read.return_value = body_bytes
    mock_s3 = MagicMock()
    mock_s3.get_object.return_value = {"Body": mock_body}

    with patch("boto3.client", return_value=mock_s3):
        s3 = S3Client(bucket="test-bucket")
        bio = s3.download_to_bytesio(key="obj.bin")
        assert isinstance(bio, io.BytesIO)
        assert bio.read() == body_bytes


def test_s3_list_objects_paginates_and_returns_contents():
    page1 = {"Contents": [{"Key": "a"}], "IsTruncated": True}
    page2 = {"Contents": [{"Key": "b"}], "IsTruncated": False}
    paginator = MagicMock()
    paginator.paginate.return_value = [page1, page2]
    mock_s3 = MagicMock()
    mock_s3.get_paginator.return_value = paginator

    with patch("boto3.client", return_value=mock_s3):
        s3 = S3Client(bucket="test-bucket")
        results = s3.list_objects(prefix="pfx")
        assert isinstance(results, list)
        assert {"Key": "a"} in results and {"Key": "b"} in results


def test_s3_delete_object_calls_delete():
    mock_s3 = MagicMock()
    mock_s3.delete_object.return_value = {"Deleted": {"Key": "k"}}
    with patch("boto3.client", return_value=mock_s3):
        s3 = S3Client(bucket="test-bucket")
        resp = s3.delete_object(key="k")
        assert resp == {"Deleted": {"Key": "k"}}
        mock_s3.delete_object.assert_called_once_with(Bucket="test-bucket", Key="k")


def test_s3_generate_presigned_url_calls_boto3():
    mock_s3 = MagicMock()
    mock_s3.generate_presigned_url.return_value = "https://signed-url"
    with patch("boto3.client", return_value=mock_s3):
        s3 = S3Client(bucket="test-bucket")
        url = s3.generate_presigned_url(key="k", bucket="test-bucket", expires_in=123, http_method="GET")
        assert url == "https://signed-url"
        mock_s3.generate_presigned_url.assert_called_once()


def make_fake_table(mock_resource, name="tbl"):
    mock_table = MagicMock()
    mock_resource.Table.return_value = mock_table
    return mock_table


def test_dynamo_put_get_delete_flow():
    # Setup a fake resource and table
    mock_resource = MagicMock()
    mock_table = make_fake_table(mock_resource, name="test-table")
    mock_table.put_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}
    mock_table.get_item.return_value = {"Item": {"pk": "1", "value": "x"}}
    mock_table.delete_item.return_value = {"ResponseMetadata": {"HTTPStatusCode": 200}}

    with patch("boto3.resource", return_value=mock_resource):
        dyn = DynamoClient(table_name="test-table")
        put_resp = dyn.put_item(item={"pk": "1", "value": "x"})
        assert "ResponseMetadata" in put_resp
        got = dyn.get_item(key={"pk": "1"})
        assert got == {"pk": "1", "value": "x"}
        del_resp = dyn.delete_item(key={"pk": "1"})
        assert "ResponseMetadata" in del_resp
        mock_table.put_item.assert_called_once()
        mock_table.get_item.assert_called_once()
        mock_table.delete_item.assert_called_once()


def test_dynamo_query_and_scan_return_items():
    mock_resource = MagicMock()
    mock_table = make_fake_table(mock_resource, name="test-table")
    mock_table.query.return_value = {"Items": [{"pk": "1"}, {"pk": "2"}]}
    mock_table.scan.return_value = {"Items": [{"pk": "3"}]}

    with patch("boto3.resource", return_value=mock_resource):
        dyn = DynamoClient(table_name="test-table")
        items_q = dyn.query(key_condition=MagicMock())
        assert isinstance(items_q, list) and len(items_q) == 2
        items_s = dyn.scan()
        assert isinstance(items_s, list) and len(items_s) == 1
