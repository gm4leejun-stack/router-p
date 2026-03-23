from pydantic import BaseModel

from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.domain.model_slots import ModelSlot
from router_p.services.routing_rules import (
    matches_boundary_request,
    matches_code_request,
    matches_complex_code_request,
    matches_complex_general_request,
)


class RouteDecision(BaseModel):
    slot: ModelSlot
    rule_name: str
    reason: str
    decision_source: str = "rule"


class RuleRouter:
    def route(self, request: ChatCompletionRequest) -> RouteDecision:
        prompt = " ".join(message.content for message in request.messages).lower()

        if matches_complex_code_request(prompt):
            return RouteDecision(
                slot=ModelSlot.CLOUD_CODE,
                rule_name="complex_code",
                reason="matched complex code request signals",
            )
        if matches_code_request(prompt):
            return RouteDecision(
                slot=ModelSlot.LOCAL_CODE,
                rule_name="code_keywords",
                reason="matched code-oriented keywords",
            )
        if matches_complex_general_request(prompt):
            return RouteDecision(
                slot=ModelSlot.CLOUD_TEXT,
                rule_name="complex_reasoning",
                reason="matched complex general reasoning signals",
            )
        if matches_boundary_request(prompt):
            return RouteDecision(
                slot=ModelSlot.LOCAL_BOUNDARY,
                rule_name="boundary_inconclusive",
                reason="matched ambiguous routing signals",
                decision_source="boundary",
            )
        return RouteDecision(
            slot=ModelSlot.LOCAL_TEXT,
            rule_name="default_local_text",
            reason="no stronger routing rule matched",
        )
