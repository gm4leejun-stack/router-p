from router_p.providers.types import ProviderChatResponse


class FallbackPolicy:
    LOW_CONFIDENCE_MARKERS = ("not sure", "i think", "maybe", "possibly")

    def should_fallback_from_exception(self, exc: Exception) -> bool:
        return isinstance(exc, (RuntimeError, TimeoutError))

    def should_fallback_from_response(self, response: ProviderChatResponse) -> bool:
        content = response.content.strip().lower()
        if response.completion_tokens <= 1:
            return True
        if response.prompt_tokens >= 20 and len(content.split()) <= 1:
            return True
        return any(marker in content for marker in self.LOW_CONFIDENCE_MARKERS)
