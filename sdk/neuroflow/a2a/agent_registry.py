"""
NeuroFlow Python SDK - A2A (Agent-to-Agent) Collaboration

Agent 间自主协作机制:
1. Agent 发现和注册
2. Agent 能力描述
3. 协作请求和响应
4. 自主协作决策
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import aiohttp
import uuid
import time
import logging

logger = logging.getLogger(__name__)


class AgentCapability(Enum):
    """Agent 能力类型"""
    TEXT_GENERATION = "text_generation"
    CODE_EXECUTION = "code_execution"
    WEB_SEARCH = "web_search"
    DATA_ANALYSIS = "data_analysis"
    IMAGE_PROCESSING = "image_processing"
    TOOL_USE = "tool_use"
    SKILL_EXECUTION = "skill_execution"
    MATH = "math"
    TRANSLATION = "translation"


class AgentStatus(Enum):
    """Agent 状态"""
    ACTIVE = "active"
    BUSY = "busy"
    OFFLINE = "offline"
    ERROR = "error"


@dataclass
class AgentInfo:
    """Agent 信息"""
    id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    endpoint: str
    tools: List[str] = field(default_factory=list)
    skills: List[str] = field(default_factory=list)
    status: AgentStatus = AgentStatus.ACTIVE
    latency_ms: int = 0
    success_rate: float = 1.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "capabilities": [c.value for c in self.capabilities],
            "endpoint": self.endpoint,
            "tools": self.tools,
            "skills": self.skills,
            "status": self.status.value,
            "latency_ms": self.latency_ms,
            "success_rate": self.success_rate,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AgentInfo":
        """从字典创建"""
        return cls(
            id=data.get("id", str(uuid.uuid4())),
            name=data.get("name", "Unknown"),
            description=data.get("description", ""),
            capabilities=[
                AgentCapability(c) for c in data.get("capabilities", [])
            ],
            endpoint=data.get("endpoint", ""),
            tools=data.get("tools", []),
            skills=data.get("skills", []),
            status=AgentStatus(data.get("status", "active")),
            latency_ms=data.get("latency_ms", 0),
            success_rate=data.get("success_rate", 1.0),
            metadata=data.get("metadata", {}),
        )
    
    def to_llm_description(self) -> str:
        """转换为 LLM 可读的描述"""
        caps = ", ".join([c.value for c in self.capabilities])
        return f"{self.name}: {self.description} (能力：{caps})"


@dataclass
class AssistanceRequest:
    """协助请求"""
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    requester_agent: str = ""
    task: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    required_capabilities: Optional[List[AgentCapability]] = None
    preferred_agents: Optional[List[str]] = None
    timeout_ms: int = 60000
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "requester_agent": self.requester_agent,
            "task": self.task,
            "context": self.context,
            "required_capabilities": [
                c.value for c in self.required_capabilities
            ] if self.required_capabilities else None,
            "preferred_agents": self.preferred_agents,
            "timeout_ms": self.timeout_ms,
        }


@dataclass
class AssistanceResponse:
    """协助响应"""
    request_id: str
    success: bool
    result: Any
    agent_id: str
    error: Optional[str] = None
    execution_time_ms: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "request_id": self.request_id,
            "success": self.success,
            "result": self.result,
            "agent_id": self.agent_id,
            "error": self.error,
            "execution_time_ms": self.execution_time_ms,
            "metadata": self.metadata,
        }


class AgentRegistry:
    """
    Agent 注册表 - 支持动态发现和选择 Agent
    """
    
    def __init__(self, discovery_endpoint: Optional[str] = None):
        self._agents: Dict[str, AgentInfo] = {}
        self._discovery_endpoint = discovery_endpoint
        self._session: Optional[aiohttp.ClientSession] = None
    
    def register_agent(self, info: AgentInfo) -> None:
        """注册 Agent"""
        self._agents[info.id] = info
        logger.info(f"Registered agent: {info.name} ({info.id})")
    
    def get_agent(self, agent_id: str) -> Optional[AgentInfo]:
        """获取 Agent 信息"""
        return self._agents.get(agent_id)
    
    def list_agents(self) -> List[AgentInfo]:
        """列出所有 Agent"""
        return list(self._agents.values())
    
    def get_agents_by_capability(
        self, 
        capability: AgentCapability
    ) -> List[AgentInfo]:
        """根据能力筛选 Agent"""
        return [
            a for a in self._agents.values() 
            if capability in a.capabilities
        ]
    
    async def discover_agents(self) -> List[AgentInfo]:
        """从发现端点动态发现 Agent"""
        if not self._discovery_endpoint:
            return []
        
        try:
            if not self._session or self._session.closed:
                self._session = aiohttp.ClientSession()
            
            async with self._session.get(
                f"{self._discovery_endpoint}/agents"
            ) as response:
                if response.status == 200:
                    agents_data = await response.json()
                    for data in agents_data:
                        info = AgentInfo.from_dict(data)
                        self.register_agent(info)
                    return self.list_agents()
        except Exception as e:
            logger.error(f"Failed to discover agents: {e}")
        
        return []
    
    async def select_best_agent(
        self,
        task_description: str,
        required_capabilities: Optional[List[AgentCapability]] = None,
    ) -> Optional[AgentInfo]:
        """
        选择最适合的 Agent
        
        Args:
            task_description: 任务描述
            required_capabilities: 必需的能力
            
        Returns:
            最佳 Agent 信息
        """
        candidates = self.list_agents()
        
        if not candidates:
            # 尝试动态发现
            await self.discover_agents()
            candidates = self.list_agents()
        
        if not candidates:
            return None
        
        # 过滤必需能力
        if required_capabilities:
            candidates = [
                a for a in candidates
                if all(cap in a.capabilities for cap in required_capabilities)
            ]
        
        if not candidates:
            return None
        
        # 评分：基于状态、延迟、成功率
        def score_agent(agent: AgentInfo) -> float:
            score = 0.0
            
            # 状态评分
            if agent.status == AgentStatus.ACTIVE:
                score += 0.3
            elif agent.status == AgentStatus.BUSY:
                score += 0.1
            
            # 延迟评分 (越低越好)
            if agent.latency_ms < 100:
                score += 0.3
            elif agent.latency_ms < 500:
                score += 0.2
            elif agent.latency_ms < 1000:
                score += 0.1
            
            # 成功率评分
            score += agent.success_rate * 0.4
            
            return score
        
        # 返回评分最高的
        return max(candidates, key=score_agent)
    
    async def request_assistance(
        self,
        request: AssistanceRequest,
    ) -> AssistanceResponse:
        """请求 Agent 协助"""
        # 选择 Agent
        if request.preferred_agents:
            # 使用指定的 Agent
            for agent_id in request.preferred_agents:
                agent = self.get_agent(agent_id)
                if agent and agent.status == AgentStatus.ACTIVE:
                    return await self._call_agent(agent, request)
        
        # 自动选择最佳 Agent
        best_agent = await self.select_best_agent(
            request.task,
            request.required_capabilities,
        )
        
        if not best_agent:
            return AssistanceResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                agent_id="",
                error="No suitable agent found",
            )
        
        return await self._call_agent(best_agent, request)
    
    async def _call_agent(
        self,
        agent: AgentInfo,
        request: AssistanceRequest,
    ) -> AssistanceResponse:
        """调用 Agent"""
        start = time.time()
        
        try:
            if not self._session or self._session.closed:
                self._session = aiohttp.ClientSession()
            
            async with self._session.post(
                f"{agent.endpoint}/assist",
                json=request.to_dict(),
                timeout=aiohttp.ClientTimeout(total=request.timeout_ms / 1000),
            ) as response:
                elapsed = int((time.time() - start) * 1000)
                
                if response.status == 200:
                    result = await response.json()
                    return AssistanceResponse(
                        request_id=request.request_id,
                        success=True,
                        result=result,
                        agent_id=agent.id,
                        execution_time_ms=elapsed,
                    )
                else:
                    error_text = await response.text()
                    return AssistanceResponse(
                        request_id=request.request_id,
                        success=False,
                        result=None,
                        agent_id=agent.id,
                        error=f"Agent error: {error_text}",
                        execution_time_ms=elapsed,
                    )
        except asyncio.TimeoutError:
            return AssistanceResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                agent_id=agent.id,
                error="Agent request timeout",
            )
        except Exception as e:
            return AssistanceResponse(
                request_id=request.request_id,
                success=False,
                result=None,
                agent_id=agent.id,
                error=str(e),
            )
    
    async def close(self) -> None:
        """关闭会话"""
        if self._session and not self._session.closed:
            await self._session.close()


__all__ = [
    "AgentCapability",
    "AgentStatus",
    "AgentInfo",
    "AssistanceRequest",
    "AssistanceResponse",
    "AgentRegistry",
]
