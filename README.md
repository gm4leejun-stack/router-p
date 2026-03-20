# Router-P

Router-P is an OpenClaw-facing model router that prefers local models first and falls back to cloud models for complex or low-confidence tasks.

## Status

Planning is complete. Implementation has not started yet.

The next coding step is `Phase 1: project scaffold and configuration system`.

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
