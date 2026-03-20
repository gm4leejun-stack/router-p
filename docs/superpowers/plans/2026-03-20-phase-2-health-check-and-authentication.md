# Phase 2 Health Check And Authentication Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a readiness-style `GET /health` endpoint and single API key protection for Router-P while keeping health checks publicly accessible.

**Architecture:** Extend the existing FastAPI app with a small auth dependency and a focused health endpoint. Keep the implementation narrow: config remains the source of truth for the API key, `/health` is unauthenticated for uptime probing, and protected routes enforce a bearer token before Phase 3 adds chat completions.

**Tech Stack:** Python 3.10+, FastAPI, Pydantic Settings, pytest, httpx/TestClient-compatible FastAPI testing

---

## File Structure

- Modify: `src/router_p/api/router.py`
  - Replace the placeholder root-only route layout with a route module that exposes `GET /health` and keeps route behavior explicit.
- Create: `src/router_p/api/dependencies.py`
  - Hold reusable API-level dependencies, starting with API key validation logic.
- Create: `tests/conftest.py`
  - Shared app factory fixtures and test client setup for API tests.
- Create: `tests/api/test_health.py`
  - Verify health endpoint shape and that it does not require auth.
- Create: `tests/api/test_authentication.py`
  - Verify missing, invalid, and valid API key behavior on protected routes.
- Modify: `README.md`
  - Document the Phase 2 API key behavior and health endpoint usage once implemented.
- Modify: `docs/development-plan.md`
  - Mark Phase 2 status when implementation is complete.
- Modify: `PROGRESS.md`
  - Update current phase and confirmed progress after verification passes.

## Implementation Notes

- Keep `/health` outside auth so container probes and reverse proxies can check service readiness without credentials.
- Use `Authorization: Bearer <ROUTER_P_API_KEY>` as the only accepted credential shape unless an approved design change says otherwise.
- Keep the root route `/` protected once auth is introduced; it is a convenient probe target for auth tests without coupling tests to Phase 3 endpoints.
- Prefer one small auth dependency over middleware for Phase 2. Middleware is harder to selectively bypass and is unnecessary at this scope.
- Use `fastapi.testclient.TestClient` to avoid extra async test complexity.

### Task 1: Establish Test Harness For API Behavior

**Files:**
- Create: `tests/conftest.py`
- Test: `tests/conftest.py`

- [ ] **Step 1: Write the failing fixture setup**

```python
from fastapi.testclient import TestClient
import pytest

from router_p.app import create_app
from router_p.config import Settings


@pytest.fixture
def settings() -> Settings:
    return Settings(
        api_key="test-router-p-key",
    )


@pytest.fixture
def client(settings: Settings) -> TestClient:
    return TestClient(create_app(settings))
```

- [ ] **Step 2: Run pytest collection to verify the repository sees the new test module**

Run: `pytest tests/conftest.py --collect-only -q`
Expected: collection succeeds and exits `0`

- [ ] **Step 3: Adjust fixture shape if collection fails because of import path or dependency issues**

```python
@pytest.fixture
def auth_headers(settings: Settings) -> dict[str, str]:
    return {"Authorization": f"Bearer {settings.api_key}"}
```

- [ ] **Step 4: Re-run collection**

Run: `pytest tests/conftest.py --collect-only -q`
Expected: collection succeeds without fixture import errors

- [ ] **Step 5: Commit**

```bash
git add tests/conftest.py
git commit -m "test: add api test fixtures"
```

### Task 2: Add Public Health Endpoint

**Files:**
- Modify: `src/router_p/api/router.py`
- Create: `tests/api/test_health.py`
- Test: `tests/api/test_health.py`

- [ ] **Step 1: Write the failing health endpoint tests**

```python
def test_health_returns_service_readiness(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "service": "router-p",
        "status": "ready",
        "environment": "development",
    }


def test_health_does_not_require_auth(client):
    response = client.get("/health")

    assert response.status_code == 200
```

- [ ] **Step 2: Run the health tests to verify they fail for the missing route or wrong payload**

Run: `pytest tests/api/test_health.py -v`
Expected: FAIL with `404 Not Found` or assertion mismatch for response body

- [ ] **Step 3: Implement the minimal health endpoint**

```python
from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/health", tags=["meta"])
async def health(request: Request) -> dict[str, str]:
    settings = request.app.state.settings
    return {
        "service": "router-p",
        "status": "ready",
        "environment": settings.environment,
    }
```

- [ ] **Step 4: Preserve or re-add the root route explicitly so later auth tests have a protected endpoint**

```python
@router.get("/", tags=["meta"])
async def root() -> dict[str, str]:
    return {"service": "router-p", "status": "booted"}
```

- [ ] **Step 5: Run the health tests again**

Run: `pytest tests/api/test_health.py -v`
Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add src/router_p/api/router.py tests/api/test_health.py
git commit -m "feat: add public health endpoint"
```

### Task 3: Add Bearer API Key Dependency

**Files:**
- Create: `src/router_p/api/dependencies.py`
- Create: `tests/api/test_authentication.py`
- Test: `tests/api/test_authentication.py`

- [ ] **Step 1: Write the failing auth tests**

```python
def test_root_rejects_requests_without_api_key(client):
    response = client.get("/")

    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"


def test_root_rejects_requests_with_wrong_api_key(client):
    response = client.get("/", headers={"Authorization": "Bearer wrong-key"})

    assert response.status_code == 401


def test_root_accepts_requests_with_valid_api_key(client, auth_headers):
    response = client.get("/", headers=auth_headers)

    assert response.status_code == 200
    assert response.json() == {"service": "router-p", "status": "booted"}
```

- [ ] **Step 2: Run the auth tests to verify they fail before implementation**

Run: `pytest tests/api/test_authentication.py -v`
Expected: FAIL because `/` is currently not protected

- [ ] **Step 3: Implement a minimal reusable bearer auth dependency**

```python
from fastapi import HTTPException, Request, status


def require_api_key(request: Request) -> None:
    expected = request.app.state.settings.api_key
    authorization = request.headers.get("Authorization")
    expected_header = f"Bearer {expected}"

    if authorization != expected_header:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Unauthorized",
        )
```

- [ ] **Step 4: Re-run the auth tests and confirm they still fail because the dependency is not wired**

Run: `pytest tests/api/test_authentication.py -v`
Expected: FAIL with `200 != 401` on unauthorized cases

- [ ] **Step 5: Commit**

```bash
git add src/router_p/api/dependencies.py tests/api/test_authentication.py
git commit -m "feat: add api key auth dependency"
```

### Task 4: Protect Non-Health Routes With The Auth Dependency

**Files:**
- Modify: `src/router_p/api/router.py`
- Test: `tests/api/test_authentication.py`
- Test: `tests/api/test_health.py`

- [ ] **Step 1: Wire the auth dependency onto protected routes only**

```python
from fastapi import APIRouter, Depends, Request

from router_p.api.dependencies import require_api_key


@router.get("/", tags=["meta"], dependencies=[Depends(require_api_key)])
async def root() -> dict[str, str]:
    return {"service": "router-p", "status": "booted"}
```

- [ ] **Step 2: Run the auth tests to verify the protected route behavior**

Run: `pytest tests/api/test_authentication.py -v`
Expected: PASS

- [ ] **Step 3: Run the health tests to verify `/health` stayed public**

Run: `pytest tests/api/test_health.py -v`
Expected: PASS

- [ ] **Step 4: Run both API test files together**

Run: `pytest tests/api/test_health.py tests/api/test_authentication.py -v`
Expected: all tests PASS

- [ ] **Step 5: Commit**

```bash
git add src/router_p/api/router.py
git commit -m "feat: protect api routes with bearer auth"
```

### Task 5: Document And Record Phase Completion

**Files:**
- Modify: `README.md`
- Modify: `docs/development-plan.md`
- Modify: `PROGRESS.md`

- [ ] **Step 1: Add README usage notes for health and auth**

```markdown
## API

- `GET /health` returns Router-P readiness and does not require authentication.
- All other current routes require `Authorization: Bearer <ROUTER_P_API_KEY>`.
```

- [ ] **Step 2: Mark Phase 2 complete in the development plan**

```markdown
## Phase 2: Health Check and Authentication

- Status: `complete`
```

- [ ] **Step 3: Update progress tracking**

```markdown
## Current Phase

Phase 2 complete. Ready for Phase 3.
```

- [ ] **Step 4: Run the full test suite**

Run: `pytest -q`
Expected: all tests PASS

- [ ] **Step 5: Smoke test the app entrypoint locally**

Run: `python -c "from router_p.main import app; print(app.title)"`
Expected: prints `Router-P`

- [ ] **Step 6: Commit**

```bash
git add README.md docs/development-plan.md PROGRESS.md
git commit -m "docs: record phase 2 completion"
```

## Verification Checklist

- [ ] `GET /health` returns `200` with service name, readiness status, and environment.
- [ ] `GET /health` is reachable without `Authorization`.
- [ ] `GET /` returns `401` without a bearer token.
- [ ] `GET /` returns `401` with an incorrect bearer token.
- [ ] `GET /` returns `200` with `Authorization: Bearer <ROUTER_P_API_KEY>`.
- [ ] `pytest -q` passes.
- [ ] `python -c "from router_p.main import app; print(app.title)"` succeeds.

## Risks And Guardrails

- Do not add middleware in Phase 2 unless route-level dependency wiring proves insufficient.
- Do not introduce chat-completion request models yet; that belongs to Phase 3.
- If FastAPI’s generated docs endpoints need to stay public later, revisit auth placement in Phase 3 or Phase 9 with an explicit decision rather than expanding scope here.

## Handoff

Plan complete and saved to `docs/superpowers/plans/2026-03-20-phase-2-health-check-and-authentication.md`.

Two execution options:

1. Subagent-Driven (recommended) - dispatch a fresh subagent per task, review between tasks, fast iteration
2. Inline Execution - execute tasks in this session using `executing-plans`, batch execution with checkpoints

In this Codex session I did not run the plan-review subagent loop because that requires explicit delegation permission. If you want, I can execute this plan inline next.
