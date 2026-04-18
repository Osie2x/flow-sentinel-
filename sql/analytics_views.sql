DROP VIEW IF EXISTS daily_health_summary;
CREATE VIEW daily_health_summary AS
SELECT
    run_date,
    total_records,
    completeness,
    error_rate,
    throughput,
    anomaly_rate,
    composite_score
FROM health_scores;

DROP VIEW IF EXISTS team_exception_summary;
CREATE VIEW team_exception_summary AS
SELECT
    date(r.flagged_at) AS run_date,
    r.team,
    r.severity,
    COUNT(*) AS exception_count
FROM exceptions r
GROUP BY date(r.flagged_at), r.team, r.severity;

DROP VIEW IF EXISTS hourly_process_kpis;
CREATE VIEW hourly_process_kpis AS
SELECT
    date,
    hour_of_day,
    COUNT(*) AS records_processed,
    SUM(CASE WHEN has_violation = 1 THEN 1 ELSE 0 END) AS violated_records,
    SUM(CASE WHEN is_anomaly = 1 THEN 1 ELSE 0 END) AS anomalous_records,
    ROUND(AVG(processing_time_ms), 2) AS avg_processing_time_ms
FROM records
GROUP BY date, hour_of_day;

