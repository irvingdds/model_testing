"""Create 200 context-rich routing questions from the labeled evaluation suite."""

from __future__ import annotations

from typing import TypedDict

from evaluate_updated_routing import CASES


class EvaluationCase(TypedDict):
    """One complex customer message and the agent expected to own it."""

    message: str
    expected_agent: str


SCENARIOS: dict[str, tuple[str, str]] = {
    "tracking_agent": (
        "I am coordinating delivery with the recipient and the status shown by the carrier no longer makes sense. ",
        "This shipment is important for an upcoming event, so I need to understand its "
        "current movement before making other plans. ",
    ),
    "quote_agent": (
        "I have not purchased the label yet and need to compare options before committing to a shipping service. ",
        "I am preparing a budget for this shipment and need the cost details before I can proceed. ",
    ),
    "delivery_change_agent": (
        "The recipient's plans changed after the shipment was created, and I need to adjust "
        "how the carrier completes delivery. ",
        "I am trying to prevent a failed delivery by changing the existing delivery arrangement in time. ",
    ),
    "notifications_agent": (
        "I will not be available to monitor the shipment continuously, so I need proactive status updates. ",
        "Several people are waiting on this delivery, and I want to manage the alerts they receive. ",
    ),
    "location_finder_agent": (
        "I am away from the normal delivery address and need a convenient nearby carrier location. ",
        "I need to plan a trip around dropping off or collecting this parcel at a physical location. ",
    ),
    "delivery_delay_refund_agent": (
        "The promised delivery window has already passed, and the late arrival affected my plans. ",
        "I paid for a service level with a delivery commitment and now need to discuss compensation for the delay. ",
    ),
    "external_question_agent": (
        "I am planning travel around this shipment, but this question is about location or "
        "weather rather than carrier operations. ",
        "Before I make travel arrangements, I need general geographic or weather information. ",
    ),
    "fee_question_agent": (
        "I noticed a cost associated with my shipment and need to understand the charge before taking further action. ",
        "I am reviewing my shipping expenses and need clarification about a price, fee, or surcharge. ",
    ),
    "claims_agent": (
        "The shipment problem may require formal documentation, and I need help with the claim process. ",
        "I have evidence related to a damaged or missing shipment and need to resolve the associated claim. ",
    ),
    "escalationagent": (
        "The self-service information has not resolved my issue, and I need a person or "
        "another direct support channel. ",
        "This requires follow-up beyond automated guidance, so I want to reach a live support option. ",
    ),
    "customs_agent": (
        "This is an international shipment and the import paperwork or charges are preventing it from moving forward. ",
        "I am reviewing cross-border shipping obligations and need help with customs, duties, or an import balance. ",
    ),
    "ieepa_refund": (
        "I am reviewing a tariff charge and believe the payment may qualify for a specific import-duty refund. ",
        "This request concerns a tariff reimbursement rather than routine customs clearance. ",
    ),
    "insureshield_agent": (
        "I am deciding how to protect the value of this shipment and need information about the available coverage. ",
        "The package contents are valuable, so I need help with the InsureShield portion of the shipment. ",
    ),
    "shipment_refuse_agent": (
        "I do not want the recipient to accept this package and need to stop or return it appropriately. ",
        "The recipient should not take possession of this shipment, and I need to handle "
        "that before delivery completes. ",
    ),
    "proof_of_delivery_agent": (
        "I need delivery evidence for a business record and must verify what happened at the destination. ",
        "The recipient disputes whether delivery occurred, so I need formal confirmation from the carrier. ",
    ),
    "general": (
        "I am looking for broad shipping guidance rather than help with a specific parcel status or claim. ",
        "I need general carrier information to decide what to do next. ",
    ),
}


COMPLEX_CASES: list[EvaluationCase] = []
for case in CASES:
    for scenario in SCENARIOS[case["expected_agent"]]:
        COMPLEX_CASES.append(
            {
                "message": f"{scenario}{case['message']}",
                "expected_agent": case["expected_agent"],
            }
        )

if len(COMPLEX_CASES) != 200:
    raise ValueError(f"Expected 200 complex cases, found {len(COMPLEX_CASES)}.")
