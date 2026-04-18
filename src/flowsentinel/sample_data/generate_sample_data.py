"""Generate synthetic business records for demos and tests."""

from __future__ import annotations

import argparse
from datetime import datetime, timedelta, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from flowsentinel.config import DATA_RAW, SOURCE_FILE, VALID_DEPARTMENTS, VALID_REGIONS, VALID_STATUSES


def generate_records(record_count: int, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    start = datetime.now(timezone.utc) - timedelta(days=30)

    statuses = sorted(VALID_STATUSES)
    departments = sorted(VALID_DEPARTMENTS)
    regions = sorted(VALID_REGIONS)
    categories = ["ORDER", "INVOICE", "RETURN", "SHIPMENT", "PAYMENT"]

    frame = pd.DataFrame(
        {
            "record_id": [f"REC-{index:07d}" for index in range(1, record_count + 1)],
            "timestamp": [(start + timedelta(seconds=int(offset))).isoformat() for offset in rng.integers(0, 30 * 24 * 3600, size=record_count)],
            "category": rng.choice(categories, size=record_count),
            "department": rng.choice(departments, size=record_count),
            "amount": rng.normal(325.0, 180.0, size=record_count).round(2),
            "quantity": rng.integers(1, 15, size=record_count),
            "status": rng.choice(statuses, size=record_count, p=[0.76, 0.14, 0.06, 0.04]),
            "region": rng.choice(regions, size=record_count),
            "customer_id": [f"CUST-{value:05d}" for value in rng.integers(1, 15_000, size=record_count)],
            "processing_time_ms": rng.normal(2400.0, 900.0, size=record_count).round(2),
        }
    )

    anomaly_size = max(10, record_count // 100)
    anomaly_indices = rng.choice(frame.index, size=anomaly_size, replace=False)
    first_cut = anomaly_size // 3
    second_cut = (2 * anomaly_size) // 3

    negative_amount_idx = anomaly_indices[:first_cut]
    slow_processing_idx = anomaly_indices[first_cut:second_cut]
    invalid_status_idx = anomaly_indices[second_cut:]

    if len(negative_amount_idx):
        frame.loc[negative_amount_idx, "amount"] = rng.normal(-25.0, 15.0, size=len(negative_amount_idx)).round(2)
    if len(slow_processing_idx):
        frame.loc[slow_processing_idx, "processing_time_ms"] = rng.normal(42_000.0, 5_000.0, size=len(slow_processing_idx)).round(2)
    if len(invalid_status_idx):
        frame.loc[invalid_status_idx, "status"] = "UNKNOWN"

    return frame


def write_sample_file(record_count: int, output_path: Path = SOURCE_FILE) -> Path:
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    frame = generate_records(record_count)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate synthetic FlowSentinel source data")
    parser.add_argument("--records", type=int, default=50_000, help="Number of records to generate")
    parser.add_argument("--output", type=Path, default=SOURCE_FILE, help="Destination CSV path")
    args = parser.parse_args()

    output_path = write_sample_file(args.records, args.output)
    print(f"Generated {args.records:,} records at {output_path}")


if __name__ == "__main__":
    main()
