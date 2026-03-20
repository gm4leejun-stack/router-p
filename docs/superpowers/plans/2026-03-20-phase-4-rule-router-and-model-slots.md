# Phase 4 Rule Router And Model Slots Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a rule-based router and centralized model-slot abstraction so chat requests can be classified into stable internal targets before real provider integrations arrive.

**Architecture:** Keep routing pure and deterministic in this phase. Introduce a small routing domain with model-slot enums, route-decision models, and a rule router service that inspects validated chat requests and returns a selected internal slot plus match metadata. Update the Phase 3 placeholder completion flow so it uses the router result and slot mapping, but still produces an in-process deterministic response rather than calling Ollama or cloud APIs.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, pytest, FastAPI TestClient

---

## File Structure

- Create: `src/router_p/domain/model_slots.py`
  - Define the internal model-slot enum and slot metadata helpers.
- Create: `src/router_p/services/routing_rules.py`
  - Own the Phase 4 rule heuristics for text, code, and complex-task categorization.
- Create: `src/router_p/services/rule_router.py`
  - Apply routing rules and return a structured route decision.
- Modify: `src/router_p/services/chat_completion.py`
  - Replace direct request-model echoing with a router-aware placeholder completion path.
- Modify: `src/router_p/api/schemas/chat.py`
  - Extend response models if route metadata needs a stable internal home for tests or future logging hooks.
- Create: `tests/domain/test_model_slots.py`
  - Verify slot definitions and central mapping behavior.
- Create: `tests/services/test_rule_router.py`
  - Verify rule matches for common text, code, and complex-task prompts.
- Modify: `tests/services/test_chat_completion_service.py`
  - Assert the completion service now uses the routed slot and preserves the Phase 3 response contract.
- Modify: `tests/api/test_chat_completions.py`
  - Verify the API still returns the Phase 3 response envelope while routing internally.
- Modify: `README.md`
  - Document the new internal routing behavior at a high level.
- Modify: `docs/development-plan.md`
  - Mark Phase 4 complete after verification passes.
- Modify: `PROGRESS.md`
  - Advance status to Phase 5 after verification passes.

## Scope And Guardrails

- Phase 4 is only about local decision-making and model-slot abstraction.
- Do not call Ollama, cloud APIs, or classification models in this phase.
- Do not add fallback logic in this phase; fallback belongs to Phase 7.
- Keep rule matching explicit, readable, and easily editable. Prefer simple heuristics over overfit scoring systems.
- The external API response should stay compatible with Phase 3; route metadata remains internal unless tests prove an external field is required.

## Proposed Routing Model

- Internal model slots:
  - `local_text`
  - `local_code`
  - `cloud_text`
  - `cloud_code`
  - `local_boundary`
- Central slot mapping:
  - `local_text -> settings.local_general_model`
  - `local_code -> settings.local_code_model`
  - `cloud_text -> settings.cloud_general_model`
  - `cloud_code -> settings.cloud_code_model`
  - `local_boundary -> settings.local_boundary_model`
- Route decision payload:
  - selected slot
  - resolved model name, when configured
  - decision source: `rule`
  - matched rule name
  - short explanation string

## Suggested Rule Set For Phase 4

- Code-oriented route to `local_code` when:
  - prompt mentions code generation, debugging, refactoring, stack traces, files, functions, APIs, SQL, regex, tests, or programming languages
  - prompt includes fenced code blocks or obvious source snippets
- Complex/general route to `cloud_text` when:
  - prompt explicitly asks for deep reasoning, multi-step strategy, architecture comparison, or exhaustive analysis
  - prompt is unusually long or combines multiple subtasks
- Complex/code route to `cloud_code` when:
  - prompt requests large-scale codebase changes, deep debugging, or multi-file refactors with strong code cues
- Default route to `local_text` when no stronger rule matches
- Keep `local_boundary` defined and mapped, but unused in routing until Phase 7

## Task 1: Add Model Slot Tests And Central Slot Mapping

**Files:**
- Create: `src/router_p/domain/model_slots.py`
- Create: `tests/domain/test_model_slots.py`

- [ ] **Step 1: Write the failing model-slot tests**

```python
from router_p.config import Settings
from router_p.domain.model_slots import ModelSlot, resolve_model_slot


def test_model_slots_resolve_to_configured_model_names():
    settings = Settings(
        local_general_model="qwen3:4b",
        local_code_model="qwen2.5-coder:7b",
        local_boundary_model="phi4-mini",
        cloud_general_model="gpt-general",
        cloud_code_model="gpt-code",
    )

    assert resolve_model_slot(ModelSlot.LOCAL_TEXT, settings) == "qwen3:4b"
    assert resolve_model_slot(ModelSlot.LOCAL_CODE, settings) == "qwen2.5-coder:7b"
    assert resolve_model_slot(ModelSlot.LOCAL_BOUNDARY, settings) == "phi4-mini"
    assert resolve_model_slot(ModelSlot.CLOUD_TEXT, settings) == "gpt-general"
    assert resolve_model_slot(ModelSlot.CLOUD_CODE, settings) == "gpt-code"
```

- [ ] **Step 2: Run the model-slot tests to verify they fail before implementation**

Run: `python3 -m pytest tests/domain/test_model_slots.py -v`
Expected: FAIL with missing module or symbol errors

- [ ] **Step 3: Implement the minimal slot enum and resolver**

```python
from enum import StrEnum

from router_p.config import Settings


class ModelSlot(StrEnum):
    LOCAL_TEXT = "local_text"
    LOCAL_CODE = "local_code"
    CLOUD_TEXT = "cloud_text"
    CLOUD_CODE = "cloud_code"
    LOCAL_BOUNDARY = "local_boundary"


def resolve_model_slot(slot: ModelSlot, settings: Settings) -> str | None:
    mapping = {
        ModelSlot.LOCAL_TEXT: settings.local_general_model,
        ModelSlot.LOCAL_CODE: settings.local_code_model,
        ModelSlot.CLOUD_TEXT: settings.cloud_general_model,
        ModelSlot.CLOUD_CODE: settings.cloud_code_model,
        ModelSlot.LOCAL_BOUNDARY: settings.local_boundary_model,
    }
    return mapping[slot]
```

- [ ] **Step 4: Re-run the model-slot tests**

Run: `python3 -m pytest tests/domain/test_model_slots.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/router_p/domain/model_slots.py tests/domain/test_model_slots.py
git commit -m "feat: add model slot mapping"
```

## Task 2: Add Rule Router Tests And Decision Models

**Files:**
- Create: `src/router_p/services/routing_rules.py`
- Create: `src/router_p/services/rule_router.py`
- Create: `tests/services/test_rule_router.py`

- [ ] **Step 1: Write the failing rule-router tests**

```python
from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.domain.model_slots import ModelSlot
from router_p.services.rule_router import RuleRouter


def test_rule_router_routes_code_requests_to_local_code():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a Python function to parse JSON safely"}],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.LOCAL_CODE
    assert decision.rule_name == "code_keywords"


def test_rule_router_routes_complex_general_requests_to_cloud_text():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Compare three deployment architectures and give a step-by-step migration strategy"}],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.CLOUD_TEXT
    assert decision.rule_name == "complex_reasoning"


def test_rule_router_defaults_to_local_text():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a short welcome message"}],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.LOCAL_TEXT
    assert decision.rule_name == "default_local_text"
```

- [ ] **Step 2: Run the rule-router tests to verify they fail before implementation**

Run: `python3 -m pytest tests/services/test_rule_router.py -v`
Expected: FAIL with missing modules or classes

- [ ] **Step 3: Add a structured route-decision model and basic rule helpers**

```python
from pydantic import BaseModel

from router_p.domain.model_slots import ModelSlot


class RouteDecision(BaseModel):
    slot: ModelSlot
    rule_name: str
    reason: str
    decision_source: str = "rule"
```

- [ ] **Step 4: Implement the minimal readable rule router**

```python
class RuleRouter:
    def route(self, request: ChatCompletionRequest) -> RouteDecision:
        prompt = " ".join(message.content for message in request.messages).lower()

        if matches_code_request(prompt):
            return RouteDecision(
                slot=ModelSlot.LOCAL_CODE,
                rule_name="code_keywords",
                reason="matched code-oriented keywords",
            )
        if matches_complex_code_request(prompt):
            return RouteDecision(
                slot=ModelSlot.CLOUD_CODE,
                rule_name="complex_code",
                reason="matched complex code request signals",
            )
        if matches_complex_general_request(prompt):
            return RouteDecision(
                slot=ModelSlot.CLOUD_TEXT,
                rule_name="complex_reasoning",
                reason="matched complex general reasoning signals",
            )
        return RouteDecision(
            slot=ModelSlot.LOCAL_TEXT,
            rule_name="default_local_text",
            reason="no stronger routing rule matched",
        )
```

- [ ] **Step 5: Re-run the rule-router tests**

Run: `python3 -m pytest tests/services/test_rule_router.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/router_p/services/routing_rules.py src/router_p/services/rule_router.py tests/services/test_rule_router.py
git commit -m "feat: add rule-based routing decisions"
```

## Task 3: Make The Completion Service Router-Aware

**Files:**
- Modify: `src/router_p/services/chat_completion.py`
- Modify: `tests/services/test_chat_completion_service.py`

- [ ] **Step 1: Extend the completion-service tests to assert routed slot usage**

```python
def test_service_uses_route_decision_to_select_internal_model():
    settings = Settings(
        local_general_model="qwen3:4b",
        local_code_model="qwen2.5-coder:7b",
        cloud_general_model="gpt-general",
        cloud_code_model="gpt-code",
    )
    service = ChatCompletionService(settings=settings)
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a Python unit test for a login handler"}],
    )

    response = service.create_completion(request)

    assert response.model == "qwen2.5-coder:7b"
    assert response.choices[0].message.content.startswith("Echo:")
```

- [ ] **Step 2: Add a test that explicit non-auto model names bypass routing**

```python
def test_service_respects_explicit_model_without_rule_override():
    settings = Settings(local_general_model="qwen3:4b")
    service = ChatCompletionService(settings=settings)
    request = ChatCompletionRequest(
        model="custom-model",
        messages=[{"role": "user", "content": "Write a short greeting"}],
    )

    response = service.create_completion(request)

    assert response.model == "custom-model"
```

- [ ] **Step 3: Run the completion-service tests to verify they fail before integration**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: FAIL because the service does not yet use routing or slot resolution

- [ ] **Step 4: Inject settings and router dependencies into the service**

```python
class ChatCompletionService:
    def __init__(
        self,
        settings: Settings,
        router: RuleRouter | None = None,
    ) -> None:
        self._settings = settings
        self._router = router or RuleRouter()
```

- [ ] **Step 5: Resolve `router-auto` requests through the rule router**

```python
        if request.model == "router-auto":
            decision = self._router.route(request)
            response_model = resolve_model_slot(decision.slot, self._settings) or decision.slot.value
        else:
            response_model = request.model
```

- [ ] **Step 6: Re-run the completion-service tests**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/router_p/services/chat_completion.py tests/services/test_chat_completion_service.py
git commit -m "feat: route placeholder completions through model slots"
```

## Task 4: Keep The API Contract Stable While Routing Internally

**Files:**
- Modify: `src/router_p/api/router.py`
- Modify: `tests/api/test_chat_completions.py`
- Test: `tests/api/test_authentication.py`
- Test: `tests/api/test_health.py`

- [ ] **Step 1: Add failing API tests for router-auto behavior**

```python
def test_chat_completions_routes_router_auto_code_requests(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Refactor this Python function"}],
            "stream": False,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["model"] == "qwen2.5-coder:7b"
```


def test_chat_completions_routes_simple_text_requests_to_local_text(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "router-auto",
            "messages": [{"role": "user", "content": "Write a short welcome message"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["model"] == "qwen3:4b"
```

- [ ] **Step 2: Run the endpoint tests to verify they fail before the API wires in settings-aware service construction**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: FAIL on wrong model selection or service initialization mismatch

- [ ] **Step 3: Update the API endpoint to construct the service with app settings**

```python
@router.post("/chat/completions", ...)
async def create_chat_completion(
    payload: ChatCompletionRequest,
    request: Request,
) -> ChatCompletionResponse:
    if payload.stream:
        ...

    service = ChatCompletionService(settings=request.app.state.settings)
    return service.create_completion(payload)
```

- [ ] **Step 4: Re-run the API tests**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: PASS

- [ ] **Step 5: Run the existing auth and health tests**

Run: `python3 -m pytest tests/api/test_authentication.py tests/api/test_health.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/router_p/api/router.py tests/api/test_chat_completions.py
git commit -m "feat: apply rule routing to chat completions"
```

## Task 5: Document Routing Behavior And Record Phase Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/development-plan.md`
- Modify: `PROGRESS.md`

- [ ] **Step 1: Update the README to describe internal routing slots**

```markdown
- `router-auto` is the internal routing model name for Phase 4.
- Rule routing now maps requests to centralized slots for local text, local code, cloud text, and cloud code.
- Phase 4 still uses placeholder responses; provider integrations arrive in Phases 5 and 6.
```

- [ ] **Step 2: Add one short example showing `router-auto`**

```bash
curl http://127.0.0.1:8000/chat/completions \
  -H "Authorization: Bearer ${ROUTER_P_API_KEY:-dev-router-p-key}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "router-auto",
    "messages": [{"role": "user", "content": "Write a Python helper for retries"}],
    "stream": false
  }'
```

- [ ] **Step 3: Mark Phase 4 complete in `docs/development-plan.md`**

```markdown
## Phase 4: Rule Router and Model Slots

- Status: `complete`
```

- [ ] **Step 4: Advance `PROGRESS.md` to Phase 5**

```markdown
## Current Phase

Phase 4 complete. Ready for Phase 5.
```

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m pytest -q`
Expected: all tests PASS

- [ ] **Step 6: Run one smoke test for slot resolution**

Run: `python3 -c "from router_p.config import Settings; from router_p.domain.model_slots import ModelSlot, resolve_model_slot; print(resolve_model_slot(ModelSlot.LOCAL_CODE, Settings()))"`
Expected: prints the configured local code model, default `qwen2.5-coder:7b`

- [ ] **Step 7: Commit**

```bash
git add README.md docs/development-plan.md PROGRESS.md
git commit -m "docs: record phase 4 completion"
```

## Verification Checklist

- [ ] Central slot mapping resolves model names from settings.
- [ ] Rule routing selects `local_code` for common code-oriented prompts.
- [ ] Rule routing selects `cloud_text` or `cloud_code` for clearly complex tasks.
- [ ] `router-auto` requests return the routed model name in the Phase 3 response envelope.
- [ ] Explicit non-auto model names still bypass routing.
- [ ] Existing auth and health behavior remain unchanged.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.config import Settings; from router_p.domain.model_slots import ModelSlot, resolve_model_slot; print(resolve_model_slot(ModelSlot.LOCAL_CODE, Settings()))"` succeeds.

## Risks And Guardrails

- Keep rules conservative and easy to understand; Phase 7 will add a boundary classifier for ambiguous requests.
- Do not overload Phase 4 with provider-specific concerns or network code.
- Be careful with rule ordering: complex code prompts should not be swallowed by a simplistic code-keyword rule if your intended behavior is cloud escalation.
- If Phase 3 has not yet been executed, complete it first before implementing this plan; this phase assumes the non-stream chat endpoint and placeholder completion service already exist.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-20-phase-4-rule-router-and-model-slots.md`.

Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using `executing-plans`, batch execution with checkpoints

In this Codex session I did not run the plan-review subagent loop because that requires explicit delegation permission.
