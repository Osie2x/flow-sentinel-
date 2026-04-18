"""Business rule validation engine."""

from __future__ import annotations

import logging
from typing import Callable

import pandas as pd

from flowsentinel.config import BUSINESS_RULES, VALID_DEPARTMENTS, VALID_STATUSES


logger = logging.getLogger(__name__)


def _check_amount_positive(row: pd.Series) -> bool:
    return pd.notna(row.get("amount")) and float(row["amount"]) > 0


def _check_valid_status(row: pd.Series) -> bool:
    return str(row.get("status", "")).upper() in VALID_STATUSES


def _check_quantity_non_negative(row: pd.Series) -> bool:
    return pd.notna(row.get("quantity")) and int(row["quantity"]) >= 0


def _check_processing_time(row: pd.Series) -> bool:
    return pd.notna(row.get("processing_time_ms")) and float(row["processing_time_ms"]) < 30_000


def _check_valid_department(row: pd.Series) -> bool:
    return str(row.get("department", "")).upper() in VALID_DEPARTMENTS


def _check_record_id_present(row: pd.Series) -> bool:
    value = row.get("record_id")
    return value is not None and str(value).strip() not in ("", "NAN", "NONE", "<NA>")


RULE_EVALUATORS: dict[str, Callable[[pd.Series], bool]] = {
    "RULE_001": _check_amount_positive,
    "RULE_002": _check_valid_status,
    "RULE_003": _check_quantity_non_negative,
    "RULE_004": _check_processing_time,
    "RULE_005": _check_valid_department,
    "RULE_006": _check_record_id_present,
}


class RuleEngine:
    """Evaluate configured rules and return exceptions."""

    def __init__(self, rules: list[dict] = BUSINESS_RULES):
        self.rules = rules

    def validate(self, df: pd.DataFrame) -> tuple[pd.DataFrame, list[dict]]:
        exceptions: list[dict] = []
        violation_ids: set[str] = set()

        for rule in self.rules:
            evaluator = RULE_EVALUATORS.get(rule["id"])
            if evaluator is None:
                logger.warning("No evaluator registered for rule %s", rule["id"])
                continue

            failed_rows = df[~df.apply(evaluator, axis=1)]
            for _, row in failed_rows.iterrows():
                record_id = str(row.get("record_id", "UNKNOWN"))
                violation_ids.add(record_id)
                exceptions.append(
                    {
                        "record_id": record_id,
                        "rule_id": rule["id"],
                        "rule_description": rule["description"],
                        "field": rule["field"],
                        "severity": rule["severity"],
                        "team": rule["team"],
                    }
                )

        validated = df.copy()
        validated["has_violation"] = validated["record_id"].astype(str).isin(violation_ids)
        logger.info("Rule validation flagged %s violations across %s records", len(exceptions), len(violation_ids))
        return validated, exceptions

