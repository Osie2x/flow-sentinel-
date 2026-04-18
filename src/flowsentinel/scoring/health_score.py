"""Composite daily health score."""

from __future__ import annotations

import logging
from datetime import date

from flowsentinel.config import EXPECTED_DAILY_VOLUME, HEALTH_SCORE_WEIGHTS


logger = logging.getLogger(__name__)


class HealthScoreEngine:
    """Compute a 0-100 process health score."""

    def __init__(self, weights: dict[str, float] = HEALTH_SCORE_WEIGHTS, expected_volume: int = EXPECTED_DAILY_VOLUME):
        self.weights = weights
        self.expected_volume = expected_volume

    def compute(
        self,
        total_records: int,
        completeness_pct: float,
        violation_count: int,
        anomaly_count: int,
        run_date: date | None = None,
    ) -> dict:
        if total_records == 0:
            return self._zero_score(run_date)

        completeness = completeness_pct / 100.0
        error_rate = max(0.0, 1.0 - (violation_count / total_records))
        throughput = min(1.0, total_records / self.expected_volume)
        anomaly_rate = max(0.0, 1.0 - (anomaly_count / total_records))

        composite = (
            completeness * self.weights["completeness"]
            + error_rate * self.weights["error_rate"]
            + throughput * self.weights["throughput"]
            + anomaly_rate * self.weights["anomaly_rate"]
        ) * 100

        score_record = {
            "run_date": str(run_date or date.today()),
            "total_records": total_records,
            "completeness": round(completeness * 100, 2),
            "error_rate": round(error_rate * 100, 2),
            "throughput": round(throughput * 100, 2),
            "anomaly_rate": round(anomaly_rate * 100, 2),
            "composite_score": round(composite, 2),
        }
        logger.info("Composite health score computed: %s", score_record["composite_score"])
        return score_record

    @staticmethod
    def _zero_score(run_date: date | None) -> dict:
        return {
            "run_date": str(run_date or date.today()),
            "total_records": 0,
            "completeness": 0.0,
            "error_rate": 0.0,
            "throughput": 0.0,
            "anomaly_rate": 0.0,
            "composite_score": 0.0,
        }

