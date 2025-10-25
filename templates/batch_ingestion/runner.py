#!/usr/bin/env python3
# This file is a duplicate copy of templates/batch-ingestion/runner.py
# placed under a valid Python package path `templates.batch_ingestion`
# so tests and imports can resolve it as a module.
from __future__ import annotations
import argparse
import logging
import os
import sys
import tempfile
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any

import yaml

# Optional imports
try:
    import boto3
    from botocore.exceptions import BotoCoreError, ClientError
except Exception:
    boto3 = None
    BotoCoreError = ClientError = Exception  # type: ignore

try:
    import pandas as pd
except Exception:
    pd = None

# Parquet backend optional
_parquet_available = False
try:
    import pyarrow  # noqa: F401
    _parquet_available = True
except Exception:
    try:
        import fastparquet  # noqa: F401
        _parquet_available = True
    except Exception:
        _parquet_available = False

logger = logging.getLogger("batch_ingest")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

def retry(fn, max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """Simple retry wrapper with exponential backoff."""
    def wrapper(*args, **kwargs):
        tries = 0
        while True:
            try:
                return fn(*args, **kwargs)
            except Exception as e:
                tries += 1
                if tries > max_retries:
                    logger.exception("Exceeded retries for %s", fn.__name__)
                    raise
                sleep = delay * (backoff ** (tries - 1))
                logger.warning("Retry %d/%d after error: %s (sleep %.1fs)", tries, max_retries, e, sleep)
                time.sleep(sleep)
    return wrapper

class StorageAdapter:
    def exists(self, path: str) -> bool:
        raise NotImplementedError

    def download(self, remote_path: str, local_path: str):
        raise NotImplementedError

    def upload(self, local_path: str, remote_path: str):
        raise NotImplementedError

    def list(self, prefix: str):
        raise NotImplementedError

class LocalStorageAdapter(StorageAdapter):
    def exists(self, path: str) -> bool:
        return os.path.exists(path)

    def download(self, remote_path: str, local_path: str):
        # remote_path is treated as a filesystem path here
        if not os.path.exists(remote_path):
            raise FileNotFoundError(f"Local source not found: {remote_path}")
        logger.info("Copying local file %s -> %s", remote_path, local_path)
        with open(remote_path, "rb") as rf, open(local_path, "wb") as wf:
            wf.write(rf.read())

    def upload(self, local_path: str, remote_path: str):
        os.makedirs(os.path.dirname(remote_path) or ".", exist_ok=True)
        logger.info("Writing local file %s -> %s", local_path, remote_path)
        with open(local_path, "rb") as rf, open(remote_path, "wb") as wf:
            wf.write(rf.read())

    def list(self, prefix: str):
        results = []
        if os.path.isdir(prefix):
            for root, _, files in os.walk(prefix):
                for f in files:
                    results.append(os.path.join(root, f))
        elif os.path.isfile(prefix):
            results.append(prefix)
        return results

class S3StorageAdapter(StorageAdapter):
    def __init__(self, s3_client=None):
        if boto3 is None:
            raise RuntimeError("boto3 is required for S3 operations but it's not installed")
        self.s3 = s3_client or boto3.client("s3")

    def _parse_s3_path(self, s3_path: str):
        # Accept either "bucket/key" or "s3://bucket/key"
        if s3_path.startswith("s3://"):
            s3_path = s3_path[5:]
        parts = s3_path.split("/", 1)
        if len(parts) == 1:
            return parts[0], ""
        return parts[0], parts[1]

    def exists(self, s3_path: str) -> bool:
        bucket, key = self._parse_s3_path(s3_path)
        try:
            self.s3.head_object(Bucket=bucket, Key=key)
            return True
        except ClientError as e:
            if getattr(e, "response", {}).get("Error", {}).get("Code") in ("404", "NoSuchKey", "NotFound"):
                return False
            raise

    @retry
    def download(self, s3_path: str, local_path: str):
        bucket, key = self._parse_s3_path(s3_path)
        os.makedirs(os.path.dirname(local_path) or ".", exist_ok=True)
        logger.info("Downloading s3://%s/%s -> %s", bucket, key, local_path)
        try:
            self.s3.download_file(bucket, key, local_path)
        except (BotoCoreError, ClientError):
            logger.exception("S3 download failed for s3://%s/%s", bucket, key)
            raise

    @retry
    def upload(self, local_path: str, s3_path: str):
        bucket, key = self._parse_s3_path(s3_path)
        logger.info("Uploading %s -> s3://%s/%s", local_path, bucket, key)
        try:
            self.s3.upload_file(local_path, bucket, key)
        except (BotoCoreError, ClientError):
            logger.exception("S3 upload failed for s3://%s/%s", bucket, key)
            raise

    def list(self, prefix: str):
        bucket, key_prefix = self._parse_s3_path(prefix)
        paginator = self.s3.get_paginator("list_objects_v2")
        results = []
        for page in paginator.paginate(Bucket=bucket, Prefix=key_prefix):
            for obj in page.get("Contents", []):
                results.append(f"s3://{bucket}/{obj['Key']}")
        return results

@dataclass
class PipelineConfig:
    name: str
    source: Dict[str, Any]
    transform: Dict[str, Any]
    destination: Dict[str, Any]
    options: Dict[str, Any]

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "PipelineConfig":
        return PipelineConfig(
            name=d.get("name", "batch"),
            source=d.get("source", {}),
            transform=d.get("transform", {}),
            destination=d.get("destination", {}),
            options=d.get("options", {}),
        )

class BatchIngestionRunner:
    def __init__(self, config: PipelineConfig):
        self.config = config
        self.options = config.options or {}
        self.max_retries = int(self.options.get("max_retries", 3))
        self.overwrite = bool(self.options.get("overwrite", False))

        # Choose adapters based on config
        self.source_adapter = self._adapter_for(self.config.source)
        self.dest_adapter = self._adapter_for(self.config.destination)

    def _adapter_for(self, spec: Dict[str, Any]) -> StorageAdapter:
        t = spec.get("type", "local")
        if t == "s3":
            return S3StorageAdapter()
        return LocalStorageAdapter()

    def _local_temp(self, suffix: str = "") -> str:
        fd, path = tempfile.mkstemp(suffix=suffix)
        os.close(fd)
        return path

    def _derive_destination_key(self, source_path: str) -> str:
        # Simple idempotency: use source filename with .parquet under destination prefix
        src_name = os.path.basename(source_path)
        dest_prefix = self.config.destination.get("s3_key_prefix") or self.config.destination.get("local_path") or ""
        dest_name = os.path.splitext(src_name)[0] + ".parquet"
        if self.config.destination.get("type") == "s3":
            # ensure prefix ends with /
            if dest_prefix and not dest_prefix.endswith("/"):
                dest_prefix = dest_prefix + "/"
            return f"s3://{self.config.destination.get('s3_bucket')}/{dest_prefix}{dest_name}"
        else:
            os.makedirs(dest_prefix or ".", exist_ok=True)
            return os.path.join(dest_prefix or ".", dest_name)

    def run_once(self):
        # Determine source path(s)
        src = self.config.source
        t = src.get("type", "local")
        if t == "s3":
            # build s3 path
            bucket = src.get("s3_bucket")
            key = src.get("s3_key")
            if not bucket or not key:
                raise ValueError("s3 source requires s3_bucket and s3_key")
            source_path = f"s3://{bucket}/{key}"
        else:
            source_path = src.get("local_path")
            if not source_path:
                raise ValueError("local source requires local_path")

        dest_path = self._derive_destination_key(source_path)
        logger.info("Source: %s, Destination: %s", source_path, dest_path)

        # Idempotency: skip if dest exists and not overwrite
        if self.dest_adapter.exists(dest_path) and not self.overwrite:
            logger.info("Destination %s exists and overwrite is false — skipping", dest_path)
            return {"status": "skipped", "dest": dest_path}

        # Download source to temp
        tmp_src = self._local_temp(suffix=os.path.splitext(source_path)[1] or "")
        try:
            self.source_adapter.download(source_path, tmp_src)
        except Exception:
            logger.exception("Failed to download source %s", source_path)
            raise

        # Transform
        try:
            tmp_out = self._transform(tmp_src)
        except Exception:
            logger.exception("Transform failed for %s", tmp_src)
            raise

        # Upload
        try:
            self.dest_adapter.upload(tmp_out, dest_path)
        except Exception:
            logger.exception("Failed to upload to destination %s", dest_path)
            raise
        finally:
            # cleanup
            for p in (tmp_src, tmp_out):
                try:
                    if os.path.exists(p):
                        os.remove(p)
                except Exception:
                    logger.warning("Failed to cleanup temp file %s", p)

        logger.info("Ingestion successful: %s", dest_path)
        return {"status": "success", "dest": dest_path}

    def _transform(self, local_src_path: str) -> str:
        """Transform CSV -> Parquet (if possible). Return local path to output file."""
        transform_spec = self.config.transform or {}
        csv_spec = transform_spec.get("csv", {})
        delimiter = csv_spec.get("delimiter", ",")
        if pd is None:
            # No pandas installed — fallback to copying file (compress)
            logger.warning("pandas not available; performing passthrough copy (gz)")
            out_path = local_src_path + ".gz"
            import gzip
            with open(local_src_path, "rb") as fr, gzip.open(out_path, "wb") as fw:
                fw.write(fr.read())
            return out_path

        # Read CSV
        logger.info("Reading CSV %s", local_src_path)
        try:
            df = pd.read_csv(local_src_path, sep=delimiter)
        except Exception:
            logger.exception("Failed to read CSV %s", local_src_path)
            raise

        # Simple schema checks & cast safety can be added here
        out_path = self._local_temp(suffix=".parquet" if _parquet_available else ".csv.gz")
        if _parquet_available:
            logger.info("Writing Parquet to %s", out_path)
            try:
                df.to_parquet(out_path, index=False)
            except Exception:
                logger.exception("Failed to write parquet, falling back to gz CSV")
                import gzip
                out_path = self._local_temp(suffix=".csv.gz")
                with gzip.open(out_path, "wb") as fw:
                    fw.write(df.to_csv(index=False).encode("utf-8"))
        else:
            logger.warning("Parquet backend not available; writing gzipped CSV to %s", out_path)
            import gzip
            with gzip.open(out_path, "wb") as fw:
                fw.write(df.to_csv(index=False).encode("utf-8"))
        return out_path

def load_config(path: str) -> PipelineConfig:
    with open(path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)
    return PipelineConfig.from_dict(raw)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=str, required=True, help="Path to pipeline YAML config")
    args = parser.parse_args()
    cfg = load_config(args.config)
    runner = BatchIngestionRunner(cfg)
    res = runner.run_once()
    logger.info("Run result: %s", res)

if __name__ == "__main__":
    main()
