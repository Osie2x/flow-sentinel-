from flowsentinel.scoring.health_score import HealthScoreEngine


def test_health_score_computes_expected_fields():
    engine = HealthScoreEngine(expected_volume=100)
    score = engine.compute(
        total_records=100,
        completeness_pct=95.0,
        violation_count=10,
        anomaly_count=5,
    )

    assert score["total_records"] == 100
    assert score["composite_score"] > 0
    assert score["completeness"] == 95.0

