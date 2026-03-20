# Router-P v1 Development Plan

## Execution Rule

Work phases in order. Do not skip to a later phase until the current phase is complete and progress is updated.

## Phase 1: Project Scaffold and Configuration System

- Status: `complete`
- Goal: create the Python project skeleton, dependency setup, app entrypoint, and environment-based configuration
- Done when:
  - FastAPI app boots locally
  - config loads from environment
  - project structure is established

## Phase 2: Health Check and Authentication

- Status: `ready to start`
- Goal: add `GET /health` and single API key protection
- Done when:
  - health endpoint returns service readiness
  - unauthorized requests are rejected

## Phase 3: Non-Streaming Chat Completions

- Status: `not started`
- Goal: implement the base `POST /chat/completions` flow for non-streaming requests
- Done when:
  - OpenAI-style `messages` are accepted
  - a unified response shape is returned

## Phase 4: Rule Router and Model Slots

- Status: `not started`
- Goal: implement routing rules and internal model slot abstraction
- Done when:
  - rule-based routing covers common text, code, and complex task categories
  - model slot mapping is centralized

## Phase 5: Ollama Adapter

- Status: `not started`
- Goal: integrate local `Ollama` models
- Done when:
  - `phi4-mini`, `qwen3:4b`, and `qwen2.5-coder:7b` can be called through one provider interface

## Phase 6: Cloud Adapter

- Status: `not started`
- Goal: integrate one OpenAI-compatible cloud provider interface for general and code models
- Done when:
  - cloud requests can be routed through the same internal provider abstraction

## Phase 7: Boundary Classification and Fallback

- Status: `not started`
- Goal: add `phi4-mini` classification and cloud fallback policy
- Done when:
  - inconclusive tasks are classified by `phi4-mini`
  - local failures, timeouts, short outputs, and low-confidence text trigger fallback

## Phase 8: Streaming Support

- Status: `not started`
- Goal: add streaming response support for local and cloud calls
- Done when:
  - streaming requests work end to end through the OpenAI-compatible endpoint

## Phase 9: Logging and Error Handling

- Status: `not started`
- Goal: add decision-level logging and consistent error responses
- Done when:
  - routing logs are emitted with model and fallback metadata
  - provider and auth failures return stable API errors

## Phase 10: Compose, Docs, and OpenClaw Validation

- Status: `not started`
- Goal: add deployment assets and verify OpenClaw integration
- Done when:
  - `docker-compose.yml` and `.env.example` exist
  - README setup flow is complete
  - one end-to-end OpenClaw integration path is validated

## Next Coding Task

Begin with `Phase 2: Health Check and Authentication`.
