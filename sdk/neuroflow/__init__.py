"""
NeuroFlow Python SDK - AI Native 版本 (v0.3.0)

核心概念:
- AINativeAgent: 新一代 Agent，支持自主工具使用、A2A 协作、技能学习
- LLMOrchestrator: LLM 编排器，自主决定使用工具
- UnifiedToolRegistry: 统一工具注册表 (MCP/Skills/Local)

用法:
    from neuroflow import AINativeAgent, create_agent, LLMConfig
    
    # 创建 Agent
    agent = await create_agent(
        name="assistant",
        llm_config=LLMConfig(provider="openai", model="gpt-4"),
    )
    
    # 注册工具
    @agent.tool(name="greet", description="问候某人")
    async def greet(name: str) -> str:
        return f"Hello, {name}!"
    
    # 处理请求
    result = await agent.handle("帮我问候张三")
    print(result["response"])
"""

__version__ = "0.3.0"

# 核心 Agent
from .agent.ai_native_agent import (
    AINativeAgent,
    AINativeAgentConfig,
    create_agent,
)

# LLM 相关
from .orchestrator.llm_client import (
    LLMProvider,
    LLMConfig,
    Message,
    LLMResponse,
    LLMClient,
)

from .orchestrator.llm_orchestrator import (
    OrchestratorMode,
    OrchestratorConfig,
    TurnResult,
    LLMOrchestrator,
)

# 工具相关
from .tools.protocol import (
    ToolSource,
    ToolExecutionMode,
    ToolParameter,
    ToolDefinition,
    ToolCall,
    ToolResult,
    ToolExecutor,
    UnifiedToolRegistry,
)

from .tools.executors import (
    LocalFunctionExecutor,
    MCPToolExecutor,
    SkillExecutor,
)

# A2A 相关 (Phase 3)
from .a2a import (
    AgentCapability,
    AgentStatus,
    AgentInfo,
    AssistanceRequest,
    AssistanceResponse,
    AgentRegistry,
    CollaborativeOrchestrator,
)

# 学习相关 (Phase 3)
from .learning import (
    SkillExample,
    LearnedSkill,
    SkillLearner,
    SkillSandboxExecutor,
)

# 记忆相关 (Phase 3)
from .memory import (
    MemoryType,
    MemoryEntry,
    VectorMemoryStore,
)

# 保留旧版导入以兼容
try:
    from .core import (
        NeuroFlowSDK,
        SDKConfig,
        get_sdk,
    )
except ImportError:
    pass

try:
    from .context import get_context, Context
except ImportError:
    pass

try:
    from .tools import ToolManager, ToolInfo, PermissionLevel
except ImportError:
    pass


__all__ = [
    # Version
    "__version__",
    
    # Core Agent
    "AINativeAgent",
    "AINativeAgentConfig",
    "create_agent",
    
    # LLM
    "LLMProvider",
    "LLMConfig",
    "Message",
    "LLMResponse",
    "LLMClient",
    "OrchestratorMode",
    "OrchestratorConfig",
    "TurnResult",
    "LLMOrchestrator",
    
    # Tools
    "ToolSource",
    "ToolExecutionMode",
    "ToolParameter",
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    "ToolExecutor",
    "UnifiedToolRegistry",
    "LocalFunctionExecutor",
    "MCPToolExecutor",
    "SkillExecutor",
    
    # A2A (Phase 3)
    "AgentCapability",
    "AgentStatus",
    "AgentInfo",
    "AssistanceRequest",
    "AssistanceResponse",
    "AgentRegistry",
    "CollaborativeOrchestrator",
    
    # Learning (Phase 3)
    "SkillExample",
    "LearnedSkill",
    "SkillLearner",
    "SkillSandboxExecutor",
    
    # Memory (Phase 3)
    "MemoryType",
    "MemoryEntry",
    "VectorMemoryStore",
    
    # Legacy (for compatibility)
    "NeuroFlowSDK",
    "SDKConfig",
    "get_sdk",
    "get_context",
    "Context",
    "ToolManager",
    "ToolInfo",
    "PermissionLevel",
]

# 移除 None 值
__all__ = [item for item in __all__ if item is not None]
