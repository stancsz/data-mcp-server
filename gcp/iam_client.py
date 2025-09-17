"""
GCP IAM / Service Account helpers for DataMCP

Purpose:
- Provide focused helpers to manage service accounts and IAM bindings via `gcloud` CLI.
- Return structured results (CommandResult-like dicts) and rely on `tools/runner.run_cmd` for safe execution and dry-run support.
- Designed for MCP tools that need to create SA, generate keys, and grant roles.

Why use gcloud:
- Creating service accounts and keys is commonly done with `gcloud` in CI/automation contexts.
- Using `gcloud` avoids adding complex google-api client wiring and keeps behavior reproducible.

Prereqs:
- `gcloud` must be installed and authenticated on the host where these helpers run.
- For automated CI, use Workload Identity or service account with limited scope.

Usage (example):
    from gcp.iam_client import GCPIAM
    iam = GCPIAM()
    res = iam.create_service_account("my-project", "my-sa", "My SA for MCP", dry_run=True)
    # res is a dict with rc, stdout, stderr

Design notes for AI/MCP tools:
- All methods accept dry_run: True by default to prevent accidental modifications.
- Methods return dict: { "rc": int, "stdout": str, "stderr": str, "cmd": str }
- Callers should persist audit logs and mask secrets (service account keys) before exposing outputs.
"""

from __future__ import annotations
import json
import logging
from typing import Optional, Dict, Any

from tools.runner import run_cmd, CommandResult

LOG = logging.getLogger(__name__)


class GCPIAM:
    """
    Helper wrapper that uses `gcloud` to manage IAM/service accounts.

    Methods:
    - create_service_account(project, sa_id, display_name, dry_run=True) -> dict
    - delete_service_account(project, sa_email, dry_run=True) -> dict
    - create_service_account_key(sa_email, key_output_path=None, dry_run=True) -> dict
    - add_iam_policy_binding(project, member, role, dry_run=True) -> dict
    - remove_iam_policy_binding(project, member, role, dry_run=True) -> dict
    """

    def __init__(self, gcloud_bin: str = "gcloud"):
        self.gcloud = gcloud_bin

    def create_service_account(self, project: str, sa_id: str, display_name: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Create a service account.
        sa_id: short id (no @), result email: {sa_id}@{project}.iam.gserviceaccount.com
        """
        cmd = [self.gcloud, "iam", "service-accounts", "create", sa_id, "--project", project, "--display-name", display_name]
        res: CommandResult = run_cmd(cmd, dry_run=dry_run)
        return {"rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "cmd": res.cmd}

    def delete_service_account(self, project: str, sa_email: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Delete a service account by email (full resource).
        """
        cmd = [self.gcloud, "iam", "service-accounts", "delete", sa_email, "--project", project, "--quiet"]
        res: CommandResult = run_cmd(cmd, dry_run=dry_run)
        return {"rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "cmd": res.cmd}

    def create_service_account_key(self, sa_email: str, key_output_path: Optional[str] = None, dry_run: bool = True) -> Dict[str, Any]:
        """
        Create a key for the service account.
        If key_output_path is provided, the key JSON will be written there by gcloud.
        Returns stdout/stderr; callers should securely handle/download the file.
        """
        cmd = [self.gcloud, "iam", "service-accounts", "keys", "create"]
        if key_output_path:
            cmd += [key_output_path]
        else:
            # write to stdout as JSON if gcloud supports --format json; we still call create to create a local file if path omitted gcloud errors
            # Safer to require a path, but we provide default temp-file behavior not implemented here.
            cmd += ["-"]
        cmd += ["--iam-account", sa_email]
        res: CommandResult = run_cmd(cmd, dry_run=dry_run)
        return {"rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "cmd": res.cmd}

    def add_iam_policy_binding(self, project: str, member: str, role: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Add an IAM policy binding to the project.
        member examples: "serviceAccount:sa@project.iam.gserviceaccount.com", "user:foo@example.com", "group:..."
        role example: "roles/storage.admin"
        """
        cmd = [self.gcloud, "projects", "add-iam-policy-binding", project, "--member", member, "--role", role]
        res: CommandResult = run_cmd(cmd, dry_run=dry_run)
        return {"rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "cmd": res.cmd}

    def remove_iam_policy_binding(self, project: str, member: str, role: str, dry_run: bool = True) -> Dict[str, Any]:
        """
        Remove an IAM policy binding from the project.
        """
        cmd = [self.gcloud, "projects", "remove-iam-policy-binding", project, "--member", member, "--role", role]
        res: CommandResult = run_cmd(cmd, dry_run=dry_run)
        return {"rc": res.returncode, "stdout": res.stdout, "stderr": res.stderr, "cmd": res.cmd}
