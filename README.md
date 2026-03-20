# Router-P

Router-P is an OpenClaw-facing model router that prefers local models first and falls back to cloud models for complex or low-confidence tasks.

## Status

Phase 2 is complete. Router-P now exposes a public health endpoint and protects non-health routes with a bearer API key.

The next coding step is `Phase 3: non-streaming chat completions`.

## Quick Start

1. Create a virtual environment and install dependencies:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

2. Optionally define overrides in `.env`:

```env
ROUTER_P_API_KEY=dev-router-p-key
ROUTER_P_OLLAMA_BASE_URL=http://localhost:11434
ROUTER_P_CLOUD_BASE_URL=
ROUTER_P_CLOUD_API_KEY=
```

3. Start the API:

```bash
uvicorn router_p.main:app --reload
```

4. Call the API:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ -H "Authorization: Bearer ${ROUTER_P_API_KEY:-dev-router-p-key}"
```

`GET /health` is public and returns service readiness. Other current routes require `Authorization: Bearer <ROUTER_P_API_KEY>`.

## Documents

- [Project Progress](/Users/smy/project/Router-P/PROGRESS.md)
- [Requirements](/Users/smy/project/Router-P/docs/requirements.md)
- [Design](/Users/smy/project/Router-P/docs/design.md)
- [Development Plan](/Users/smy/project/Router-P/docs/development-plan.md)

## v1 Summary

- Independent Router service for OpenClaw
- `Python + FastAPI`
- OpenAI-compatible `POST /chat/completions` and `GET /health`
- Local-first routing with `Ollama`
- Default local bundle: `phi4-mini`, `qwen3:4b`, `qwen2.5-coder:7b`
- Routing flow: rules first, `phi4-mini` boundary classification, cloud fallback
- Deployment via `Docker Compose` with external `Ollama`
