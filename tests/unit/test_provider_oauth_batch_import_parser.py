import ast
import json
from pathlib import Path


def _load_parse_tokens_input():
    source = Path("src/api/admin/provider_oauth.py").read_text(encoding="utf-8")
    tree = ast.parse(source)
    target_names = {"_extract_refresh_token", "_parse_tokens_input"}
    selected_nodes = [
        node
        for node in tree.body
        if isinstance(node, ast.FunctionDef) and node.name in target_names
    ]
    module = ast.Module(
        body=[
            ast.Import(names=[ast.alias(name="json", asname=None)]),
            ast.ImportFrom(module="typing", names=[ast.alias(name="Any", asname=None)], level=0),
            *selected_nodes,
        ],
        type_ignores=[],
    )
    ast.fix_missing_locations(module)
    namespace: dict[str, object] = {}
    exec(compile(module, filename="<provider_oauth_parser>", mode="exec"), namespace)
    return namespace["_parse_tokens_input"]


_parse_tokens_input = _load_parse_tokens_input()


def test_parse_tokens_input_supports_json_object_array() -> None:
    raw = json.dumps(
        [
            {"refresh_token": "token-a", "name": "a"},
            {"refreshToken": "token-b"},
            {"auth_config": {"refresh_token": "token-c"}},
            {"authConfig": {"refreshToken": "token-d"}},
            "token-e",
        ]
    )

    assert _parse_tokens_input(raw) == [
        "token-a",
        "token-b",
        "token-c",
        "token-d",
        "token-e",
    ]


def test_parse_tokens_input_supports_single_json_object() -> None:
    raw = json.dumps({"auth_config": {"refresh_token": "token-single"}})

    assert _parse_tokens_input(raw) == ["token-single"]


def test_parse_tokens_input_supports_json_lines_objects() -> None:
    raw = "\n".join(
        [
            '{"refresh_token":"token-1"}',
            '{"authConfig":{"refreshToken":"token-2"}}',
            "# comment",
            "token-3",
        ]
    )

    assert _parse_tokens_input(raw) == ["token-1", "token-2", "token-3"]
