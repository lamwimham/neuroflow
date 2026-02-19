"""
NeuroFlow Python SDK - 核心模块

提供统一的 SDK 入口，采用显式初始化模式
"""
import asyncio
from typing import Optional, Dict, Any, Type
from dataclasses import dataclass, field

from .agent import BaseAgent, agent, tool
from .context import Context, get_context
from .tools import ToolManager, ToolInfo, PermissionLevel


@dataclass
class SDKConfig:
    """SDK 配置"""
    log_level: str = "info"
    enable_tracing: bool = True
    enable_metrics: bool = True
    server_url: str = "http://localhost:8080"


class NeuroFlowSDK:
    """
    NeuroFlow SDK 主类
    
    使用显式初始化模式，避免模块加载时的异步初始化陷阱
    
    用法:
        # 方式 1: 工厂方法
        sdk = await NeuroFlowSDK.create()
        
        # 方式 2: 显式初始化
        sdk = NeuroFlowSDK()
        await sdk.initialize()
    """
    
    _instance: Optional['NeuroFlowSDK'] = None
    
    def __init__(self, config: Optional[SDKConfig] = None):
        """
        初始化 SDK
        
        Args:
            config: SDK 配置，使用默认值如果为 None
        """
        self.config = config or SDKConfig()
        self._initialized = False
        
        # 管理器实例 (延迟初始化)
        self._tool_manager: Optional[ToolManager] = None
        self._agent_registry: Dict[str, Type[BaseAgent]] = {}
        
        # 上下文
        self._context: Optional[Context] = None
    
    @classmethod
    async def create(cls, config: Optional[SDKConfig] = None) -> 'NeuroFlowSDK':
        """
        工厂方法：创建并初始化 SDK 实例
        
        Args:
            config: SDK 配置
            
        Returns:
            已初始化的 SDK 实例
        """
        sdk = cls(config)
        await sdk.initialize()
        return sdk
    
    async def initialize(self) -> None:
        """
        显式初始化 SDK
        
        初始化以下内容:
        - 工具管理器
        - 内置工具注册
        - 上下文
        - 可观测性 (如果启用)
        
        Raises:
            RuntimeError: 如果已经初始化过
        """
        if self._initialized:
            raise RuntimeError("SDK already initialized")
        
        # 初始化工具管理器
        self._tool_manager = ToolManager()
        
        # 注册内置工具
        await self._register_builtin_tools()
        
        # 初始化上下文
        self._context = get_context()
        
        # 初始化可观测性 (如果启用)
        if self.config.enable_tracing or self.config.enable_metrics:
            await self._initialize_observability()
        
        self._initialized = True
    
    async def _register_builtin_tools(self) -> None:
        """注册内置工具"""
        if not self._tool_manager:
            return
        
        # 注册数学计算工具
        @self._tool_manager.register_tool(
            name="calculate",
            description="简单的数学计算器",
            category="utility"
        )
        async def calculate(expression: str) -> float:
            """计算数学表达式"""
            # 安全检查：只允许数字和基本运算符
            allowed = set('0123456789+-*/(). ')
            if not all(c in allowed for c in expression):
                raise ValueError("Invalid characters in expression")
            return float(eval(expression, {"__builtins__": {}}, {}))
        
        # 注册回声工具
        @self._tool_manager.register_tool(
            name="echo",
            description="回显输入",
            category="utility"
        )
        async def echo(message: str) -> str:
            """回显消息"""
            return message
    
    async def _initialize_observability(self) -> None:
        """初始化可观测性"""
        try:
            from .observability import initialize_observability
            
            await initialize_observability()
        except ImportError:
            # OpenTelemetry 未安装，跳过
            pass
    
    def get_tool_manager(self) -> ToolManager:
        """获取工具管理器"""
        if not self._tool_manager:
            raise RuntimeError("SDK not initialized")
        return self._tool_manager
    
    def get_context(self) -> Context:
        """获取上下文"""
        if not self._context:
            raise RuntimeError("SDK not initialized")
        return self._context
    
    def register_agent(self, name: str, agent_class: Type[BaseAgent]) -> None:
        """
        注册 Agent 类
        
        Args:
            name: Agent 名称
            agent_class: Agent 类
        """
        self._agent_registry[name] = agent_class
    
    def get_agent(self, name: str) -> Type[BaseAgent]:
        """
        获取 Agent 类
        
        Args:
            name: Agent 名称
            
        Returns:
            Agent 类
        """
        if name not in self._agent_registry:
            raise KeyError(f"Agent '{name}' not found")
        return self._agent_registry[name]
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        执行工具
        
        Args:
            tool_name: 工具名称
            **kwargs: 工具参数
            
        Returns:
            工具执行结果
        """
        if not self._tool_manager:
            raise RuntimeError("SDK not initialized")
        
        return await self._tool_manager.execute_tool_async(tool_name, **kwargs)
    
    @property
    def is_initialized(self) -> bool:
        """检查 SDK 是否已初始化"""
        return self._initialized
    
    async def shutdown(self) -> None:
        """关闭 SDK"""
        if not self._initialized:
            return
        
        # 关闭可观测性
        try:
            from .observability import shutdown_observability
            await shutdown_observability()
        except ImportError:
            pass
        
        self._initialized = False


# 全局 SDK 实例 (延迟创建)
_sdk_instance: Optional[NeuroFlowSDK] = None


async def get_sdk(config: Optional[SDKConfig] = None) -> NeuroFlowSDK:
    """
    获取全局 SDK 实例
    
    Args:
        config: SDK 配置 (仅在首次创建时使用)
        
    Returns:
        SDK 实例
    """
    global _sdk_instance
    
    if _sdk_instance is None:
        _sdk_instance = await NeuroFlowSDK.create(config)
    
    return _sdk_instance


# 便捷的装饰器函数
def agent(name: Optional[str] = None, description: str = ""):
    """
    Agent 装饰器
    
    用法:
        @agent(name="my_agent")
        class MyAgent(BaseAgent):
            pass
    """
    def decorator(cls):
        agent_name = name or cls.__name__
        
        # 如果 SDK 已初始化，注册到 SDK
        if _sdk_instance and _sdk_instance.is_initialized:
            _sdk_instance.register_agent(agent_name, cls)
        
        return cls
    
    return decorator


def tool(
    name: Optional[str] = None,
    description: str = "",
    category: str = "general"
):
    """
    工具装饰器
    
    用法:
        @tool(name="my_tool")
        async def my_tool(arg: str) -> str:
            return arg
    """
    def decorator(func):
        tool_name = name or func.__name__
        
        # 如果 SDK 已初始化，注册到 SDK
        if _sdk_instance and _sdk_instance.is_initialized:
            _sdk_instance.get_tool_manager().register_function(
                func=func,
                name=tool_name,
                description=description,
                category=category
            )
        
        return func
    
    return decorator


__all__ = [
    # 核心类
    "NeuroFlowSDK",
    "SDKConfig",
    
    # 装饰器
    "agent",
    "tool",
    
    # 便捷函数
    "get_sdk",
    
    # 导出的其他类
    "BaseAgent",
    "Context",
    "ToolManager",
    "ToolInfo",
    "PermissionLevel",
]
