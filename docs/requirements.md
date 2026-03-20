# Router-P v1 Requirements

## Goal

Build a local-first model router for OpenClaw so routine tasks use local open models and only complex or low-confidence tasks use cloud models.

## Core Outcomes

- Reduce unnecessary cloud token usage
- Keep OpenClaw integration low-friction and non-invasive
- Make the project easy to self-host and reuse
- Provide a stable v1 that can be extended in later versions

## Product Boundaries

- Router-P is an independent service, not an OpenClaw source modification
- v1 focuses on text chat routing, not a full platform
- v1 does not include a web admin console, database, or multi-user auth
- v1 must support streaming and non-streaming chat requests

## Default v1 Decisions

- Tech stack: `Python + FastAPI`
- Local runtime: `Ollama`
- Default local models:
  - `phi4-mini` for ultra-light tasks and boundary routing
  - `qwen3:4b` for general local tasks
  - `qwen2.5-coder:7b` for light coding tasks
- Cloud strategy:
  - one general cloud model
  - one code cloud model
- Deployment: `Docker Compose` with external `Ollama`

## Routing Expectations

- Local-first by default
- Rules handle the majority of requests
- `phi4-mini` handles boundary classification when rules are inconclusive
- Fallback to cloud for complex tasks, failures, timeouts, or low-quality local output

## Success Criteria

- OpenClaw can point to Router-P without source changes
- Router-P exposes OpenAI-compatible chat completions
- Local and cloud providers can be routed behind one endpoint
- The repository is documented enough for future implementation and reuse
