"""Chunked extraction for source records."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Generator

import pandas as pd

from flowsentinel import config


logger = logging.getLogger(__name__)


class Extractor:
    """Read the source CSV in chunks with basic schema validation."""

    def __init__(self, source_path: Path | None = None, batch_size: int | None = None):
        self.source_path = Path(source_path or config.SOURCE_FILE)
        self.batch_size = batch_size or config.BATCH_SIZE

    def _validate_columns(self, df: pd.DataFrame) -> None:
        expected = set(config.SCHEMA.keys())
        actual = set(df.columns)
        missing = expected - actual
        if missing:
            raise ValueError(
                f"Source file is missing expected columns: {sorted(missing)}. "
                f"Found columns: {sorted(actual)}"
            )

    def extract(self) -> Generator[pd.DataFrame, None, None]:
        if not self.source_path.exists():
            raise FileNotFoundError(
                f"Source file not found: {self.source_path}\n"
                "Run: python -m flowsentinel.sample_data.generate_sample_data --records 50000"
            )

        total_rows = 0
        first_chunk = True
        logger.info("Starting extraction from %s", self.source_path)

        for chunk in pd.read_csv(self.source_path, chunksize=self.batch_size, low_memory=False):
            if first_chunk:
                self._validate_columns(chunk)
                first_chunk = False

            total_rows += len(chunk)
            logger.debug("Extracted chunk with %s rows (%s total)", len(chunk), total_rows)
            yield chunk

        logger.info("Extraction complete: %s rows", total_rows)
