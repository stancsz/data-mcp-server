"""
GCP Secret Manager helper for DataMCP

Purpose:
- Focused wrapper for Google Secret Manager operations used by MCP tools and AI agents.
- Exposes single-purpose methods: access_secret (read), create_secret, add_secret_version, update_secret, delete_secret.
- Designed so each method has a clear, narrow responsibility and predictable return types for AI-driven tools.

Usage:
    from gcp.secret_manager_client import GCPSecretManager
    sm = GCPSecretManager(project="my-project")
    value = sm.access_secret("projects/my-project/secrets/my-secret")
    sm.create_secret("projects/my-project", "my-secret", replication_policy={"automatic": {}})
    sm.add_secret_version("projects/my-project/secrets/my-secret", "super-secret-value")

Design notes for AI/MCP tools:
- This wrapper uses google-cloud-secret-manager. Runtime must have the library installed and credentials available.
- access_secret returns the secret payload as a string.
- Methods raise exceptions from the underlying client; calling code should catch, audit, and sanitize outputs before exposing to agents.
"""

from __future__ import annotations
import logging
from typing import Optional, Dict, Any

# Google libs (ensure installed in runtime)
try:
    from google.cloud import secretmanager  # type: ignore
    from google.auth.exceptions import DefaultCredentialsError  # type: ignore
except Exception:  # pragma: no cover - import errors handled at runtime
    secretmanager = None  # type: ignore
    DefaultCredentialsError = Exception  # type: ignore

LOG = logging.getLogger(__name__)


class GCPSecretManager:
    """
    Minimal Secret Manager wrapper.

    Methods:
    - access_secret(secret_name: str, version: str = "latest") -> str
    - create_secret(parent: str, secret_id: str, replication: Dict[str, Any]) -> Dict[str, Any]
    - add_secret_version(secret_name: str, payload: str) -> Dict[str, Any]
    - delete_secret(secret_name: str) -> None
    """

    def __init__(self, project: Optional[str] = None, client: Optional[Any] = None):
        """
        Args:
            project: optional default project id to use when creating secrets.
            client: optional secretmanager client for testing or custom credentials.
        """
        if secretmanager is None:
            raise RuntimeError("google-cloud-secret-manager not available. Install google-cloud-secret-manager package.")
        try:
            self.client = client or secretmanager.SecretManagerServiceClient()
        except DefaultCredentialsError as exc:
            LOG.exception("Failed to initialize Secret Manager client - credentials not found")
            raise
        self.project = project

    def access_secret(self, secret_name: str, version: str = "latest") -> str:
        """
        Access the secret payload for a given secret resource name.

        Args:
            secret_name: full secret resource name or short id (if project configured).
                         Accepts either "projects/<proj>/secrets/<id>" or "<id>" when project provided.
            version: secret version, default 'latest'

        Returns:
            Secret payload as string.

        Raises:
            google.api_core.exceptions.GoogleAPICallError (or underlying) on failure.
        """
        name = self._full_name(secret_name, version)
        try:
            response = self.client.access_secret_version(name=name)
            payload = response.payload.data.decode("utf-8")
            return payload
        except Exception:
            LOG.exception("GCP Secret Manager access_secret failed for %s", name)
            raise

    def create_secret(self, parent: str, secret_id: str, replication: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Create a new secret resource.

        Args:
            parent: project resource e.g. "projects/<project-id>"
            secret_id: short secret id
            replication: replication policy dict (see google client docs)

        Returns:
            Created secret proto (as dict-like object).
        """
        if replication is None:
            replication = {"automatic": {}}
        try:
            secret = {"replication": replication}
            resp = self.client.create_secret(parent=parent, secret_id=secret_id, secret=secret)
            return {"name": resp.name}
        except Exception:
            LOG.exception("GCP Secret Manager create_secret failed for %s/%s", parent, secret_id)
            raise

    def add_secret_version(self, secret_name: str, payload: str) -> Dict[str, Any]:
        """
        Add a new secret version with given payload.

        Args:
            secret_name: full secret resource name, e.g. "projects/<proj>/secrets/<id>"
            payload: secret string

        Returns:
            Response dict with version name.
        """
        try:
            parent = secret_name
            if not secret_name.startswith("projects/"):
                # if caller passed short id and project is configured
                parent = f"projects/{self.project}/secrets/{secret_name}"
            payload_bytes = payload.encode("utf-8")
            resp = self.client.add_secret_version(parent=parent, payload={"data": payload_bytes})
            return {"name": resp.name}
        except Exception:
            LOG.exception("GCP Secret Manager add_secret_version failed for %s", secret_name)
            raise

    def delete_secret(self, secret_name: str) -> None:
        """
        Delete a secret and all versions.

        Args:
            secret_name: full resource name or short id (project required).
        """
        try:
            name = secret_name if secret_name.startswith("projects/") else f"projects/{self.project}/secrets/{secret_name}"
            self.client.delete_secret(name=name)
        except Exception:
            LOG.exception("GCP Secret Manager delete_secret failed for %s", secret_name)
            raise

    def _full_name(self, secret_name: str, version: str) -> str:
        """
        Build a full resource name for secret version.
        """
        if secret_name.startswith("projects/"):
            return f"{secret_name}/versions/{version}"
        if self.project is None:
            raise ValueError("Project not configured; provide full secret resource name or set project in constructor.")
        return f"projects/{self.project}/secrets/{secret_name}/versions/{version}"
