"""Central configuration for FlowSentinel."""

from __future__ import annotations

import os
from pathlib import Path


PACKAGE_DIR = Path(__file__).resolve().parent
SRC_DIR = PACKAGE_DIR.parent
ROOT_DIR = SRC_DIR.parent

DATA_DIR = ROOT_DIR / "data"
DATA_RAW = DATA_DIR / "raw"
DATA_PROCESSED = DATA_DIR / "processed"
OUTPUTS_DIR = ROOT_DIR / "outputs"
SQL_DIR = ROOT_DIR / "sql"
POWERBI_DIR = ROOT_DIR / "powerbi"
POWER_AUTOMATE_DIR = ROOT_DIR / "power_automate"

for path in (DATA_RAW, DATA_PROCESSED, OUTPUTS_DIR):
    path.mkdir(parents=True, exist_ok=True)

SOURCE_FILE = Path(os.getenv("FLOWSENTINEL_SOURCE_FILE", DATA_RAW / "business_records.csv"))
DB_PATH = Path(os.getenv("FLOWSENTINEL_DB_PATH", DATA_DIR / "flowsentinel.db"))

BATCH_SIZE = 5_000
MAX_RECORDS_PER_RUN = 100_000

SCHEMA = {
    "record_id": str,
    "timestamp": str,
    "category": str,
    "department": str,
    "amount": float,
    "quantity": int,
    "status": str,
    "region": str,
    "customer_id": str,
    "processing_time_ms": float,
}

VALID_STATUSES = {"COMPLETE", "PENDING", "FAILED", "CANCELLED"}
VALID_DEPARTMENTS = {"FINANCE", "LOGISTICS", "OPERATIONS", "SALES", "HR"}
VALID_REGIONS = {"NORTH", "SOUTH", "EAST", "WEST", "CENTRAL"}

BUSINESS_RULES = [
    {
        "id": "RULE_001",
        "description": "Amount must be positive",
        "field": "amount",
        "severity": "HIGH",
        "team": "finance",
    },
    {
        "id": "RULE_002",
        "description": "Status must be a valid value",
        "field": "status",
        "severity": "HIGH",
        "team": "operations",
    },
    {
        "id": "RULE_003",
        "description": "Quantity must be non-negative",
        "field": "quantity",
        "severity": "MEDIUM",
        "team": "logistics",
    },
    {
        "id": "RULE_004",
        "description": "Processing time must be reasonable (< 30,000 ms)",
        "field": "processing_time_ms",
        "severity": "MEDIUM",
        "team": "operations",
    },
    {
        "id": "RULE_005",
        "description": "Department must be a recognised value",
        "field": "department",
        "severity": "LOW",
        "team": "hr",
    },
    {
        "id": "RULE_006",
        "description": "Record must have an identifier",
        "field": "record_id",
        "severity": "HIGH",
        "team": "operations",
    },
]

ANOMALY_FIELDS = ["amount", "quantity", "processing_time_ms"]
ISOLATION_CONTAMINATION = 0.05
ZSCORE_THRESHOLD = 3.0

HEALTH_SCORE_WEIGHTS = {
    "completeness": 0.30,
    "error_rate": 0.25,
    "throughput": 0.25,
    "anomaly_rate": 0.20,
}
EXPECTED_DAILY_VOLUME = 50_000

ALERT_ROUTES = {
    "finance": os.getenv("FLOWSENTINEL_FINANCE_WEBHOOK", "https://hooks.example.com/finance"),
    "logistics": os.getenv("FLOWSENTINEL_LOGISTICS_WEBHOOK", "https://hooks.example.com/logistics"),
    "operations": os.getenv("FLOWSENTINEL_OPERATIONS_WEBHOOK", "https://hooks.example.com/operations"),
    "hr": os.getenv("FLOWSENTINEL_HR_WEBHOOK", "https://hooks.example.com/hr"),
    "sales": os.getenv("FLOWSENTINEL_SALES_WEBHOOK", "https://hooks.example.com/sales"),
}
ALERT_SEVERITY_THRESHOLD = {"HIGH", "MEDIUM"}
ALERT_MAX_RETRIES = 3
ALERT_RETRY_BACKOFF_S = 2

PDF_COMPANY_NAME = "FlowSentinel Analytics"
PDF_REPORT_TITLE = "Daily Process Health Report"
PDF_MAX_EXCEPTIONS = 50

DASHBOARD_PORT = 8050
DASHBOARD_REFRESH_MS = 60_000
DASHBOARD_TREND_DAYS = 30

POWERBI_EXPORT_TABLES = {
    "records": "SELECT * FROM records",
    "exceptions": "SELECT * FROM exceptions",
    "anomalies": "SELECT * FROM anomalies",
    "health_scores": "SELECT * FROM health_scores",
    "daily_health_summary": "SELECT * FROM daily_health_summary",
    "team_exception_summary": "SELECT * FROM team_exception_summary",
}

