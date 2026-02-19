"""
MCP Health Checker

MCP 服务器健康检查模块
"""

import asyncio
import time
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
import logging

from .config_parser import MCPConfig
from .server_manager import MCPServerManager

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """健康状态"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """健康检查结果"""
    server_name: str
    status: HealthStatus
    latency_ms: float = 0.0
    error: Optional[str] = None
    timestamp: float = 0.0
    details: dict = None
    
    def __post_init__(self):
        if self.timestamp == 0.0:
            self.timestamp = time.time()
        if self.details is None:
            self.details = {}
    
    def to_dict(self) -> dict:
        """转换为字典"""
        return {
            "server_name": self.server_name,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "error": self.error,
            "timestamp": self.timestamp,
            "details": self.details,
        }


class MCPHealthChecker:
    """
    MCP 健康检查器
    
    用法:
        checker = MCPHealthChecker(manager)
        
        # 检查所有
        results = await checker.check_all()
        
        # 检查单个
        result = await checker.check_server("filesystem")
        
        # 获取报告
        report = checker.get_health_report()
    """
    
    def __init__(
        self,
        manager: MCPServerManager,
        check_interval: float = 60.0,
        timeout: float = 5.0,
    ):
        self.manager = manager
        self.check_interval = check_interval
        self.timeout = timeout
        
        self._results: Dict[str, HealthCheckResult] = {}
        self._running = False
        self._task: Optional[asyncio.Task] = None
    
    async def check_server(self, server_name: str) -> HealthCheckResult:
        """检查单个服务器"""
        start_time = time.time()
        
        try:
            # 检查连接状态
            if not self.manager.is_connected(server_name):
                return HealthCheckResult(
                    server_name=server_name,
                    status=HealthStatus.UNHEALTHY,
                    error="Not connected",
                )
            
            # TODO: 实现实际的健康检查逻辑
            # 这里使用模拟实现
            
            latency = (time.time() - start_time) * 1000
            
            result = HealthCheckResult(
                server_name=server_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
            )
            
            self._results[server_name] = result
            logger.debug(f"Health check passed for {server_name}: {latency:.2f}ms")
            
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                server_name=server_name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
            )
            self._results[server_name] = result
            logger.error(f"Health check failed for {server_name}: {e}")
            
            return result
    
    async def check_all(self) -> Dict[str, HealthCheckResult]:
        """检查所有服务器"""
        results = {}
        
        for server_name in self.manager.list_servers():
            result = await self.check_server(server_name)
            results[server_name] = result
        
        return results
    
    def get_health_report(self) -> dict:
        """获取健康报告"""
        if not self._results:
            return {
                "status": HealthStatus.UNKNOWN.value,
                "servers": {},
                "healthy_count": 0,
                "degraded_count": 0,
                "unhealthy_count": 0,
            }
        
        healthy = sum(1 for r in self._results.values() if r.status == HealthStatus.HEALTHY)
        degraded = sum(1 for r in self._results.values() if r.status == HealthStatus.DEGRADED)
        unhealthy = sum(1 for r in self._results.values() if r.status == HealthStatus.UNHEALTHY)
        
        # 总体状态
        if unhealthy > 0:
            overall_status = HealthStatus.DEGRADED if healthy > 0 else HealthStatus.UNHEALTHY
        elif degraded > 0:
            overall_status = HealthStatus.DEGRADED
        else:
            overall_status = HealthStatus.HEALTHY
        
        return {
            "status": overall_status.value,
            "servers": {
                name: result.to_dict() 
                for name, result in self._results.items()
            },
            "healthy_count": healthy,
            "degraded_count": degraded,
            "unhealthy_count": unhealthy,
            "total_count": len(self._results),
        }
    
    async def start_periodic_check(self):
        """启动定期检查"""
        self._running = True
        
        async def _check_loop():
            while self._running:
                try:
                    await self.check_all()
                except Exception as e:
                    logger.error(f"Periodic health check error: {e}")
                
                await asyncio.sleep(self.check_interval)
        
        self._task = asyncio.create_task(_check_loop())
        logger.info(f"Started periodic health check (interval: {self.check_interval}s)")
    
    async def stop_periodic_check(self):
        """停止定期检查"""
        self._running = False
        
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
        
        logger.info("Stopped periodic health check")
    
    def is_healthy(self, server_name: str) -> bool:
        """检查服务器是否健康"""
        result = self._results.get(server_name)
        return result.status == HealthStatus.HEALTHY if result else False
    
    def get_unhealthy_servers(self) -> List[str]:
        """获取不健康的服务器列表"""
        return [
            name for name, result in self._results.items()
            if result.status != HealthStatus.HEALTHY
        ]


async def create_health_checker(
    manager: MCPServerManager,
    config_path: Optional[str] = None,
) -> MCPHealthChecker:
    """便捷函数：创建健康检查器"""
    checker = MCPHealthChecker(manager)
    
    # 初始检查
    await checker.check_all()
    
    return checker


if __name__ == "__main__":
    # 测试代码
    async def test():
        # 创建模拟管理器
        manager = MCPServerManager()
        manager.servers = {
            "filesystem": type('obj', (object,), {"connected": True, "name": "filesystem"})(),
            "memory": type('obj', (object,), {"connected": True, "name": "memory"})(),
            "terminal": type('obj', (object,), {"connected": False, "name": "terminal"})(),
        }
        
        checker = MCPHealthChecker(manager)
        
        # 检查所有
        print("Running health checks...")
        await checker.check_all()
        
        # 获取报告
        report = checker.get_health_report()
        
        print("\nHealth Report:")
        print("=" * 50)
        print(f"Overall Status: {report['status']}")
        print(f"Healthy: {report['healthy_count']}")
        print(f"Degraded: {report['degraded_count']}")
        print(f"Unhealthy: {report['unhealthy_count']}")
        print()
        
        for name, server_data in report['servers'].items():
            icon = "✅" if server_data['status'] == 'healthy' else "❌"
            print(f"{icon} {name}: {server_data['status']}")
            if server_data.get('latency_ms'):
                print(f"   Latency: {server_data['latency_ms']:.2f}ms")
            if server_data.get('error'):
                print(f"   Error: {server_data['error']}")
    
    asyncio.run(test())
