from router_p.config import Settings
from router_p.domain.model_slots import ModelSlot, resolve_model_slot


def test_model_slots_resolve_to_configured_model_names():
    settings = Settings(
        local_general_model="qwen3:4b",
        local_code_model="qwen2.5-coder:7b",
        local_boundary_model="phi4-mini",
        cloud_general_model="gpt-general",
        cloud_code_model="gpt-code",
    )

    assert resolve_model_slot(ModelSlot.LOCAL_TEXT, settings) == "qwen3:4b"
    assert resolve_model_slot(ModelSlot.LOCAL_CODE, settings) == "qwen2.5-coder:7b"
    assert resolve_model_slot(ModelSlot.LOCAL_BOUNDARY, settings) == "phi4-mini"
    assert resolve_model_slot(ModelSlot.CLOUD_TEXT, settings) == "gpt-general"
    assert resolve_model_slot(ModelSlot.CLOUD_CODE, settings) == "gpt-code"
