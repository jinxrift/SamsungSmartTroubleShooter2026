# samsung-smart-troubleshooter
# Samsung Smart Guided Troubleshooting Engine

An AI-powered troubleshooting engine developed for the **Samsung PRISM Gen AI Hackathon 3.0**.

The system exposes a REST API that receives a user's Samsung device troubleshooting query together with a SIIS (Samsung Internal Knowledge Store) response, converts the knowledge into structured troubleshooting actions and steps, matches relevant Samsung Settings deeplinks, and returns a schema-compliant `ContextDeeplinkResponse`.

---

## Project Objective

The core API endpoint is:

```text
POST /v1/troubleshoot
```

The API is responsible for:

1. Understanding the user's troubleshooting query.
2. Processing the supplied SIIS knowledge.
3. Extracting relevant troubleshooting goals, actions, and steps.
4. Classifying actions as `auto`, `manual`, or `critical`.
5. Matching applicable steps to Samsung Settings deeplinks.
6. Including validation deeplinks when available.
7. Returning a valid `ContextDeeplinkResponse`.
8. Supporting caching for repeated and semantically similar queries.
9. Generalizing to unseen troubleshooting scenarios.

The SIIS response is the source of truth for troubleshooting steps. The system must not invent troubleshooting instructions that are not supported by the supplied SIIS content.

---

## Team Responsibilities

### Person 1 — Backend / Integration

Responsible for:

* FastAPI application
* REST endpoints
* Request/response models
* Pydantic validation
* API integration
* Error handling
* Integrating SIIS, deeplink, and cache modules
* Final response generation

### Person 2 — SIIS + LLM

Responsible for:

* Understanding SIIS responses
* LLM prompting
* Extracting goals, actions, categories, and steps
* Ensuring generated steps remain grounded in SIIS
* Handling unseen SIIS content

### Person 3 — Deeplink Matching

Responsible for:

* Processing `deeplinks.json`
* Searching/indexing deeplink metadata
* Semantic matching between troubleshooting steps and deeplinks
* Handling actionable deeplinks
* Handling validation deeplinks
* Implementing the required fallback

### Person 4 — Cache + Testing

Responsible for:

* Query normalization
* Response caching
* Semantic/paraphrase cache matching
* Latency testing
* Cache hit-rate testing
* Schema/output testing
* Edge cases and unseen-scenario testing
* Query variation generation/testing

---

## Project Structure

```text
samsung-smart-troubleshooter/
│
├── app/
│   ├── __init__.py
│   ├── main.py
│   ├── models.py
│   ├── routes.py
│   │
│   └── services/
│       ├── __init__.py
│       ├── siis_engine.py
│       ├── deeplink_matcher.py
│       └── cache.py
│
├── data/
│   ├── siis_responses.json
│   └── deeplinks.json
│
├── tests/
│
├── .env
├── .gitignore
├── requirements.txt
└── README.md
```

### `app/main.py`

Application entry point for the FastAPI server.

### `app/models.py`

Pydantic request and response models.

The final response must follow Samsung's required `ContextDeeplinkResponse` schema.

### `app/routes.py`

Defines API endpoints such as:

```text
GET  /health
POST /v1/troubleshoot
```

### `app/services/siis_engine.py`

Handles SIIS processing and troubleshooting-step extraction.

### `app/services/deeplink_matcher.py`

Matches troubleshooting steps to entries in Samsung's deeplink catalog.

### `app/services/cache.py`

Handles repeated and semantically similar queries.

### `data/siis_responses.json`

Samsung-provided sample SIIS responses used for development and testing.

### `data/deeplinks.json`

Samsung-provided masked Galaxy Settings deeplink catalog.

### `tests/`

Automated tests for API behavior, schema validity, deeplink matching, caching, and edge cases.

---

## API Flow

```text
User Query + SIIS Response
          |
          v
     FastAPI API
          |
          v
    Cache Check
      /       \
    HIT       MISS
     |          |
     |          v
     |     SIIS / LLM Engine
     |          |
     |          v
     |    Actions + Steps
     |          |
     |          v
     |    Deeplink Matcher
     |          |
     |          v
     |    Response Builder
     |          |
     +----------+
          |
          v
   Pydantic Validation
          |
          v
 ContextDeeplinkResponse
```

---

## Samsung Response Structure

The expected response hierarchy is:

```text
ContextDeeplinkResponse
└── contexts[]
    └── Goal
        ├── goal
        ├── title
        ├── score
        └── actions[]
            └── Action
                ├── actionName
                ├── description
                ├── category
                └── stepGroups[]
                    └── StepGroup
                        ├── steps[]
                        ├── actionableDeeplink
                        └── validationDeeplink
```

---

## Action Categories

### `auto`

An action that can be performed through a deeplink.

An `auto` action must have an `actionableDeeplink`.

### `manual`

An action that requires the user to manually follow instructions.

### `critical`

A critical or safety-related action. It is treated similarly to a manual action for deeplink purposes.

---

## Important Constraints

* Troubleshooting steps must be derived from the supplied SIIS content.
* Do not invent troubleshooting steps.
* Deeplinks must be selected from the provided deeplink catalog when applicable.
* Masked deeplink URIs must be preserved exactly.
* Do not expose real URLs in the response.
* The response must conform to the required Pydantic schema.
* `goal` must follow the required format.
* `title` must contain 2–3 words.
* Action descriptions must start with `It will` and contain 5–7 words.
* Scores must be between `0.0` and `1.0`.
* Step groups must contain non-empty steps.
* `auto` actions require an actionable deeplink.
* The API must provide a working `/health` endpoint.

---

## Development Setup

Python 3.10+ is required.

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it on Windows:

```bash
.venv\Scripts\activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run the API:

```bash
uvicorn app.main:app --reload
```

The API should then be available locally through the FastAPI server.

---

## Environment Variables

API keys and other secrets must be stored in environment variables or `.env`.

Example:

```text
LLM_API_KEY=your_key_here
```

Never commit `.env` or API keys to GitHub.

---

## Git Workflow

The `main` branch contains the integrated project.

Each team member works on a separate feature branch:

```text
main
├── backend
├── siis-llm
├── deeplink-matcher
└── cache-testing
```

Workflow:

```bash
git checkout -b feature-name
git add .
git commit -m "Describe the change"
git push -u origin feature-name
```

Create a Pull Request and merge into `main` after the implementation has been tested.

---

## Evaluation Focus

The system is designed around the major evaluation areas:

* Schema and formatting validity
* Deeplink validity and coverage
* Cache performance and latency
* Generalization to unseen scenarios
* Query variation quality

The implementation should therefore prioritize correctness, robustness, semantic matching, caching, and strict schema compliance rather than only the frontend presentation.

---

## Team

Samsung PRISM Gen AI Hackathon 3.0

## Team File Division

Each member should primarily work only on their assigned files. Coordinate with the team before modifying shared files.

### Person 1 — Backend / Integration

**Branch:** `backend`

Files:

* `app/main.py`
* `app/api/routes.py`

Responsibilities:

* FastAPI setup
* API endpoints
* Integration of SIIS engine, deeplink matcher, and cache
* Final response validation

### Person 2 — SIIS + LLM

**Branch:** `siis-llm`

File:

* `app/services/siis_engine.py`

Responsibilities:

* SIIS response processing
* Troubleshooting logic
* LLM integration
* Generate troubleshooting structure

### Person 3 — Deeplink Matching

**Branch:** `deeplink-matcher`

File:

* `app/services/deeplink_matcher.py`

Responsibilities:

* Deeplink loading
* Semantic matching
* Selecting appropriate Samsung deeplinks
* Handling unmatched deeplinks

### Person 4 — Cache + Testing

**Branch:** `cache-testing`

Files:

* `app/services/cache.py`
* `tests/test_health.py`
* `tests/test_troubleshoot.py`
* `tests/test_deeplink.py`
* `tests/test_cache.py`

Responsibilities:

* Query caching
* Cache hit handling
* Performance testing
* Automated tests

### Shared Files

These files are common to the whole team:

* `app/models/schema.py` — Samsung-provided schema; do not modify without team coordination
* `data/siis_responses.json` — Samsung-provided data; do not modify
* `data/deeplinks.json` — Samsung-provided data; do not modify
* `requirements.txt`
* `README.md`

**Important:** Do not directly push to `main`. Work on your assigned branch and create a Pull Request when your changes are ready.

**Team Members**

* Person 1 — Backend / Integration
* Person 2 — SIIS + LLM
* Person 3 — Deeplink Matching
* Person 4 — Cache + Testing
