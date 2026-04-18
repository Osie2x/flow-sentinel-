"""Route exception alerts to team endpoints."""

from __future__ import annotations

import logging
import time
from datetime import datetime, timezone

import httpx

from flowsentinel.config import (
    ALERT_MAX_RETRIES,
    ALERT_RETRY_BACKOFF_S,
    ALERT_ROUTES,
    ALERT_SEVERITY_THRESHOLD,
)


logger = logging.getLogger(__name__)


class AlertRouter:
    """Dispatch webhook payloads for exceptions above the severity threshold."""

    def __init__(
        self,
        routes: dict[str, str] = ALERT_ROUTES,
        severity_threshold: set[str] = ALERT_SEVERITY_THRESHOLD,
        max_retries: int = ALERT_MAX_RETRIES,
        retry_backoff_s: int = ALERT_RETRY_BACKOFF_S,
        dry_run: bool = True,
    ):
        self.routes = routes
        self.severity_threshold = severity_threshold
        self.max_retries = max_retries
        self.retry_backoff_s = retry_backoff_s
        self.dry_run = dry_run

    def _build_payload(self, exception: dict) -> dict:
        return {
            "source": "FlowSentinel",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "record_id": exception.get("record_id"),
            "rule_id": exception.get("rule_id"),
            "description": exception.get("rule_description"),
            "field": exception.get("field"),
            "severity": exception.get("severity"),
            "team": exception.get("team"),
        }

    def _post_with_retry(self, url: str, payload: dict) -> bool:
        for attempt in range(1, self.max_retries + 1):
            try:
                response = httpx.post(url, json=payload, timeout=5.0)
                if response.is_success:
                    return True
                logger.warning("Webhook returned %s on attempt %s", response.status_code, attempt)
            except httpx.RequestError as error:
                logger.warning("Webhook request failed on attempt %s: %s", attempt, error)

            if attempt < self.max_retries:
                time.sleep(self.retry_backoff_s * attempt)
        return False

    def route(self, exceptions: list[dict]) -> dict:
        summary = {"dispatched": 0, "failed": 0, "skipped": 0, "by_team": {}}

        for exception in exceptions:
            severity = str(exception.get("severity", "LOW")).upper()
            team = str(exception.get("team", "operations")).lower()

            if severity not in self.severity_threshold:
                summary["skipped"] += 1
                continue

            url = self.routes.get(team)
            if not url:
                summary["skipped"] += 1
                continue

            payload = self._build_payload(exception)

            if self.dry_run:
                summary["dispatched"] += 1
            else:
                if self._post_with_retry(url, payload):
                    summary["dispatched"] += 1
                else:
                    summary["failed"] += 1

            summary["by_team"][team] = summary["by_team"].get(team, 0) + 1

        return summary

