"""Tests for the TypeSafe/Jev classification API."""

from types import SimpleNamespace

from fastapi.testclient import TestClient

from laya_classification.jev_api import AGENTS, app


def test_jev_classify_returns_compact_and_full_results(monkeypatch) -> None:
    """The endpoint returns a routed agent, score, and elapsed classification time."""
    answer = SimpleNamespace(
        choice="tracking_agent",
        confidence=0.92,
        probabilities={"tracking_agent": 0.92, "general": 0.08},
    )

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def system_one(self, state, questions):
            assert "Where is my package?" in state
            assert questions["route"].criteria == AGENTS
            return SimpleNamespace(answers={"route": answer})

    monkeypatch.setattr("laya_classification.jev_api.TypeSafeClient", FakeClient)

    response = TestClient(app).post(
        "/jev/classify",
        json={"message": "Where is my package?"},
    )

    assert response.status_code == 200
    response_body = response.json()
    assert response_body["result"]["agent"] == "tracking_agent"
    assert response_body["resp"]["tracking_agent"] == 0.92
    assert response_body["classification_time_ms"] >= 0


def test_jev_uses_general_when_confidence_is_below_threshold(monkeypatch) -> None:
    """Low-confidence model selections use the configured fallback agent."""
    answer = SimpleNamespace(
        choice="tracking_agent",
        confidence=0.4,
        probabilities={"tracking_agent": 0.4, "general": 0.6},
    )

    class FakeClient:
        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def system_one(self, **_kwargs):
            return SimpleNamespace(answers={"route": answer})

    monkeypatch.setattr("laya_classification.jev_api.TypeSafeClient", FakeClient)

    response = TestClient(app).post(
        "/jev/classify",
        json={"message": "Where is my package?", "threshold": 0.75},
    )

    assert response.status_code == 200
    assert response.json()["result"]["agent"] == "general"