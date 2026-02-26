"""
代理节点模块

提供海外 VPS 代理节点的注册、心跳、管理功能。
aether-proxy 部署在海外 VPS 上，通过 WebSocket 隧道连接 Aether 转发 API 请求。
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from src.core.modules.base import (
    ModuleCategory,
    ModuleDefinition,
    ModuleHealth,
    ModuleMetadata,
)

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


def _reset_tunnel_connected_on_startup() -> None:
    """服务端启动时将所有 tunnel_connected=True 的节点重置为 False/UNHEALTHY。

    服务端重启后 TunnelManager 内存状态丢失，但 DB 中可能残留
    tunnel_connected=True 的记录。如果不重置，health_scheduler 会错误地
    将这些节点标记为 ONLINE，而实际上 tunnel 并未连接。
    """
    from datetime import datetime, timezone

    from src.core.logger import logger
    from src.database import create_session
    from src.models.database import ProxyNode, ProxyNodeStatus

    db = create_session()
    try:
        now = datetime.now(timezone.utc)
        stale_nodes = (
            db.query(ProxyNode)
            .filter(
                ProxyNode.tunnel_connected == True,  # noqa: E712
                ProxyNode.is_manual == False,  # noqa: E712
            )
            .all()
        )
        if stale_nodes:
            for node in stale_nodes:
                node.tunnel_connected = False
                node.tunnel_connected_at = now
                node.status = ProxyNodeStatus.UNHEALTHY
                node.updated_at = now
            db.commit()
            logger.info(
                "重置 {} 个节点的残留 tunnel 连接状态 (tunnel_connected -> False)",
                len(stale_nodes),
            )
    except Exception as e:
        try:
            db.rollback()
        except Exception:
            pass
        logger.warning("重置 tunnel 连接状态失败: {}", e)
    finally:
        db.close()


def _get_router() -> Any:
    """延迟导入路由"""
    from src.api.admin.proxy_nodes import router

    return router


async def _on_startup() -> None:
    """启动心跳检测调度器"""
    import logging

    from src.services.proxy_node.auto_fetch_scheduler import get_proxy_node_auto_fetch_scheduler
    from src.services.proxy_node.health_scheduler import get_proxy_node_health_scheduler
    from src.utils.task_coordinator import StartupTaskCoordinator

    logger = logging.getLogger("aether.modules.proxy_nodes")

    # 服务端启动时，TunnelManager 内存为空，所有 tunnel 连接都需要重新建立。
    # 重置 DB 中残留的 tunnel_connected=True 状态，避免 health_scheduler
    # 误将未连接的节点标记为 ONLINE。
    _reset_tunnel_connected_on_startup()

    from src.clients import get_redis_client

    redis_client = await get_redis_client()
    task_coordinator = StartupTaskCoordinator(redis_client)

    proxy_node_health_scheduler = get_proxy_node_health_scheduler()
    active = await task_coordinator.acquire("proxy_node_health")
    if active:
        logger.info("启动 ProxyNode 心跳检测调度器...")
        await proxy_node_health_scheduler.start()
    else:
        logger.info("检测到其他 worker 已运行 ProxyNode 心跳检测，本实例跳过")

    proxy_node_auto_fetch_scheduler = get_proxy_node_auto_fetch_scheduler()
    auto_fetch_active = await task_coordinator.acquire("proxy_node_auto_fetch")
    if auto_fetch_active:
        logger.info("启动 ProxyNode 自动抓取代理任务...")
        await proxy_node_auto_fetch_scheduler.start()
        if not proxy_node_auto_fetch_scheduler.running:
            await task_coordinator.release("proxy_node_auto_fetch")
    else:
        logger.info("检测到其他 worker 已运行 ProxyNode 自动抓取任务，本实例跳过")


async def _on_shutdown() -> None:
    """停止心跳检测调度器"""
    import logging

    from src.services.proxy_node.auto_fetch_scheduler import get_proxy_node_auto_fetch_scheduler
    from src.services.proxy_node.health_scheduler import get_proxy_node_health_scheduler
    from src.utils.task_coordinator import StartupTaskCoordinator

    logger = logging.getLogger("aether.modules.proxy_nodes")

    from src.clients import get_redis_client

    redis_client = await get_redis_client()
    task_coordinator = StartupTaskCoordinator(redis_client)

    scheduler = get_proxy_node_health_scheduler()
    if scheduler.running:
        logger.info("停止 ProxyNode 心跳检测调度器...")
        await scheduler.stop()
        await task_coordinator.release("proxy_node_health")

    auto_fetch_scheduler = get_proxy_node_auto_fetch_scheduler()
    if auto_fetch_scheduler.running:
        logger.info("停止 ProxyNode 自动抓取代理任务...")
        await auto_fetch_scheduler.stop()
    await task_coordinator.release("proxy_node_auto_fetch")


async def _health_check() -> ModuleHealth:
    """健康检查 - 检查是否有在线节点"""
    return ModuleHealth.HEALTHY


def _validate_config(db: Session) -> tuple[bool, str]:
    """验证配置（tunnel 模式无需额外密钥配置）"""
    return True, ""


proxy_nodes_module = ModuleDefinition(
    metadata=ModuleMetadata(
        name="proxy_nodes",
        display_name="代理节点",
        description="海外 VPS 代理节点管理，通过 WebSocket 隧道转发 API 请求",
        category=ModuleCategory.INTEGRATION,
        env_key="PROXY_NODES_AVAILABLE",
        default_available=True,
        required_packages=[],
        api_prefix="/api/admin/proxy-nodes",
        admin_route="/admin/proxy-nodes",
        admin_menu_icon="Server",
        admin_menu_group="system",
        admin_menu_order=60,
    ),
    router_factory=_get_router,
    on_startup=_on_startup,
    on_shutdown=_on_shutdown,
    health_check=_health_check,
    validate_config=_validate_config,
)
