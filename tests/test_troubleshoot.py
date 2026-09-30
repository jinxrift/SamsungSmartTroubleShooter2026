import json
from pathlib import Path
from types import SimpleNamespace

from fastapi.testclient import TestClient

from app.main import app
from app.services.siis_engine import process_siis
from app.services.llm_engine import extract_with_llm
from app.models.schema import Goal


def test_extraction_wrapper_falls_back_to_grounded_siis_actions(monkeypatch):
    content = "## Restart the device\nPress and hold the Power and Volume down buttons for 20 seconds."
    monkeypatch.setattr(
        "app.services.llm_engine._request_llm",
        lambda query, title, source: None,
    )

    result = extract_with_llm("Device will not start", "Device startup", content)

    assert result["actions"]
    for action in result["actions"]:
        assert action["actionName"] in content
        assert action["description"]
        assert action["steps"]
        assert all(step in content for step in action["steps"])
        assert action["category"] in {"auto", "manual", "critical"}


def test_troubleshoot_attaches_catalog_deeplinks():
    client = TestClient(app)
    response = client.post(
        "/v1/troubleshoot",
        json={
            "query": "enable Bluetooth scanning",
            "siis_response": {
                "title": "Bluetooth scanning",
                "content": "## Enable Bluetooth scanning\nEnable Bluetooth scanning.",
            },
        },
    )

    assert response.status_code == 200
    action = response.json()["contexts"][0]["actions"][0]
    step_group = action["stepGroups"][0]
    assert action["category"] == "auto"
    assert step_group["actionableDeeplink"]["originalType"] == "onURL"
    assert step_group["validationDeeplink"]["key"] == "Bluetooth scanning"


def test_troubleshoot_cache_includes_siis_payload():
    client = TestClient(app)
    query = "cache payload regression"
    first = client.post(
        "/v1/troubleshoot",
        json={
            "query": query,
            "siis_response": {
                "title": "First issue",
                "content": "## First action\nInspect the power button.",
            },
        },
    )
    second = client.post(
        "/v1/troubleshoot",
        json={
            "query": query,
            "siis_response": {
                "title": "Second issue",
                "content": "## Second action\nInspect the charging cable.",
            },
        },
    )

    assert first.status_code == second.status_code == 200
    assert first.json()["contexts"][0]["title"] == "First issue"
    assert second.json()["contexts"][0]["title"] == "Second issue"


def test_troubleshoot_rejects_invalid_payload():
    response = TestClient(app).post(
        "/v1/troubleshoot",
        json={"query": "invalid payload", "siis_response": {"title": "Missing content"}},
    )

    assert response.status_code == 422


def test_all_siis_responses():
    data_path = Path("data/siis_responses.json")

    with open(data_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    responses = data["responses"]

    print(f"\nTotal SIIS records: {len(responses)}")

    for i, record in enumerate(responses, start=1):

        query = record["original_query"]

        siis_response = SimpleNamespace(
            title=record["siis_response"]["title"],
            content=record["siis_response"]["content"]
        )

        result = process_siis(query, siis_response)

        goals = result.get("goals", [])

        print(f"\nRecord {i}")
        print(
            f"Actions generated: "
            f"{len(goals[0]['actions']) if goals else 0}"
        )

        # Print full output only for Record 17
        if i == 19:
            print("\n========== RECORD 17 OUTPUT ==========")
            print(json.dumps(result, indent=2))
            print("======================================")

        assert "goals" in result
        assert len(goals) > 0

        for goal_data in goals:
            goal = Goal(**goal_data)

            assert goal.goal
            assert goal.title
            assert goal.actions
            assert 0.0 <= goal.score <= 1.0