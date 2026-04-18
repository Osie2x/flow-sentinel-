"""SQLite persistence and Power BI export helpers."""

from __future__ import annotations

import logging
import sqlite3
from pathlib import Path

import pandas as pd

from flowsentinel import config


logger = logging.getLogger(__name__)


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    db_path = Path(db_path or config.DB_PATH)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.execute("PRAGMA journal_mode=WAL;")
    connection.execute("PRAGMA foreign_keys=ON;")
    return connection


def _execute_sql_file(connection: sqlite3.Connection, sql_path: Path) -> None:
    connection.executescript(sql_path.read_text(encoding="utf-8"))
    connection.commit()


class Loader:
    """Write pipeline outputs to SQLite and export analytics marts."""

    def __init__(self, db_path: Path | None = None):
        self.db_path = Path(db_path or config.DB_PATH)
        self.conn = get_connection(self.db_path)
        self.initialise_schema()

    def initialise_schema(self) -> None:
        _execute_sql_file(self.conn, config.SQL_DIR / "schema.sql")
        logger.debug("Schema initialized from SQL script")

    def refresh_views(self) -> None:
        _execute_sql_file(self.conn, config.SQL_DIR / "analytics_views.sql")
        logger.debug("Analytics views refreshed")

    def load_records(self, df: pd.DataFrame) -> int:
        columns = [
            "record_id",
            "timestamp",
            "category",
            "department",
            "amount",
            "quantity",
            "status",
            "region",
            "customer_id",
            "processing_time_ms",
            "date",
            "hour_of_day",
            "amount_bucket",
            "is_complete",
            "has_violation",
            "is_anomaly",
        ]
        subset = df[[column for column in columns if column in df.columns]].copy()
        if subset.empty:
            return 0

        for column in ("timestamp", "date", "amount_bucket"):
            if column in subset.columns:
                subset[column] = subset[column].astype(str)

        for column in ("is_complete", "has_violation", "is_anomaly"):
            if column in subset.columns:
                subset[column] = subset[column].astype(int)

        subset.to_sql("records", self.conn, if_exists="append", index=False)
        self.conn.commit()
        return len(subset)

    def load_exceptions(self, exceptions: list[dict]) -> None:
        if exceptions:
            pd.DataFrame(exceptions).to_sql("exceptions", self.conn, if_exists="append", index=False)
            self.conn.commit()

    def load_anomalies(self, anomalies: list[dict]) -> None:
        if anomalies:
            pd.DataFrame(anomalies).to_sql("anomalies", self.conn, if_exists="append", index=False)
            self.conn.commit()

    def save_health_score(self, score_record: dict) -> None:
        pd.DataFrame([score_record]).to_sql("health_scores", self.conn, if_exists="append", index=False)
        self.conn.commit()

    def log_pipeline_run(self, run_record: dict) -> None:
        pd.DataFrame([run_record]).to_sql("pipeline_runs", self.conn, if_exists="append", index=False)
        self.conn.commit()

    def export_powerbi_tables(self, output_dir: Path) -> list[Path]:
        self.refresh_views()
        output_dir.mkdir(parents=True, exist_ok=True)
        exported_paths: list[Path] = []

        for name, sql in config.POWERBI_EXPORT_TABLES.items():
            frame = pd.read_sql_query(sql, self.conn)
            path = output_dir / f"{name}.csv"
            frame.to_csv(path, index=False)
            exported_paths.append(path)

        logger.info("Exported %s Power BI-ready datasets", len(exported_paths))
        return exported_paths

    def close(self) -> None:
        self.conn.close()
