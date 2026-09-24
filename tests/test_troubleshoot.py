import json
from pathlib import Path
from types import SimpleNamespace

from app.services.siis_engine import process_siis
from app.models.schema import Goal


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

        # Debug Record 8
        if i == 8:
            print("\n========== RECORD 8 CONTENT ==========")
            print(f"Title: {siis_response.title}")
            print("\nContent:")
            print(siis_response.content)
            print("======================================")

        result = process_siis(query, siis_response)

        goals = result.get("goals", [])

        print(f"\nRecord {i}")
        print(f"Query: {query}")
        print(
            f"Actions generated: "
            f"{len(goals[0]['actions']) if goals else 0}"
        )

        assert "goals" in result
        assert len(goals) > 0

        for goal_data in goals:
            goal = Goal(**goal_data)

            assert goal.goal
            assert goal.title
            assert goal.actions
            assert 0.0 <= goal.score <= 1.0