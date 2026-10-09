"""Evaluate the current Laya agent duties with 100 representative questions."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import TypedDict

from fastapi.testclient import TestClient

from laya_classification.api import app


class EvaluationCase(TypedDict):
    """One customer question and its expected routing agent."""

    message: str
    expected_agent: str


QUESTION_SETS: dict[str, list[str]] = {
    "tracking_agent": [
        "Where is my package right now?",
        "My shipment has not moved in three days.",
        "The tracker says delivered but nothing is at my door.",
        "I think my parcel was sent to the wrong address.",
        "My package appears to be lost in transit.",
        "Can I track a shipment using this tracking number?",
        "Why is my delivery delayed?",
        "My package was marked delivered to my neighbor by mistake.",
        "The shipment status has been in transit for a week.",
        "Has my parcel arrived at the local facility?",
        "What should I do if I missed my delivery?",
    ],
    "quote_agent": [
        "How much does it cost to ship a 10 pound box?",
        "Can you give me a shipping rate from Dallas to Seattle?",
        "What are the prices for overnight shipping?",
        "I need a quote for sending documents internationally.",
        "How long and how much will ground shipping cost?",
        "Please estimate the shipping fee for my package.",
    ],
    "delivery_change_agent": [
        "I need to change the delivery address.",
        "Can I reschedule my delivery for Friday?",
        "Please hold my parcel at a UPS location for pickup.",
        "Return this shipment to the sender.",
        "Can my package be redelivered to a different address?",
        "I want to upgrade my delivery speed.",
    ],
    "notifications_agent": [
        "How do I get text updates about my package?",
        "Sign me up for delivery notifications.",
        "I want email alerts when my shipment status changes.",
        "Please alert me when the driver is close.",
        "Can I receive a notification when my package is delivered?",
        "How do I stop shipment-status notifications?",
    ],
    "location_finder_agent": [
        "Where is the nearest UPS drop-off point?",
        "Find a UPS Store where I can leave this package.",
        "Where can I pick up my package near me?",
        "Locate the closest UPS access point.",
        "Find a nearby UPS location for package pickup.",
        "Where can I drop this return package?",
    ],
    "delivery_delay_refund_agent": [
        "My delivery was late and I need a refund.",
        "Can I get reimbursed because my shipment arrived late?",
        "I want a refund for a delayed package.",
        "A late delivery ruined my event; can I be refunded?",
        "My guaranteed shipment arrived after the delivery date; request a refund.",
        "How do I claim a refund for a late package?",
    ],
    "external_question_agent": [
        "What will the weather be in Chicago tomorrow?",
        "How far is Miami from Orlando?",
        "What is the distance between New York and Boston?",
        "Will snow affect the weather in Denver today?",
        "How many miles is Los Angeles from San Diego?",
        "What is the forecast for Seattle this weekend?",
    ],
    "fee_question_agent": [
        "Is there a fee for changing a delivery address?",
        "Why was I charged an extra delivery fee?",
        "What fees apply to this shipment?",
        "Is there a fee to hold a package for pickup?",
        "Do I need to pay a residential delivery surcharge?",
        "Can you explain this shipping fee on my bill?",
    ],
    "claims_agent": [
        "I need to file a claim for damage.",
        "Please help with claim number C-123456.",
        "What is the status of my lost package claim?",
        "I have a claim number C-9981 to discuss.",
        "How do I submit an insurance claim for my shipment?",
        "My claim C-456789 was denied; what should I do?",
    ],
    "escalationagent": [
        "Connect me to a live agent.",
        "I want to chat with customer service.",
        "Can I have the customer service phone number?",
        "Please send me an SMS support option.",
        "I want to speak with a representative now.",
        "Start a click-to-call request for me.",
    ],
    "customs_agent": [
        "Do I owe customs duties on this international shipment?",
        "Why is there an outstanding import balance?",
        "How do I request a CBP reimbursement?",
        "Explain the IOR refund process.",
        "Why is my import tariff so high?",
        "What is the CAPE platform refund process?",
    ],
    "ieepa_refund": [
        "I need an IEEPA tariff refund.",
        "Can you request an IEEPA refund for me?",
        "How do I apply for a reciprocal tariff refund?",
        "I want an executive order tariff refund.",
        "Can I get a refund for an IEEPA duty charge?",
        "Help me obtain an IEEPA import refund.",
    ],
    "insureshield_agent": [
        "I have questions about my InsureShield coverage.",
        "How does InsureShield protect my shipment?",
        "Can I buy InsureShield for a package?",
        "What does InsureShield cover when a parcel is damaged?",
        "How do I submit an InsureShield claim?",
        "Is InsureShield available for international shipping?",
    ],
    "shipment_refuse_agent": [
        "I want to refuse delivery of this package.",
        "Can I reject a shipment that is coming to me?",
        "How do I refuse a package at my door?",
        "Please stop this package and send it back.",
        "Can the sender receive my refused shipment?",
        "I do not want to accept this parcel.",
    ],
    "proof_of_delivery_agent": [
        "I need proof that my package was delivered.",
        "Can I get a proof of delivery document?",
        "I need delivery confirmation for my order.",
        "I need a delivery receipt signed by the recipient.",
        "Can you provide a POD for this shipment?",
        "Who signed for my delivered package?",
    ],
    "general": [
        "How can I cancel a shipment before it goes out?",
        "I need help with a delivery issue that does not fit these options.",
        "What services does UPS offer?",
        "Tell me about UPS business solutions.",
        "What are the UPS holiday hours?",
    ],
}

CASES: list[EvaluationCase] = [
    {"message": message, "expected_agent": agent}
    for agent, messages in QUESTION_SETS.items()
    for message in messages
]


def main() -> None:
    """Run exactly 100 questions and save their compact response summaries."""
    if len(CASES) != 100:
        raise ValueError(f"Expected 100 cases, found {len(CASES)}.")

    report_path = Path("reports/routing_evaluation.json")
    records: list[dict[str, object]] = []
    with TestClient(app) as client:
        for number, case in enumerate(CASES, start=1):
            response = client.post("/classify", json={"message": case["message"]})
            response.raise_for_status()
            body = response.json()
            predicted_agent = body["result"]["answers"]["agent"]["choice"]
            records.append(
                {
                    "number": number,
                    "expected_agent": case["expected_agent"],
                    "predicted_agent": predicted_agent,
                    "matched_expected_agent": predicted_agent == case["expected_agent"],
                    "resp": body["resp"],
                }
            )
            print(f"{number:03}/100: {predicted_agent}")

    summary = {
        "total_questions": len(records),
        "matched_expected_agent": sum(record["matched_expected_agent"] for record in records),
        "average_classification_time_ms": round(
            sum(record["resp"]["classification_time_ms"] for record in records) / len(records),
            2,
        ),
        "predicted_agent_counts": dict(Counter(record["predicted_agent"] for record in records)),
    }
    report_path.write_text(
        json.dumps({"summary": summary, "responses": records}, indent=2),
        encoding="utf-8",
    )
    print(f"Report written to {report_path}")


if __name__ == "__main__":
    main()
