"""
MCP Health Monitor

Health monitoring and error handling for MCP servers with retry logic,
timeout management, and fallback mechanisms.
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class HealthStatus(Enum):
    """Health status"""
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"
    UNKNOWN = "unknown"


@dataclass
class HealthCheckResult:
    """Health check result"""
    server_name: str
    status: HealthStatus
    latency_ms: float = 0.0
    error: Optional[str] = None
    last_check: float = field(default_factory=time.time)
    consecutive_failures: int = 0


@dataclass
class RetryConfig:
    """Retry configuration"""
    max_retries: int = 3
    initial_delay_ms: int = 100
    max_delay_ms: int = 5000
    exponential_base: float = 2.0
    jitter: bool = True


class MCPHealthMonitor:
    """
    MCP Health Monitor
    
    Features:
    - Periodic health checks
    - Automatic retry with exponential backoff
    - Circuit breaker pattern
    - Fallback mechanisms
    
    Usage:
        monitor = MCPHealthMonitor()
        await monitor.start_monitoring(executor)
        
        # Check health
        result = monitor.get_health("filesystem")
        
        # Execute with retry
        result = await monitor.execute_with_retry(
            executor.execute_tool,
            server_name="filesystem",
            tool_name="read_file",
            arguments={"path": "/tmp/test.txt"},
        )
    """
    
    def __init__(
        self,
        retry_config: Optional[RetryConfig] = None,
        check_interval_seconds: int = 30,
        failure_threshold: int = 5,
        recovery_threshold: int = 2,
    ):
        self.retry_config = retry_config or RetryConfig()
        self.check_interval_seconds = check_interval_seconds
        self.failure_threshold = failure_threshold
        self.recovery_threshold = recovery_threshold
        
        self._health_results: Dict[str, HealthCheckResult] = {}
        self._circuit_breakers: Dict[str, bool] = {}  # server_name -> is_open
        self._monitoring_task: Optional[asyncio.Task] = None
        self._is_monitoring = False
    
    async def start_monitoring(self, executor: Any) -> None:
        """Start periodic health monitoring"""
        self._is_monitoring = True
        self._monitoring_task = asyncio.create_task(
            self._monitoring_loop(executor)
        )
        logger.info("MCP health monitoring started")
    
    async def stop_monitoring(self) -> None:
        """Stop health monitoring"""
        self._is_monitoring = False
        if self._monitoring_task:
            self._monitoring_task.cancel()
            try:
                await self._monitoring_task
            except asyncio.CancelledError:
                pass
        logger.info("MCP health monitoring stopped")
    
    async def _monitoring_loop(self, executor: Any) -> None:
        """Periodic health check loop"""
        while self._is_monitoring:
            try:
                server_names = executor.list_servers()
                for server_name in server_names:
                    await self._check_health(executor, server_name)
            except Exception as e:
                logger.error(f"Error in health monitoring loop: {e}")
            
            await asyncio.sleep(self.check_interval_seconds)
    
    async def _check_health(self, executor: Any, server_name: str) -> HealthCheckResult:
        """Check health of a single server"""
        start = time.time()
        
        try:
            connection = executor.get_connection(server_name)
            if not connection or not connection.connected:
                result = HealthCheckResult(
                    server_name=server_name,
                    status=HealthStatus.UNHEALTHY,
                    error="Not connected",
                    last_check=time.time(),
                )
                self._update_health_result(result)
                return result
            
            # Simple latency check
            latency = (time.time() - start) * 1000
            
            result = HealthCheckResult(
                server_name=server_name,
                status=HealthStatus.HEALTHY,
                latency_ms=latency,
                last_check=time.time(),
            )
            
            self._update_health_result(result)
            return result
            
        except Exception as e:
            result = HealthCheckResult(
                server_name=server_name,
                status=HealthStatus.UNHEALTHY,
                error=str(e),
                last_check=time.time(),
            )
            self._update_health_result(result)
            return result
    
    def _update_health_result(self, result: HealthCheckResult) -> None:
        """Update health result and manage circuit breaker"""
        old_result = self._health_results.get(result.server_name)
        
        if result.status == HealthStatus.UNHEALTHY:
            # Increment failure count
            if old_result:
                result.consecutive_failures = old_result.consecutive_failures + 1
            else:
                result.consecutive_failures = 1
            
            # Open circuit breaker if threshold exceeded
            if result.consecutive_failures >= self.failure_threshold:
                self._circuit_breakers[result.server_name] = True
                logger.warning(
                    f"Circuit breaker opened for {result.server_name} "
                    f"(failures: {result.consecutive_failures})"
                )
        else:
            # Reset on success
            if old_result and old_result.status == HealthStatus.UNHEALTHY:
                logger.info(f"{result.server_name} recovered")
            
            result.consecutive_failures = 0
            
            # Close circuit breaker after recovery threshold
            if result.consecutive_failures == 0:
                self._circuit_breakers[result.server_name] = False
        
        self._health_results[result.server_name] = result
    
    def get_health(self, server_name: str) -> Optional[HealthCheckResult]:
        """Get current health status"""
        return self._health_results.get(server_name)
    
    def get_all_health(self) -> Dict[str, HealthCheckResult]:
        """Get health status of all servers"""
        return self._health_results.copy()
    
    def is_healthy(self, server_name: str) -> bool:
        """Check if server is healthy"""
        result = self._health_results.get(server_name)
        if not result:
            return False
        return result.status == HealthStatus.HEALTHY
    
    def is_circuit_breaker_open(self, server_name: str) -> bool:
        """Check if circuit breaker is open"""
        return self._circuit_breakers.get(server_name, False)
    
    async def execute_with_retry(
        self,
        func: Callable,
        *args,
        server_name: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Execute a function with retry logic
        
        Args:
            func: Async function to execute
            *args: Positional arguments
            server_name: Server name for circuit breaker check
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        # Check circuit breaker
        if server_name and self.is_circuit_breaker_open(server_name):
            logger.warning(f"Circuit breaker open for {server_name}, rejecting request")
            raise Exception(f"Circuit breaker open for {server_name}")
        
        last_error = None
        delay_ms = self.retry_config.initial_delay_ms
        
        for attempt in range(self.retry_config.max_retries + 1):
            try:
                result = await func(*args, **kwargs)
                
                # Success - close circuit breaker
                if server_name:
                    self._circuit_breakers[server_name] = False
                
                return result
                
            except Exception as e:
                last_error = e
                logger.warning(
                    f"Attempt {attempt + 1}/{self.retry_config.max_retries + 1} failed: {e}"
                )
                
                if attempt < self.retry_config.max_retries:
                    # Calculate delay with exponential backoff
                    delay_seconds = delay_ms / 1000.0
                    if self.retry_config.jitter:
                        import random
                        delay_seconds *= (0.5 + random.random() * 0.5)
                    
                    logger.info(f"Retrying in {delay_seconds:.2f}s")
                    await asyncio.sleep(delay_seconds)
                    
                    # Increase delay for next attempt
                    delay_ms = min(
                        delay_ms * self.retry_config.exponential_base,
                        self.retry_config.max_delay_ms,
                    )
        
        # All retries failed
        logger.error(f"All retries failed for {server_name}: {last_error}")
        
        # Open circuit breaker
        if server_name:
            result = self._health_results.get(server_name)
            if result:
                result.consecutive_failures = self.failure_threshold
            self._circuit_breakers[server_name] = True
        
        raise last_error
    
    async def execute_with_fallback(
        self,
        primary_func: Callable,
        fallback_func: Callable,
        *args,
        server_name: Optional[str] = None,
        **kwargs,
    ) -> Any:
        """
        Execute with fallback on failure
        
        Args:
            primary_func: Primary async function
            fallback_func: Fallback async function
            *args: Arguments
            server_name: Server name
            **kwargs: Keyword arguments
            
        Returns:
            Function result
        """
        try:
            return await self.execute_with_retry(
                primary_func, *args, server_name=server_name, **kwargs
            )
        except Exception as e:
            logger.warning(f"Primary failed, using fallback: {e}")
            try:
                return await fallback_func(*args, **kwargs)
            except Exception as fallback_error:
                logger.error(f"Fallback also failed: {fallback_error}")
                raise
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get monitoring statistics"""
        total = len(self._health_results)
        healthy = sum(1 for r in self._health_results.values() if r.status == HealthStatus.HEALTHY)
        unhealthy = sum(1 for r in self._health_results.values() if r.status == HealthStatus.UNHEALTHY)
        open_breakers = sum(1 for v in self._circuit_breakers.values() if v)
        
        return {
            "total_servers": total,
            "healthy": healthy,
            "unhealthy": unhealthy,
            "degraded": total - healthy - unhealthy,
            "open_circuit_breakers": open_breakers,
            "check_interval_seconds": self.check_interval_seconds,
        }


__all__ = [
    "HealthStatus",
    "HealthCheckResult",
    "RetryConfig",
    "MCPHealthMonitor",
]
