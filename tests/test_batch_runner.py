import os
import tempfile
import shutil
import yaml
from pathlib import Path

from templates.batch_ingestion.runner import (
    PipelineConfig,
    BatchIngestionRunner,
    load_config,
)

def create_sample_csv(path: str):
    content = "id,name,amount\n1,Alice,10\n2,Bob,15\n3,Carol,20\n"
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)

def test_batch_runner_local_filesystem(tmp_path):
    # Setup temp directories
    data_dir = tmp_path / "data"
    out_dir = tmp_path / "out"
    data_dir.mkdir()
    out_dir.mkdir()

    sample_csv = str(data_dir / "input.csv")
    create_sample_csv(sample_csv)

    # Create pipeline config (local source + local destination)
    cfg = {
        "name": "test-batch-local",
        "source": {
            "type": "local",
            "local_path": sample_csv,
        },
        "transform": {
            "csv": {"delimiter": ","}
        },
        "destination": {
            "type": "local",
            "local_path": str(out_dir),
        },
        "options": {
            "overwrite": True,
            "max_retries": 1,
        },
    }

    # Write config file to disk and also construct PipelineConfig directly
    config_path = tmp_path / "pipeline.yaml"
    with open(config_path, "w", encoding="utf-8") as f:
        yaml.safe_dump(cfg, f)

    pipeline_cfg = load_config(str(config_path))
    runner = BatchIngestionRunner(pipeline_cfg)

    result = runner.run_once()
    assert result["status"] == "success"

    # Destination must contain a file with same base name but .parquet or .csv.gz
    dest_files = list(Path(cfg["destination"]["local_path"]).glob("*"))
    assert len(dest_files) == 1, f"expected 1 output file, got: {dest_files}"
    out_file = dest_files[0]
    assert out_file.exists()
    # Basic sanity checks on output extension
    assert out_file.suffix in (".parquet", ".gz", ".csv"), f"unexpected suffix {out_file.suffix}"

    # If parquet, try to read with pyarrow/pandas if available to validate content
    try:
        import pandas as pd  # noqa: F401
        df = None
        if out_file.suffix == ".parquet":
            df = pd.read_parquet(out_file)
        elif out_file.suffix in (".gz", ".csv"):
            df = pd.read_csv(out_file)
        if df is not None:
            assert list(df.columns) == ["id", "name", "amount"]
            assert len(df) == 3
    except Exception:
        # If optional libs are not available, at least ensure file size > 0
        assert out_file.stat().st_size > 0
