# Phase 9 Logging And Error Handling Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add decision-level logging and stable API error responses across auth, provider, routing, fallback, and streaming paths.

**Architecture:** Introduce a lightweight observability layer centered on structured route decision records plus a small API error contract. Keep logging isolated from business logic with helper functions or a narrow logger module, and centralize FastAPI exception handling so auth and provider failures return predictable JSON payloads while preserving successful behavior.

**Tech Stack:** Python 3.10+, FastAPI, Python `logging`, pytest, FastAPI TestClient

---

## File Structure

- Create: `src/router_p/observability/logging.py`
  - Build decision-level logging helpers and route metadata records.
- Create: `src/router_p/api/errors.py`
  - Define stable API error models and exception-to-response helpers.
- Modify: `src/router_p/app.py`
  - Register exception handlers and app logger configuration.
- Modify: `src/router_p/api/dependencies.py`
  - Return stable auth failures through the shared error contract.
- Modify: `src/router_p/services/chat_completion.py`
  - Emit route/fallback/provider decision logs.
- Modify: `src/router_p/api/router.py`
  - Ensure streaming and non-streaming provider failures map to shared API errors.
- Create: `tests/api/test_error_handling.py`
  - Verify stable JSON errors for auth and provider failures.
- Create: `tests/observability/test_decision_logging.py`
  - Verify route decision log payloads.
- Modify: `tests/api/test_authentication.py`
  - Update auth error expectations if needed.
- Modify: `tests/api/test_chat_completions.py`
  - Verify provider errors are wrapped consistently.
- Modify: `README.md`
  - Document logging/error behavior.
- Modify: `docs/development-plan.md`
  - Mark Phase 9 complete.
- Modify: `PROGRESS.md`
  - Advance status to Phase 10.

## Scope And Guardrails

- Phase 9 only adds logging and stable error handling.
- Do not alter routing strategy or provider selection rules.
- Keep log payloads concise and machine-readable.
- Avoid leaking secrets like API keys or full prompt bodies into logs.
- Preserve existing success responses exactly unless tests prove a necessary compatibility fix.

## Tasks

### Task 1: Add Stable API Error Contract

- [ ] Write failing tests for:
  - unauthorized auth response shape
  - provider failure response shape
  - streaming failure response shape before any chunks are emitted
- [ ] Implement `src/router_p/api/errors.py`
- [ ] Register exception handlers in `src/router_p/app.py`
- [ ] Re-run focused API error tests
- [ ] Commit

### Task 2: Add Decision Logging Helpers

- [ ] Write failing tests for decision log payload fields:
  - provider
  - selected model
  - route layer / rule
  - fallback reason
- [ ] Implement `src/router_p/observability/logging.py`
- [ ] Re-run logging tests
- [ ] Commit

### Task 3: Emit Logs From ChatCompletionService

- [ ] Write failing tests asserting logs for:
  - direct local route
  - boundary-classified route
  - local-to-cloud fallback
- [ ] Update `ChatCompletionService` to emit decision logs
- [ ] Re-run service and logging tests
- [ ] Commit

### Task 4: Wrap Auth And Provider Failures Consistently

- [ ] Update auth dependency to use the shared API error format
- [ ] Update router/service exception edges to raise shared provider errors
- [ ] Re-run API auth/chat error tests plus auth/health regressions
- [ ] Commit

### Task 5: Document And Verify Phase Completion

- [ ] Update README with logging and error behavior
- [ ] Mark Phase 9 complete in `docs/development-plan.md`
- [ ] Advance `PROGRESS.md` to Phase 10
- [ ] Run `python3 -m pytest -q`
- [ ] Run `python3 -c "from router_p.api.errors import ApiErrorDetail; print(ApiErrorDetail.__name__)"`
- [ ] Commit

## Verification Checklist

- [ ] Unauthorized requests return a stable JSON error shape.
- [ ] Provider failures return a stable JSON error shape.
- [ ] Decision logs include provider/model/rule/fallback metadata.
- [ ] Secrets are not logged.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.api.errors import ApiErrorDetail; print(ApiErrorDetail.__name__)"` succeeds.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-23-phase-9-logging-and-error-handling.md`.
