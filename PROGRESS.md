# Router-P Progress

## Current Phase

Phase 1 complete. Ready for Phase 2.

## Confirmed

- Product goal: provide a local-first router for OpenClaw to reduce unnecessary cloud token spend
- Architecture: `OpenClaw -> Router-P -> Ollama / Cloud API`
- Tech stack: `Python + FastAPI`
- Default local bundle: `phi4-mini`, `qwen3:4b`, `qwen2.5-coder:7b`
- Routing flow: rules first, `phi4-mini` boundary classification, cloud fallback
- Deployment: `Docker Compose`, external `Ollama`, single API key, streaming required

## Pending

- Phase 2: health check and authentication
- Phase 3: non-stream chat completions
- Phase 4: rule router and model slots
- Phase 5: Ollama adapter
- Phase 6: cloud adapter
- Phase 7: boundary classification and fallback
- Phase 8: streaming support
- Phase 9: logging and error handling
- Phase 10: Compose, docs, and OpenClaw validation

## Next Step

Start `Phase 2: health check and authentication`.
