# Router-P v1 Design

## Architecture

Router-P is a standalone API service between OpenClaw and model providers.

`OpenClaw -> Router-P -> Ollama / OpenAI-compatible Cloud`

## Public Interface

- `POST /chat/completions`
- `GET /health`

The chat endpoint must support both streaming and non-streaming modes and accept standard OpenAI-style `messages`.

## Core Subsystems

### API Layer

- FastAPI app
- request parsing and validation
- API key authentication
- streaming and non-streaming response handling

### Routing Layer

- rule-first selection
- `phi4-mini` boundary classification when rules are inconclusive
- fallback policy for failures and low-quality local responses

### Provider Layer

- Ollama adapter for local models
- OpenAI-compatible cloud adapter for general and code models

### Observability Layer

Decision-level logging for:

- request id
- selected model
- route layer
- matched rule
- fallback reason
- latency
- provider

## Model Roles

- `phi4-mini`: ultra-light tasks and model boundary classification
- `qwen3:4b`: local general-purpose text tasks
- `qwen2.5-coder:7b`: local coding-oriented tasks
- cloud general model: complex reasoning and high-value general tasks
- cloud code model: complex code generation and difficult code tasks

## Routing Flow

1. Evaluate explicit routing rules.
2. If no rule is decisive, ask `phi4-mini` to classify the target slot.
3. Execute against the selected provider/model.
4. Trigger fallback to cloud when local execution fails, times out, returns output that is too short, or includes low-confidence wording.

## Deployment

- Main deployment path is `Docker Compose`
- Compose starts Router-P
- `Ollama` runs outside Compose by default
- Configuration is environment-variable driven
- A single API key protects the Router-P endpoint
