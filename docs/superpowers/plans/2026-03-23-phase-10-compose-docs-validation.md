# Phase 10 Compose Docs Validation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add deployment assets, environment templates, and OpenClaw-compatible integration validation to close out Router-P v1.

**Architecture:** Keep deployment intentionally small: Docker Compose starts Router-P only, while Ollama remains an external dependency. Validate the public API contract through integration tests that cover health, auth, non-streaming chat, streaming chat, and stable provider errors without introducing real external provider dependencies.

**Tech Stack:** Python 3.10+, FastAPI, pytest, Docker Compose, uvicorn

---

## File Structure

- Create: `Dockerfile`
  - Minimal image for running Router-P with uvicorn.
- Create: `docker-compose.yml`
  - Single-service compose definition for Router-P plus health check and env loading.
- Create: `.env.example`
  - Safe environment template for local/self-hosted setup.
- Create: `tests/integration/test_deployment_contract.py`
  - Deployment-facing contract tests for health, auth, chat, stream, and provider errors.
- Modify: `README.md`
  - Document env setup, Compose usage, curl verification, OpenClaw configuration, and troubleshooting.
- Modify: `docs/development-plan.md`
  - Mark Phase 10 complete and v1 finished.
- Modify: `PROGRESS.md`
  - Mark overall status complete.

## Scope And Guardrails

- Phase 10 is deployment/documentation/integration validation only.
- Do not change routing logic or provider-selection behavior unless a deployment test reveals a real contract issue.
- Keep Docker assets minimal and readable.
- Assume Docker may not be runnable in every environment; repository tests remain the primary verification source.

## Tasks

### Task 1: Add Deployment Contract Tests

- [ ] Write failing tests in `tests/integration/test_deployment_contract.py` for:
  - health readiness response
  - unauthorized stable error envelope
  - non-streaming OpenAI-style chat response
  - streaming SSE response ending with `[DONE]`
  - provider failure stable error envelope
- [ ] Run `python3 -m pytest -q tests/integration/test_deployment_contract.py`
- [ ] Implement the minimum fixture/helpers needed so those tests pass
- [ ] Re-run `python3 -m pytest -q tests/integration/test_deployment_contract.py`
- [ ] Commit

### Task 2: Add Docker Deployment Assets

- [ ] Write failing asset tests or assertions if needed for required files/contents
- [ ] Create `Dockerfile`
- [ ] Create `docker-compose.yml`
- [ ] Create `.env.example`
- [ ] Run focused verification:
  - `python3 -m pytest -q tests/integration/test_deployment_contract.py`
  - `docker compose config` if Docker is available
- [ ] Commit

### Task 3: Update Operator Documentation

- [ ] Update `README.md` with:
  - prerequisites
  - `.env.example` copy/setup flow
  - local run instructions
  - Docker Compose run instructions
  - curl verification examples
  - OpenClaw base URL / API key configuration notes
  - troubleshooting notes for auth/provider errors
- [ ] Update `docs/development-plan.md` to mark Phase 10 complete
- [ ] Update `PROGRESS.md` to mark Router-P v1 complete
- [ ] Re-read docs to ensure commands and file names match checked-in assets
- [ ] Commit

### Task 4: Final Verification And Closeout

- [ ] Run `python3 -m pytest -q`
- [ ] Run `python3 -c "from router_p.app import create_app; print(create_app().title)"`
- [ ] Run `docker compose config` if available in the environment
- [ ] Update `/Users/smy/.codex/memories/router-p.md` with Phase 10 completion and latest commit
- [ ] Commit

## Verification Checklist

- [ ] Repository contains `Dockerfile`, `docker-compose.yml`, and `.env.example`.
- [ ] Integration tests verify the OpenClaw-facing API contract.
- [ ] README has complete setup and verification instructions.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.app import create_app; print(create_app().title)"` succeeds.
- [ ] `docker compose config` succeeds if Docker is available.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-23-phase-10-compose-docs-validation.md`.
