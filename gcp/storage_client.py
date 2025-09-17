"""
GCP Cloud Storage helper for DataMCP

Purpose:
- Focused wrapper for Google Cloud Storage operations used by MCP tools and AI agents.
- Exposes single-purpose methods with clear semantics: upload_bytes, upload_fileobj, download_to_bytesio, list_blobs, delete_blob, generate_signed_url.
- Designed for tools that need object storage access analogous to AWS S3.

Usage example:
    from gcp.storage_client import GCSClient
    gcs = GCSClient(bucket="my-bucket")
    gcs.upload_bytes(b"payload", "path/to/obj")
    bio = gcs.download_to_bytesio("path/to/obj")

Design notes for AI/MCP tools:
- This wrapper uses the google-cloud-storage library. The runtime environment must have the
  google-cloud-storage package and credentials available (Application Default Credentials or a service account).
- generate_signed_url will attempt to use service account credentials to sign URLs; if not possible an error is raised.
- Methods raise exceptions from the underlying library; callers should catch, audit, and sanitize outputs before exposing to agents.
"""

from __future__ import annotations
import io
import logging
from typing import Optional, List, Dict, Any

# google cloud libraries (ensure installed in runtime environment)
try:
    from google.cloud import storage  # type: ignore
    from google.auth.exceptions import DefaultCredentialsError  # type: ignore
except Exception:  # pragma: no cover - import errors handled at runtime
    storage = None  # type: ignore
    DefaultCredentialsError = Exception  # type: ignore

LOG = logging.getLogger(__name__)


class GCSClient:
    """
    GCSClient - minimal Google Cloud Storage wrapper.

    Methods:
    - upload_bytes(data: bytes, key: str, bucket: Optional[str] = None, content_type: Optional[str] = None) -> Dict[str, Any]
    - upload_fileobj(fileobj: io.BytesIO, key: str, bucket: Optional[str] = None, content_type: Optional[str] = None) -> None
    - download_to_bytesio(key: str, bucket: Optional[str] = None) -> io.BytesIO
    - list_blobs(prefix: Optional[str] = None, bucket: Optional[str] = None) -> List[Dict[str, Any]]
    - delete_blob(key: str, bucket: Optional[str] = None) -> bool
    - generate_signed_url(key: str, bucket: Optional[str] = None, expires_in: int = 3600, method: str = "GET") -> str
    """

    def __init__(self, bucket: Optional[str] = None, client: Optional[Any] = None):
        """
        Args:
            bucket: default bucket name to operate on (optional).
            client: optional google.cloud.storage.Client instance (for testing or custom credentials).
        """
        if storage is None:
            raise RuntimeError("google-cloud-storage is not available. Install google-cloud-storage package.")
        try:
            self.client = client or storage.Client()
        except DefaultCredentialsError as exc:
            LOG.exception("Failed to initialize GCS client - credentials not found")
            raise
        self.bucket_name = bucket

    def _bucket(self, bucket: Optional[str] = None):
        bname = bucket or self.bucket_name
        if not bname:
            raise ValueError("No GCS bucket specified")
        return self.client.bucket(bname)

    def upload_bytes(self, data: bytes, key: str, bucket: Optional[str] = None, content_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Upload raw bytes to GCS as an object. Returns minimal metadata dict on success.
        """
        b = self._bucket(bucket)
        blob = b.blob(key)
        try:
            blob.upload_from_string(data, content_type=content_type)
            return {"bucket": b.name, "name": blob.name, "size": blob.size}
        except Exception:
            LOG.exception("GCS upload_bytes failed")
            raise

    def upload_fileobj(self, fileobj: io.BytesIO, key: str, bucket: Optional[str] = None, content_type: Optional[str] = None) -> None:
        """
        Upload a file-like object to GCS.
        """
        b = self._bucket(bucket)
        blob = b.blob(key)
        try:
            fileobj.seek(0)
        except Exception:
            pass
        try:
            blob.upload_from_file(fileobj, content_type=content_type)
        except Exception:
            LOG.exception("GCS upload_fileobj failed")
            raise

    def download_to_bytesio(self, key: str, bucket: Optional[str] = None) -> io.BytesIO:
        """
        Download an object from GCS and return a BytesIO with its contents.
        """
        b = self._bucket(bucket)
        blob = b.blob(key)
        bio = io.BytesIO()
        try:
            blob.download_to_file(bio)
            bio.seek(0)
            return bio
        except Exception:
            LOG.exception("GCS download_to_bytesio failed")
            raise

    def list_blobs(self, prefix: Optional[str] = None, bucket: Optional[str] = None, max_results: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        List blobs in the target bucket under the given prefix.
        Returns a list of metadata dicts.
        """
        b = self._bucket(bucket)
        try:
            iterator = b.list_blobs(prefix=prefix, max_results=max_results)
            results = []
            for blob in iterator:
                results.append({"name": blob.name, "size": blob.size, "updated": blob.updated})
            return results
        except Exception:
            LOG.exception("GCS list_blobs failed")
            raise

    def delete_blob(self, key: str, bucket: Optional[str] = None) -> bool:
        """
        Delete an object from GCS. Returns True on success.
        """
        b = self._bucket(bucket)
        blob = b.blob(key)
        try:
            blob.delete()
            return True
        except Exception:
            LOG.exception("GCS delete_blob failed")
            raise

    def generate_signed_url(self, key: str, bucket: Optional[str] = None, expires_in: int = 3600, method: str = "GET") -> str:
        """
        Generate a signed URL for GET/PUT operations on an object.
        Requires credentials capable of signing (service account).
        """
        b = self._bucket(bucket)
        blob = b.blob(key)
        try:
            url = blob.generate_signed_url(expiration=expires_in, method=method)
            return url
        except Exception:
            LOG.exception("GCS generate_signed_url failed")
            raise
