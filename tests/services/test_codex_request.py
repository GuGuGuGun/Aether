from __future__ import annotations

from src.services.provider.adapters.codex.request_patching import (
    maybe_patch_request_for_codex,
    patch_openai_cli_request_for_codex,
)


def test_patch_openai_cli_request_for_codex_sets_store_and_instructions() -> None:
    req = {"model": "gpt-test", "input": []}
    out = patch_openai_cli_request_for_codex(req)

    assert out is not req
    assert out["store"] is False
    assert "instructions" in out
    assert isinstance(out["instructions"], str)


def test_patch_openai_cli_request_for_codex_strips_rejected_params() -> None:
    req = {
        "model": "gpt-test",
        "input": [],
        "max_output_tokens": 123,
        "max_completion_tokens": 456,
        "max_tokens": 789,
        "temperature": 0.5,
        "top_p": 0.9,
        "service_tier": "default",
    }
    out = patch_openai_cli_request_for_codex(req)

    for key in (
        "max_output_tokens",
        "max_completion_tokens",
        "max_tokens",
        "temperature",
        "top_p",
        "service_tier",
    ):
        assert key not in out


def test_patch_openai_cli_request_for_codex_converts_system_role_to_developer() -> None:
    req = {
        "model": "gpt-test",
        "instructions": "ignored",
        "input": [
            {
                "type": "message",
                "role": "system",
                "content": [{"type": "input_text", "text": "You are a pirate."}],
            },
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Hello"}],
            },
        ],
    }
    out = patch_openai_cli_request_for_codex(req)

    assert isinstance(out.get("input"), list)
    assert out["input"][0]["role"] == "developer"
    assert out["input"][1]["role"] == "user"


def test_patch_openai_cli_request_for_codex_adds_required_include_item() -> None:
    req = {"model": "gpt-test", "input": []}
    out = patch_openai_cli_request_for_codex(req)

    assert "include" in out
    assert "reasoning.encrypted_content" in out["include"]


def test_patch_openai_cli_request_for_codex_normalizes_reasoning_effort_for_gpt_5_3() -> None:
    req = {"model": "gpt-5.3", "input": [], "reasoning": {"effort": "medium", "summary": "auto"}}
    out = patch_openai_cli_request_for_codex(req)

    assert out["reasoning"]["effort"] == "high"
    assert out["reasoning"]["summary"] == "auto"


def test_patch_openai_cli_request_for_codex_accepts_xhigh_alias_for_gpt_5_2_codex() -> None:
    req = {"model": "gpt-5.2-codex", "input": [], "reasoning": {"effort": "x-high"}}
    out = patch_openai_cli_request_for_codex(req)

    assert out["reasoning"]["effort"] == "xhigh"


def test_patch_openai_cli_request_for_codex_keeps_reasoning_effort_for_other_models() -> None:
    req = {"model": "gpt-5.4", "input": [], "reasoning": {"effort": "medium"}}
    out = patch_openai_cli_request_for_codex(req)

    assert out["reasoning"]["effort"] == "medium"


def test_maybe_patch_request_for_codex_is_noop_for_non_codex() -> None:
    req = {"model": "gpt-test", "input": []}
    out = maybe_patch_request_for_codex(
        provider_type="custom",
        provider_api_format="openai:cli",
        request_body=req,
    )
    assert out is req


def test_maybe_patch_request_for_codex_is_noop_for_non_openai_cli() -> None:
    req = {"model": "gpt-test", "input": []}
    out = maybe_patch_request_for_codex(
        provider_type="codex",
        provider_api_format="openai:chat",
        request_body=req,
    )
    assert out is req


def test_maybe_patch_request_for_codex_patches_for_codex_openai_cli() -> None:
    req = {"model": "gpt-test", "input": []}
    out = maybe_patch_request_for_codex(
        provider_type="codex",
        provider_api_format="openai:cli",
        request_body=req,
    )

    assert out is not req
    assert out["store"] is False
    assert "instructions" in out


def test_codex_envelope_extra_headers_includes_sse_accept_and_session() -> None:
    from src.services.provider.adapters.codex.envelope import codex_oauth_envelope

    headers = codex_oauth_envelope.extra_headers() or {}
    assert headers.get("Accept") == "text/event-stream"
    assert headers.get("x-oai-web-search-eligible") == "true"
    assert headers.get("originator") == "codex_cli_rs"
    assert isinstance(headers.get("session_id"), str)
    assert headers.get("session_id")
