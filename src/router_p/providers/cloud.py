import json

import httpx

from router_p.providers.types import ProviderChatRequest, ProviderChatResponse, ProviderStreamChunk


class OpenAICompatibleCloudProvider:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._client = client or httpx.Client(base_url=self._base_url)

    def complete(self, request: ProviderChatRequest) -> ProviderChatResponse:
        response = self._client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": request.model,
                "messages": [message.model_dump() for message in request.messages],
                "stream": False,
            },
            timeout=request.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError("Cloud request failed")

        payload = response.json()
        content = payload["choices"][0]["message"]["content"]
        usage = payload.get("usage") or {}

        return ProviderChatResponse(
            content=content,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            raw_model=payload.get("model", request.model),
        )

    def stream_complete(self, request: ProviderChatRequest):
        response = self._client.post(
            "/chat/completions",
            headers={"Authorization": f"Bearer {self._api_key}"},
            json={
                "model": request.model,
                "messages": [message.model_dump() for message in request.messages],
                "stream": True,
            },
            timeout=request.timeout_seconds,
        )
        if response.status_code >= 400:
            raise RuntimeError("Cloud request failed")

        for line in response.text.splitlines():
            if not line.startswith("data: "):
                continue
            data = line.removeprefix("data: ").strip()
            if data == "[DONE]":
                break
            payload = json.loads(data)
            content = payload["choices"][0].get("delta", {}).get("content", "")
            if content:
                yield ProviderStreamChunk(
                    content_delta=content,
                    raw_model=payload.get("model", request.model),
                )
