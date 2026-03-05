    db: Session,
    *,
    provider_id: str,
    name: str,
    access_token: str,
    auth_config: dict[str, Any],
    api_formats: list[str],
    flush_only: bool = False,
    proxy: dict[str, Any] | None = None,
    auto_fetch_models: bool = True,
) -> "ProviderAPIKey":
    """閸掓稑缂?OAuth Key 鐠佹澘缍嶉獮鑸靛瘮娑斿懎瀵查妴?

    Args:
        flush_only: True 閺冩湹绮?flush閿涘牊澹掗柌蹇撻崗銉ユ簚閺呯礆閿涘瓗alse 閺?commit + refresh閵?
        proxy: Key 缁狙冨焼娴狅絿鎮婇柊宥囩枂閿涘牆 {"node_id": "xxx", "enabled": True}閿涘绱?
               閸掓稑缂撻弮鎯扮純鎮楅敍灞芥倵缂?token 閸掗攱鏌婇妴渚€鎼达箑鍩涢弬鎵搼閹垮秳缍旂粩瀣祮鐠ч鍞悶鍡礉闁灝鍘?IP 濮光剝鐓嬮妴?
        auto_fetch_models: 閺勬儊閸氭暏閼峰З閼惧嘲褰囨稉濠冪埗濡€崇€烽敍宀勬姜 custom 閹绘劒绶甸崯鍡涚帛鐠併倕绱戦崥鈧?
    """
    from src.models.database import ProviderAPIKey as ProviderAPIKeyModel

