CODE_KEYWORDS = {
    "code",
    "python",
    "javascript",
    "typescript",
    "function",
    "api",
    "sql",
    "regex",
    "test",
    "debug",
    "refactor",
    "stack trace",
    "json",
}

COMPLEX_GENERAL_KEYWORDS = {
    "compare",
    "strategy",
    "step-by-step",
    "architecture",
    "architectures",
    "migration",
    "deep reasoning",
    "exhaustive",
}

COMPLEX_CODE_KEYWORDS = {
    "multi-file",
    "codebase",
    "large-scale",
    "deep debugging",
}

BOUNDARY_KEYWORDS = {
    "best model",
    "figure out",
    "which model",
    "decide the best route",
}


def matches_code_request(prompt: str) -> bool:
    return any(keyword in prompt for keyword in CODE_KEYWORDS) or "```" in prompt


def matches_complex_general_request(prompt: str) -> bool:
    return any(keyword in prompt for keyword in COMPLEX_GENERAL_KEYWORDS)


def matches_complex_code_request(prompt: str) -> bool:
    return any(keyword in prompt for keyword in COMPLEX_CODE_KEYWORDS) and matches_code_request(prompt)


def matches_boundary_request(prompt: str) -> bool:
    return any(keyword in prompt for keyword in BOUNDARY_KEYWORDS)
