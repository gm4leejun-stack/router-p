# Phase 8 Streaming Support Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add end-to-end streaming support for local and cloud chat completions through the OpenAI-compatible `POST /chat/completions` endpoint.

**Architecture:** Extend the provider boundary with streaming methods that yield normalized text chunks. Add a streaming response path in the chat completion service and FastAPI route that emits OpenAI-style Server-Sent Events while preserving the existing non-streaming path. Keep the fallback and routing decisions from Phase 7 intact, but only stream the final selected execution path for this phase.

**Tech Stack:** Python 3.10+, FastAPI, Starlette `StreamingResponse`, httpx, pytest, FastAPI TestClient

---

## File Structure

- Modify: `src/router_p/providers/types.py`
  - Add provider-neutral streaming chunk types.
- Modify: `src/router_p/providers/ollama.py`
  - Add non-blocking local streaming translation from Ollama chat streams.
- Modify: `src/router_p/providers/cloud.py`
  - Add OpenAI-compatible cloud streaming translation.
- Create: `src/router_p/api/streaming.py`
  - Build OpenAI-style SSE frames from normalized provider chunks.
- Modify: `src/router_p/services/chat_completion.py`
  - Add a streaming orchestration path parallel to `create_completion`.
- Modify: `src/router_p/api/router.py`
  - Route `stream=true` requests to the streaming response path instead of rejecting them.
- Create: `tests/providers/test_streaming_providers.py`
  - Verify local and cloud provider stream translation.
- Modify: `tests/services/test_chat_completion_service.py`
  - Verify `stream_completion()` routing and provider selection.
- Modify: `tests/api/test_chat_completions.py`
  - Verify SSE output for local and cloud paths.
- Modify: `README.md`
  - Document streaming usage.
- Modify: `docs/development-plan.md`
  - Mark Phase 8 complete.
- Modify: `PROGRESS.md`
  - Advance status to Phase 9.

## Scope And Guardrails

- Phase 8 adds streaming only; do not mix in Phase 9 logging/error contract work.
- Keep non-streaming behavior unchanged.
- Do not implement mid-stream fallback switching in this phase. Routing/fallback selection should happen before streaming begins.
- SSE output should stay OpenAI-compatible enough for OpenClaw clients: chunk objects plus terminal `[DONE]`.

## Tasks

### Task 1: Add Streaming Provider Types And SSE Helpers

- [ ] Write failing tests for normalized stream chunk models and SSE formatting.
- [ ] Implement provider-neutral stream event types and `src/router_p/api/streaming.py`.
- [ ] Re-run focused tests and commit.

### Task 2: Add Local And Cloud Provider Streaming Methods

- [ ] Write failing tests for Ollama and cloud streaming translation.
- [ ] Implement `stream_complete(...)` on both providers.
- [ ] Re-run provider streaming tests and commit.

### Task 3: Add Streaming Orchestration To ChatCompletionService

- [ ] Write failing service tests for `stream_completion()` on local, cloud, and boundary-classified requests.
- [ ] Implement streaming orchestration using existing routing / boundary / fallback decisions.
- [ ] Re-run service tests and commit.

### Task 4: Enable API Streaming

- [ ] Add failing API tests asserting `stream=true` returns `text/event-stream` and emits OpenAI-style chunks.
- [ ] Replace the current `400 Streaming is not supported yet` path with `StreamingResponse`.
- [ ] Re-run API tests and auth/health regressions, then commit.

### Task 5: Document And Verify Phase Completion

- [ ] Update README with streaming example.
- [ ] Mark Phase 8 complete in `docs/development-plan.md`.
- [ ] Advance `PROGRESS.md` to Phase 9.
- [ ] Run `python3 -m pytest -q`.
- [ ] Run `python3 -c "from router_p.api.streaming import format_sse_done; print(format_sse_done())"`.
- [ ] Commit.

## Verification Checklist

- [ ] `stream=true` no longer returns `400`.
- [ ] Local streaming emits OpenAI-style SSE chunks.
- [ ] Cloud streaming emits OpenAI-style SSE chunks.
- [ ] Non-streaming behavior remains unchanged.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.api.streaming import format_sse_done; print(format_sse_done())"` succeeds.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-23-phase-8-streaming-support.md`.
