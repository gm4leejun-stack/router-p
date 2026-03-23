from router_p.api.schemas.chat import ChatCompletionRequest
from router_p.domain.model_slots import ModelSlot
from router_p.services.rule_router import RuleRouter


def test_rule_router_routes_code_requests_to_local_code():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a Python function to parse JSON safely"}],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.LOCAL_CODE
    assert decision.rule_name == "code_keywords"


def test_rule_router_routes_complex_general_requests_to_cloud_text():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[
            {
                "role": "user",
                "content": "Compare three deployment architectures and give a step-by-step migration strategy",
            }
        ],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.CLOUD_TEXT
    assert decision.rule_name == "complex_reasoning"


def test_rule_router_defaults_to_local_text():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Write a short welcome message"}],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.LOCAL_TEXT
    assert decision.rule_name == "default_local_text"


def test_rule_router_marks_ambiguous_requests_for_boundary_classification():
    router = RuleRouter()
    request = ChatCompletionRequest(
        model="router-auto",
        messages=[{"role": "user", "content": "Help me figure out the best model for this task"}],
    )

    decision = router.route(request)

    assert decision.slot is ModelSlot.LOCAL_BOUNDARY
    assert decision.rule_name == "boundary_inconclusive"
