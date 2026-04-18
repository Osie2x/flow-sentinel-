CREATE TABLE IF NOT EXISTS records (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id           TEXT NOT NULL,
    timestamp           TEXT,
    category            TEXT,
    department          TEXT,
    amount              REAL,
    quantity            INTEGER,
    status              TEXT,
    region              TEXT,
    customer_id         TEXT,
    processing_time_ms  REAL,
    date                TEXT,
    hour_of_day         INTEGER,
    amount_bucket       TEXT,
    is_complete         INTEGER DEFAULT 0,
    has_violation       INTEGER DEFAULT 0,
    is_anomaly          INTEGER DEFAULT 0,
    ingested_at         TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS exceptions (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id           TEXT NOT NULL,
    rule_id             TEXT NOT NULL,
    rule_description    TEXT,
    field               TEXT,
    severity            TEXT,
    team                TEXT,
    flagged_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS anomalies (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    record_id           TEXT NOT NULL,
    detector            TEXT,
    field               TEXT,
    score               REAL,
    flagged_at          TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS health_scores (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date            TEXT NOT NULL,
    total_records       INTEGER,
    completeness        REAL,
    error_rate          REAL,
    throughput          REAL,
    anomaly_rate        REAL,
    composite_score     REAL,
    computed_at         TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS pipeline_runs (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    run_date            TEXT,
    status              TEXT,
    records_total       INTEGER,
    records_flagged     INTEGER,
    anomalies_found     INTEGER,
    health_score        REAL,
    duration_s          REAL,
    started_at          TEXT,
    finished_at         TEXT DEFAULT (datetime('now'))
);

CREATE INDEX IF NOT EXISTS idx_records_record_id ON records(record_id);
CREATE INDEX IF NOT EXISTS idx_records_date ON records(date);
CREATE INDEX IF NOT EXISTS idx_exceptions_record_id ON exceptions(record_id);
CREATE INDEX IF NOT EXISTS idx_exceptions_team ON exceptions(team);
CREATE INDEX IF NOT EXISTS idx_anomalies_record_id ON anomalies(record_id);
CREATE INDEX IF NOT EXISTS idx_health_scores_run_date ON health_scores(run_date);

