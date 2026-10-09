"""Run 100 representative customer questions through the Laya API."""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import TypedDict

from fastapi.testclient import TestClient

from laya_classification.api import app


class EvaluationCase(TypedDict):
    """One customer question and its intended routing agent."""

    message: str
    expected_agent: str


CASES: list[EvaluationCase] = [
    {"message": "Where is my package right now?", "expected_agent": "tracking_agent"},
    {"message": "My shipment has not moved in three days.", "expected_agent": "tracking_agent"},
    {"message": "The tracker says delivered but nothing is at my door.", "expected_agent": "tracking_agent"},
    {"message": "I think my parcel was sent to the wrong address.", "expected_agent": "tracking_agent"},
    {"message": "My package appears to be lost in transit.", "expected_agent": "tracking_agent"},
    {"message": "Can I track a shipment using this tracking number?", "expected_agent": "tracking_agent"},
    {"message": "Why is my delivery delayed?", "expected_agent": "tracking_agent"},
    {"message": "My package was marked delivered to my neighbor by mistake.", "expected_agent": "tracking_agent"},
    {"message": "The shipment status has been in transit for a week.", "expected_agent": "tracking_agent"},
    {"message": "Has my parcel arrived at the local facility?", "expected_agent": "tracking_agent"},
    {"message": "How much does it cost to ship a 10 pound box?", "expected_agent": "quote_agent"},
    {"message": "Can you give me a shipping rate from Dallas to Seattle?", "expected_agent": "quote_agent"},
    {"message": "What are the prices for overnight shipping?", "expected_agent": "quote_agent"},
    {"message": "I need a quote for sending documents internationally.", "expected_agent": "quote_agent"},
    {"message": "How long and how much will ground shipping cost?", "expected_agent": "quote_agent"},
    {"message": "Please estimate the shipping fee for my package.", "expected_agent": "quote_agent"},
    {"message": "What is the rate to mail a box to Canada?", "expected_agent": "quote_agent"},
    {"message": "Can I compare two-day and next-day delivery prices?", "expected_agent": "quote_agent"},
    {"message": "I need help getting a quote for a shipment.", "expected_agent": "quote_agent_old"},
    {"message": "How do I start a shipping flow for my package?", "expected_agent": "quote_agent_old"},
    {"message": "I need to change the delivery address.", "expected_agent": "delivery_change_agent"},
    {"message": "Can I reschedule my delivery for Friday?", "expected_agent": "delivery_change_agent"},
    {"message": "Please hold my parcel at a UPS location for pickup.", "expected_agent": "delivery_change_agent"},
    {"message": "Return this shipment to the sender.", "expected_agent": "delivery_change_agent"},
    {"message": "Can my package be redelivered to a different address?", "expected_agent": "delivery_change_agent"},
    {"message": "I want to upgrade my delivery speed.", "expected_agent": "delivery_change_agent"},
    {"message": "Move my delivery date to next Monday.", "expected_agent": "delivery_change_agent"},
    {"message": "How do I get text updates about my package?", "expected_agent": "notifications_agent"},
    {"message": "Sign me up for delivery notifications.", "expected_agent": "notifications_agent"},
    {"message": "I want email alerts when my shipment status changes.", "expected_agent": "notifications_agent"},
    {"message": "Where is the nearest UPS drop-off point?", "expected_agent": "drop_off_agent"},
    {"message": "Find a UPS Store where I can leave this package.", "expected_agent": "drop_off_agent"},
    {"message": "Where can I pick up my package near me?", "expected_agent": "drop_off_agent"},
    {"message": "Locate the closest UPS access point.", "expected_agent": "location_finder_agent_v2"},
    {"message": "Find a nearby UPS location for package pickup.", "expected_agent": "location_finder_agent_v2"},
    {"message": "My delivery was late and I need a refund.", "expected_agent": "delivery_delay_refund_agent"},
    {
        "message": "Can I get reimbursed because my shipment arrived late?",
        "expected_agent": "delivery_delay_refund_agent",
    },
    {"message": "I want a refund for a delayed package.", "expected_agent": "delivery_delay_refund_agent"},
    {"message": "What will the weather be in Chicago tomorrow?", "expected_agent": "external_question_agent"},
    {"message": "How far is Miami from Orlando?", "expected_agent": "external_question_agent"},
    {"message": "What is the distance between New York and Boston?", "expected_agent": "external_question_agent"},
    {"message": "Is there a fee for changing a delivery address?", "expected_agent": "fee_question_agent"},
    {"message": "Why was I charged an extra delivery fee?", "expected_agent": "fee_question_agent"},
    {"message": "What fees apply to this shipment?", "expected_agent": "fee_question_agent"},
    {"message": "I need to file a claim for damage.", "expected_agent": "claims_agent"},
    {"message": "Please help with claim number C-123456.", "expected_agent": "claims_agent"},
    {"message": "What is the status of my lost package claim?", "expected_agent": "claims_agent"},
    {"message": "I have a claim number C-9981 to discuss.", "expected_agent": "claims_agent_v2"},
    {"message": "How do I submit an insurance claim for my shipment?", "expected_agent": "claims_agent_v2"},
    {"message": "Connect me to a live agent.", "expected_agent": "escalationagent"},
    {"message": "I want to chat with customer service.", "expected_agent": "escalationagent"},
    {"message": "Can I have the customer service phone number?", "expected_agent": "escalationagent"},
    {"message": "Please send me an SMS support option.", "expected_agent": "escalationagent"},
    {"message": "Do I owe customs duties on this international shipment?", "expected_agent": "customs_agent"},
    {"message": "Why is there an outstanding import balance?", "expected_agent": "customs_agent"},
    {"message": "How do I request a CBP reimbursement?", "expected_agent": "customs_agent"},
    {"message": "Explain the IOR refund process.", "expected_agent": "customs_agent"},
    {"message": "I need an IEEPA tariff refund.", "expected_agent": "ieepa_refund"},
    {"message": "Can you request an IEEPA refund for me?", "expected_agent": "ieepa_refund"},
    {"message": "I have questions about my InsureShield coverage.", "expected_agent": "insureshield_agent"},
    {"message": "How does InsureShield protect my shipment?", "expected_agent": "insureshield_agent"},
    {"message": "I want to refuse delivery of this package.", "expected_agent": "shipment_refuse_agent"},
    {"message": "Can I reject a shipment that is coming to me?", "expected_agent": "shipment_refuse_agent"},
    {"message": "I need proof that my package was delivered.", "expected_agent": "proof_of_delivery_agent"},
    {"message": "Can I get a proof of delivery document?", "expected_agent": "proof_of_delivery_agent"},
    {"message": "I need delivery confirmation for my order.", "expected_agent": "proof_of_delivery_agent"},
    {"message": "How can I cancel a shipment before it goes out?", "expected_agent": "guided_flow_agent"},
    {"message": "What should I do if I missed my delivery?", "expected_agent": "guided_flow_agent"},
    {
        "message": "I need help with a delivery issue that does not fit these options.",
        "expected_agent": "guided_flow_agent",
    },
    {"message": "How do I update my UPS account profile?", "expected_agent": "watson_assistant"},
    {"message": "I cannot log into my shipping account.", "expected_agent": "watson_assistant"},
    {"message": "I have a billing problem on my UPS account.", "expected_agent": "watson_assistant"},
    {"message": "What services does UPS offer?", "expected_agent": "general"},
    {"message": "Tell me about UPS business solutions.", "expected_agent": "general"},
    {"message": "What are the UPS holiday hours?", "expected_agent": "general"},
    {"message": "Show me insights from my UPS My Choice shipments.", "expected_agent": "myChoice"},
    {"message": "Can you analyze delivery trends in my My Choice account?", "expected_agent": "myChoice"},
    {"message": "What shipment analytics are available in My Choice?", "expected_agent": "myChoice"},
    {"message": "My box is 20 by 10 by 8 inches and weighs 12 pounds.", "expected_agent": "dimension"},
    {"message": "What dimensions and weight can I ship in this carton?", "expected_agent": "dimension"},
    {"message": "How should I package a 25 pound item?", "expected_agent": "dimension"},
    {"message": "What does your knowledge base say about shipping batteries?", "expected_agent": "direct_rag"},
    {"message": "Give me a knowledge-base answer for international paperwork.", "expected_agent": "direct_rag"},
    {"message": "Find the help article about package packaging rules.", "expected_agent": "direct_rag"},
    {
        "message": "Analyze my account dashboard and recommend improvements.",
        "expected_agent": "account_dashboard_insights",
    },
    {"message": "Summarize trends from my account dashboard data.", "expected_agent": "account_dashboard_insights"},
    {
        "message": "Give actionable recommendations from my shipping dashboard.",
        "expected_agent": "account_dashboard_insights",
    },
    {"message": "My parcel has no tracking updates since Tuesday.", "expected_agent": "tracking_agent"},
    {"message": "Can I reroute a shipment to my office?", "expected_agent": "delivery_change_agent"},
    {"message": "Please alert me when the driver is close.", "expected_agent": "notifications_agent"},
    {"message": "Find the closest place to return a package.", "expected_agent": "drop_off_agent"},
    {"message": "A late delivery ruined my event; can I be refunded?", "expected_agent": "delivery_delay_refund_agent"},
    {"message": "Why is my import tariff so high?", "expected_agent": "customs_agent"},
    {"message": "I need a delivery receipt signed by the recipient.", "expected_agent": "proof_of_delivery_agent"},
    {"message": "I want to speak with a representative now.", "expected_agent": "escalationagent"},
    {"message": "Track my package with this shipment ID.", "expected_agent": "tracking_agent"},
    {"message": "What is the cost to ship a package overseas?", "expected_agent": "quote_agent"},
    {"message": "Can I change my delivery instructions?", "expected_agent": "delivery_change_agent"},
    {"message": "Where can I drop this return package?", "expected_agent": "drop_off_agent"},
    {"message": "I need help with claim C-456789.", "expected_agent": "claims_agent"},
]


def main() -> None:
    """Write the live API responses for all evaluation cases to a report."""
    if len(CASES) != 100:
        raise ValueError(f"Expected 100 cases, found {len(CASES)}.")

    report_path = Path("reports/routing_evaluation.json")
    report_path.parent.mkdir(exist_ok=True)
    records: list[dict[str, object]] = []

    with TestClient(app) as client:
        for number, case in enumerate(CASES, start=1):
            response = client.post("/classify", json={"message": case["message"]})
            response.raise_for_status()
            body = response.json()
            selected_agent = body["result"]["answers"]["agent"]["choice"]
            records.append(
                {
                    "number": number,
                    "expected_agent": case["expected_agent"],
                    "predicted_agent": selected_agent,
                    "matched_expected_agent": selected_agent == case["expected_agent"],
                    "resp": body["resp"],
                }
            )
            print(f"{number:03}/100: {selected_agent}")

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
