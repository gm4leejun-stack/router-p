from enum import Enum

from router_p.config import Settings


class ModelSlot(str, Enum):
    LOCAL_TEXT = "local_text"
    LOCAL_CODE = "local_code"
    CLOUD_TEXT = "cloud_text"
    CLOUD_CODE = "cloud_code"
    LOCAL_BOUNDARY = "local_boundary"


def resolve_model_slot(slot: ModelSlot, settings: Settings) -> str | None:
    mapping = {
        ModelSlot.LOCAL_TEXT: settings.local_general_model,
        ModelSlot.LOCAL_CODE: settings.local_code_model,
        ModelSlot.CLOUD_TEXT: settings.cloud_general_model,
        ModelSlot.CLOUD_CODE: settings.cloud_code_model,
        ModelSlot.LOCAL_BOUNDARY: settings.local_boundary_model,
    }
    return mapping[slot]


def is_local_slot(slot: ModelSlot) -> bool:
    return slot in {
        ModelSlot.LOCAL_TEXT,
        ModelSlot.LOCAL_CODE,
        ModelSlot.LOCAL_BOUNDARY,
    }


def is_cloud_slot(slot: ModelSlot) -> bool:
    return slot in {
        ModelSlot.CLOUD_TEXT,
        ModelSlot.CLOUD_CODE,
    }
