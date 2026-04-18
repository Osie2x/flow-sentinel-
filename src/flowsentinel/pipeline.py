"""Main pipeline entrypoint."""

from __future__ import annotations

import argparse
import logging
import sys
import time
from datetime import date, datetime

from flowsentinel.alerts.alert_router import AlertRouter
from flowsentinel.config import DATA_PROCESSED, SOURCE_FILE
from flowsentinel.etl.extractor import Extractor
from flowsentinel.etl.loader import Loader
from flowsentinel.etl.transformer import Transformer
from flowsentinel.reports.pdf_generator import PDFReportGenerator
from flowsentinel.scoring.health_score import HealthScoreEngine
from flowsentinel.validation.anomaly_detector import AnomalyDetector
from flowsentinel.validation.rules import RuleEngine


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)-8s %(name)s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout), logging.FileHandler("flowsentinel.log", mode="a")],
)
logger = logging.getLogger("flowsentinel.pipeline")


def run_pipeline(dry_run: bool = True, generate_pdf: bool = True) -> dict:
    logger.info("Pipeline starting with source file %s", SOURCE_FILE)
    started_at = time.time()
    run_date = date.today()

    all_exceptions: list[dict] = []
    all_anomalies: list[dict] = []
    total_records = 0
    completeness_sum = 0.0
    batch_count = 0

    extractor = Extractor()
    transformer = Transformer()
    loader = Loader()
    rule_engine = RuleEngine()
    detector = AnomalyDetector()

    for raw_batch in extractor.extract():
        batch_count += 1
        clean_batch, metrics = transformer.transform(raw_batch)
        validated_batch, batch_exceptions = rule_engine.validate(clean_batch)
        scored_batch, batch_anomalies = detector.detect(validated_batch)

        loader.load_records(scored_batch)
        loader.load_exceptions(batch_exceptions)
        loader.load_anomalies(batch_anomalies)

        all_exceptions.extend(batch_exceptions)
        all_anomalies.extend(batch_anomalies)
        total_records += int(metrics["rows_out"])
        completeness_sum += float(metrics["completeness_pct"])

        logger.info(
            "Batch %s processed: %s records, %s exceptions, %s anomalies",
            batch_count,
            metrics["rows_out"],
            len(batch_exceptions),
            len(batch_anomalies),
        )

    mean_completeness = completeness_sum / max(batch_count, 1)
    anomaly_record_count = len({item["record_id"] for item in all_anomalies})

    score_engine = HealthScoreEngine()
    score_record = score_engine.compute(
        total_records=total_records,
        completeness_pct=mean_completeness,
        violation_count=len(all_exceptions),
        anomaly_count=anomaly_record_count,
        run_date=run_date,
    )
    loader.save_health_score(score_record)

    alert_summary = AlertRouter(dry_run=dry_run).route(all_exceptions)
    pdf_path = None
    if generate_pdf:
        pdf_path = PDFReportGenerator().generate(
            score_record=score_record,
            exceptions=all_exceptions,
            anomaly_count=anomaly_record_count,
            run_date=str(run_date),
        )

    exported = loader.export_powerbi_tables(DATA_PROCESSED)

    duration = round(time.time() - started_at, 2)
    run_record = {
        "run_date": str(run_date),
        "status": "SUCCESS",
        "records_total": total_records,
        "records_flagged": len({item["record_id"] for item in all_exceptions}),
        "anomalies_found": anomaly_record_count,
        "health_score": score_record["composite_score"],
        "duration_s": duration,
        "started_at": datetime.fromtimestamp(started_at).isoformat(),
    }
    loader.log_pipeline_run(run_record)
    loader.close()

    logger.info(
        "Pipeline complete in %ss | records=%s | violations=%s | anomalies=%s | exports=%s",
        duration,
        total_records,
        len(all_exceptions),
        anomaly_record_count,
        len(exported),
    )

    return {
        **run_record,
        "alert_summary": alert_summary,
        "pdf_path": str(pdf_path) if pdf_path else None,
        "exported_assets": [str(path) for path in exported],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Run the FlowSentinel pipeline")
    parser.add_argument("--live-alerts", action="store_true", help="Send real alert webhooks")
    parser.add_argument("--no-pdf", action="store_true", help="Skip PDF generation")
    args = parser.parse_args()

    try:
        result = run_pipeline(dry_run=not args.live_alerts, generate_pdf=not args.no_pdf)
        print(result)
    except Exception as error:
        logger.exception("Pipeline failed: %s", error)
        raise SystemExit(1) from error


if __name__ == "__main__":
    main()

