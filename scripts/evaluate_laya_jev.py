"""Evaluate TypeSafe/Jev routing on 100 customer questions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

from evaluate_updated_routing import CASES
from typesafe_sdk import TypeSafeClient

from laya_classification.jev_api import route_query

REPORT_PATH = Path("reports/laya_jev_comparison.json")


def jev_result(client: TypeSafeClient, message: str) -> dict[str, Any]:
    """Run one TypeSafe/Jev route prediction and return its compact result."""
    started_at = perf_counter()
    result = route_query(client, message, [], None, threshold=0.75)
    elapsed_ms = round((perf_counter() - started_at) * 1_000, 2)
    return {
        "agent": result["agent"],
        "score": result["confidence"],
        "classification_time_ms": elapsed_ms,
    }


def jev_summary(records: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate evaluation metrics for the recorded Jev results."""
    matches = [record["jev_matched"] for record in records]
    timings = [record["jev"]["classification_time_ms"] for record in records]
    high_confidence = [record for record in records if record["jev"]["score"] > 0.9]
    high_confidence_wrong = [
        record
        for record in records
        if not record["jev_matched"] and record["jev"]["score"] > 0.9
    ]
    return {
        "matched_expected_agent": sum(matches),
        "average_classification_time_ms": round(sum(timings) / len(timings), 2),
        "score_above_0_9": len(high_confidence),
        "high_confidence_incorrect": len(high_confidence_wrong),
        "predicted_agent_counts": dict(Counter(record["jev"]["agent"] for record in records)),
    }


def main() -> None:
    """Evaluate Jev against the fixed 100-question test set."""
    if len(CASES) != 100:
        raise ValueError(f"Expected 100 cases, found {len(CASES)}.")

    records: list[dict[str, Any]] = []
    with TypeSafeClient() as client:
        warmup_message = CASES[0]["message"]
        jev_result(client, warmup_message)
        print("Warm-up complete: discarded the first Jev result.")
        for number, case in enumerate(CASES, start=1):
            jev = jev_result(client, case["message"])
            records.append(
                {
                    "number": number,
                    "message": case["message"],
                    "expected_agent": case["expected_agent"],
                    "jev": jev,
                    "jev_matched": jev["agent"] == case["expected_agent"],
                }
            )
            print(f"{number:03}/100: Jev={jev['agent']}")

    report = {
        "summary": {
            "total_questions": len(records),
            "warmup": {
                "message": warmup_message,
                "discarded_results": 1,
                "description": "First Jev call was excluded from all results and timing metrics.",
            },
            "jev": jev_summary(records),
        },
        "responses": records,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Comparison report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
