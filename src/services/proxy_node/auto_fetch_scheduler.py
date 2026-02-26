"""Auto fetch public proxies and sync them into manual proxy nodes."""

from __future__ import annotations

import asyncio
import os
import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

import httpx

from src.core.logger import logger
from src.database import create_session
from src.models.database import ProxyNode, ProxyNodeStatus
from src.services.system.scheduler import get_scheduler


def _safe_int_env(key: str, default: int, *, minimum: int) -> int:
    raw_value = os.getenv(key)
    if raw_value is None or not raw_value.strip():
        return default
    try:
        value = int(raw_value)
    except ValueError:
        logger.warning("Invalid {}='{}', fallback to {}", key, raw_value, default)
        return default
    return max(minimum, value)


_SOURCE_URL = os.getenv("PROXY_AUTO_FETCH_URL", "https://tomcat1235.nyc.mn/proxy_list").strip()
_AUTO_FETCH_ENABLED = os.getenv("PROXY_AUTO_FETCH_ENABLED", "true").lower() == "true"
_AUTO_FETCH_INTERVAL_SECONDS = _safe_int_env(
    "PROXY_AUTO_FETCH_INTERVAL_SECONDS",
    1800,
    minimum=60,
)
_AUTO_FETCH_MAX_ITEMS = _safe_int_env(
    "PROXY_AUTO_FETCH_MAX_ITEMS",
    60,
    minimum=1,
)

_AUTO_NODE_PREFIX = "tomcat1235-auto"

_PROXY_LINE_RE = re.compile(
    r"^(?P<scheme>https?|socks5)\s+(?P<host>\S+)\s+(?P<port>\d{1,5})(?:\s+(?P<meta>.+))?$",
    re.IGNORECASE,
)
_METADATA_NOISE_RE = re.compile(r"(?:\s+复制|\s+已复制|复制|已复制)+$", re.IGNORECASE)


@dataclass(frozen=True)
class ProxyCandidate:
    scheme: str
    host: str
    port: int
    region: str | None

    @property
    def proxy_url(self) -> str:
        host = self.host
        if ":" in host and not host.startswith("[") and not host.endswith("]"):
            host = f"[{host}]"
        return f"{self.scheme}://{host}:{self.port}"

    @property
    def node_name(self) -> str:
        name = f"{_AUTO_NODE_PREFIX}-{self.scheme}-{self.host}:{self.port}"
        return name[:100]


def _normalize_storage_host(scheme: str, host: str) -> str:
    """Keep uniqueness behavior consistent with manual node creation."""
    normalized_scheme = (scheme or "http").lower()
    return host if normalized_scheme == "http" else f"{normalized_scheme}://{host}"


def _cleanup_region(raw_meta: str | None) -> str | None:
    if not raw_meta:
        return None
    cleaned = _METADATA_NOISE_RE.sub("", raw_meta).strip()
    return cleaned[:100] if cleaned else None


def _parse_proxy_candidates(page_text: str) -> list[ProxyCandidate]:
    candidates: list[ProxyCandidate] = []
    seen: set[tuple[str, str, int]] = set()

    for raw_line in page_text.splitlines():
        line = raw_line.strip()
        if not line:
            continue

        match = _PROXY_LINE_RE.match(line)
        if not match:
            continue

        scheme = match.group("scheme").lower()
        host = match.group("host").strip()
        try:
            port = int(match.group("port"))
        except (TypeError, ValueError):
            continue
        if not 1 <= port <= 65535:
            continue

        key = (scheme, host, port)
        if key in seen:
            continue
        seen.add(key)

        candidates.append(
            ProxyCandidate(
                scheme=scheme,
                host=host,
                port=port,
                region=_cleanup_region(match.group("meta")),
            )
        )

    return candidates


async def _fetch_proxy_candidates() -> list[ProxyCandidate]:
    headers = {"User-Agent": "AetherProxyAutoFetcher/1.0"}
    timeout = httpx.Timeout(15.0, connect=10.0)

    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True, headers=headers) as client:
        response = await client.get(_SOURCE_URL)
        response.raise_for_status()
        parsed = _parse_proxy_candidates(response.text)
        return parsed[:_AUTO_FETCH_MAX_ITEMS]


def _sync_candidates_to_db(candidates: list[ProxyCandidate]) -> dict[str, int]:
    now = datetime.now(timezone.utc)
    db = create_session()
    created = 0
    updated = 0
    skipped = 0

    try:
        for item in candidates:
            storage_host = _normalize_storage_host(item.scheme, item.host)
            existing = (
                db.query(ProxyNode)
                .filter(ProxyNode.ip == storage_host, ProxyNode.port == item.port)
                .first()
            )

            if existing:
                is_managed_auto_node = bool(existing.is_manual) and (
                    existing.name.startswith(_AUTO_NODE_PREFIX)
                    or (existing.proxy_url or "").lower() == item.proxy_url.lower()
                )
                if not is_managed_auto_node:
                    skipped += 1
                    continue

                changed = False
                if existing.name != item.node_name:
                    existing.name = item.node_name
                    changed = True
                if existing.proxy_url != item.proxy_url:
                    existing.proxy_url = item.proxy_url
                    changed = True
                if existing.region != item.region:
                    existing.region = item.region
                    changed = True

                if existing.proxy_username is not None:
                    existing.proxy_username = None
                    changed = True
                if existing.proxy_password is not None:
                    existing.proxy_password = None
                    changed = True

                if existing.status != ProxyNodeStatus.ONLINE:
                    existing.status = ProxyNodeStatus.ONLINE
                    changed = True

                if changed:
                    existing.updated_at = now
                    updated += 1
                else:
                    skipped += 1
                continue

            db.add(
                ProxyNode(
                    id=str(uuid.uuid4()),
                    name=item.node_name,
                    ip=storage_host,
                    port=item.port,
                    region=item.region,
                    is_manual=True,
                    proxy_url=item.proxy_url,
                    proxy_username=None,
                    proxy_password=None,
                    status=ProxyNodeStatus.ONLINE,
                    registered_by=None,
                    last_heartbeat_at=None,
                    heartbeat_interval=0,
                    active_connections=0,
                    total_requests=0,
                    avg_latency_ms=None,
                    created_at=now,
                    updated_at=now,
                )
            )
            created += 1

        if created or updated:
            db.commit()
        else:
            db.rollback()

        return {"fetched": len(candidates), "created": created, "updated": updated, "skipped": skipped}
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


class ProxyNodeAutoFetchScheduler:
    """Sync proxies from a fixed remote source into manual proxy nodes."""

    def __init__(self) -> None:
        self.running = False

    async def start(self) -> Any:
        if self.running:
            logger.warning("ProxyNodeAutoFetchScheduler already running")
            return
        if not _AUTO_FETCH_ENABLED:
            logger.info("Proxy auto fetch is disabled by PROXY_AUTO_FETCH_ENABLED")
            return

        self.running = True
        scheduler = get_scheduler()
        scheduler.add_interval_job(
            self._scheduled_sync,
            seconds=_AUTO_FETCH_INTERVAL_SECONDS,
            job_id="proxy_node_auto_fetch",
            name="proxy node auto fetch",
        )
        logger.info(
            "ProxyNodeAutoFetchScheduler started: source={}, interval={}s, max_items={}",
            _SOURCE_URL,
            _AUTO_FETCH_INTERVAL_SECONDS,
            _AUTO_FETCH_MAX_ITEMS,
        )

        await self._scheduled_sync()

    async def stop(self) -> Any:
        if not self.running:
            return
        self.running = False
        logger.info("ProxyNodeAutoFetchScheduler stopped")

    async def _scheduled_sync(self) -> None:
        if not self.running:
            return

        try:
            candidates = await _fetch_proxy_candidates()
            stats = await asyncio.to_thread(_sync_candidates_to_db, candidates)
            logger.info(
                "Proxy auto fetch synced: fetched={}, created={}, updated={}, skipped={}",
                stats["fetched"],
                stats["created"],
                stats["updated"],
                stats["skipped"],
            )
        except Exception as exc:
            logger.warning("Proxy auto fetch failed from {}: {}", _SOURCE_URL, exc)


_proxy_node_auto_fetch_scheduler: ProxyNodeAutoFetchScheduler | None = None


def get_proxy_node_auto_fetch_scheduler() -> ProxyNodeAutoFetchScheduler:
    global _proxy_node_auto_fetch_scheduler
    if _proxy_node_auto_fetch_scheduler is None:
        _proxy_node_auto_fetch_scheduler = ProxyNodeAutoFetchScheduler()
    return _proxy_node_auto_fetch_scheduler
