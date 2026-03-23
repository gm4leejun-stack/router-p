# Phase 6 Cloud Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add one OpenAI-compatible cloud provider adapter for general and code models so cloud-routed requests use the same internal provider abstraction as local Ollama-backed requests.

**Architecture:** Extend the provider boundary introduced in Phase 5 with a cloud adapter that speaks OpenAI-compatible non-streaming chat completions over HTTP. Update the chat completion service so local targets still use Ollama, cloud-routed slots use the cloud adapter, and explicit cloud model names can also use the cloud adapter without changing the public API contract.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, httpx, pytest, FastAPI TestClient

---

## File Structure

- Create: `src/router_p/providers/cloud.py`
  - Implement the OpenAI-compatible cloud provider adapter.
- Modify: `src/router_p/providers/__init__.py`
  - Export the cloud provider.
- Modify: `src/router_p/services/chat_completion.py`
  - Inject and use both local and cloud providers.
- Modify: `src/router_p/domain/model_slots.py`
  - Add a helper to identify cloud slots.
- Modify: `tests/providers/test_cloud_adapter.py`
  - Verify cloud request payloads, auth headers, parsing, and error handling.
- Modify: `tests/services/test_chat_completion_service.py`
  - Verify cloud-routed and explicit cloud-model requests use the cloud provider.
- Modify: `tests/api/test_chat_completions.py`
  - Verify routed cloud requests preserve the public response envelope.
- Modify: `README.md`
  - Document required cloud env vars and current cloud behavior.
- Modify: `docs/development-plan.md`
  - Mark Phase 6 complete.
- Modify: `PROGRESS.md`
  - Advance status to Phase 7.

## Scope And Guardrails

- Phase 6 only adds the cloud adapter.
- Keep all provider calls non-streaming.
- Do not implement fallback policy yet; Phase 7 owns fallback.
- Do not remove or weaken Phase 5 Ollama integration.
- Cloud adapter should rely only on `cloud_base_url`, `cloud_api_key`, `cloud_general_model`, and `cloud_code_model`.

## Tasks

### Task 1: Add Cloud Provider Tests And Adapter

**Files:**
- Create: `src/router_p/providers/cloud.py`
- Modify: `tests/providers/test_cloud_adapter.py`

- [ ] Write failing tests for:
  - auth header `Authorization: Bearer <cloud_api_key>`
  - `POST /chat/completions`
  - OpenAI-style request payload with `model`, `messages`, `stream: false`
  - response parsing from `choices[0].message.content` and `usage`
  - HTTP error handling
- [ ] Run `python3 -m pytest tests/providers/test_cloud_adapter.py -v` and confirm failure
- [ ] Implement `OpenAICompatibleCloudProvider.complete(...)`
- [ ] Re-run `python3 -m pytest tests/providers/test_cloud_adapter.py -v`
- [ ] Commit

### Task 2: Route Cloud Targets Through The Cloud Provider

**Files:**
- Modify: `src/router_p/domain/model_slots.py`
- Modify: `src/router_p/services/chat_completion.py`
- Modify: `tests/services/test_chat_completion_service.py`

- [ ] Add failing tests for:
  - `router-auto` complex general requests use the cloud provider
  - `router-auto` complex code requests use the cloud provider
  - explicit configured cloud model names use the cloud provider
- [ ] Run `python3 -m pytest tests/services/test_chat_completion_service.py -v` and confirm failure
- [ ] Add `is_cloud_slot(...)`
- [ ] Update `ChatCompletionService` to accept `local_provider` and `cloud_provider`
- [ ] Route local slots to Ollama and cloud slots / explicit cloud models to the cloud provider
- [ ] Re-run `python3 -m pytest tests/services/test_chat_completion_service.py -v`
- [ ] Commit

### Task 3: Verify API Behavior With Cloud Provider Integration

**Files:**
- Modify: `tests/api/test_chat_completions.py`
- Modify: `src/router_p/api/router.py` only if minimal wiring extraction is needed

- [ ] Add failing API tests for:
  - `router-auto` complex general request returns configured cloud general model
  - `router-auto` complex code request returns configured cloud code model
  - explicit cloud model requests preserve the response envelope
- [ ] Monkeypatch provider constructors to avoid real network
- [ ] Run `python3 -m pytest tests/api/test_chat_completions.py -v` and confirm failure
- [ ] Make minimal wiring changes if needed
- [ ] Re-run `python3 -m pytest tests/api/test_chat_completions.py -v`
- [ ] Run `python3 -m pytest tests/api/test_authentication.py tests/api/test_health.py -v`
- [ ] Commit

### Task 4: Document And Verify Phase Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/development-plan.md`
- Modify: `PROGRESS.md`

- [ ] Update README with cloud env vars and note that cloud provider is now active for cloud-routed requests
- [ ] Mark Phase 6 complete in `docs/development-plan.md`
- [ ] Advance `PROGRESS.md` to Phase 7
- [ ] Run `python3 -m pytest -q`
- [ ] Run `python3 -c "from router_p.providers.cloud import OpenAICompatibleCloudProvider; print(OpenAICompatibleCloudProvider.__name__)"`
- [ ] Commit

## Verification Checklist

- [ ] Cloud adapter sends OpenAI-compatible non-stream requests.
- [ ] Cloud adapter attaches bearer auth.
- [ ] Cloud-routed requests use the cloud provider.
- [ ] Explicit cloud model names use the cloud provider.
- [ ] Local Ollama paths still work.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.providers.cloud import OpenAICompatibleCloudProvider; print(OpenAICompatibleCloudProvider.__name__)"` succeeds.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-23-phase-6-cloud-adapter.md`.
