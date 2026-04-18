"""Transform and enrich incoming records."""

from __future__ import annotations

import logging

import pandas as pd


logger = logging.getLogger(__name__)


class Transformer:
    """Apply type coercion, normalization, and enrichment."""

    def transform(self, df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
        metrics: dict[str, float | int] = {"rows_in": len(df)}
        df = df.copy()

        str_fields = ["record_id", "category", "department", "status", "region", "customer_id"]
        for column in str_fields:
            if column in df.columns:
                df[column] = df[column].astype("string").str.strip().str.upper()

        df["amount"] = pd.to_numeric(df["amount"], errors="coerce")
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
        df["processing_time_ms"] = pd.to_numeric(df["processing_time_ms"], errors="coerce")
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce", utc=True)

        critical_fields = ["record_id", "timestamp", "amount"]
        pre_drop = len(df)
        df = df.dropna(subset=critical_fields).copy()
        metrics["dropped_critical_null"] = pre_drop - len(df)

        df["date"] = df["timestamp"].dt.date.astype("string")
        df["hour_of_day"] = df["timestamp"].dt.hour
        df["amount_bucket"] = pd.cut(
            df["amount"],
            bins=[-float("inf"), 0, 100, 1_000, 10_000, float("inf")],
            labels=["NEGATIVE", "MICRO", "SMALL", "MEDIUM", "LARGE"],
        ).astype("string")

        optional_fields = ["customer_id", "region", "department"]
        completeness_source = df[optional_fields].fillna("")
        df["is_complete"] = completeness_source.apply(lambda row: all(str(value).strip() != "" for value in row), axis=1)

        metrics["rows_out"] = len(df)
        metrics["incomplete"] = int((~df["is_complete"]).sum())
        metrics["completeness_pct"] = round(float(df["is_complete"].mean() * 100), 2) if len(df) else 0.0

        logger.debug(
            "Transform complete: %s in, %s out, %s%% complete",
            metrics["rows_in"],
            metrics["rows_out"],
            metrics["completeness_pct"],
        )
        return df, metrics

