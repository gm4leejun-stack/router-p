import logging
from dataclasses import dataclass


@dataclass(frozen=True)
class DecisionLogRecord:
    provider: str
    selected_model: str
    route_layer: str
    rule: str
    fallback_reason: str | None = None


def log_route_decision(
    logger: logging.Logger,
    record: DecisionLogRecord,
) -> dict[str, str]:
    payload = {
        "provider": record.provider,
        "selected_model": record.selected_model,
        "route_layer": record.route_layer,
        "rule": record.rule,
    }
    if record.fallback_reason:
        payload["fallback_reason"] = record.fallback_reason

    logger.info("route.decision", extra={"route_decision": payload})
    return payload
