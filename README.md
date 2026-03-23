# Router-P

Router-P is an OpenClaw-facing model router that prefers local models first and falls back to cloud models for complex or low-confidence tasks.

## Status

Phase 9 is complete. Router-P now supports stable API error envelopes and decision-level routing logs.

The next coding step is `Phase 10: Compose, docs, and OpenClaw validation`.

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
curl http://127.0.0.1:8000/chat/completions \
  -H "Authorization: Bearer ${ROUTER_P_API_KEY:-dev-router-p-key}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "router-auto",
    "messages": [{"role": "user", "content": "Write a Python helper for retries"}],
    "stream": false
  }'
```

`GET /health` is public and returns service readiness. Other current routes require `Authorization: Bearer <ROUTER_P_API_KEY>`.
`POST /chat/completions` accepts both non-streaming and streaming OpenAI-style chat payloads.
`router-auto` is the internal routing model name for Phase 4. Rule routing now maps requests to centralized slots for local text, local code, cloud text, and cloud code.
Phase 5 routes local text and code requests through Ollama. Ensure `Ollama` is running and the default models are available locally.
Phase 6 routes cloud targets through an OpenAI-compatible provider using `ROUTER_P_CLOUD_BASE_URL` and `ROUTER_P_CLOUD_API_KEY`.
Phase 7 uses `phi4-mini`-style boundary classification for ambiguous requests and falls back to cloud when local executions fail, time out, or return low-confidence / too-short results.
Phase 8 emits OpenAI-style SSE chunks plus terminal `[DONE]` for `stream: true` requests.
Phase 9 adds structured decision logs with provider / selected model / route layer / fallback metadata, plus stable API errors for auth and provider failures in the form `{"error": {"code", "message", "type"}}`.

5. Prepare local Ollama models:

```bash
ollama pull phi4-mini
ollama pull qwen3:4b
ollama pull qwen2.5-coder:7b
```

6. Configure cloud models when needed:

```env
ROUTER_P_CLOUD_BASE_URL=https://your-openai-compatible-provider.example/v1
ROUTER_P_CLOUD_API_KEY=your-cloud-api-key
ROUTER_P_CLOUD_GENERAL_MODEL=gpt-general
ROUTER_P_CLOUD_CODE_MODEL=gpt-code
```

7. Stream a response:

```bash
curl http://127.0.0.1:8000/chat/completions \
  -H "Authorization: Bearer ${ROUTER_P_API_KEY:-dev-router-p-key}" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "router-auto",
    "messages": [{"role": "user", "content": "Write a Python helper for retries"}],
    "stream": true
  }'
```

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
- Structured routing logs and stable auth/provider API errors
- Deployment via `Docker Compose` with external `Ollama`
