"""ML and statistical anomaly detection."""

from __future__ import annotations

import logging

import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from flowsentinel.config import ANOMALY_FIELDS, ISOLATION_CONTAMINATION, ZSCORE_THRESHOLD


logger = logging.getLogger(__name__)


class AnomalyDetector:
    """Apply Isolation Forest and per-column z-score checks."""

    def __init__(
        self,
        fields: list[str] = ANOMALY_FIELDS,
        contamination: float = ISOLATION_CONTAMINATION,
        zscore_threshold: float = ZSCORE_THRESHOLD,
    ):
        self.fields = fields
        self.contamination = contamination
        self.zscore_threshold = zscore_threshold

    def detect(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
        anomalies: list[dict] = []
        available_fields = [field for field in self.fields if field in df.columns]

        if not available_fields or df.empty:
            flagged = df.copy()
            flagged["is_anomaly"] = False
            return flagged, anomalies

        numeric_df = df[available_fields].apply(pd.to_numeric, errors="coerce").fillna(0)
        scaled = StandardScaler().fit_transform(numeric_df)

        isolation_forest = IsolationForest(
            contamination=self.contamination,
            random_state=42,
            n_jobs=-1,
        )
        labels = isolation_forest.fit_predict(scaled)
        scores = isolation_forest.score_samples(scaled)

        for idx in df.index[labels == -1]:
            anomalies.append(
                {
                    "record_id": str(df.at[idx, "record_id"]),
                    "detector": "isolation_forest",
                    "field": ",".join(available_fields),
                    "score": round(float(scores[df.index.get_loc(idx)]), 4),
                }
            )

        for field in available_fields:
            series = numeric_df[field]
            std = float(series.std())
            if std == 0:
                continue
            z_scores = (series - float(series.mean())) / std
            z_mask = z_scores.abs() > self.zscore_threshold
            for idx in df.index[z_mask]:
                anomalies.append(
                    {
                        "record_id": str(df.at[idx, "record_id"]),
                        "detector": "zscore",
                        "field": field,
                        "score": round(float(z_scores.loc[idx]), 4),
                    }
                )

        anomalous_ids = {anomaly["record_id"] for anomaly in anomalies}
        flagged = df.copy()
        flagged["is_anomaly"] = flagged["record_id"].astype(str).isin(anomalous_ids)
        logger.info("Anomaly detection flagged %s records", len(anomalous_ids))
        return flagged, anomalies
