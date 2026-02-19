"""
NeuroFlow Python SDK - A2A Registry Service V2

Enhanced Agent Registry with:
- In-memory registry for single-machine use
- Redis-backed registry for distributed use
- HTTP API for agent discovery and communication
- Health checking and automatic deregistration
"""

import asyncio
import json
import time
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class RegistryBackend(Enum):
    """Registry backend type"""
    MEMORY = "memory"
    REDIS = "redis"


@dataclass
class AgentRegistration:
    """Agent registration information"""
    id: str
    name: str
    description: str
    endpoint: str
    capabilities: List[str]
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    status: str = "active"
    latency_ms: float = 0.0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: float = field(default_factory=time.time)
    last_heartbeat: float = field(default_factory=time.time)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "endpoint": self.endpoint,
            "capabilities": self.capabilities,
            "tools": self.tools,
            "skills": self.skills,
            "status": self.status,
            "latency_ms": self.latency_ms,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
            "registered_at": self.registered_at,
            "last_heartbeat": self.last_heartbeat,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentRegistration":
        """Create from dictionary"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            endpoint=data.get("endpoint", ""),
            capabilities=data.get("capabilities", []),
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            status=data.get("status", "active"),
            latency_ms=data.get("latency_ms", 0.0),
            success_rate=data.get("success_rate", 1.0),
            metadata=data.get("metadata", {}),
            registered_at=data.get("registered_at", time.time()),
            last_heartbeat=data.get("last_heartbeat", time.time()),
        )
    
    def is_healthy(self, timeout_seconds: int = 60) -> bool:
        """Check if agent is healthy based on heartbeat"""
        return (
            self.status == "active" and
            (time.time() - self.last_heartbeat) < timeout_seconds
        )


class MemoryRegistry:
    """
    In-memory agent registry
    
    Suitable for single-machine deployments and development.
    """
    
    def __init__(self):
        self._agents: Dict[str, AgentRegistration] = {}
        self._lock = asyncio.Lock()
        self._health_check_interval = 30  # seconds
        self._health_check_task: Optional[asyncio.Task] = None
        self._is_running = False
    
    async def start(self) -> None:
        """Start health check background task"""
        self._is_running = True
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )
        logger.info("Memory registry started")
    
    async def stop(self) -> None:
        """Stop registry"""
        self._is_running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        logger.info("Memory registry stopped")
    
    async def _health_check_loop(self) -> None:
        """Periodic health check"""
        while self._is_running:
            try:
                await self._check_health()
            except Exception as e:
                logger.error(f"Health check error: {e}")
            await asyncio.sleep(self._health_check_interval)
    
    async def _check_health(self) -> None:
        """Check health of all agents"""
        async with self._lock:
            current_time = time.time()
            for agent_id, agent in list(self._agents.items()):
                # Mark as unhealthy if no heartbeat for 2 minutes
                if current_time - agent.last_heartbeat > 120:
                    logger.warning(f"Agent {agent.name} ({agent_id}) marked as unhealthy")
                    agent.status = "unhealthy"
    
    async def register(self, agent: AgentRegistration) -> bool:
        """Register an agent"""
        async with self._lock:
            self._agents[agent.id] = agent
            logger.info(f"Registered agent: {agent.name} ({agent.id})")
            return True
    
    async def deregister(self, agent_id: str) -> bool:
        """Deregister an agent"""
        async with self._lock:
            if agent_id in self._agents:
                del self._agents[agent_id]
                logger.info(f"Deregistered agent: {agent_id}")
                return True
            return False
    
    async def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent by ID"""
        async with self._lock:
            return self._agents.get(agent_id)
    
    async def list_agents(
        self,
        status_filter: Optional[str] = None,
        capability_filter: Optional[List[str]] = None,
    ) -> List[AgentRegistration]:
        """List agents with optional filters"""
        async with self._lock:
            agents = list(self._agents.values())
        
        # Apply filters
        if status_filter:
            agents = [a for a in agents if a.status == status_filter]
        
        if capability_filter:
            agents = [
                a for a in agents
                if any(cap in a.capabilities for cap in capability_filter)
            ]
        
        return agents
    
    async def update_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat"""
        async with self._lock:
            if agent_id in self._agents:
                self._agents[agent_id].last_heartbeat = time.time()
                if self._agents[agent_id].status == "unhealthy":
                    self._agents[agent_id].status = "active"
                return True
            return False
    
    async def update_stats(
        self,
        agent_id: str,
        latency_ms: Optional[float] = None,
        success_rate: Optional[float] = None,
    ) -> bool:
        """Update agent statistics"""
        async with self._lock:
            if agent_id in self._agents:
                if latency_ms is not None:
                    self._agents[agent_id].latency_ms = latency_ms
                if success_rate is not None:
                    self._agents[agent_id].success_rate = success_rate
                return True
            return False
    
    async def discover_by_capability(
        self,
        capability: str,
        limit: int = 10,
    ) -> List[AgentRegistration]:
        """Discover agents by capability"""
        async with self._lock:
            agents = [
                a for a in self._agents.values()
                if capability in a.capabilities and a.status == "active"
            ]
            return agents[:limit]


class RedisRegistry:
    """
    Redis-backed agent registry
    
    Suitable for distributed deployments with multiple agents.
    """
    
    def __init__(
        self,
        redis_url: str = "redis://localhost:6379",
        key_prefix: str = "neuroflow:agents:",
    ):
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._redis: Optional[Any] = None
        self._pubsub: Optional[Any] = None
        self._is_running = False
        self._health_check_task: Optional[asyncio.Task] = None
    
    async def _get_redis(self) -> Any:
        """Get Redis connection"""
        if self._redis is None:
            try:
                import redis.asyncio as redis
                self._redis = redis.from_url(
                    self._redis_url,
                    decode_responses=True,
                )
                await self._redis.ping()
                logger.info("Connected to Redis")
            except ImportError:
                logger.error("Redis package not installed. Run: pip install redis")
                raise
            except Exception as e:
                logger.error(f"Failed to connect to Redis: {e}")
                raise
        return self._redis
    
    async def start(self) -> None:
        """Start registry"""
        await self._get_redis()
        self._is_running = True
        self._health_check_task = asyncio.create_task(
            self._health_check_loop()
        )
        logger.info("Redis registry started")
    
    async def stop(self) -> None:
        """Stop registry"""
        self._is_running = False
        if self._health_check_task:
            self._health_check_task.cancel()
            try:
                await self._health_check_task
            except asyncio.CancelledError:
                pass
        if self._redis:
            await self._redis.close()
        logger.info("Redis registry stopped")
    
    async def _health_check_loop(self) -> None:
        """Periodic health check"""
        while self._is_running:
            try:
                await self._check_health()
            except Exception as e:
                logger.error(f"Health check error: {e}")
            await asyncio.sleep(30)
    
    async def _check_health(self) -> None:
        """Check health of all agents"""
        redis = await self._get_redis()
        
        # Get all agent IDs
        pattern = f"{self._key_prefix}agent:*"
        async for key in redis.scan_iter(match=pattern):
            agent_data = await redis.hgetall(key)
            if agent_data:
                last_heartbeat = float(agent_data.get("last_heartbeat", 0))
                if time.time() - last_heartbeat > 120:
                    # Mark as unhealthy
                    await redis.hset(key, "status", "unhealthy")
                    logger.warning(f"Agent {key} marked as unhealthy")
    
    def _agent_key(self, agent_id: str) -> str:
        """Get Redis key for agent"""
        return f"{self._key_prefix}agent:{agent_id}"
    
    def _capability_key(self, capability: str) -> str:
        """Get Redis key for capability index"""
        return f"{self._key_prefix}capability:{capability}"
    
    async def register(self, agent: AgentRegistration) -> bool:
        """Register an agent"""
        redis = await self._get_redis()
        
        # Store agent data
        key = self._agent_key(agent.id)
        await redis.hset(key, mapping={
            k: json.dumps(v) if isinstance(v, (dict, list)) else str(v)
            for k, v in agent.to_dict().items()
        })
        
        # Index by capability
        for cap in agent.capabilities:
            await redis.sadd(self._capability_key(cap), agent.id)
        
        # Publish registration event
        await redis.publish(
            f"{self._key_prefix}events",
            json.dumps({
                "event": "agent_registered",
                "agent_id": agent.id,
                "agent_name": agent.name,
            })
        )
        
        logger.info(f"Registered agent: {agent.name} ({agent.id})")
        return True
    
    async def deregister(self, agent_id: str) -> bool:
        """Deregister an agent"""
        redis = await self._get_redis()
        
        # Get agent to remove from capability indexes
        key = self._agent_key(agent_id)
        agent_data = await redis.hgetall(key)
        
        if not agent_data:
            return False
        
        # Remove from capability indexes
        if "capabilities" in agent_data:
            capabilities = json.loads(agent_data["capabilities"])
            for cap in capabilities:
                await redis.srem(self._capability_key(cap), agent_id)
        
        # Delete agent
        await redis.delete(key)
        
        # Publish deregistration event
        await redis.publish(
            f"{self._key_prefix}events",
            json.dumps({
                "event": "agent_deregistered",
                "agent_id": agent_id,
            })
        )
        
        logger.info(f"Deregistered agent: {agent_id}")
        return True
    
    async def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent by ID"""
        redis = await self._get_redis()
        key = self._agent_key(agent_id)
        
        agent_data = await redis.hgetall(key)
        if not agent_data:
            return None
        
        return AgentRegistration.from_dict({
            k: json.loads(v) if v.startswith(("[", "{")) else v
            for k, v in agent_data.items()
        })
    
    async def list_agents(
        self,
        status_filter: Optional[str] = None,
        capability_filter: Optional[List[str]] = None,
    ) -> List[AgentRegistration]:
        """List agents with optional filters"""
        redis = await self._get_redis()
        
        # Get all agent IDs
        pattern = f"{self._key_prefix}agent:*"
        agents = []
        
        async for key in redis.scan_iter(match=pattern):
            agent_data = await redis.hgetall(key)
            if agent_data:
                agent = AgentRegistration.from_dict({
                    k: json.loads(v) if v.startswith(("[", "{")) else v
                    for k, v in agent_data.items()
                })
                
                # Apply filters
                if status_filter and agent.status != status_filter:
                    continue
                if capability_filter and not any(
                    cap in agent.capabilities for cap in capability_filter
                ):
                    continue
                
                agents.append(agent)
        
        return agents
    
    async def update_heartbeat(self, agent_id: str) -> bool:
        """Update agent heartbeat"""
        redis = await self._get_redis()
        key = self._agent_key(agent_id)
        
        exists = await redis.exists(key)
        if exists:
            await redis.hset(key, "last_heartbeat", str(time.time()))
            await redis.hset(key, "status", "active")
            return True
        return False
    
    async def discover_by_capability(
        self,
        capability: str,
        limit: int = 10,
    ) -> List[AgentRegistration]:
        """Discover agents by capability"""
        redis = await self._get_redis()
        
        # Get agent IDs with this capability
        agent_ids = await redis.smembers(self._capability_key(capability))
        
        agents = []
        for agent_id in agent_ids:
            agent = await self.get_agent(agent_id)
            if agent and agent.status == "active":
                agents.append(agent)
                if len(agents) >= limit:
                    break
        
        return agents


class AgentRegistryService:
    """
    Unified agent registry service
    
    Supports both memory and Redis backends.
    
    Usage:
        # Memory backend
        registry = AgentRegistryService(backend="memory")
        
        # Redis backend
        registry = AgentRegistryService(
            backend="redis",
            redis_url="redis://localhost:6379",
        )
        
        await registry.start()
        
        # Register agent
        await registry.register(agent_registration)
        
        # Discover agents
        agents = await registry.discover_by_capability("web_search")
        
        await registry.stop()
    """
    
    def __init__(
        self,
        backend: str = "memory",
        redis_url: Optional[str] = None,
        health_check_interval: int = 30,
    ):
        self._backend_type = RegistryBackend(backend)
        self._redis_url = redis_url
        self._health_check_interval = health_check_interval
        
        if self._backend_type == RegistryBackend.MEMORY:
            self._backend = MemoryRegistry()
        elif self._backend_type == RegistryBackend.REDIS:
            if not redis_url:
                raise ValueError("Redis URL required for Redis backend")
            self._backend = RedisRegistry(redis_url=redis_url)
        else:
            raise ValueError(f"Unknown backend type: {self._backend_type}")
    
    async def start(self) -> None:
        """Start registry service"""
        await self._backend.start()
        logger.info(f"Agent registry service started ({self._backend_type.value})")
    
    async def stop(self) -> None:
        """Stop registry service"""
        await self._backend.stop()
        logger.info("Agent registry service stopped")
    
    async def register(self, agent: AgentRegistration) -> bool:
        """Register an agent"""
        return await self._backend.register(agent)
    
    async def deregister(self, agent_id: str) -> bool:
        """Deregister an agent"""
        return await self._backend.deregister(agent_id)
    
    async def get_agent(self, agent_id: str) -> Optional[AgentRegistration]:
        """Get agent by ID"""
        return await self._backend.get_agent(agent_id)
    
    async def list_agents(
        self,
        status_filter: Optional[str] = None,
        capability_filter: Optional[List[str]] = None,
    ) -> List[AgentRegistration]:
        """List agents"""
        return await self._backend.list_agents(
            status_filter=status_filter,
            capability_filter=capability_filter,
        )
    
    async def update_heartbeat(self, agent_id: str) -> bool:
        """Update heartbeat"""
        return await self._backend.update_heartbeat(agent_id)
    
    async def update_stats(
        self,
        agent_id: str,
        latency_ms: Optional[float] = None,
        success_rate: Optional[float] = None,
    ) -> bool:
        """Update agent statistics"""
        if hasattr(self._backend, 'update_stats'):
            return await self._backend.update_stats(
                agent_id,
                latency_ms=latency_ms,
                success_rate=success_rate,
            )
        return False
    
    async def discover_by_capability(
        self,
        capability: str,
        limit: int = 10,
    ) -> List[AgentRegistration]:
        """Discover agents by capability"""
        return await self._backend.discover_by_capability(
            capability,
            limit=limit,
        )


__all__ = [
    "AgentRegistration",
    "RegistryBackend",
    "MemoryRegistry",
    "RedisRegistry",
    "AgentRegistryService",
]
