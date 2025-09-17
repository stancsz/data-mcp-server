"""
BigQuery helper for DataMCP

Purpose:
- Focused wrapper for Google BigQuery operations used by MCP tools and AI agents.
- Exposes single-purpose methods with clear semantics:
  - run_query(sql, job_config=None, timeout=300) -> job_id
  - get_query_results(job_id, max_results=1000) -> rows (list of dicts) or iterator
  - create_dataset(dataset_id, exists_ok=True)
  - delete_dataset(dataset_id, delete_contents=False)
  - create_table(table_ref or table_id, schema, exists_ok=True)
  - list_datasets() -> List[str]
  - list_tables(dataset_id) -> List[str]
- Designed for tools that need programmatic BigQuery access analogous to Athena/Redshift.

Usage example:
    from gcp.bigquery_client import BigQueryClient
    bq = BigQueryClient(project="my-project")
    job_id = bq.run_query("SELECT 1 as x")
    rows = bq.get_query_results(job_id)

Design notes for AI/MCP tools:
- This wrapper uses google-cloud-bigquery. The runtime environment must have google-cloud-bigquery installed and credentials available.
- run_query returns the job id (string). get_query_results returns a list of dict rows (uses row.to_dict()).
- Methods raise exceptions from the underlying library; calling tools should catch, audit, and sanitize outputs before exposing to agents.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any, List

# google bigquery libs (ensure installed in runtime)
try:
    from google.cloud import bigquery  # type: ignore
    from google.auth.exceptions import DefaultCredentialsError  # type: ignore
except Exception:  # pragma: no cover
    bigquery = None  # type: ignore
    DefaultCredentialsError = Exception  # type: ignore

LOG = logging.getLogger(__name__)


class BigQueryClient:
    """
    Minimal BigQuery wrapper.

    Methods:
    - run_query(sql: str, job_config: Optional[bigquery.QueryJobConfig] = None, timeout: int = 300) -> str
    - get_query_results(job_id: str, max_results: int = 1000) -> List[Dict[str, Any]]
    - create_dataset(dataset_id: str, exists_ok: bool = True) -> Dict[str, Any]
    - delete_dataset(dataset_id: str, delete_contents: bool = False) -> None
    - create_table(table_id: str, schema: List[bigquery.SchemaField], exists_ok: bool = True) -> Dict[str, Any]
    - list_datasets() -> List[str]
    - list_tables(dataset_id: str) -> List[str]
    """

    def __init__(self, project: Optional[str] = None, client: Optional[Any] = None):
        """
        Args:
            project: optional default GCP project id
            client: optional bigquery.Client instance for testing or custom credentials
        """
        if bigquery is None:
            raise RuntimeError("google-cloud-bigquery is not available. Install google-cloud-bigquery package.")
        try:
            self.client = client or bigquery.Client(project=project)
        except DefaultCredentialsError:
            LOG.exception("Failed to initialize BigQuery client - credentials not found")
            raise
        self.project = project

    def run_query(self, sql: str, job_config: Optional[Any] = None, timeout: int = 300) -> str:
        """
        Run a query asynchronously and return the job id.

        Args:
            sql: SQL string to execute
            job_config: optional bigquery.QueryJobConfig
            timeout: seconds to wait for job to start (not total query runtime)

        Returns:
            job_id (str)
        """
        try:
            job = self.client.query(sql, job_config=job_config)
            # job.job_id is the id; wait for job to start/complete if needed externally
            job.result(timeout=timeout)  # wait for completion up to timeout
            return job.job_id
        except Exception:
            LOG.exception("BigQuery run_query failed")
            raise

    def get_query_results(self, job_id: str, max_results: int = 1000) -> List[Dict[str, Any]]:
        """
        Fetch results for a given job id. Returns list of dict rows.

        Args:
            job_id: BigQuery job id (string)
            max_results: maximum number of rows to return (client may return fewer)

        Returns:
            List of row dicts
        """
        try:
            job = self.client.get_job(job_id)
            iterator = job.result(max_results=max_results)
            rows: List[Dict[str, Any]] = []
            for row in iterator:
                try:
                    rows.append(dict(row))
                except Exception:
                    # fallback: convert fields manually
                    rows.append({k: getattr(row, k) for k in row._field_names})  # type: ignore
            return rows
        except Exception:
            LOG.exception("BigQuery get_query_results failed for job %s", job_id)
            raise

    def create_dataset(self, dataset_id: str, exists_ok: bool = True) -> Dict[str, Any]:
        """
        Create a dataset. dataset_id may be 'project.dataset' or 'dataset' if project provided.
        """
        try:
            dataset_ref = self.client.dataset(dataset_id) if "." not in dataset_id and self.project else bigquery.Dataset(dataset_id)
            dataset = self.client.create_dataset(dataset_ref, exists_ok=exists_ok)
            return {"dataset_id": dataset.dataset_id}
        except Exception:
            LOG.exception("BigQuery create_dataset failed for %s", dataset_id)
            raise

    def delete_dataset(self, dataset_id: str, delete_contents: bool = False) -> None:
        """
        Delete a dataset. Set delete_contents=True to delete non-empty dataset.
        """
        try:
            dataset_ref = dataset_id if "." in dataset_id else f"{self.project}.{dataset_id}" if self.project else dataset_id
            self.client.delete_dataset(dataset_ref, delete_contents=delete_contents, not_found_ok=True)
        except Exception:
            LOG.exception("BigQuery delete_dataset failed for %s", dataset_id)
            raise

    def create_table(self, table_id: str, schema: Optional[List[Any]] = None, exists_ok: bool = True) -> Dict[str, Any]:
        """
        Create a table with the provided schema. schema is list of bigquery.SchemaField or similar.
        """
        try:
            table = bigquery.Table(table_id, schema=schema) if schema is not None else bigquery.Table(table_id)
            table = self.client.create_table(table, exists_ok=exists_ok)
            return {"table_id": table.table_id}
        except Exception:
            LOG.exception("BigQuery create_table failed for %s", table_id)
            raise

    def list_datasets(self) -> List[str]:
        """
        List datasets in the configured project.
        """
        try:
            datasets = [d.dataset_id for d in self.client.list_datasets()]
            return datasets
        except Exception:
            LOG.exception("BigQuery list_datasets failed")
            raise

    def list_tables(self, dataset_id: str) -> List[str]:
        """
        List tables in a dataset.
        """
        try:
            ds_ref = dataset_id if "." in dataset_id else f"{self.project}.{dataset_id}" if self.project else dataset_id
            tables = [t.table_id for t in self.client.list_tables(ds_ref)]
            return tables
        except Exception:
            LOG.exception("BigQuery list_tables failed for dataset %s", dataset_id)
            raise
