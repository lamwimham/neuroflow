"""
NeuroFlow Python SDK - A2A HTTP Protocol

HTTP API protocol for Agent-to-Agent communication.

Endpoints:
- GET  /agents              - List all agents
- GET  /agents/{id}         - Get agent details
- POST /agents/register     - Register an agent
- POST /agents/deregister   - Deregister an agent
- POST /agents/{id}/assist  - Request assistance from agent
- GET  /health              - Health check
- POST /heartbeat           - Update heartbeat
"""

import json
import time
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Message type"""
    ASSIST_REQUEST = "assist_request"
    ASSIST_RESPONSE = "assist_response"
    HEARTBEAT = "heartbeat"
    DISCOVERY = "discovery"
    STATUS = "status"


@dataclass
class A2AMessage:
    """A2A message structure"""
    message_id: str
    message_type: MessageType
    sender_id: str
    recipient_id: Optional[str]
    timestamp: float
    payload: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "message_id": self.message_id,
            "message_type": self.message_type.value,
            "sender_id": self.sender_id,
            "recipient_id": self.recipient_id,
            "timestamp": self.timestamp,
            "payload": self.payload,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "A2AMessage":
        """Create from dictionary"""
        return cls(
            message_id=data.get("message_id", ""),
            message_type=MessageType(data.get("message_type", "assist_request")),
            sender_id=data.get("sender_id", ""),
            recipient_id=data.get("recipient_id"),
            timestamp=data.get("timestamp", time.time()),
            payload=data.get("payload", {}),
            metadata=data.get("metadata", {}),
        )
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict())
    
    @classmethod
    def from_json(cls, json_str: str) -> "A2AMessage":
        """Create from JSON string"""
        return cls.from_dict(json.loads(json_str))


@dataclass
class AssistRequest:
    """Assistance request payload"""
    request_id: str
    task: str
    context: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: Optional[List[str]] = None
    preferred_agents: Optional[List[str]] = None
    timeout_ms: int = 60000
    max_depth: int = 5
    current_depth: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "task": self.task,
            "context": self.context,
            "required_capabilities": self.required_capabilities,
            "preferred_agents": self.preferred_agents,
            "timeout_ms": self.timeout_ms,
            "max_depth": self.max_depth,
            "current_depth": self.current_depth,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssistRequest":
        """Create from dictionary"""
        return cls(
            request_id=data.get("request_id", ""),
            task=data.get("task", ""),
            context=data.get("context", {}),
            required_capabilities=data.get("required_capabilities"),
            preferred_agents=data.get("preferred_agents"),
            timeout_ms=data.get("timeout_ms", 60000),
            max_depth=data.get("max_depth", 5),
            current_depth=data.get("current_depth", 0),
        )


@dataclass
class AssistResponse:
    """Assistance response payload"""
    request_id: str
    success: bool
    result: Any = None
    error: Optional[str] = None
    execution_time_ms: float = 0.0
    agent_id: str = ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "agent_id": self.agent_id,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AssistResponse":
        """Create from dictionary"""
        return cls(
            request_id=data.get("request_id", ""),
            success=data.get("success", False),
            result=data.get("result"),
            error=data.get("error"),
            execution_time_ms=data.get("execution_time_ms", 0.0),
            agent_id=data.get("agent_id", ""),
        )


class A2AProtocol:
    """
    A2A Protocol handler
    
    Provides methods for creating and parsing A2A messages.
    
    Usage:
        protocol = A2AProtocol()
        
        # Create assist request message
        message = protocol.create_assist_request(
            sender_id="agent1",
            recipient_id="agent2",
            task="Analyze this data",
            context={"data": [...]},
        )
        
        # Send message via HTTP
        response = await http_client.post(
            f"{agent2_endpoint}/assist",
            json=message.to_dict(),
        )
        
        # Parse response
        response_message = A2AMessage.from_dict(response.json())
        assist_response = protocol.parse_assist_response(response_message)
    """
    
    def __init__(self):
        pass
    
    def create_assist_request(
        self,
        sender_id: str,
        recipient_id: Optional[str],
        task: str,
        context: Optional[Dict[str, Any]] = None,
        required_capabilities: Optional[List[str]] = None,
        preferred_agents: Optional[List[str]] = None,
        timeout_ms: int = 60000,
        max_depth: int = 5,
        current_depth: int = 0,
    ) -> A2AMessage:
        """Create an assist request message"""
        import uuid
        
        request = AssistRequest(
            request_id=str(uuid.uuid4()),
            task=task,
            context=context or {},
            required_capabilities=required_capabilities,
            preferred_agents=preferred_agents,
            timeout_ms=timeout_ms,
            max_depth=max_depth,
            current_depth=current_depth,
        )
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ASSIST_REQUEST,
            sender_id=sender_id,
            recipient_id=recipient_id,
            timestamp=time.time(),
            payload=request.to_dict(),
            metadata={
                "timeout_ms": timeout_ms,
                "max_depth": max_depth,
            },
        )
    
    def create_assist_response(
        self,
        request_id: str,
        success: bool,
        result: Any = None,
        error: Optional[str] = None,
        execution_time_ms: float = 0.0,
        agent_id: str = "",
    ) -> A2AMessage:
        """Create an assist response message"""
        import uuid
        
        response = AssistResponse(
            request_id=request_id,
            success=success,
            result=result,
            error=error,
            execution_time_ms=execution_time_ms,
            agent_id=agent_id,
        )
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.ASSIST_RESPONSE,
            sender_id=agent_id,
            recipient_id=None,
            timestamp=time.time(),
            payload=response.to_dict(),
        )
    
    def create_heartbeat(
        self,
        sender_id: str,
        status: str = "active",
        latency_ms: float = 0.0,
        success_rate: float = 1.0,
    ) -> A2AMessage:
        """Create a heartbeat message"""
        import uuid
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.HEARTBEAT,
            sender_id=sender_id,
            recipient_id=None,
            timestamp=time.time(),
            payload={
                "status": status,
                "latency_ms": latency_ms,
                "success_rate": success_rate,
            },
        )
    
    def create_discovery_request(
        self,
        sender_id: str,
        capability: Optional[str] = None,
    ) -> A2AMessage:
        """Create a discovery request message"""
        import uuid
        
        return A2AMessage(
            message_id=str(uuid.uuid4()),
            message_type=MessageType.DISCOVERY,
            sender_id=sender_id,
            recipient_id=None,
            timestamp=time.time(),
            payload={
                "capability": capability,
            },
        )
    
    def parse_assist_request(
        self,
        message: A2AMessage,
    ) -> AssistRequest:
        """Parse an assist request from message"""
        if message.message_type != MessageType.ASSIST_REQUEST:
            raise ValueError(f"Expected ASSIST_REQUEST, got {message.message_type}")
        return AssistRequest.from_dict(message.payload)
    
    def parse_assist_response(
        self,
        message: A2AMessage,
    ) -> AssistResponse:
        """Parse an assist response from message"""
        if message.message_type != MessageType.ASSIST_RESPONSE:
            raise ValueError(f"Expected ASSIST_RESPONSE, got {message.message_type}")
        return AssistResponse.from_dict(message.payload)


class A2AHTTPClient:
    """
    HTTP client for A2A communication
    
    Usage:
        client = A2AHTTPClient()
        
        # Request assistance
        response = await client.request_assistance(
            endpoint="http://localhost:8081",
            sender_id="agent1",
            task="Analyze this data",
            context={"data": [...]},
        )
        
        # Get agent info
        agent_info = await client.get_agent_info(
            endpoint="http://localhost:8081",
            agent_id="agent2",
        )
        
        # Send heartbeat
        await client.send_heartbeat(
            endpoint="http://localhost:8081",
            agent_id="agent1",
        )
    """
    
    def __init__(self, timeout_seconds: int = 60):
        self._timeout_seconds = timeout_seconds
        self._session: Optional[Any] = None
        self._protocol = A2AProtocol()
    
    async def _get_session(self) -> Any:
        """Get aiohttp session"""
        if self._session is None or self._session.closed:
            import aiohttp
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self._timeout_seconds),
            )
        return self._session
    
    async def close(self) -> None:
        """Close HTTP session"""
        if self._session and not self._session.closed:
            await self._session.close()
    
    async def request_assistance(
        self,
        endpoint: str,
        sender_id: str,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        required_capabilities: Optional[List[str]] = None,
        preferred_agents: Optional[List[str]] = None,
        timeout_ms: int = 60000,
        max_depth: int = 5,
        current_depth: int = 0,
    ) -> AssistResponse:
        """Request assistance from an agent"""
        session = await self._get_session()
        
        # Create assist request message
        message = self._protocol.create_assist_request(
            sender_id=sender_id,
            recipient_id=None,
            task=task,
            context=context,
            required_capabilities=required_capabilities,
            preferred_agents=preferred_agents,
            timeout_ms=timeout_ms,
            max_depth=max_depth,
            current_depth=current_depth,
        )
        
        try:
            async with session.post(
                f"{endpoint}/assist",
                json=message.to_dict(),
            ) as response:
                if response.status == 200:
                    response_data = await response.json()
                    response_message = A2AMessage.from_dict(response_data)
                    return self._protocol.parse_assist_response(response_message)
                else:
                    error_text = await response.text()
                    return AssistResponse(
                        request_id=message.message_id,
                        success=False,
                        error=f"HTTP error {response.status}: {error_text}",
                    )
        except Exception as e:
            logger.error(f"Failed to request assistance: {e}")
            return AssistResponse(
                request_id=message.message_id,
                success=False,
                error=str(e),
            )
    
    async def get_agent_info(
        self,
        endpoint: str,
        agent_id: str,
    ) -> Optional[Dict[str, Any]]:
        """Get agent information"""
        session = await self._get_session()
        
        try:
            async with session.get(f"{endpoint}/agents/{agent_id}") as response:
                if response.status == 200:
                    return await response.json()
                return None
        except Exception as e:
            logger.error(f"Failed to get agent info: {e}")
            return None
    
    async def list_agents(self, endpoint: str) -> List[Dict[str, Any]]:
        """List all agents"""
        session = await self._get_session()
        
        try:
            async with session.get(f"{endpoint}/agents") as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as e:
            logger.error(f"Failed to list agents: {e}")
            return []
    
    async def send_heartbeat(
        self,
        endpoint: str,
        agent_id: str,
        status: str = "active",
        latency_ms: float = 0.0,
        success_rate: float = 1.0,
    ) -> bool:
        """Send heartbeat"""
        session = await self._get_session()
        
        message = self._protocol.create_heartbeat(
            sender_id=agent_id,
            status=status,
            latency_ms=latency_ms,
            success_rate=success_rate,
        )
        
        try:
            async with session.post(
                f"{endpoint}/heartbeat",
                json=message.to_dict(),
            ) as response:
                return response.status == 200
        except Exception as e:
            logger.error(f"Failed to send heartbeat: {e}")
            return False
    
    async def discover_agents(
        self,
        endpoint: str,
        capability: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Discover agents"""
        session = await self._get_session()
        
        message = self._protocol.create_discovery_request(
            sender_id="discovery_client",
            capability=capability,
        )
        
        try:
            url = f"{endpoint}/agents/discover"
            if capability:
                url += f"?capability={capability}"
            
            async with session.post(
                url,
                json=message.to_dict(),
            ) as response:
                if response.status == 200:
                    return await response.json()
                return []
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
            return []


__all__ = [
    "MessageType",
    "A2AMessage",
    "AssistRequest",
    "AssistResponse",
    "A2AProtocol",
    "A2AHTTPClient",
]
