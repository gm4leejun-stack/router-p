# Phase 5 Ollama Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Integrate local Ollama models behind one provider interface so `phi4-mini`, `qwen3:4b`, and `qwen2.5-coder:7b` can be called through Router-P’s existing routing and completion flow.

**Architecture:** Introduce a small provider boundary with a provider-neutral completion input/output contract, then implement an Ollama-specific adapter using `httpx`. Update the current chat completion service so local slots and explicit local models call Ollama through the provider interface, while unresolved cloud slots remain intentionally out of scope for this phase and continue using placeholder behavior or a clearly bounded temporary path until Phase 6 adds the cloud adapter.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, httpx, pytest, FastAPI TestClient

---

## File Structure

- Create: `src/router_p/providers/types.py`
  - Define provider-neutral request and response models for chat generation.
- Create: `src/router_p/providers/ollama.py`
  - Implement the Ollama adapter and response translation logic.
- Create: `src/router_p/providers/__init__.py`
  - Expose provider entrypoints cleanly.
- Modify: `src/router_p/services/chat_completion.py`
  - Replace local placeholder completions with Ollama-backed provider calls for local models.
- Modify: `src/router_p/domain/model_slots.py`
  - Add a helper that distinguishes local slots from cloud slots if needed.
- Create: `tests/providers/test_ollama_adapter.py`
  - Verify Ollama request payload shape, response parsing, and error handling.
- Modify: `tests/services/test_chat_completion_service.py`
  - Verify local slots now call the provider adapter and preserve response shape.
- Modify: `tests/api/test_chat_completions.py`
  - Verify local routed and explicit local-model requests flow through the adapter.
- Modify: `README.md`
  - Document Ollama requirements and local-model behavior.
- Modify: `docs/development-plan.md`
  - Mark Phase 5 complete after verification passes.
- Modify: `PROGRESS.md`
  - Advance status to Phase 6 after verification passes.

## Scope And Guardrails

- Phase 5 only adds the local Ollama adapter.
- Do not implement cloud API calls in this phase.
- Do not add fallback behavior yet; that belongs to Phase 7.
- Keep Phase 4 routing rules intact.
- For cloud-routed slots in this phase:
  - preserve current placeholder behavior, or
  - keep them on a temporary non-provider path with explicit comments saying Phase 6 replaces it.
- Do not add streaming provider logic yet; keep the adapter non-streaming only.

## Proposed Provider Contract

- Provider request:
  - `model: str`
  - `messages: list[ChatMessage]`
  - `timeout_seconds: float`
- Provider response:
  - `content: str`
  - `prompt_tokens: int`
  - `completion_tokens: int`
  - `raw_model: str`
- Translation rules:
  - Router-P request models stay unchanged.
  - Provider results are translated into the existing `ChatCompletionResponse`.
  - Ollama-specific HTTP details stay inside `src/router_p/providers/ollama.py`.

## Ollama API Assumption

- Use Ollama’s chat endpoint for non-stream requests:
  - `POST {settings.ollama_base_url}/api/chat`
- Request payload shape:
  - `model`
  - `messages`
  - `stream: false`
- Response fields expected:
  - assistant message content
  - prompt and eval token counts when available
- If Ollama omits token counts, compute conservative placeholder counts inside the adapter.

## Task 1: Add Provider Type Tests And Neutral Provider Models

**Files:**
- Create: `src/router_p/providers/types.py`
- Create: `tests/providers/test_ollama_adapter.py`

- [ ] **Step 1: Write the failing provider-type tests**

```python
from router_p.api.schemas.chat import ChatMessage
from router_p.providers.types import ProviderChatRequest, ProviderChatResponse


def test_provider_chat_request_accepts_model_messages_and_timeout():
    request = ProviderChatRequest(
        model="qwen3:4b",
        messages=[ChatMessage(role="user", content="Hello")],
        timeout_seconds=30.0,
    )

    assert request.model == "qwen3:4b"
    assert request.timeout_seconds == 30.0


def test_provider_chat_response_holds_normalized_result_fields():
    response = ProviderChatResponse(
        content="Hello back",
        prompt_tokens=3,
        completion_tokens=2,
        raw_model="qwen3:4b",
    )

    assert response.content == "Hello back"
    assert response.raw_model == "qwen3:4b"
```

- [ ] **Step 2: Run the provider tests to verify they fail before implementation**

Run: `python3 -m pytest tests/providers/test_ollama_adapter.py -v`
Expected: FAIL with missing provider types module

- [ ] **Step 3: Implement the minimal provider request and response models**

```python
from pydantic import BaseModel, Field

from router_p.api.schemas.chat import ChatMessage


class ProviderChatRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[ChatMessage]
    timeout_seconds: float = Field(gt=0)


class ProviderChatResponse(BaseModel):
    content: str
    prompt_tokens: int
    completion_tokens: int
    raw_model: str
```

- [ ] **Step 4: Re-run the provider tests**

Run: `python3 -m pytest tests/providers/test_ollama_adapter.py -v`
Expected: PASS for the provider type tests

- [ ] **Step 5: Commit**

```bash
git add src/router_p/providers/types.py tests/providers/test_ollama_adapter.py
git commit -m "feat: add provider request and response types"
```

## Task 2: Add Ollama Adapter Tests And Minimal HTTP Translation

**Files:**
- Create: `src/router_p/providers/ollama.py`
- Modify: `tests/providers/test_ollama_adapter.py`

- [ ] **Step 1: Extend the provider tests with an Ollama success case**

```python
import httpx

from router_p.api.schemas.chat import ChatMessage
from router_p.providers.ollama import OllamaChatProvider
from router_p.providers.types import ProviderChatRequest


def test_ollama_provider_sends_chat_request_and_parses_response():
    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/chat"
        payload = json.loads(request.content.decode())
        assert payload["model"] == "qwen3:4b"
        assert payload["stream"] is False
        return httpx.Response(
            200,
            json={
                "model": "qwen3:4b",
                "message": {"role": "assistant", "content": "Hello back"},
                "prompt_eval_count": 3,
                "eval_count": 2,
            },
        )

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama.test")
    provider = OllamaChatProvider(client=client, base_url="http://ollama.test")

    response = provider.complete(
        ProviderChatRequest(
            model="qwen3:4b",
            messages=[ChatMessage(role="user", content="Hello")],
            timeout_seconds=30.0,
        )
    )

    assert response.content == "Hello back"
    assert response.prompt_tokens == 3
    assert response.completion_tokens == 2
```

- [ ] **Step 2: Add an adapter error test for non-200 or malformed responses**

```python
def test_ollama_provider_raises_on_http_error():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, json={"error": "boom"})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://ollama.test")
    provider = OllamaChatProvider(client=client, base_url="http://ollama.test")

    with pytest.raises(RuntimeError, match="Ollama request failed"):
        provider.complete(
            ProviderChatRequest(
                model="qwen3:4b",
                messages=[ChatMessage(role="user", content="Hello")],
                timeout_seconds=30.0,
            )
        )
```

- [ ] **Step 3: Run the provider tests to verify they fail before implementation**

Run: `python3 -m pytest tests/providers/test_ollama_adapter.py -v`
Expected: FAIL with missing `OllamaChatProvider`

- [ ] **Step 4: Implement the minimal Ollama adapter**

```python
class OllamaChatProvider:
    def __init__(self, base_url: str, client: httpx.Client | None = None) -> None:
        self._base_url = base_url.rstrip("/")
        self._client = client or httpx.Client(base_url=self._base_url)

    def complete(self, request: ProviderChatRequest) -> ProviderChatResponse:
        response = self._client.post(
            "/api/chat",
            json={
                "model": request.model,
                "messages": [message.model_dump() for message in request.messages],
                "stream": False,
            },
            timeout=request.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError("Ollama request failed")

        payload = response.json()
        content = payload["message"]["content"]
        prompt_tokens = payload.get("prompt_eval_count") or len(" ".join(m.content for m in request.messages).split())
        completion_tokens = payload.get("eval_count") or len(content.split())

        return ProviderChatResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            raw_model=payload.get("model", request.model),
        )
```

- [ ] **Step 5: Re-run the provider tests**

Run: `python3 -m pytest tests/providers/test_ollama_adapter.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/router_p/providers/ollama.py tests/providers/test_ollama_adapter.py
git commit -m "feat: add ollama chat provider"
```

## Task 3: Route Local Completion Service Calls Through Ollama

**Files:**
- Modify: `src/router_p/services/chat_completion.py`
- Modify: `src/router_p/domain/model_slots.py`
- Modify: `tests/services/test_chat_completion_service.py`

- [ ] **Step 1: Extend the service tests to verify provider delegation for local routed requests**

```python
class StubProvider:
    def complete(self, request):
        return ProviderChatResponse(
            content="Provider hello",
            prompt_tokens=4,
            completion_tokens=2,
            raw_model=request.model,
        )


def test_service_calls_provider_for_router_auto_local_code():
    settings = Settings(local_code_model="qwen2.5-coder:7b")
    service = ChatCompletionService(settings=settings, provider=StubProvider())
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a Python function"}],
    )

    response = service.create_completion(request)

    assert response.model == "qwen2.5-coder:7b"
    assert response.choices[0].message.content == "Provider hello"
```

- [ ] **Step 2: Add a test for explicit local model names**

```python
def test_service_calls_provider_for_explicit_local_model():
    settings = Settings(local_general_model="qwen3:4b")
    service = ChatCompletionService(settings=settings, provider=StubProvider())
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[{"role": "user", "content": "Hello"}],
    )

    response = service.create_completion(request)

    assert response.model == "qwen3:4b"
    assert response.choices[0].message.content == "Provider hello"
```

- [ ] **Step 3: Add a test that cloud slots still stay on the temporary non-provider path in Phase 5**

```python
def test_service_keeps_cloud_routed_requests_on_placeholder_path_for_now():
    settings = Settings(cloud_general_model="gpt-general")
    service = ChatCompletionService(settings=settings, provider=StubProvider())
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Compare three architectures and migration strategy"}],
    )

    response = service.create_completion(request)

    assert response.model == "gpt-general"
    assert response.choices[0].message.content.startswith("Echo:")
```

- [ ] **Step 4: Run the service tests to verify they fail before integration**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: FAIL because `ChatCompletionService` does not yet accept provider injection or delegate to Ollama/provider logic

- [ ] **Step 5: Add local-slot helpers and provider injection**

```python
def is_local_slot(slot: ModelSlot) -> bool:
    return slot in {ModelSlot.LOCAL_TEXT, ModelSlot.LOCAL_CODE, ModelSlot.LOCAL_BOUNDARY}
```

- [ ] **Step 6: Update the completion service to call the provider for local targets**

```python
class ChatCompletionService:
    def __init__(..., provider: OllamaChatProvider | None = None) -> None:
        ...
        self._provider = provider or OllamaChatProvider(base_url=self._settings.ollama_base_url)

    def create_completion(...):
        ...
        if target should use local provider:
            provider_response = self._provider.complete(
                ProviderChatRequest(
                    model=response_model,
                    messages=request.messages,
                    timeout_seconds=self._settings.request_timeout_seconds,
                )
            )
            content = provider_response.content
            prompt_tokens = provider_response.prompt_tokens
            completion_tokens = provider_response.completion_tokens
            response_model = provider_response.raw_model
```

- [ ] **Step 7: Re-run the service tests**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: PASS

- [ ] **Step 8: Commit**

```bash
git add src/router_p/services/chat_completion.py src/router_p/domain/model_slots.py tests/services/test_chat_completion_service.py
git commit -m "feat: use ollama provider for local chat completions"
```

## Task 4: Verify API Behavior With Local Provider Integration

**Files:**
- Modify: `tests/api/test_chat_completions.py`
- Modify: `tests/conftest.py` if provider injection helper fixtures are needed
- Modify: `src/router_p/api/router.py` only if adapter construction needs a small factory extraction

- [ ] **Step 1: Add API tests that verify local requests still return the same envelope after provider integration**

```python
def test_chat_completions_uses_local_provider_for_explicit_local_model(client, auth_headers, monkeypatch):
    class StubProvider:
        def complete(self, request):
            return ProviderChatResponse(
                content="Stub local reply",
                prompt_tokens=3,
                completion_tokens=3,
                raw_model=request.model,
            )

    monkeypatch.setattr("router_p.services.chat_completion.OllamaChatProvider", lambda **kwargs: StubProvider())

    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )

    assert response.status_code == 200
    assert response.json()["choices"][0]["message"]["content"] == "Stub local reply"
```

- [ ] **Step 2: Add one routed local-code API test using the same stub provider**

```python
def test_chat_completions_router_auto_code_uses_local_provider(...):
    ...
    assert response.json()["model"] == "qwen2.5-coder:7b"
    assert response.json()["choices"][0]["message"]["content"] == "Stub local reply"
```

- [ ] **Step 3: Run the API tests to verify they fail before the local provider path is fully wired**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: FAIL on response content mismatch

- [ ] **Step 4: Make any minimal API wiring changes needed for clean provider construction**

```python
def build_chat_completion_service(settings: Settings) -> ChatCompletionService:
    return ChatCompletionService(settings=settings)
```

- [ ] **Step 5: Re-run the API tests**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: PASS

- [ ] **Step 6: Run the auth and health tests**

Run: `python3 -m pytest tests/api/test_authentication.py tests/api/test_health.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/router_p/api/router.py tests/api/test_chat_completions.py tests/conftest.py
git commit -m "feat: integrate ollama provider with chat api"
```

## Task 5: Document Ollama Requirements And Record Phase Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/development-plan.md`
- Modify: `PROGRESS.md`

- [ ] **Step 1: Update the README for Ollama-backed local models**

```markdown
- Phase 5 routes local text and code requests through Ollama.
- Ensure `Ollama` is running and the default models are available locally.
- Cloud-routed slots remain temporary until the Phase 6 cloud adapter is added.
```

- [ ] **Step 2: Add one quick local setup example**

```bash
ollama pull phi4-mini
ollama pull qwen3:4b
ollama pull qwen2.5-coder:7b
```

- [ ] **Step 3: Mark Phase 5 complete in `docs/development-plan.md`**

```markdown
## Phase 5: Ollama Adapter

- Status: `complete`
```

- [ ] **Step 4: Advance `PROGRESS.md` to Phase 6**

```markdown
## Current Phase

Phase 5 complete. Ready for Phase 6.
```

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m pytest -q`
Expected: all tests PASS

- [ ] **Step 6: Run one smoke test for provider construction**

Run: `python3 -c "from router_p.providers.ollama import OllamaChatProvider; print(OllamaChatProvider.__name__)"`
Expected: prints `OllamaChatProvider`

- [ ] **Step 7: Commit**

```bash
git add README.md docs/development-plan.md PROGRESS.md
git commit -m "docs: record phase 5 completion"
```

## Verification Checklist

- [ ] Provider-neutral request and response models exist.
- [ ] Ollama adapter sends non-stream chat requests to `/api/chat`.
- [ ] Ollama responses are normalized into Router-P’s provider contract.
- [ ] Local routed requests use the Ollama adapter.
- [ ] Explicit local model requests use the Ollama adapter.
- [ ] Cloud-routed requests remain on the temporary non-provider path until Phase 6.
- [ ] Existing auth and health behavior remain unchanged.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.providers.ollama import OllamaChatProvider; print(OllamaChatProvider.__name__)"` succeeds.

## Risks And Guardrails

- Keep provider concerns isolated in `src/router_p/providers/`; do not let Ollama payload details leak into API routes.
- Be careful about creating network-bound providers in tests; inject or monkeypatch them instead.
- Do not break Phase 4 cloud-slot decisions just because the cloud adapter is not ready yet.
- Keep all provider calls non-streaming for now; streaming belongs to Phase 8.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-20-phase-5-ollama-adapter.md`.

Two execution options:

1. Subagent-Driven (recommended) - I dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using `executing-plans`, batch execution with checkpoints

In this Codex session I did not run the plan-review subagent loop because that requires explicit delegation permission.
