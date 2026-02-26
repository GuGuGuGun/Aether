from src.services.proxy_node.auto_fetch_scheduler import (
    _normalize_storage_host,
    _parse_proxy_candidates,
)


def test_parse_proxy_candidates() -> None:
    page = """
    socks5 154.213.4.12 1007 [机房] 美国 加州 洛杉矶 复制 已复制
    http 8.8.8.8 8080 some region
    """
    items = _parse_proxy_candidates(page)

    assert len(items) == 2
    assert items[0].scheme == "socks5"
    assert items[0].host == "154.213.4.12"
    assert items[0].port == 1007
    assert items[0].region == "[机房] 美国 加州 洛杉矶"
    assert items[0].proxy_url == "socks5://154.213.4.12:1007"
    assert items[0].node_name.startswith("tomcat1235-auto-socks5-")


def test_parse_proxy_candidates_deduplicates_and_ignores_invalid_lines() -> None:
    page = """
    socks5 1.2.3.4 1080 x
    socks5 1.2.3.4 1080 y
    socks5 1.2.3.4 99999 invalid
    something else
    """
    items = _parse_proxy_candidates(page)

    assert len(items) == 1
    assert items[0].proxy_url == "socks5://1.2.3.4:1080"


def test_normalize_storage_host_matches_manual_node_behavior() -> None:
    assert _normalize_storage_host("http", "1.2.3.4") == "1.2.3.4"
    assert _normalize_storage_host("https", "1.2.3.4") == "https://1.2.3.4"
    assert _normalize_storage_host("socks5", "1.2.3.4") == "socks5://1.2.3.4"
