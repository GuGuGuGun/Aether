"""
Codex provider request patching helpers (passthrough path).

This is the **primary** Codex request transformation used by the normalizer's
``patch_for_variant("codex")`` fast path.  It applies minimal, non-destructive
patches directly on the original request dict -- no internal representation
round-trip, so every field the client sent is preserved as-is unless explicitly
modified here.

Transformations applied:
- Force ``store=false`` (avoid persistence features not supported by some gateways).
- Force ``stream=true`` (Codex gateways require streaming).
- Force ``parallel_tool_calls=true``.
- Ensure ``instructions`` exists (Codex expects it in some deployments).
- Convert ``role=system`` messages to ``role=developer`` (Codex may not accept ``system``).
- Drop request parameters known to be rejected by Codex gateways.
- Ensure ``include`` contains ``"reasoning.encrypted_content"`` for parity with CLI behavior.
- Remove ``previous_response_id`` (not supported by Codex gateways).
"""

from __future__ import annotations

from typing import Any

from src.core.provider_types import ProviderType

_REJECTED_PARAMS: frozenset[str] = frozenset(
    {
        "max_output_tokens",
        "max_completion_tokens",
        "max_tokens",
        "temperature",
        "top_p",
        "service_tier",
        "previous_response_id",
    }
)

_REQUIRED_INCLUDE_ITEM = "reasoning.encrypted_content"

_CODEX_HIGH_REASONING_MODELS: frozenset[str] = frozenset(
    {
        "gpt-5.3",
        "gpt-5.2-codex",
    }
)

_CODEX_REASONING_EFFORT_ALIASES: dict[str, str] = {
    "x-high": "xhigh",
    "x_high": "xhigh",
    "very-high": "xhigh",
    "very_high": "xhigh",
    "max": "xhigh",
}


def _normalize_codex_reasoning_config(model: Any, reasoning: Any) -> Any:
    if not isinstance(reasoning, dict):
        return reasoning

    effort = reasoning.get("effort")
    if not isinstance(effort, str) or not effort.strip():
        return reasoning

    normalized_model = str(model or "").strip().lower()
    normalized_effort = _CODEX_REASONING_EFFORT_ALIASES.get(
        effort.strip().lower(), effort.strip().lower()
    )

    if normalized_model in _CODEX_HIGH_REASONING_MODELS and normalized_effort not in {
        "high",
        "xhigh",
    }:
        normalized_effort = "high"

    if normalized_effort == effort:
        return reasoning

    patched_reasoning = dict(reasoning)
    patched_reasoning["effort"] = normalized_effort
    return patched_reasoning


def patch_openai_cli_request_for_codex(request_body: dict[str, Any]) -> dict[str, Any]:
    """
    Patch an OpenAI CLI (Responses API style) request body for Codex gateways.

    This function never mutates the input object.
    """
    out: dict[str, Any] = dict(request_body)

    for k in _REJECTED_PARAMS:
        out.pop(k, None)

    # Codex gateways often reject/ignore persistence; be explicit.
    out["store"] = False

    # Codex gateways require streaming.
    out["stream"] = True

    # Codex expects parallel tool calls enabled.
    out["parallel_tool_calls"] = True

    out["reasoning"] = _normalize_codex_reasoning_config(out.get("model"), out.get("reasoning"))

    # Ensure instructions exists (some gateways require it even if empty).
    instructions = out.get("instructions")
    if not isinstance(instructions, str):
        out["instructions"] = "You are a helpful coding assistant."

    # Convert "system" role to "developer" (Codex behavior).
    input_items = out.get("input")
    if isinstance(input_items, list):
        patched_items: list[Any] = []
        for item in input_items:
            if isinstance(item, dict):
                patched = dict(item)
                if patched.get("role") == "system":
                    patched["role"] = "developer"
                patched_items.append(patched)
            else:
                patched_items.append(item)
        out["input"] = patched_items

    # Ensure required include item exists.
    include = out.get("include")
    if include is None:
        out["include"] = [_REQUIRED_INCLUDE_ITEM]
    elif isinstance(include, str):
        out["include"] = (
            [include] if include == _REQUIRED_INCLUDE_ITEM else [include, _REQUIRED_INCLUDE_ITEM]
        )
    elif isinstance(include, (list, tuple, set)):
        include_list = list(include)
        if _REQUIRED_INCLUDE_ITEM not in include_list:
            include_list.append(_REQUIRED_INCLUDE_ITEM)
        out["include"] = include_list
    else:
        # Unknown type; overwrite to keep behavior deterministic.
        out["include"] = [_REQUIRED_INCLUDE_ITEM]

    return out


def maybe_patch_request_for_codex(
    *,
    provider_type: str | None,
    provider_api_format: str | None,
    request_body: Any,
) -> Any:
    """
    Conditionally patch request body for Codex gateways.

    No-op for:
    - Non-Codex providers
    - Non OpenAI CLI / Responses-style endpoints
    - Non-dict request bodies
    """
    if (provider_type or "").lower() != ProviderType.CODEX:
        return request_body
    if (provider_api_format or "").lower() != "openai:cli":
        return request_body
    if not isinstance(request_body, dict):
        return request_body
    return patch_openai_cli_request_for_codex(request_body)


__all__ = [
    "maybe_patch_request_for_codex",
    "patch_openai_cli_request_for_codex",
]
