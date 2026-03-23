# Router-P Phase 10 Compose Docs Validation Design

**Goal:** close out v1 by making Router-P deployable with Docker Compose, configurable from a checked-in template, and verifiable through OpenClaw-compatible integration checks.

## Scope

Phase 10 is a delivery and validation phase, not a routing feature phase. It adds the deployment assets, the environment template, and repository-level validation that proves Router-P exposes the OpenAI-compatible contract OpenClaw needs.

Included:
- `docker-compose.yml` for running Router-P
- `.env.example` with the minimum supported configuration
- integration tests for deployment-facing API behavior
- README setup, deployment, validation, and troubleshooting updates
- progress/docs updates marking v1 complete

Excluded:
- new routing rules
- new providers
- real OpenClaw process automation
- production hardening beyond v1 scope

## Recommended Approach

Use a compose file that starts only Router-P and expects Ollama to stay external. This matches the existing requirements, avoids coupling to a second local runtime inside Compose, and keeps the deployment path small enough for self-hosting users to reason about.

For validation, add repository integration tests that exercise the public API contract rather than internal service behavior. That gives us repeatable coverage for the exact surface OpenClaw uses without turning the test suite into a fragile end-to-end environment orchestration problem.

## Components

### Compose Asset

`docker-compose.yml` defines one `router-p` service:
- builds from the repository
- exposes the FastAPI port
- reads variables from `.env`
- performs a health check against `/health`
- starts the existing app entrypoint

This phase may also require a minimal `Dockerfile` if the repository does not already have one. The Docker image should be intentionally simple: install the package, expose the API port, and run `uvicorn router_p.main:app`.

### Environment Template

`.env.example` documents:
- API key
- environment name
- listen host/port if supported by launch command
- Ollama base URL
- local model names
- optional cloud base URL / API key / cloud model names
- request timeout

The template should remain safe to commit and should guide a user toward the smallest working configuration first.

### Integration Validation

`tests/integration/` validates the deployment-facing API contract:
- `GET /health` returns readiness metadata
- protected routes reject missing auth with the stable error envelope
- `POST /chat/completions` returns OpenAI-style non-streaming responses
- `POST /chat/completions` returns SSE plus `[DONE]` when `stream=true`
- provider failure paths preserve the stable provider error envelope

These tests should avoid real network dependencies by monkeypatching providers or using app-level test fixtures. The goal is to validate contract shape, not external providers.

### README Closeout

README should become the primary operator document for v1:
- prerequisites
- environment setup from `.env.example`
- local dev startup
- Docker Compose startup
- curl verification commands
- OpenClaw connection settings example
- common failure modes and fixes

## Data Flow

1. Operator copies `.env.example` to `.env` and fills in local/cloud variables.
2. `docker compose up` starts Router-P.
3. Router-P exposes `/health` publicly and protects `/` and `/chat/completions` with Bearer auth.
4. OpenClaw or a curl client sends OpenAI-style chat requests to Router-P.
5. Router-P handles rule routing, boundary classification, fallback, streaming, logging, and stable API errors using the already-completed phases.

## Error Handling

Phase 9 introduced the stable API error envelope. Phase 10 preserves and documents it:
- auth failure: `401` with `error.code=unauthorized`
- provider failure: `502` with `error.code=provider_error`

Compose and README guidance should explicitly tell users to validate these responses so misconfiguration is easy to identify.

## Testing Strategy

Follow TDD for any code changes required by Phase 10:
- write failing integration or asset tests first
- implement the minimum Docker/deployment changes
- rerun focused tests
- finish with full `pytest`

Validation commands at completion:
- `python3 -m pytest -q`
- if Docker is available, a lightweight compose config check such as `docker compose config`

## Risks And Controls

- Docker may be unavailable in the execution environment.
  Control: keep repository tests authoritative and treat compose runtime verification as best-effort.
- README can drift from code.
  Control: only document commands backed by the checked-in assets and tested routes.
- Deployment files can grow beyond v1 needs.
  Control: keep Compose single-service and avoid unrelated infrastructure.
