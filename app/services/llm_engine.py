from app.services.llm_engine import extract_with_llm


def process_siis(query, siis_response):

    llm_result = extract_with_llm(
        query,
        siis_response.title,
        siis_response.content
    )

    actions = []

    for item in llm_result["actions"]:

        action = {
            "actionName": item["actionName"],
            "description": item["description"],
            "stepGroups": [
                {
                    "steps": item["steps"],
                    "actionableDeeplink": None,
                    "validationDeeplink": None
                }
            ],
            "category": item.get("category", "manual")
        }

        actions.append(action)

    return {
        "goals": [
            {
                "goal": f"Follow these steps to perform this {siis_response.title} Troubleshooting",
                "title": siis_response.title,
                "actions": actions,
                "score": 0.95
            }
        ]
    }