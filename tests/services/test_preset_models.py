from src.services.provider.preset_models import get_preset_models


def test_codex_preset_models_include_gpt_5_4() -> None:
    model_ids = {item.get("id") for item in get_preset_models("codex")}

    assert "gpt-5.4" in model_ids
