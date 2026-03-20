import httpx

from router_p.providers.types import ProviderChatRequest, ProviderChatResponse


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
        prompt_tokens = payload.get("prompt_eval_count") or len(
            " ".join(message.content for message in request.messages).split()
        )
        completion_tokens = payload.get("eval_count") or len(content.split())

        return ProviderChatResponse(
            content=content,
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            raw_model=payload.get("model", request.model),
        )
