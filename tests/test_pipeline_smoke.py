import os
from importlib import reload
from pathlib import Path

from flowsentinel.sample_data.generate_sample_data import write_sample_file


def test_pipeline_smoke(tmp_path: Path):
    source_path = tmp_path / "sample.csv"
    db_path = tmp_path / "flowsentinel.db"
    output_dir = tmp_path / "processed"
    output_dir.mkdir()

    write_sample_file(250, source_path)

    os.environ["FLOWSENTINEL_SOURCE_FILE"] = str(source_path)
    os.environ["FLOWSENTINEL_DB_PATH"] = str(db_path)

    import flowsentinel.config as config
    import flowsentinel.pipeline as pipeline

    reload(config)
    reload(pipeline)

    result = pipeline.run_pipeline(dry_run=True, generate_pdf=False)

    assert result["status"] == "SUCCESS"
    assert db_path.exists()
