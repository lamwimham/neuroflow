"""
NeuroFlow Python SDK - LLM Orchestrator

LLM 编排器 - AI Native 的核心
负责：意图理解、工具选择、执行规划、结果整合
"""

import asyncio
import json
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import logging

from .llm_client import LLMClient, LLMConfig, Message, LLMResponse
from ..tools import (
    UnifiedToolRegistry,
    ToolCall,
    ToolResult,
    ToolDefinition,
)

logger = logging.getLogger(__name__)


class OrchestratorMode:
    """编排器模式"""
    AUTO = "auto"              # LLM 自主决定是否使用工具
    FORCE_TOOL = "force_tool"  # 强制使用工具
    NO_TOOL = "no_tool"        # 不使用工具


@dataclass
class OrchestratorConfig:
    """编排器配置"""
    mode: str = "auto"
    max_tool_calls_per_turn: int = 5  # 每轮最多工具调用次数
    parallel_tool_calls: bool = True   # 是否并行执行工具
    tool_timeout_ms: int = 30000       # 工具调用超时
    require_tool_confirmation: bool = False  # 是否需要用户确认


@dataclass
class TurnResult:
    """单轮执行结果"""
    final_response: str           # 最终回复
    tool_results: List[ToolResult]  # 工具执行结果
    turns_taken: int               # 实际执行轮数
    reasoning_trace: List[str] = field(default_factory=list)  # 推理追踪


class LLMOrchestrator:
    """
    LLM 编排器 - AI Native 的核心
    
    核心能力:
    1. 意图理解 - 分析用户输入，理解真实意图
    2. 工具选择 - 从统一工具集中选择合适工具
    3. 执行规划 - 决定工具调用顺序和参数
    4. 结果整合 - 整合工具结果，生成最终回复
    
    用法:
        orchestrator = LLMOrchestrator(
            llm_client=LLMClient(config),
            tool_registry=registry,
        )
        
        result = await orchestrator.execute(
            user_message="帮我计算 123 + 456",
        )
        print(result.final_response)
    """
    
    def __init__(
        self,
        llm_client: LLMClient,
        tool_registry: UnifiedToolRegistry,
        config: Optional[OrchestratorConfig] = None,
    ):
        self.llm = llm_client
        self.registry = tool_registry
        self.config = config or OrchestratorConfig()
        
        # 系统提示词模板
        self.system_prompts = {
            "auto": self._build_auto_system_prompt(),
        }
    
    def _build_auto_system_prompt(self) -> str:
        """构建自主决策模式的系统提示词"""
        return """你是一个智能助手，可以调用各种工具来帮助用户。

你拥有以下工具：
{tools_description}

请遵循以下规则：
1. 仔细分析用户的请求，理解真实意图
2. 如果需要工具帮助，请调用相应的工具
3. 如果不需要工具，直接回复用户
4. 每次调用工具前，请说明你的推理过程
5. 工具调用后，整合结果给用户一个完整的回复

可用工具列表：
{tools_schema}
"""
    
    def _generate_tools_description(self) -> str:
        """生成工具描述文本"""
        tools = self.registry.list_tools()
        if not tools:
            return "暂无可用工具"
        
        lines = []
        for tool in tools:
            params_desc = ", ".join([
                f"{p.name} ({p.parameter_type})" 
                for p in tool.parameters
            ])
            lines.append(f"- {tool.name}({params_desc}): {tool.description}")
        
        return "\n".join(lines)
    
    def _build_messages(
        self,
        user_message: str,
        history: Optional[List[Message]],
        system_prompt: Optional[str],
    ) -> List[Message]:
        """构建消息列表"""
        messages = []
        
        # 添加系统提示词
        if system_prompt:
            messages.append(Message.system(system_prompt))
        else:
            # 使用默认系统提示词，注入工具信息
            tools_desc = self._generate_tools_description()
            tools_schema = json.dumps(
                self.registry.get_all_llm_schemas(), 
                indent=2
            )
            messages.append(Message.system(
                self.system_prompts["auto"].format(
                    tools_description=tools_desc,
                    tools_schema=tools_schema,
                )
            ))
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 添加用户消息
        messages.append(Message.user(user_message))
        
        return messages
    
    def _parse_tool_calls(self, response: LLMResponse) -> List[ToolCall]:
        """解析 LLM 响应中的工具调用"""
        tool_calls = []
        
        if response.tool_calls:
            for tc in response.tool_calls:
                # 处理 OpenAI 格式
                if hasattr(tc, 'function') and hasattr(tc.function, 'name'):
                    try:
                        arguments = json.loads(tc.function.arguments)
                    except (json.JSONDecodeError, AttributeError):
                        arguments = {}
                    
                    tool_calls.append(ToolCall(
                        tool_id=tc.id or str(uuid.uuid4()),
                        tool_name=tc.function.name,
                        arguments=arguments,
                        call_id=tc.id or str(uuid.uuid4()),
                        timeout_ms=self.config.tool_timeout_ms,
                    ))
                # 处理 Anthropic 格式
                elif hasattr(tc, 'type') and tc.type == "tool_use":
                    tool_calls.append(ToolCall(
                        tool_id=tc.id or str(uuid.uuid4()),
                        tool_name=tc.name,
                        arguments=tc.input or {},
                        call_id=tc.id or str(uuid.uuid4()),
                        timeout_ms=self.config.tool_timeout_ms,
                    ))
        
        return tool_calls
    
    async def execute(
        self,
        user_message: str,
        conversation_history: Optional[List[Message]] = None,
        system_prompt: Optional[str] = None,
    ) -> TurnResult:
        """
        执行单轮对话
        
        Args:
            user_message: 用户消息
            conversation_history: 对话历史
            system_prompt: 自定义系统提示词
            
        Returns:
            执行结果
        """
        # 构建消息历史
        messages = self._build_messages(
            user_message, 
            conversation_history,
            system_prompt
        )
        
        tool_results = []
        reasoning_trace = []
        turns_taken = 0
        
        while turns_taken < self.config.max_tool_calls_per_turn:
            turns_taken += 1
            
            # 调用 LLM
            response = await self.llm.chat(
                messages=messages,
                tools=self.registry.get_all_llm_schemas(),
                tool_choice="auto" if self.config.mode == "auto" else "none",
            )
            
            # 解析响应
            tool_calls = self._parse_tool_calls(response)
            
            if not tool_calls:
                # 没有工具调用，直接返回
                return TurnResult(
                    final_response=response.content,
                    tool_results=tool_results,
                    turns_taken=turns_taken,
                    reasoning_trace=reasoning_trace,
                )
            
            # 记录推理
            reasoning_trace.append(
                f"LLM decided to call tools: {[tc.tool_name for tc in tool_calls]}"
            )
            
            # 执行工具调用
            if self.config.parallel_tool_calls:
                results = await self._execute_tools_parallel(tool_calls)
            else:
                results = await self._execute_tools_sequential(tool_calls)
            
            tool_results.extend(results)
            
            # 将工具结果添加到消息历史
            messages.append(Message.assistant(
                content=response.content,
                tool_calls=response.tool_calls,
            ))
            for result in results:
                messages.append(Message.tool(
                    content=json.dumps(result.result) if result.success else result.error,
                    tool_call_id=result.call_id,
                ))
        
        # 达到最大轮数，让 LLM 整合结果
        final_response = await self._synthesize_final_response(
            messages, tool_results
        )
        
        return TurnResult(
            final_response=final_response,
            tool_results=tool_results,
            turns_taken=turns_taken,
            reasoning_trace=reasoning_trace,
        )
    
    async def _execute_tools_parallel(self, calls: List[ToolCall]) -> List[ToolResult]:
        """并行执行工具调用"""
        tasks = [self.registry.execute(call) for call in calls]
        return await asyncio.gather(*tasks)
    
    async def _execute_tools_sequential(self, calls: List[ToolCall]) -> List[ToolResult]:
        """顺序执行工具调用"""
        results = []
        for call in calls:
            result = await self.registry.execute(call)
            results.append(result)
        return results
    
    async def _synthesize_final_response(
        self, 
        messages: List[Message], 
        tool_results: List[ToolResult],
    ) -> str:
        """整合工具结果，生成最终回复"""
        # 让 LLM 整合结果
        synthesis_prompt = Message.user(
            "请根据以上工具执行结果，给用户一个完整的回复。"
        )
        
        response = await self.llm.chat(
            messages=messages + [synthesis_prompt],
            tools=[],  # 不再需要工具
        )
        
        return response.content
    
    async def plan(
        self,
        user_message: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        规划执行计划（不实际执行）
        
        用于预览 LLM 会如何响应用户请求
        """
        reasoning_prompt = """你是一个善于推理的 AI 助手。请按以下步骤处理用户请求：

1. 【分析】分析用户请求，识别关键信息和潜在需求
2. 【规划】决定是否需要工具，如果需要，选择合适的工具
3. 【输出】用 JSON 格式输出你的计划

请用以下 JSON 格式输出:
{
    "analysis": "你的分析",
    "plan": "你的计划",
    "tool_calls": [{"name": "工具名", "arguments": {...}}],
    "needs_user_confirmation": false
}
"""
        
        messages = [
            Message.system(reasoning_prompt),
            Message.user(user_message),
        ]
        
        response = await self.llm.chat(
            messages=messages,
            response_format={"type": "json_object"},
        )
        
        try:
            plan_data = json.loads(response.content)
            return plan_data
        except json.JSONDecodeError:
            return {
                "analysis": "解析失败",
                "plan": response.content,
                "tool_calls": [],
            }


__all__ = [
    "OrchestratorMode",
    "OrchestratorConfig",
    "TurnResult",
    "LLMOrchestrator",
]
