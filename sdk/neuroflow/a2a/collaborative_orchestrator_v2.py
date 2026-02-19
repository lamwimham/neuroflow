"""
NeuroFlow Python SDK - A2A Collaborative Orchestrator V2

Enhanced collaboration orchestrator with:
- Real HTTP communication between agents
- Collaboration depth limiting (prevents infinite recursion)
- Timeout control for collaboration requests
- Circuit breaker pattern for fault tolerance
"""

import json
import time
import asyncio
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
import logging

from .agent_registry import (
    AgentRegistry,
    AgentInfo,
    AssistanceRequest,
    AssistanceResponse,
    AgentCapability,
)
from .registry_service import AgentRegistryService, AgentRegistration
from .http_protocol import (
    A2AProtocol,
    A2AHTTPClient,
    AssistRequest,
    AssistResponse,
    A2AMessage,
)
from ..orchestrator import LLMOrchestrator, Message

logger = logging.getLogger(__name__)


@dataclass
class CollaborationPlan:
    """协作计划"""
    needs_collaboration: bool
    target_agents: List[AgentInfo]
    tasks: List[str]
    reasoning: str
    confidence: float = 0.0


@dataclass
class CollaborationResult:
    """协作结果"""
    success: bool
    response: str
    collaboration_used: bool
    collaborating_agents: List[str]
    assistance_results: List[AssistanceResponse]
    reasoning: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class CollaborationContext:
    """Collaboration context for tracking depth and preventing cycles"""
    request_id: str
    current_depth: int = 0
    max_depth: int = 5
    visited_agents: List[str] = field(default_factory=list)
    start_time: float = field(default_factory=time.time)
    timeout_ms: int = 60000
    
    def can_collaborate(self, agent_id: str) -> bool:
        """Check if collaboration is allowed"""
        # Check depth
        if self.current_depth >= self.max_depth:
            logger.warning(f"Max collaboration depth reached ({self.max_depth})")
            return False
        
        # Check for cycles
        if agent_id in self.visited_agents:
            logger.warning(f"Cycle detected: {agent_id} already visited")
            return False
        
        # Check timeout
        elapsed = (time.time() - self.start_time) * 1000
        if elapsed > self.timeout_ms:
            logger.warning(f"Collaboration timeout ({self.timeout_ms}ms)")
            return False
        
        return True
    
    def create_child(self, agent_id: str) -> "CollaborationContext":
        """Create a child context for nested collaboration"""
        return CollaborationContext(
            request_id=self.request_id,
            current_depth=self.current_depth + 1,
            max_depth=self.max_depth,
            visited_agents=self.visited_agents + [agent_id],
            start_time=self.start_time,
            timeout_ms=self.timeout_ms,
        )


class CollaborativeOrchestratorV2:
    """
    Enhanced Collaborative Orchestrator v2
    
    Features:
    - Real HTTP communication between agents
    - Depth limiting to prevent infinite recursion
    - Timeout control for collaboration requests
    - Circuit breaker pattern for fault tolerance
    
    Usage:
        orchestrator = CollaborativeOrchestratorV2(
            llm_orchestrator=llm_orchestrator,
            agent_registry_service=registry_service,
            max_depth=5,
            timeout_ms=30000,
        )
        
        result = await orchestrator.execute_with_collaboration(
            user_message="帮我分析这个数据集并生成可视化",
        )
    """
    
    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        agent_registry_service: Optional[AgentRegistryService] = None,
        agent_registry: Optional[AgentRegistry] = None,
        max_depth: int = 5,
        timeout_ms: int = 30000,
        default_endpoint: Optional[str] = None,
    ):
        self.orchestrator = llm_orchestrator
        self.registry_service = agent_registry_service
        self.registry = agent_registry
        self.max_depth = max_depth
        self.timeout_ms = timeout_ms
        self.default_endpoint = default_endpoint
        
        self._protocol = A2AProtocol()
        self._http_client = A2AHTTPClient(timeout_seconds=timeout_ms // 1000)
        
        # Circuit breaker state
        self._circuit_breakers: Dict[str, Dict[str, Any]] = {}
        self._failure_threshold = 5
        self._recovery_timeout = 60
    
    async def start(self) -> None:
        """Start orchestrator"""
        if self.registry_service:
            await self.registry_service.start()
        logger.info("Collaborative orchestrator started")
    
    async def stop(self) -> None:
        """Stop orchestrator"""
        await self._http_client.close()
        if self.registry_service:
            await self.registry_service.stop()
        logger.info("Collaborative orchestrator stopped")
    
    async def analyze_collaboration_need(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationPlan:
        """分析是否需要协作"""
        # Get available agents
        agents = []
        if self.registry_service:
            agents = await self.registry_service.list_agents()
        elif self.registry:
            agents = self.registry.list_agents()
        
        # Build agent description for LLM
        agents_desc = "\n".join([
            f"- {a.name if isinstance(a, AgentRegistration) else a.name}: "
            f"{a.description if isinstance(a, AgentRegistration) else a.description} "
            f"(capabilities: {', '.join(a.capabilities) if isinstance(a, AgentRegistration) else ', '.join([c.value for c in a.capabilities])})"
            for a in agents
        ])
        
        if not agents_desc:
            agents_desc = "暂无可用的其他 Agent"
        
        messages = [
            Message.system(
                f"""你是一个善于协作的 AI 助手。你可以请求其他专业 Agent 的协助。

可用的其他 Agent:
{agents_desc}

请分析用户请求，判断是否需要其他 Agent 的协助。
如果需要，请说明需要哪个 Agent 以及具体任务。

请用以下 JSON 格式输出:
{{
    "needs_collaboration": true/false,
    "target_agents": ["agent_name1", "agent_name2"],
    "tasks": ["具体任务描述 1", "具体任务描述 2"],
    "reasoning": "为什么需要这些 Agent 协助",
    "confidence": 0.9
}}
"""
            ),
            Message.user(user_message),
        ]
        
        try:
            response = await self.orchestrator.llm.chat(
                messages=messages,
                response_format={"type": "json_object"},
            )
            
            plan_data = json.loads(response.content)
            
            # Get target agents
            target_agents = []
            for agent_name in plan_data.get("target_agents", []):
                agent = await self._find_agent(agent_name)
                if agent:
                    target_agents.append(agent)
            
            return CollaborationPlan(
                needs_collaboration=plan_data.get("needs_collaboration", False),
                target_agents=target_agents,
                tasks=plan_data.get("tasks", []),
                reasoning=plan_data.get("reasoning", ""),
                confidence=plan_data.get("confidence", 0.0),
            )
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse collaboration plan: {e}")
            return CollaborationPlan(
                needs_collaboration=False,
                target_agents=[],
                tasks=[],
                reasoning="无法解析协作计划",
                confidence=0.0,
            )
        except Exception as e:
            logger.error(f"Failed to analyze collaboration need: {e}")
            return CollaborationPlan(
                needs_collaboration=False,
                target_agents=[],
                tasks=[],
                reasoning=f"分析失败：{e}",
                confidence=0.0,
            )
    
    async def _find_agent(self, agent_name: str) -> Optional[Any]:
        """Find agent by name"""
        if self.registry_service:
            agents = await self.registry_service.list_agents()
            for agent in agents:
                if agent.name == agent_name:
                    return agent
        elif self.registry:
            agents = self.registry.list_agents()
            for agent in agents:
                if agent.name == agent_name:
                    return agent
        return None
    
    async def execute_with_collaboration(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
        collaboration_context: Optional[CollaborationContext] = None,
    ) -> CollaborationResult:
        """
        Execute with collaboration
        
        Args:
            user_message: User message
            context: Context information
            collaboration_context: Collaboration tracking context
            
        Returns:
            Collaboration result
        """
        # Initialize collaboration context
        if collaboration_context is None:
            collaboration_context = CollaborationContext(
                request_id=str(time.time()),
                current_depth=0,
                max_depth=self.max_depth,
                timeout_ms=self.timeout_ms,
            )
        
        # Analyze collaboration need
        collab_plan = await self.analyze_collaboration_need(
            user_message,
            context,
        )
        
        if not collab_plan.needs_collaboration or not collab_plan.target_agents:
            # No collaboration needed, execute directly
            result = await self.orchestrator.execute(user_message)
            
            return CollaborationResult(
                success=True,
                response=result.final_response if hasattr(result, 'final_response') else str(result),
                collaboration_used=False,
                collaborating_agents=[],
                assistance_results=[],
                reasoning=collab_plan.reasoning,
            )
        
        # Request assistance from target agents
        assistance_results = []
        collaborating_agents = []
        
        for i, agent in enumerate(collab_plan.target_agents):
            # Check if collaboration is allowed
            agent_id = agent.id if hasattr(agent, 'id') else agent.name
            if not collaboration_context.can_collaborate(agent_id):
                logger.warning(f"Skipping agent {agent_id} due to depth/cycle/timeout constraints")
                continue
            
            # Get task
            task = collab_plan.tasks[i] if i < len(collab_plan.tasks) else user_message
            
            # Create child context
            child_context = collaboration_context.create_child(agent_id)
            
            # Request assistance
            result = await self._request_assistance(
                agent=agent,
                task=task,
                context=context,
                collaboration_context=child_context,
            )
            
            assistance_results.append(result)
            
            if result.success:
                collaborating_agents.append(agent_id)
        
        # Synthesize results
        if any(r.success for r in assistance_results):
            # Successful collaboration, synthesize results
            results_text = "\n\n".join([
                f"Agent {r.agent_id}: {r.result if r.success else f'失败：{r.error}'}"
                for r in assistance_results
            ])
            
            synthesis_messages = [
                Message.system(
                    f"""请根据以下协助结果，给用户一个完整的回复。

用户原始请求：{user_message}

协助结果:
{results_text}

请整合这些结果，提供一个清晰、完整的回复。"""
                ),
                Message.user("请整合这些结果并回复用户。"),
            ]
            
            response = await self.orchestrator.llm.chat(
                messages=synthesis_messages,
            )
            
            return CollaborationResult(
                success=True,
                response=response.content,
                collaboration_used=True,
                collaborating_agents=collaborating_agents,
                assistance_results=assistance_results,
                reasoning=collab_plan.reasoning,
                metadata={"plan": collab_plan, "context": collaboration_context},
            )
        else:
            # All collaboration failed, try to handle ourselves
            result = await self.orchestrator.execute(user_message)
            
            return CollaborationResult(
                success=True,
                response=result.final_response if hasattr(result, 'final_response') else str(result),
                collaboration_used=False,
                collaborating_agents=[],
                assistance_results=assistance_results,
                reasoning=f"协作失败 ({collab_plan.reasoning}), 已尝试自己处理",
                metadata={
                    "failures": [
                        {"agent": r.agent_id, "error": r.error}
                        for r in assistance_results
                    ],
                },
            )
    
    async def _request_assistance(
        self,
        agent: Any,
        task: str,
        context: Optional[Dict[str, Any]] = None,
        collaboration_context: Optional[CollaborationContext] = None,
    ) -> AssistanceResponse:
        """
        Request assistance from an agent
        
        Args:
            agent: Agent to request from
            task: Task description
            context: Context information
            collaboration_context: Collaboration tracking context
            
        Returns:
            Assistance response
        """
        start_time = time.time()
        agent_id = agent.id if hasattr(agent, 'id') else agent.name
        
        # Check circuit breaker
        if self._is_circuit_breaker_open(agent_id):
            logger.warning(f"Circuit breaker open for {agent_id}, rejecting request")
            return AssistanceResponse(
                request_id=collaboration_context.request_id if collaboration_context else str(time.time()),
                success=False,
                result=None,
                agent_id=agent_id,
                error="Circuit breaker open",
            )
        
        # Get agent endpoint
        endpoint = None
        if hasattr(agent, 'endpoint'):
            endpoint = agent.endpoint
        elif self.default_endpoint:
            endpoint = self.default_endpoint
        
        if not endpoint:
            logger.error(f"No endpoint for agent {agent_id}")
            return AssistanceResponse(
                request_id=collaboration_context.request_id if collaboration_context else str(time.time()),
                success=False,
                result=None,
                agent_id=agent_id,
                error="No endpoint available",
            )
        
        try:
            # Create assist request
            assist_request = AssistRequest(
                request_id=collaboration_context.request_id if collaboration_context else str(time.time()),
                task=task,
                context=context or {},
                timeout_ms=self.timeout_ms,
                max_depth=collaboration_context.max_depth if collaboration_context else self.max_depth,
                current_depth=collaboration_context.current_depth if collaboration_context else 0,
            )
            
            # Send HTTP request
            response = await self._http_client.request_assistance(
                endpoint=endpoint,
                sender_id="orchestrator",
                task=task,
                context=context,
                timeout_ms=self.timeout_ms,
            )
            
            # Update circuit breaker
            if response.success:
                self._record_success(agent_id)
            else:
                self._record_failure(agent_id)
            
            execution_time = (time.time() - start_time) * 1000
            
            return AssistanceResponse(
                request_id=assist_request.request_id,
                success=response.success,
                result=response.result,
                agent_id=agent_id,
                error=response.error,
                execution_time_ms=int(execution_time),
            )
            
        except asyncio.TimeoutError:
            self._record_failure(agent_id)
            logger.error(f"Request to {agent_id} timed out")
            return AssistanceResponse(
                request_id=assist_request.request_id if 'assist_request' in locals() else str(time.time()),
                success=False,
                result=None,
                agent_id=agent_id,
                error="Request timeout",
            )
        except Exception as e:
            self._record_failure(agent_id)
            logger.error(f"Request to {agent_id} failed: {e}")
            return AssistanceResponse(
                request_id=assist_request.request_id if 'assist_request' in locals() else str(time.time()),
                success=False,
                result=None,
                agent_id=agent_id,
                error=str(e),
            )
    
    def _is_circuit_breaker_open(self, agent_id: str) -> bool:
        """Check if circuit breaker is open"""
        if agent_id not in self._circuit_breakers:
            return False
        
        cb = self._circuit_breakers[agent_id]
        if cb["failures"] >= self._failure_threshold:
            # Check if recovery timeout has passed
            if time.time() - cb["last_failure"] < self._recovery_timeout:
                return True
            else:
                # Reset circuit breaker
                cb["failures"] = 0
        return False
    
    def _record_success(self, agent_id: str) -> None:
        """Record successful request"""
        if agent_id in self._circuit_breakers:
            self._circuit_breakers[agent_id]["failures"] = 0
    
    def _record_failure(self, agent_id: str) -> None:
        """Record failed request"""
        if agent_id not in self._circuit_breakers:
            self._circuit_breakers[agent_id] = {"failures": 0, "last_failure": time.time()}
        self._circuit_breakers[agent_id]["failures"] += 1
        self._circuit_breakers[agent_id]["last_failure"] = time.time()
    
    async def get_recommended_agents(
        self,
        task_description: str,
        limit: int = 3,
    ) -> List[Any]:
        """
        Get recommended agents for a task
        
        Args:
            task_description: Task description
            limit: Maximum number of recommendations
            
        Returns:
            List of recommended agents
        """
        # Use LLM to analyze required capabilities
        messages = [
            Message.system("""你是一个任务分析专家。请分析任务需要的能力，并推荐合适的 Agent。

请用以下 JSON 格式输出:
{
    "required_capabilities": ["capability1", "capability2"],
    "recommended_agents": ["agent1", "agent2"]
}
"""),
            Message.user(f"任务：{task_description}"),
        ]
        
        try:
            response = await self.orchestrator.llm.chat(
                messages=messages,
                response_format={"type": "json_object"},
            )
            
            plan_data = json.loads(response.content)
            
            # Get recommended agents
            recommended = []
            for agent_name in plan_data.get("recommended_agents", [])[:limit]:
                agent = await self._find_agent(agent_name)
                if agent:
                    recommended.append(agent)
            
            # Fill with available agents if not enough recommendations
            if len(recommended) < limit:
                if self.registry_service:
                    all_agents = await self.registry_service.list_agents()
                elif self.registry:
                    all_agents = self.registry.list_agents()
                else:
                    all_agents = []
                
                for agent in all_agents:
                    if agent not in recommended:
                        recommended.append(agent)
                    if len(recommended) >= limit:
                        break
            
            return recommended
            
        except Exception as e:
            logger.error(f"Failed to get recommended agents: {e}")
            
            # Return all available agents
            if self.registry_service:
                return (await self.registry_service.list_agents())[:limit]
            elif self.registry:
                return self.registry.list_agents()[:limit]
            return []


__all__ = [
    "CollaborationPlan",
    "CollaborationResult",
    "CollaborationContext",
    "CollaborativeOrchestratorV2",
]
