"""Tests for the classification API."""

import json

from fastapi.testclient import TestClient

from laya_classification.api import app


def test_classify_sends_message_to_laya_and_returns_result(monkeypatch) -> None:
    """The endpoint passes the posted message to Laya and returns its output."""
    expected_result = {
        "answers": {
            "agent": {
                "choice": "tracking_agent",
                "reasoning": "The delivery is reported as missing.",
            }
        }
    }

    def fake_predict(state, questions):
        assert state == {"message": "My package says delivered, but I cannot find it."}
        assert questions["agent"]["type"] == "choice"
        return expected_result

    monkeypatch.setattr("laya_classification.api.router.predict", fake_predict)

    response = TestClient(app).post(
        "/classify",
        json={"message": "My package says delivered, but I cannot find it."},
    )

    assert response.status_code == 200
    response_body = response.json()
    assert response_body["message"] == "My package says delivered, but I cannot find it."
    assert response_body["result"] == expected_result
    assert response_body["classification_time_ms"] >= 0
    assert response_body["resp"] == {
        "message": "My package says delivered, but I cannot find it.",
        "tracking_agent": 0,
        "classification_time_ms": response_body["classification_time_ms"],
    }


def test_classify_rejects_an_empty_message() -> None:
    """The endpoint requires a non-empty message."""
    response = TestClient(app).post("/classify", json={"message": ""})

    assert response.status_code == 422


def test_classify_accepts_json_sent_as_raw_text(monkeypatch) -> None:
    """The endpoint supports clients that post the JSON body as text."""
    monkeypatch.setattr(
        "laya_classification.api.router.predict",
        lambda state, questions: {"answers": {"agent": {"choice": "tracking_agent"}}},
    )

    response = TestClient(app).post(
        "/classify",
        content=json.dumps({"message": "Where is my package?"}),
        headers={"Content-Type": "text/plain"},
    )

    assert response.status_code == 200
    assert response.json()["result"]["answers"]["agent"]["choice"] == "tracking_agent"
    assert response.json()["classification_time_ms"] >= 0