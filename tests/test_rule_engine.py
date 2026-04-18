import pandas as pd

from flowsentinel.validation.rules import RuleEngine


def test_rule_engine_flags_invalid_records():
    frame = pd.DataFrame(
        [
            {
                "record_id": "REC-1",
                "amount": -5,
                "quantity": 1,
                "status": "COMPLETE",
                "department": "FINANCE",
                "processing_time_ms": 500,
            }
        ]
    )

    validated, exceptions = RuleEngine().validate(frame)

    assert validated["has_violation"].iloc[0] == 1
    assert len(exceptions) >= 1
    assert exceptions[0]["rule_id"] == "RULE_001"

