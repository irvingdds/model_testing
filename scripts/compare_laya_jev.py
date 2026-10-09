"""Compare Laya and TypeSafe/Jev on the same labeled routing questions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from time import perf_counter
from typing import Any

from complex_routing_questions import COMPLEX_CASES
from laya import Router
from typesafe_sdk import TypeSafeClient

from laya_classification.api import QUESTIONS
from laya_classification.jev_api import route_query

REPORT_PATH = Path("reports/laya_jev_complex_200.json")


def run_laya(router: Router, message: str) -> dict[str, Any]:
    """Classify one message with Laya and measure prediction time."""
    started_at = perf_counter()
    result = router.predict({"message": message}, QUESTIONS)
    elapsed_ms = round((perf_counter() - started_at) * 1_000, 2)
    answer = result["answers"]["agent"]
    agent = answer["choice"]
    return {
        "agent": agent,
        "score": answer["probabilities"].get(agent, answer["answer_confidence"]),
        "classification_time_ms": elapsed_ms,
    }


def run_jev(client: TypeSafeClient, message: str) -> dict[str, Any]:
    """Classify one message with TypeSafe/Jev and measure prediction time."""
    started_at = perf_counter()
    result = route_query(client, message, [], None, threshold=0.75)
    elapsed_ms = round((perf_counter() - started_at) * 1_000, 2)
    return {
        "agent": result["agent"],
        "score": result["confidence"],
        "classification_time_ms": elapsed_ms,
    }


def summarize(records: list[dict[str, Any]], model: str) -> dict[str, Any]:
    """Calculate match and timing metrics for one model."""
    model_records = [record[model] for record in records]
    matched = [record[f"{model}_matched"] for record in records]
    high_confidence_wrong = [
        record
        for record in records
        if not record[f"{model}_matched"] and record[model]["score"] > 0.9
    ]
    return {
        "matched_expected_agent": sum(matched),
        "average_classification_time_ms": round(
            sum(record["classification_time_ms"] for record in model_records) / len(model_records),
            2,
        ),
        "score_above_0_9": sum(record["score"] > 0.9 for record in model_records),
        "high_confidence_incorrect": len(high_confidence_wrong),
        "predicted_agent_counts": dict(Counter(record["agent"] for record in model_records)),
    }


def main() -> None:
    """Warm up each model, then compare both on the identical complex question set."""
    cases = COMPLEX_CASES
    if len(cases) != 200:
        raise ValueError(f"Expected 200 cases, found {len(cases)}.")

    router = Router()
    records: list[dict[str, Any]] = []
    with TypeSafeClient() as client:
        warmup_message = cases[0]["message"]
        run_laya(router, warmup_message)
        run_jev(client, warmup_message)
        print("Warm-up complete: discarded the first Laya and Jev results.")

        for number, case in enumerate(cases, start=1):
            laya = run_laya(router, case["message"])
            jev = run_jev(client, case["message"])
            record = {
                "number": number,
                "message": case["message"],
                "expected_agent": case["expected_agent"],
                "laya": laya,
                "laya_matched": laya["agent"] == case["expected_agent"],
                "jev": jev,
                "jev_matched": jev["agent"] == case["expected_agent"],
                "models_agree": laya["agent"] == jev["agent"],
            }
            records.append(record)
            print(f"{number:03}/{len(cases)}: Laya={laya['agent']}; Jev={jev['agent']}")

    report = {
        "summary": {
            "total_questions": len(records),
            "warmup": "First call to each model was discarded.",
            "laya": summarize(records, "laya"),
            "jev": summarize(records, "jev"),
            "models_agree": sum(record["models_agree"] for record in records),
        },
        "responses": records,
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"Side-by-side report written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
