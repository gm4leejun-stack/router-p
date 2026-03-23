import logging

from router_p.observability.logging import DecisionLogRecord, log_route_decision


def test_log_route_decision_emits_expected_payload_fields(caplog):
    logger = logging.getLogger("router_p.test")

    with caplog.at_level(logging.INFO, logger="router_p.test"):
        payload = log_route_decision(
            logger,
            DecisionLogRecord(
                provider="ollama",
                selected_model="qwen3:4b",
                route_layer="rule_router",
                rule="simple_text",
                fallback_reason=None,
            ),
        )

    assert payload == {
        "provider": "ollama",
        "selected_model": "qwen3:4b",
        "route_layer": "rule_router",
        "rule": "simple_text",
    }
    record = caplog.records[0]
    assert record.msg == "route.decision"
    assert record.route_decision == payload


def test_log_route_decision_includes_fallback_reason_when_present(caplog):
    logger = logging.getLogger("router_p.test")

    with caplog.at_level(logging.INFO, logger="router_p.test"):
        payload = log_route_decision(
            logger,
            DecisionLogRecord(
                provider="cloud",
                selected_model="gpt-general",
                route_layer="fallback",
                rule="local_exception",
                fallback_reason="local provider raised runtime error",
            ),
        )

    assert payload == {
        "provider": "cloud",
        "selected_model": "gpt-general",
        "route_layer": "fallback",
        "rule": "local_exception",
        "fallback_reason": "local provider raised runtime error",
    }
    assert caplog.records[0].route_decision == payload
