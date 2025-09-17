"""
AWS compute and streaming helpers for DataMCP.

Provides lightweight wrappers for:
- Kinesis (put_record, put_records, get_records)
- Firehose (put_record, put_record_batch)
- Lambda (invoke)
- Step Functions (start_execution, describe_execution, stop_execution)
- Redshift Data API (execute_statement, get_statement_result)
- EMR (run_job_flow, add_steps, list_clusters, describe_cluster, terminate_job_flows)

All wrappers use boto3 clients created with credentials from config.aws_credentials_dict().
They return raw boto3 response dicts (or simplified structured results) and raise on boto3 errors.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List

import boto3
import botocore

from config import aws_credentials_dict

LOG = logging.getLogger(__name__)


def _client(service_name: str, **kwargs: Any):
    creds = aws_credentials_dict()
    init_kwargs = {**creds, **(kwargs or {})}
    return boto3.client(service_name, **{k: v for k, v in init_kwargs.items() if v is not None})


class KinesisClient:
    def __init__(self, stream_name: Optional[str] = None, **client_kwargs: Any):
        self.client = _client("kinesis", **client_kwargs)
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
        """
        records: list of {"Data": b"...", "PartitionKey": "key"}
        """
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


class FirehoseClient:
    def __init__(self, delivery_stream_name: Optional[str] = None, **client_kwargs: Any):
        self.client = _client("firehose", **client_kwargs)
        self.delivery_stream_name = delivery_stream_name

    def put_record(self, data: bytes, delivery_stream_name: Optional[str] = None) -> Dict[str, Any]:
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
        records: list of {"Data": b"..."}
        """
        name = delivery_stream_name or self.delivery_stream_name
        if not name:
            raise ValueError("No Firehose delivery stream specified")
        try:
            return self.client.put_record_batch(DeliveryStreamName=name, Records=records)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Firehose put_record_batch failed")
            raise


class LambdaClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("lambda", **client_kwargs)

    def invoke(self, function_name: str, payload: Optional[bytes] = None, invocation_type: str = "RequestResponse", log_type: Optional[str] = None, qualifier: Optional[str] = None) -> Dict[str, Any]:
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


class StepFunctionsClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("stepfunctions", **client_kwargs)

    def start_execution(self, state_machine_arn: str, name: Optional[str] = None, input: Optional[str] = None) -> Dict[str, Any]:
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
        try:
            return self.client.describe_execution(executionArn=execution_arn)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("StepFunctions describe_execution failed")
            raise

    def stop_execution(self, execution_arn: str, error: Optional[str] = None, cause: Optional[str] = None) -> Dict[str, Any]:
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


class RedshiftDataClient:
    def __init__(self, cluster_identifier: Optional[str] = None, database: Optional[str] = None, db_user: Optional[str] = None, **client_kwargs: Any):
        """
        Uses the Redshift Data API (service name 'redshift-data') to run SQL statements.
        cluster_identifier: optional cluster identifier or workgroup; one of cluster identifier or workgroup must be provided per AWS docs in real usage.
        """
        self.client = _client("redshift-data", **client_kwargs)
        self.cluster_identifier = cluster_identifier
        self.database = database
        self.db_user = db_user

    def execute_statement(self, sql: str, cluster_identifier: Optional[str] = None, database: Optional[str] = None, db_user: Optional[str] = None, with_event: bool = False) -> Dict[str, Any]:
        try:
            params: Dict[str, Any] = {"Sql": sql}
            if cluster_identifier or self.cluster_identifier:
                params["ClusterIdentifier"] = cluster_identifier or self.cluster_identifier
            if database or self.database:
                params["Database"] = database or self.database
            if db_user or self.db_user:
                params["DbUser"] = db_user or self.db_user
            if with_event:
                params["WithEvent"] = True
            return self.client.execute_statement(**params)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Redshift Data execute_statement failed")
            raise

    def get_statement_result(self, id: str, max_results: int = 1000) -> Dict[str, Any]:
        try:
            return self.client.get_statement_result(Id=id, MaxResults=max_results)
        except botocore.exceptions.BotoCoreError:
            LOG.exception("Redshift Data get_statement_result failed")
            raise


class EMRClient:
    def __init__(self, **client_kwargs: Any):
        self.client = _client("emr", **client_kwargs)

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
