"""Export the saved Laya evaluation responses to a review-friendly CSV file."""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any

REPORT_PATH = Path("reports/routing_evaluation.json")
CSV_PATH = Path("reports/routing_evaluation.csv")


def build_analysis(record: dict[str, Any]) -> str:
    """Describe whether Laya selected the agent assigned to the test question."""
    expected = record["expected_agent"]
    predicted = record["predicted_agent"]
    if record["matched_expected_agent"]:
        return f"Matched the expected agent: {expected}."
    return f"Expected {expected}, but Laya selected {predicted}."


def main() -> None:
    """Create a CSV containing each concise API response and routing analysis."""
    report = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    responses: list[dict[str, Any]] = report["responses"]

    with CSV_PATH.open("w", newline="", encoding="utf-8") as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=[
                "message",
                "agent_name",
                "confidence_score",
                "classification_time_ms",
                "analysis",
            ],
        )
        writer.writeheader()
        for record in responses:
            response_summary = record["resp"]
            agent_name = record["predicted_agent"]
            writer.writerow(
                {
                    "message": response_summary["message"],
                    "agent_name": agent_name,
                    "confidence_score": response_summary[agent_name],
                    "classification_time_ms": response_summary["classification_time_ms"],
                    "analysis": build_analysis(record),
                }
            )

    print(f"CSV report written to {CSV_PATH}")


if __name__ == "__main__":
    main()
