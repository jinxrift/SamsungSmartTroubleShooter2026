# Samsung Smart Troubleshooter

A FastAPI service that turns caller-supplied SIIS knowledge into grounded troubleshooting actions, matches applicable Samsung Settings deeplinks, and returns a `ContextDeeplinkResponse`.

## Architecture

```text
POST /v1/troubleshoot
  -> request validation
  -> cache lookup (normalized query + SIIS payload fingerprint)
  -> optional LLM extraction with strict source checks
       -> deterministic SIIS parsing when unavailable or invalid
  -> Pydantic goal validation
  -> catalog deeplink matching
  -> validated response cached and returned
```

The main modules are:

* `app/api/routes.py`: request contract, cache key, orchestration, and response validation.
* `app/services/siis_engine.py`: numbered-section and heading-based parsing; schema-shaped goals.
* `app/services/llm_engine.py`: optional OpenAI-compatible chat-completions request and SIIS-grounded output validation.
* `app/deeplink/matcher.py`: local phrase and token scoring over the deeplink catalog.
* `app/services/deeplink_matcher.py`: attaches actionable and validation links to step groups.
* `app/services/cache.py`: bounded, thread-safe in-memory cache with TTL and defensive copies.
* `app/models/schema.py`: Pydantic response models.

## Setup And Run

Python 3.10 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate         #On Windows  .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API listens on `http://127.0.0.1:8000`. `GET /health` returns `{"status":"ok"}`. Run the tests with:

```bash
python -m pytest -q
```

## LLM Configuration

LLM extraction is optional. Without all three settings, or if the provider call or payload validation fails, the deterministic SIIS parser is used.

```bash
export LLM_API_URL="https://api.openai.com/v1/chat/completions"
export LLM_API_KEY="..."
export LLM_MODEL="gpt-4o-mini"
```
```bash
For local LLM 
ollama pull qwen2.5:7b     #Or any other local LLM

export LLM_API_URL="http://localhost:11434/v1/chat/completions"
export LLM_API_KEY="ollama"
export LLM_MODEL="qwen2.5:7b"     #Or any other local LLM
```

The configured endpoint must accept an OpenAI-compatible chat-completions request with JSON response format. Returned action titles and steps must be present verbatim in the supplied SIIS content; otherwise the response is rejected and parsed deterministically.

## API Contract

`POST /v1/troubleshoot` accepts:

```json
{
  "query": "Enable Bluetooth scanning",
  "siis_response": {
    "title": "Bluetooth scanning",
    "content": "## Enable Bluetooth scanning\nEnable Bluetooth scanning."
  }
}
```

The response is wrapped in `contexts` and follows the `Goal`, `Action`, `StepGroup`, and deeplink models in `app/models/schema.py`. A representative matched response is:

```json
{
  "contexts": [
    {
      "goal": "Follow these steps to troubleshoot Bluetooth scanning",
      "title": "Bluetooth scanning",
      "actions": [
        {
          "actionName": "Enable Bluetooth scanning",
          "description": "It will help you troubleshoot this issue",
          "stepGroups": [
            {
              "steps": ["Enable Bluetooth scanning."],
              "actionableDeeplink": {
                "deeplink": "voiceassist://masked/act/c76675fafa",
                "description": "Enables Bluetooth scanning via device Settings on the device.",
                "message": "Enable Bluetooth",
                "classes": null,
                "originalType": "onURL"
              },
              "validationDeeplink": {
                "deeplink": "voiceassist://masked/val/6c79c8628b",
                "key": "Bluetooth scanning",
                "resultType": "boolean",
                "condition": "equal",
                "value": "True"
              }
            }
          ],
          "category": "auto"
        }
      ],
      "score": 0.95
    }
  ]
}
```

Invalid request bodies receive FastAPI's `422` validation response. Unrelated issues retain null deeplinks rather than receiving a weak catalog match.

## Data Flow And Constraints

* The caller supplies both the query and SIIS `title`/`content`; this service does not fetch SIIS records itself.
* Troubleshooting steps come from the supplied content. The deterministic parser strips heading/list formatting but does not add instructions.
* Deeplink URIs are copied from `data/deeplinks.json`. The current catalog contains masked placeholder URIs, not production links.
* A matched state-changing deeplink (`onURL`, `offURL`, or `updateURL`) marks a non-critical action as `auto`; navigation-only and unmatched actions remain `manual`.
* Cache keys include the normalized query and a fingerprint of the exact SIIS title/content, preventing a hit from reusing another payload's result. Cache entries are process-local and expire after five minutes by default.
* Matching is local phrase/token ranking, not an external semantic search service. New or ambiguous setting names may remain unmatched.
* LLM grounding checks reduce unsupported output, but this is not a substitute for reviewing SIIS source quality.

## Team Responsibilities

* API integration: request/response models, route orchestration, validation, and error behavior.
* SIIS and LLM: extraction prompts, deterministic parsing, grounding checks, and category policy.
* Deeplink matching: catalog indexing, specificity ranking, and actionable/validation link selection.
* Cache and testing: cache policy, regression coverage, and end-to-end verification.

## Completion Checklist

* [x] One canonical SIIS pipeline with a deterministic fallback and schema validation.
* [x] Optional structured LLM extraction with source-grounding validation.
* [x] Catalog matching with exact-setting preference and unrelated-query rejection.
* [x] Health and troubleshooting routes with payload-aware caching.
* [x] Cache normalization, TTL, size limits, and mutation isolation.
* [x] Tests for SIIS samples, deeplink matching, API behavior, health, and cache behavior.