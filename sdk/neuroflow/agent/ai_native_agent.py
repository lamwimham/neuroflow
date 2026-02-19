"""
NeuroFlow Python SDK - AI Native Agent

新一代 Agent 基类，支持:
1. 自主工具使用 - LLM 自主决定使用 MCP/Skills/Tools
2. 记忆管理 - 长短期记忆支持
3. 工具装饰器 - 简单的工具注册方式
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
import asyncio
import logging
import inspect
import functools

from ..orchestrator import (
    LLMClient,
    LLMConfig,
    Message,
    LLMOrchestrator,
    OrchestratorConfig,
    TurnResult,
)
from ..tools import (
    UnifiedToolRegistry,
    ToolDefinition,
    ToolParameter,
    ToolSource,
    ToolExecutionMode,
    LocalFunctionExecutor,
    MCPToolExecutor,
    SkillExecutor,
)

logger = logging.getLogger(__name__)


@dataclass
class AINativeAgentConfig:
    """AI Native Agent 配置"""
    name: str
    description: str = ""
    llm_config: Optional[LLMConfig] = None
    orchestrator_config: Optional[OrchestratorConfig] = None
    kernel_endpoint: str = "http://localhost:8080"
    mcp_endpoint: str = "http://localhost:8081"
    enable_memory: bool = True
    max_memory_items: int = 100


class AINativeAgent:
    """
    AI Native Agent - 新一代 Agent 基类
    
    核心能力:
    1. 自主工具使用 - LLM 自主决定使用工具
    2. 统一工具接口 - 支持 Local/MCP/Skills
    3. 记忆管理 - 简单的键值记忆
    
    用法:
        agent = AINativeAgent(
            name="assistant",
            description="一个智能助手",
            llm_config=LLMConfig(provider="openai", model="gpt-4"),
        )
        
        @agent.tool(name="greet", description="问候某人")
        async def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        result = await agent.handle("帮我问候张三")
        print(result["response"])
    """
    
    def __init__(self, config: AINativeAgentConfig):
        self.config = config
        
        # 初始化 LLM 客户端
        self.llm = LLMClient(config.llm_config or LLMConfig())
        
        # 初始化工具注册表和执行器
        self.tool_registry = UnifiedToolRegistry()
        self._setup_tool_executors()
        
        # 初始化 LLM 编排器
        self.orchestrator = LLMOrchestrator(
            llm_client=self.llm,
            tool_registry=self.tool_registry,
            config=config.orchestrator_config,
        )
        
        # 记忆存储
        self._memory: Dict[str, Any] = {}
        
        # 对话历史
        self._conversation_history: List[Message] = []
    
    def _setup_tool_executors(self):
        """设置工具执行器"""
        # 本地函数执行器
        self.local_executor = LocalFunctionExecutor()
        self.tool_registry.register_executor(
            ToolSource.LOCAL_FUNCTION, 
            self.local_executor
        )
        
        # MCP 执行器
        self.mcp_executor = MCPToolExecutor(self.config.mcp_endpoint)
        self.tool_registry.register_executor(
            ToolSource.MCP_SERVER, 
            self.mcp_executor
        )
        
        # Skills 执行器
        self.skill_executor = SkillExecutor(self.config.kernel_endpoint)
        self.tool_registry.register_executor(
            ToolSource.SKILL, 
            self.skill_executor
        )
    
    # ========== 装饰器方法 ==========
    
    def tool(self, name: Optional[str] = None, description: str = ""):
        """
        工具装饰器
        
        用法:
            @agent.tool(name="calculate", description="数学计算器")
            async def calculate(self, expression: str) -> float:
                return eval(expression)
        """
        def decorator(func):
            tool_name = name or func.__name__
            
            # 从函数签名推断参数
            sig = inspect.signature(func)
            parameters = []
            for param_name, param in sig.parameters.items():
                if param_name == 'self':
                    continue
                
                # 推断类型
                param_type = "string"
                if param.annotation == int:
                    param_type = "integer"
                elif param.annotation == float:
                    param_type = "number"
                elif param.annotation == bool:
                    param_type = "boolean"
                elif param.annotation == list:
                    param_type = "array"
                elif param.annotation == dict:
                    param_type = "object"
                
                parameters.append(ToolParameter(
                    name=param_name,
                    parameter_type=param_type,
                    description=f"Parameter {param_name}",
                    required=param.default == inspect.Parameter.empty,
                    default_value=(
                        param.default 
                        if param.default != inspect.Parameter.empty 
                        else None
                    ),
                ))
            
            # 创建工具定义
            definition = ToolDefinition(
                id=f"local:{tool_name}",
                name=tool_name,
                description=description,
                source=ToolSource.LOCAL_FUNCTION,
                parameters=parameters,
            )
            
            # 注册工具
            self.tool_registry.register_tool(definition)
            
            # 创建包装函数
            @functools.wraps(func)
            async def wrapper(**kwargs):
                # 绑定 self
                return await func(self, **kwargs)
            
            # 注册函数
            self.local_executor.register_function(wrapper, definition)
            
            logger.info(f"Registered tool: {tool_name}")
            
            return func
        return decorator
    
    # ========== 核心处理方法 ==========
    
    async def handle(self, user_message: str, context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        处理用户请求 - 主入口
        
        Args:
            user_message: 用户消息
            context: 上下文信息
            
        Returns:
            响应字典
        """
        # 添加到对话历史
        self._conversation_history.append(Message.user(user_message))
        
        try:
            # 使用 LLM 编排器处理
            result = await self.orchestrator.execute(
                user_message=user_message,
                conversation_history=self._conversation_history[:-1],
            )
            
            # 记录回复
            self._conversation_history.append(Message.assistant(result.final_response))
            
            return {
                "response": result.final_response,
                "tool_results": [
                    {
                        "tool": r.call_id, 
                        "result": r.result, 
                        "success": r.success,
                        "error": r.error,
                    }
                    for r in result.tool_results
                ],
                "turns_taken": result.turns_taken,
                "success": True,
            }
        except Exception as e:
            logger.exception(f"Error handling message: {e}")
            return {
                "response": f"Error: {str(e)}",
                "tool_results": [],
                "turns_taken": 0,
                "success": False,
                "error": str(e),
            }
    
    # ========== 记忆管理方法 ==========
    
    def store_memory(self, key: str, value: Any, tags: Optional[List[str]] = None) -> None:
        """
        存储记忆
        
        Args:
            key: 记忆键
            value: 记忆值
            tags: 标签列表
        """
        if not self.config.enable_memory:
            return
        
        # 检查记忆数量限制
        if len(self._memory) >= self.config.max_memory_items:
            # 移除最旧的记忆
            oldest_key = next(iter(self._memory))
            del self._memory[oldest_key]
        
        self._memory[key] = {
            "value": value,
            "tags": tags or [],
        }
        
        logger.debug(f"Stored memory: {key}")
    
    def retrieve_memory(self, key: str) -> Optional[Any]:
        """
        检索记忆
        
        Args:
            key: 记忆键
            
        Returns:
            记忆值
        """
        if not self.config.enable_memory:
            return None
        
        entry = self._memory.get(key)
        return entry["value"] if entry else None
    
    def search_memories(self, tags: List[str]) -> List[Any]:
        """
        根据标签搜索记忆
        
        Args:
            tags: 标签列表
            
        Returns:
            记忆值列表
        """
        if not self.config.enable_memory:
            return []
        
        results = []
        for entry in self._memory.values():
            if any(tag in entry.get("tags", []) for tag in tags):
                results.append(entry["value"])
        return results
    
    def clear_memory(self) -> None:
        """清空记忆"""
        self._memory.clear()
    
    # ========== 工具管理方法 ==========
    
    async def discover_mcp_tools(self, server_url: Optional[str] = None) -> List[str]:
        """
        发现并注册 MCP 工具
        
        Args:
            server_url: MCP 服务器 URL
            
        Returns:
            发现的工具名称列表
        """
        tools = await self.mcp_executor.discover_tools(server_url)
        return [t.name for t in tools]
    
    def list_available_tools(self) -> List[str]:
        """列出所有可用工具"""
        return [t.name for t in self.tool_registry.list_tools()]
    
    def get_tool_names(self) -> List[str]:
        """获取工具名称列表"""
        return self.list_available_tools()
    
    # ========== 对话历史管理 ==========
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """获取对话历史"""
        return [m.to_dict() for m in self._conversation_history]
    
    def clear_conversation_history(self) -> None:
        """清空对话历史"""
        self._conversation_history.clear()
    
    def set_system_prompt(self, prompt: str) -> None:
        """
        设置系统提示词
        
        这会替换当前的系统提示词
        """
        # 移除旧的系统消息
        self._conversation_history = [
            m for m in self._conversation_history 
            if m.role != "system"
        ]
        
        # 添加新的系统消息
        self._conversation_history.insert(0, Message.system(prompt))


# ========== 便捷创建函数 ==========

async def create_agent(
    name: str,
    description: str = "",
    llm_config: Optional[LLMConfig] = None,
    **kwargs,
) -> AINativeAgent:
    """
    创建 AI Native Agent
    
    用法:
        agent = await create_agent(
            name="assistant",
            description="一个智能助手",
            llm_config=LLMConfig(provider="openai", model="gpt-4"),
        )
        
        @agent.tool(name="greet", description="问候")
        async def greet(name: str) -> str:
            return f"Hello, {name}!"
        
        result = await agent.handle("帮我问候张三")
    """
    config = AINativeAgentConfig(
        name=name,
        description=description,
        llm_config=llm_config,
        **kwargs,
    )
    return AINativeAgent(config)


__all__ = [
    "AINativeAgent",
    "AINativeAgentConfig",
    "create_agent",
]
