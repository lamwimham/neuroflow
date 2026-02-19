"""
NeuroFlow Python SDK - A2A Collaborative Orchestrator

协作编排器 - 让 Agent 自主决定何时寻求其他 Agent 协助
"""

import json
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


class CollaborativeOrchestrator:
    """
    协作编排器 - 让 Agent 自主决定何时寻求其他 Agent 协助
    
    核心能力:
    1. 分析任务是否需要协作
    2. 选择合适的 Agent
    3. 请求协助并整合结果
    4. 生成最终回复
    
    用法:
        orchestrator = CollaborativeOrchestrator(
            llm_orchestrator=llm_orchestrator,
            agent_registry=agent_registry,
        )
        
        result = await orchestrator.execute_with_collaboration(
            user_message="帮我分析这个数据集并生成可视化",
        )
    """
    
    def __init__(
        self,
        llm_orchestrator: LLMOrchestrator,
        agent_registry: AgentRegistry,
    ):
        self.orchestrator = llm_orchestrator
        self.registry = agent_registry
        
        # 协作分析提示词
        self.collaboration_prompt = """你是一个善于协作的 AI 助手。你可以请求其他专业 Agent 的协助。

可用的其他 Agent:
{agents_description}

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
        
        # 结果整合提示词
        self.synthesis_prompt = """请根据以下协助结果，给用户一个完整的回复。

用户原始请求：{user_message}

协助结果:
{assistance_results}

请整合这些结果，提供一个清晰、完整的回复。"""
    
    async def analyze_collaboration_need(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationPlan:
        """分析是否需要其他 Agent 协助"""
        # 构建提示词
        agents_desc = "\n".join([
            f"- {a.to_llm_description()}"
            for a in self.registry.list_agents()
        ])
        
        if not agents_desc:
            agents_desc = "暂无可用的其他 Agent"
        
        messages = [
            Message.system(
                self.collaboration_prompt.format(
                    agents_description=agents_desc
                )
            ),
            Message.user(user_message),
        ]
        
        # 调用 LLM 分析
        try:
            response = await self.orchestrator.llm.chat(
                messages=messages,
                response_format={"type": "json_object"},
            )
            
            plan_data = json.loads(response.content)
            
            # 获取目标 Agent
            target_agents = []
            for agent_name in plan_data.get("target_agents", []):
                agent = self.registry.get_agent(agent_name)
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
    
    async def execute_with_collaboration(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> CollaborationResult:
        """
        执行带协作的任务
        
        流程:
        1. 分析是否需要协作
        2. 如果需要，请求其他 Agent 协助
        3. 整合协作结果，回复用户
        
        Args:
            user_message: 用户消息
            context: 上下文信息
            
        Returns:
            协作结果
        """
        # 步骤 1: 分析协作需求
        collab_plan = await self.analyze_collaboration_need(
            user_message, 
            context,
        )
        
        if not collab_plan.needs_collaboration or not collab_plan.target_agents:
            # 不需要协作，直接处理
            result = await self.orchestrator.execute(user_message)
            
            return CollaborationResult(
                success=True,
                response=result.final_response,
                collaboration_used=False,
                collaborating_agents=[],
                assistance_results=[],
                reasoning=collab_plan.reasoning,
            )
        
        # 步骤 2: 请求协助
        assistance_results = []
        collaborating_agents = []
        
        for i, agent in enumerate(collab_plan.target_agents):
            task = collab_plan.tasks[i] if i < len(collab_plan.tasks) else user_message
            
            assistance_request = AssistanceRequest(
                requester_agent=self.orchestrator.llm.config.model,
                task=task,
                context=context or {},
            )
            
            result = await self.registry.request_assistance(assistance_request)
            assistance_results.append(result)
            
            if result.success:
                collaborating_agents.append(agent.name)
        
        # 步骤 3: 整合结果
        if any(r.success for r in assistance_results):
            # 有成功的协助，整合结果
            results_text = "\n\n".join([
                f"Agent {r.agent_id}: {r.result if r.success else f'失败：{r.error}'}"
                for r in assistance_results
            ])
            
            synthesis_messages = [
                Message.system(
                    self.synthesis_prompt.format(
                        user_message=user_message,
                        assistance_results=results_text,
                    )
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
                metadata={"plan": collab_plan},
            )
        else:
            # 所有协助都失败，尝试自己处理
            result = await self.orchestrator.execute(user_message)
            
            return CollaborationResult(
                success=True,
                response=result.final_response,
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
    
    async def get_recommended_agents(
        self,
        task_description: str,
        limit: int = 3,
    ) -> List[AgentInfo]:
        """
        获取推荐的 Agent
        
        Args:
            task_description: 任务描述
            limit: 最大推荐数量
            
        Returns:
            推荐的 Agent 列表
        """
        # 使用 LLM 分析需要的能力
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
            
            # 获取推荐 Agent
            recommended = []
            for agent_name in plan_data.get("recommended_agents", [])[:limit]:
                agent = self.registry.get_agent(agent_name)
                if agent:
                    recommended.append(agent)
            
            # 如果推荐不足，补充可用 Agent
            if len(recommended) < limit:
                all_agents = self.registry.list_agents()
                for agent in all_agents:
                    if agent not in recommended:
                        recommended.append(agent)
                    if len(recommended) >= limit:
                        break
            
            return recommended
        except Exception as e:
            logger.error(f"Failed to get recommended agents: {e}")
            
            # 返回所有可用 Agent
            return self.registry.list_agents()[:limit]


__all__ = [
    "CollaborationPlan",
    "CollaborationResult",
    "CollaborativeOrchestrator",
]
