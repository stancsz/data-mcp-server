"""
Configuration helpers for DataMCP.

Loads environment variables (optionally from a .env file) and provides
convenience accessors for AWS configuration and defaults.
"""

from __future__ import annotations
import os
from typing import Optional
from pathlib import Path

try:
    # optional dependency for local development; it's ok if not installed
    from dotenv import load_dotenv  # type: ignore
    _HAS_DOTENV = True
except Exception:
    _HAS_DOTENV = False

# Load .env from repository root if present and python-dotenv is installed
ROOT = Path(__file__).resolve().parent
DOTENV_PATH = ROOT / ".env"
if _HAS_DOTENV and DOTENV_PATH.exists():
    load_dotenv(DOTENV_PATH)


def get_env(name: str, default: Optional[str] = None) -> Optional[str]:
    """Get environment variable or default."""
    val = os.environ.get(name, default)
    return val


def aws_access_key_id() -> Optional[str]:
    return get_env("AWS_ACCESS_KEY_ID")


def aws_secret_access_key() -> Optional[str]:
    return get_env("AWS_SECRET_ACCESS_KEY")


def aws_region() -> Optional[str]:
    return get_env("AWS_REGION", "us-east-1")


def default_s3_bucket() -> Optional[str]:
    return get_env("DEFAULT_S3_BUCKET")


def default_dynamo_table() -> Optional[str]:
    return get_env("DEFAULT_DYNAMO_TABLE")


def aws_credentials_dict() -> dict:
    """
    Return a credentials dict suitable for passing to boto3.client/resource
    if explicit credentials are provided via env vars. If not present,
    return an empty dict so that boto3's normal credential resolution will run.
    """
    ak = aws_access_key_id()
    sk = aws_secret_access_key()
    region = aws_region()
    creds: dict = {}
    if ak and sk:
        creds["aws_access_key_id"] = ak
        creds["aws_secret_access_key"] = sk
    if region:
        creds["region_name"] = region
    return creds
