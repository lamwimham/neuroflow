"""
NeuroFlow Python SDK - A2A Module

Agent-to-Agent 协作模块

v0.4.2: Enhanced with real HTTP communication and registry service
"""

from .agent_registry import (
    AgentCapability,
    AgentStatus,
    AgentInfo,
    AssistanceRequest,
    AssistanceResponse,
    AgentRegistry,
)

from .collaborative_orchestrator import (
    CollaborationPlan,
    CollaborationResult,
    CollaborativeOrchestrator,
)

from .collaborative_orchestrator_v2 import (
    CollaborationContext,
    CollaborativeOrchestratorV2,
)

from .registry_service import (
    AgentRegistration,
    RegistryBackend,
    MemoryRegistry,
    RedisRegistry,
    AgentRegistryService,
)

from .http_protocol import (
    MessageType,
    A2AMessage,
    AssistRequest,
    AssistResponse,
    A2AProtocol,
    A2AHTTPClient,
)


__all__ = [
    # Agent Registry
    "AgentCapability",
    "AgentStatus",
    "AgentInfo",
    "AssistanceRequest",
    "AssistanceResponse",
    "AgentRegistry",

    # Collaborative Orchestrator (v0.4.1)
    "CollaborationPlan",
    "CollaborationResult",
    "CollaborativeOrchestrator",
    
    # Collaborative Orchestrator V2 (v0.4.2)
    "CollaborationContext",
    "CollaborativeOrchestratorV2",
    
    # Registry Service (v0.4.2)
    "AgentRegistration",
    "RegistryBackend",
    "MemoryRegistry",
    "RedisRegistry",
    "AgentRegistryService",
    
    # HTTP Protocol (v0.4.2)
    "MessageType",
    "A2AMessage",
    "AssistRequest",
    "AssistResponse",
    "A2AProtocol",
    "A2AHTTPClient",
]
