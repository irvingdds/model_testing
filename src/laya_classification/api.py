"""FastAPI application for Laya-powered request classification."""

import json
from time import perf_counter
from typing import Any

from fastapi import FastAPI, HTTPException, Request
from laya import Router
from pydantic import BaseModel, Field, ValidationError

app = FastAPI(
    title="Laya Classification API",
    version="0.1.0",
    description="Classifies customer requests using Laya.",
)

router = Router()

QUESTIONS: dict[str, dict[str, Any]] = {
    "agent": {
        "type": "choice",
        "instructions": "Which agent should handle the customer's current request?",
        "criteria": {
            "tracking_agent": (
                "For tracking, delayed, misdelivered, lost package (or parcel or "
                "shipment), and missed-delivery guidance. Do not handle delivery changes, "
                "claims, or general policy questions."
            ),
            "quote_agent": "For general shipping, quotes or rates questions.",
            "delivery_change_agent": (
                "For changing delivery address, reschedule delivery date, hold at a UPS "
                "location for pickup, return to sender, redeliver to an address, change "
                "delivery speed."
            ),
            "notifications_agent": "Handles delivery notification signup for parcel status.",
            "location_finder_agent": (
                "For finding nearest UPS locations to drop off or pickup a package."
            ),
            "delivery_delay_refund_agent": (
                "Handles refund requests specifically for delayed or late packages/shipments only."
            ),
            "external_question_agent": "For weather and distance between two locations.",
            "fee_question_agent": (
                "Route any question asking about a fee, charge, surcharge, or price here, "
                "even when it also mentions delivery changes."
            ),
            "claims_agent": (
                "For handling all claim-related inquiries and any request containing a claim "
                "number that begins with C-."
            ),
            "escalationagent": (
                "For handling escalations to live chat, live agent, click-to-call, SMS, and "
                "customer service phone numbers."
            ),
            "customs_agent": (
                "For customs, duties, tariff, outstanding balance, Importer of Record (IOR), "
                "CAPE platform, and CBP reimbursement questions. Do not handle IEEPA, "
                "reciprocal-tariff, executive-order-tariff, or tariff-refund requests."
            ),
            "ieepa_refund": (
                "For all IEEPA (International Emergency Economic Powers Act), reciprocal-"
                "tariff, executive-order-tariff, and tariff-refund requests."
            ),
            "insureshield_agent": "For all InsureShield related questions.",
            "shipment_refuse_agent": (
                "For refusing a shipment or package, including requests to stop the package, "
                "send it back, reject delivery, or do not accept it."
            ),
            "proof_of_delivery_agent": "For Proof of Delivery (POD) or delivery confirmation.",
            "general": (
                "This is a fallback agent responsible for Proof of Delivery, and any intents "
                "outside of tracking, shipping, quotes, claims, notifications, agent-related "
                "queries, cancel shipment, weather, distance, or UPS location lookups."
            ),
           },
    }
}


class ClassificationRequest(BaseModel):
    """Request body accepted by the classification endpoint."""

    message: str = Field(min_length=1, description="Customer message to classify.")


class ClassificationResponse(BaseModel):
    """Classification data returned by Laya."""

    resp: dict[str, str | float]
    message: str
    result: dict[str, Any]
    classification_time_ms: float = Field(
        description="Time spent running Laya classification, in milliseconds."
    )


@app.post("/classify", response_model=ClassificationResponse)
async def classify(request: Request) -> ClassificationResponse:
    """Classify the supplied customer message and return Laya's full result."""
    try:
        payload = ClassificationRequest.model_validate(await request.json())
    except json.JSONDecodeError as error:
        raise HTTPException(
            status_code=422,
            detail="Request body must be a JSON object containing a message.",
        ) from error
    except ValidationError as error:
        raise HTTPException(status_code=422, detail=error.errors()) from error

    started_at = perf_counter()
    result = router.predict({"message": payload.message}, QUESTIONS)
    classification_time_ms = round((perf_counter() - started_at) * 1_000, 2)
    answer = result["answers"]["agent"]
    selected_agent = answer["choice"]
    selected_agent_probability = answer.get("probabilities", {}).get(
        selected_agent,
        answer.get("answer_confidence", 0.0),
    )
    response_summary = {
        "message": payload.message,
        selected_agent: selected_agent_probability,
        "classification_time_ms": classification_time_ms,
    }
    return ClassificationResponse(
        resp=response_summary,
        message=payload.message,
        result=result,
        classification_time_ms=classification_time_ms,
    )