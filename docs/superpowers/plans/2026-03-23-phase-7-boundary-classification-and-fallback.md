# Phase 7 Boundary Classification And Fallback Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add `phi4-mini` boundary classification for inconclusive requests and a first-pass fallback policy for local failures, timeouts, short outputs, and low-confidence local responses.

**Architecture:** Introduce a small orchestration layer above the existing rule router and provider adapters. When rule routing is inconclusive, the service should ask a lightweight boundary classifier which slot to use. For local executions, add a fallback evaluator that inspects provider failures and weak outputs, then reroutes to the configured cloud slot through the existing cloud adapter while preserving the same public response contract.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, httpx, pytest, FastAPI TestClient

---

## File Structure

- Create: `src/router_p/services/boundary_classifier.py`
  - Implement `phi4-mini`-style boundary classification through the local provider interface.
- Create: `src/router_p/services/fallback_policy.py`
  - Centralize fallback trigger rules and failure/quality checks.
- Modify: `src/router_p/services/rule_router.py`
  - Return an “inconclusive” decision for boundary cases instead of forcing a final slot.
- Modify: `src/router_p/services/chat_completion.py`
  - Orchestrate rule routing, boundary classification, local execution, and cloud fallback.
- Modify: `src/router_p/domain/model_slots.py`
  - Add any small helpers needed for fallback target selection.
- Create: `tests/services/test_boundary_classifier.py`
  - Verify classification prompts and normalized classification outputs.
- Create: `tests/services/test_fallback_policy.py`
  - Verify fallback triggers for local failure, timeout, short outputs, and low-confidence wording.
- Modify: `tests/services/test_rule_router.py`
  - Add coverage for inconclusive rule outcomes.
- Modify: `tests/services/test_chat_completion_service.py`
  - Verify boundary classification and fallback orchestration.
- Modify: `tests/api/test_chat_completions.py`
  - Verify end-to-end cloud fallback behavior through the API.
- Modify: `README.md`
  - Document boundary classification and fallback behavior.
- Modify: `docs/development-plan.md`
  - Mark Phase 7 complete.
- Modify: `PROGRESS.md`
  - Advance status to Phase 8.

## Scope And Guardrails

- Phase 7 only adds boundary classification and fallback policy.
- Do not add streaming in this phase.
- Do not add logging/structured error surface changes in this phase; Phase 9 owns that.
- Boundary classification should only run when rules are inconclusive, not on every request.
- Fallback should initially target cloud slots only for local execution paths, not the reverse.

## Proposed Behavior

- Rule router may now return:
  - explicit slot decision
  - or an inconclusive boundary decision, e.g. `slot=local_boundary` plus `decision_source="boundary"`
- Boundary classifier input:
  - request messages
  - candidate slot labels
- Boundary classifier output:
  - `local_text`
  - `local_code`
  - `cloud_text`
  - `cloud_code`
- Fallback triggers for local executions:
  - provider exception
  - timeout exception
  - completion too short relative to prompt
  - low-confidence wording such as “not sure”, “I think”, “maybe”, “possibly”

## Task 1: Add Boundary Classifier Tests And Service

**Files:**
- Create: `src/router_p/services/boundary_classifier.py`
- Create: `tests/services/test_boundary_classifier.py`

- [ ] Write failing tests for:
  - classifier builds a request using `settings.local_boundary_model`
  - classifier normalizes provider text like `cloud_code` into a `ModelSlot`
  - invalid classifier output falls back to `local_text`
- [ ] Run `python3 -m pytest tests/services/test_boundary_classifier.py -v` and confirm failure
- [ ] Implement the minimal boundary classifier service
- [ ] Re-run `python3 -m pytest tests/services/test_boundary_classifier.py -v`
- [ ] Commit

### Task 2: Add Fallback Policy Tests And Rules

**Files:**
- Create: `src/router_p/services/fallback_policy.py`
- Create: `tests/services/test_fallback_policy.py`

- [ ] Write failing tests for:
  - local exception triggers fallback
  - timeout triggers fallback
  - short outputs trigger fallback
  - low-confidence wording triggers fallback
  - healthy local outputs do not trigger fallback
- [ ] Run `python3 -m pytest tests/services/test_fallback_policy.py -v` and confirm failure
- [ ] Implement the minimal fallback policy
- [ ] Re-run `python3 -m pytest tests/services/test_fallback_policy.py -v`
- [ ] Commit

### Task 3: Make Rule Router Return Inconclusive Boundary Decisions

**Files:**
- Modify: `src/router_p/services/rule_router.py`
- Modify: `tests/services/test_rule_router.py`

- [ ] Add failing tests for prompts that are intentionally ambiguous and should route to boundary classification
- [ ] Run `python3 -m pytest tests/services/test_rule_router.py -v` and confirm failure
- [ ] Update `RuleRouter` to emit an inconclusive/boundary decision
- [ ] Re-run `python3 -m pytest tests/services/test_rule_router.py -v`
- [ ] Commit

### Task 4: Orchestrate Boundary Classification And Fallback In ChatCompletionService

**Files:**
- Modify: `src/router_p/services/chat_completion.py`
- Modify: `tests/services/test_chat_completion_service.py`

- [ ] Add failing tests for:
  - boundary requests call the boundary classifier before provider selection
  - local provider exception falls back to cloud provider
  - short local output falls back to cloud provider
  - low-confidence local output falls back to cloud provider
- [ ] Run `python3 -m pytest tests/services/test_chat_completion_service.py -v` and confirm failure
- [ ] Inject `BoundaryClassifier` and `FallbackPolicy`
- [ ] Re-run `python3 -m pytest tests/services/test_chat_completion_service.py -v`
- [ ] Commit

### Task 5: Verify API Behavior And Record Phase Completion

**Files:**
- Modify: `tests/api/test_chat_completions.py`
- Modify: `README.md`
- Modify: `docs/development-plan.md`
- Modify: `PROGRESS.md`

- [ ] Add API tests for boundary classification and fallback behavior using provider/classifier stubs
- [ ] Run `python3 -m pytest tests/api/test_chat_completions.py -v`
- [ ] Run `python3 -m pytest tests/api/test_authentication.py tests/api/test_health.py -v`
- [ ] Update README with fallback and boundary classification notes
- [ ] Mark Phase 7 complete in `docs/development-plan.md`
- [ ] Advance `PROGRESS.md` to Phase 8
- [ ] Run `python3 -m pytest -q`
- [ ] Run `python3 -c "from router_p.services.fallback_policy import FallbackPolicy; print(FallbackPolicy.__name__)"`
- [ ] Commit

## Verification Checklist

- [ ] Inconclusive requests invoke boundary classification.
- [ ] Boundary classifier output maps to internal model slots.
- [ ] Local provider failures trigger cloud fallback.
- [ ] Short or low-confidence local outputs trigger cloud fallback.
- [ ] Local and cloud provider paths both still work.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.services.fallback_policy import FallbackPolicy; print(FallbackPolicy.__name__)"` succeeds.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-23-phase-7-boundary-classification-and-fallback.md`.
