from router_p.api.streaming import format_sse_chunk, format_sse_done
from router_p.providers.types import ProviderStreamChunk


def test_provider_stream_chunk_holds_delta_content():
    chunk = ProviderStreamChunk(content_delta="Hello", raw_model="qwen3:4b")

    assert chunk.content_delta == "Hello"
    assert chunk.raw_model == "qwen3:4b"


def test_format_sse_chunk_emits_openai_style_data_frame():
    chunk = ProviderStreamChunk(content_delta="Hello", raw_model="qwen3:4b")

    payload = format_sse_chunk(chunk, chunk_id="chatcmpl-test")

    assert payload.startswith("data: ")
    assert "\"chat.completion.chunk\"" in payload
    assert "\"Hello\"" in payload


def test_format_sse_done_emits_done_marker():
    assert format_sse_done() == "data: [DONE]\n\n"
