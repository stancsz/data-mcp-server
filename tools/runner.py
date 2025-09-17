"""
Safe command runner for executing CLI tools (terraform, helm, gcloud, argocd) from MCP tools.

Features:
- dry_run flag to avoid destructive actions
- capture stdout/stderr
- return structured result
- basic timeout support
- logging of commands (caller should handle storing audit logs)
"""

from __future__ import annotations
import shlex
import subprocess
import logging
from dataclasses import dataclass
from typing import Optional, Sequence, Dict, Any

LOG = logging.getLogger(__name__)


@dataclass
class CommandResult:
    returncode: int
    stdout: str
    stderr: str
    cmd: str
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None


def run_cmd(
    cmd: Sequence[str] | str,
    cwd: Optional[str] = None,
    env: Optional[Dict[str, str]] = None,
    dry_run: bool = False,
    timeout: Optional[int] = None,
    check: bool = False,
) -> CommandResult:
    """
    Execute a command safely.

    - cmd: list of args or shell string. If string provided, it will be split using shlex.
    - cwd: working directory to run in
    - env: environment variables to pass (merged with current os.environ by caller if desired)
    - dry_run: if True, the command will not be executed; a simulated successful result is returned
    - timeout: seconds to wait before killing the process
    - check: if True, raise CalledProcessError on non-zero exit (subprocess.CalledProcessError)
    """

    if isinstance(cmd, str):
        cmd_list = shlex.split(cmd)
        cmd_str = cmd
    else:
        cmd_list = list(cmd)
        cmd_str = " ".join(shlex.quote(c) for c in cmd_list)

    LOG.debug("Running command (dry_run=%s): %s (cwd=%s)", dry_run, cmd_str, cwd)

    if dry_run:
        # Return a simulated success result with empty output to indicate what would be run.
        return CommandResult(returncode=0, stdout=f"[dry_run] {cmd_str}", stderr="", cmd=cmd_str, cwd=cwd, env=env)

    try:
        proc = subprocess.run(
            cmd_list,
            cwd=cwd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout,
            check=check,
            text=True,
        )
        stdout = proc.stdout or ""
        stderr = proc.stderr or ""
        return CommandResult(returncode=proc.returncode, stdout=stdout, stderr=stderr, cmd=cmd_str, cwd=cwd, env=env)
    except subprocess.CalledProcessError as exc:
        # CalledProcessError contains returncode, stdout, stderr
        out = getattr(exc, "stdout", "") or ""
        err = getattr(exc, "stderr", "") or ""
        LOG.error("Command failed: %s (rc=%s) stdout=%s stderr=%s", cmd_str, exc.returncode, out, err)
        return CommandResult(returncode=exc.returncode or 1, stdout=out, stderr=err, cmd=cmd_str, cwd=cwd, env=env)
    except subprocess.TimeoutExpired as exc:
        out = getattr(exc, "stdout", "") or ""
        err = getattr(exc, "stderr", "") or ""
        LOG.error("Command timed out: %s (timeout=%s)", cmd_str, timeout)
        return CommandResult(returncode=124, stdout=out, stderr=(err or f"timeout after {timeout}s"), cmd=cmd_str, cwd=cwd, env=env)
    except Exception as exc:  # fallback
        LOG.exception("Unexpected error running command: %s", cmd_str)
        return CommandResult(returncode=1, stdout="", stderr=str(exc), cmd=cmd_str, cwd=cwd, env=env)
