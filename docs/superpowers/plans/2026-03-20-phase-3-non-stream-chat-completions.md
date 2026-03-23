# Phase 3 Non-Streaming Chat Completions Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a non-streaming `POST /chat/completions` endpoint that accepts OpenAI-style `messages` and returns a stable OpenAI-compatible response envelope.

**Architecture:** Keep Phase 3 focused on transport and schema boundaries. Introduce request/response Pydantic models plus a small in-process completion service that turns validated chat input into one unified response shape; do not implement routing rules or external providers yet. The completion service should be isolated behind a function or class boundary so Phases 4-6 can replace the placeholder responder without rewriting the endpoint contract.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic v2, pytest, FastAPI TestClient

---

## File Structure

- Create: `src/router_p/api/schemas/chat.py`
  - Own the Phase 3 request and response models for chat completions.
- Create: `src/router_p/services/chat_completion.py`
  - Hold the non-streaming completion service and placeholder responder logic.
- Modify: `src/router_p/api/router.py`
  - Register `POST /chat/completions` and keep auth behavior consistent with Phase 2.
- Create: `tests/api/test_chat_completions.py`
  - Cover endpoint auth, request validation, non-stream success path, and stream rejection behavior.
- Create: `tests/services/test_chat_completion_service.py`
  - Cover the service contract separately from the HTTP layer.
- Modify: `README.md`
  - Document the new non-stream endpoint shape and temporary placeholder behavior.
- Modify: `docs/development-plan.md`
  - Mark Phase 3 complete once verification passes.
- Modify: `PROGRESS.md`
  - Advance project status to Phase 4 after verification passes.

## Scope And Guardrails

- Phase 3 covers only non-streaming `POST /chat/completions`.
- `stream=true` should be explicitly rejected with a stable client error rather than silently ignored.
- Keep the placeholder completion logic deterministic and in-process. Do not call Ollama or cloud APIs in this phase.
- Do not introduce rule routing, model slot selection, or fallback policy yet. Those belong to later phases.
- Keep the response OpenAI-compatible enough for OpenClaw integration work: `id`, `object`, `created`, `model`, `choices`, and `usage`.

## Proposed API Contract

- Request fields required in Phase 3:
  - `model: str`
  - `messages: list[ChatMessage]`
  - `stream: bool = False`
- Supported message roles in Phase 3:
  - `system`
  - `user`
  - `assistant`
- Message content in Phase 3:
  - plain string only
- Placeholder completion behavior:
  - select the most recent `user` message
  - return it prefixed with a deterministic marker such as `"Echo: "`
  - use the request `model` value in the response
- Usage accounting:
  - keep it simple and deterministic, for example approximate token counts by whitespace splitting or character length; document that it is placeholder accounting until provider integration arrives

## Task 1: Add Chat Schema Tests And Models

**Files:**
- Create: `src/router_p/api/schemas/chat.py`
- Create: `tests/services/test_chat_completion_service.py`

- [ ] **Step 1: Write the failing schema-focused service tests**

```python
from router_p.api.schemas.chat import ChatCompletionRequest


def test_chat_completion_request_accepts_openai_style_messages():
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Hello"},
        ],
    )

    assert request.model == "qwen3:4b"
    assert request.stream is False
    assert request.messages[0].role == "system"


def test_chat_completion_request_requires_at_least_one_message():
    try:
        ChatCompletionRequest(model="qwen3:4b", messages=[])
    except ValueError as exc:
        assert "at least one message" in str(exc)
    else:
        raise AssertionError("expected validation error")
```

- [ ] **Step 2: Run the schema tests to verify they fail because the models do not exist**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: FAIL with import errors or missing model definitions

- [ ] **Step 3: Implement the minimal request and response models**

```python
from typing import Literal

from pydantic import BaseModel, Field, field_validator


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(min_length=1)
    messages: list[ChatMessage]
    stream: bool = False

    @field_validator("messages")
    @classmethod
    def validate_messages(cls, value: list[ChatMessage]) -> list[ChatMessage]:
        if not value:
            raise ValueError("messages must contain at least one message")
        return value
```

- [ ] **Step 4: Add the Phase 3 response envelope models in the same module**

```python
class ChatCompletionResponseMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str


class ChatCompletionChoice(BaseModel):
    index: int = 0
    finish_reason: Literal["stop"] = "stop"
    message: ChatCompletionResponseMessage


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: list[ChatCompletionChoice]
    usage: ChatCompletionUsage
```

- [ ] **Step 5: Re-run the schema tests**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: PASS for schema validation tests

- [ ] **Step 6: Commit**

```bash
git add src/router_p/api/schemas/chat.py tests/services/test_chat_completion_service.py
git commit -m "feat: add chat completion schemas"
```

## Task 2: Add Deterministic Non-Streaming Completion Service

**Files:**
- Create: `src/router_p/services/chat_completion.py`
- Modify: `tests/services/test_chat_completion_service.py`

- [ ] **Step 1: Extend the service tests with the desired completion behavior**

```python
from router_p.services.chat_completion import ChatCompletionService


def test_service_returns_assistant_message_for_latest_user_prompt():
    service = ChatCompletionService()
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[
            {"role": "system", "content": "Be concise."},
            {"role": "user", "content": "Summarize Phase 3"},
        ],
    )

    response = service.create_completion(request)

    assert response.object == "chat.completion"
    assert response.model == "qwen3:4b"
    assert response.choices[0].message.content == "Echo: Summarize Phase 3"
    assert response.choices[0].message.role == "assistant"
```

- [ ] **Step 2: Run the service tests to verify they fail before implementation**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: FAIL with missing `ChatCompletionService`

- [ ] **Step 3: Implement the minimal deterministic completion service**

```python
from time import time
from uuid import uuid4

from router_p.api.schemas.chat import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionResponseMessage,
    ChatCompletionUsage,
)


class ChatCompletionService:
    def create_completion(self, request: ChatCompletionRequest) -> ChatCompletionResponse:
        last_user_message = next(
            message.content for message in reversed(request.messages) if message.role == "user"
        )
        content = f"Echo: {last_user_message}"
        prompt_tokens = sum(len(message.content.split()) for message in request.messages)
        completion_tokens = len(content.split())

        return ChatCompletionResponse(
            id=f"chatcmpl-{uuid4().hex}",
            created=int(time()),
            model=request.model,
            choices=[
                ChatCompletionChoice(
                    message=ChatCompletionResponseMessage(content=content),
                )
            ],
            usage=ChatCompletionUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
        )
```

- [ ] **Step 4: Add one guard test for requests without any user message**

```python
def test_service_rejects_requests_without_user_message():
    service = ChatCompletionService()
    request = ChatCompletionRequest(
        model="qwen3:4b",
        messages=[{"role": "system", "content": "Only instructions"}],
    )

    with pytest.raises(ValueError, match="at least one user message"):
        service.create_completion(request)
```

- [ ] **Step 5: Implement the minimal guard**

```python
        for message in reversed(request.messages):
            if message.role == "user":
                last_user_message = message.content
                break
        else:
            raise ValueError("messages must contain at least one user message")
```

- [ ] **Step 6: Re-run the service tests**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add src/router_p/services/chat_completion.py tests/services/test_chat_completion_service.py
git commit -m "feat: add non-stream chat completion service"
```

## Task 3: Add HTTP Endpoint Tests For Chat Completions

**Files:**
- Create: `tests/api/test_chat_completions.py`

- [ ] **Step 1: Write the failing endpoint tests**

```python
def test_chat_completions_requires_api_key(client):
    response = client.post(
        "/chat/completions",
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
        },
    )

    assert response.status_code == 401


def test_chat_completions_returns_non_stream_response(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": False,
        },
    )

    body = response.json()

    assert response.status_code == 200
    assert body["object"] == "chat.completion"
    assert body["model"] == "qwen3:4b"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == "Echo: Hello"
    assert body["usage"]["total_tokens"] >= body["usage"]["completion_tokens"]
```


def test_chat_completions_rejects_streaming_requests(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={
            "model": "qwen3:4b",
            "messages": [{"role": "user", "content": "Hello"}],
            "stream": True,
        },
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Streaming is not supported yet"
```

- [ ] **Step 2: Run the endpoint tests to verify they fail because the route does not exist**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: FAIL with `404 Not Found`

- [ ] **Step 3: Add one validation test for malformed message payloads**

```python
def test_chat_completions_validates_message_shape(client, auth_headers):
    response = client.post(
        "/chat/completions",
        headers=auth_headers,
        json={"model": "qwen3:4b", "messages": [{"role": "tool", "content": "bad"}]},
    )

    assert response.status_code == 422
```

- [ ] **Step 4: Re-run the endpoint tests**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: still FAIL on missing route, while malformed request shape is ready to pass once the endpoint exists

- [ ] **Step 5: Commit**

```bash
git add tests/api/test_chat_completions.py
git commit -m "test: add chat completions endpoint coverage"
```

## Task 4: Wire The Endpoint Into The API Router

**Files:**
- Modify: `src/router_p/api/router.py`
- Modify: `src/router_p/api/__init__.py` if needed
- Test: `tests/api/test_chat_completions.py`
- Test: `tests/api/test_authentication.py`
- Test: `tests/api/test_health.py`

- [ ] **Step 1: Add the endpoint with explicit request and response models**

```python
from fastapi import APIRouter, Depends, HTTPException, Request, status

from router_p.api.schemas.chat import ChatCompletionRequest, ChatCompletionResponse
from router_p.services.chat_completion import ChatCompletionService

chat_completion_service = ChatCompletionService()


@router.post(
    "/chat/completions",
    tags=["chat"],
    dependencies=[Depends(require_api_key)],
    response_model=ChatCompletionResponse,
)
async def create_chat_completion(
    payload: ChatCompletionRequest,
) -> ChatCompletionResponse:
    if payload.stream:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Streaming is not supported yet",
        )
    return chat_completion_service.create_completion(payload)
```

- [ ] **Step 2: Run the endpoint tests**

Run: `python3 -m pytest tests/api/test_chat_completions.py -v`
Expected: PASS

- [ ] **Step 3: Run the existing auth and health tests to catch regressions**

Run: `python3 -m pytest tests/api/test_authentication.py tests/api/test_health.py -v`
Expected: PASS

- [ ] **Step 4: Run the service tests again**

Run: `python3 -m pytest tests/services/test_chat_completion_service.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/router_p/api/router.py src/router_p/api/__init__.py
git commit -m "feat: add non-stream chat completions endpoint"
```

## Task 5: Document Placeholder Behavior And Record Phase Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/development-plan.md`
- Modify: `PROGRESS.md`

- [ ] **Step 1: Update the README API section**

```markdown
- `POST /chat/completions` now accepts OpenAI-style non-streaming chat requests.
- `stream: true` returns `400` until Phase 8 adds streaming support.
- Phase 3 uses a deterministic in-process placeholder response so API contract work can proceed before provider integration.
```

- [ ] **Step 2: Add one curl example for non-stream chat completions**

```bash
curl http://127.0.0.1:8000/chat/completions \
  -H "Authorization: Bearer ${ROUTER_P_API_KEY:-dev-router-p-key}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "qwen3:4b",
    "messages": [{"role": "user", "content": "Hello"}],
    "stream": false
  }'
```

- [ ] **Step 3: Mark Phase 3 complete in `docs/development-plan.md`**

```markdown
## Phase 3: Non-Streaming Chat Completions

- Status: `complete`
```

- [ ] **Step 4: Advance `PROGRESS.md` to Phase 4**

```markdown
## Current Phase

Phase 3 complete. Ready for Phase 4.
```

- [ ] **Step 5: Run the full test suite**

Run: `python3 -m pytest -q`
Expected: all tests PASS

- [ ] **Step 6: Run one import smoke test for the endpoint models**

Run: `python3 -c "from router_p.api.schemas.chat import ChatCompletionRequest, ChatCompletionResponse; print(ChatCompletionRequest.__name__, ChatCompletionResponse.__name__)"`
Expected: prints `ChatCompletionRequest ChatCompletionResponse`

- [ ] **Step 7: Commit**

```bash
git add README.md docs/development-plan.md PROGRESS.md
git commit -m "docs: record phase 3 completion"
```

## Verification Checklist

- [ ] `POST /chat/completions` rejects missing API keys with `401`.
- [ ] `POST /chat/completions` accepts valid non-streaming OpenAI-style `messages`.
- [ ] The response includes `id`, `object`, `created`, `model`, `choices`, and `usage`.
- [ ] `stream: true` is rejected with `400` and a stable error message.
- [ ] Unsupported message roles are rejected by request validation.
- [ ] Existing `GET /health` behavior stays public and unchanged.
- [ ] Existing root-route auth behavior stays unchanged.
- [ ] `python3 -m pytest -q` passes.
- [ ] `python3 -c "from router_p.api.schemas.chat import ChatCompletionRequest, ChatCompletionResponse; print(ChatCompletionRequest.__name__, ChatCompletionResponse.__name__)"` succeeds.

## Risks And Guardrails

- Do not hardwire routing logic into the Phase 3 service. It should be easy to replace with routed providers in Phase 4-6.
- Keep placeholder token accounting simple and clearly documented as provisional.
- Do not add streaming response objects yet; rejecting streaming explicitly is enough for this phase.
- If OpenClaw compatibility requires additional response fields during execution, add them in the schema tests first rather than expanding the endpoint ad hoc.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-20-phase-3-non-stream-chat-completions.md`.

Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using `executing-plans`, batch execution with checkpoints

In this Codex session I did not run the plan-review subagent loop because that requires explicit delegation permission.
