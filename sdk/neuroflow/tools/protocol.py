"""
NeuroFlow Python SDK - Unified Tool Protocol

统一工具协议层，支持多种工具来源:
- Local Functions: 本地 Python 函数
- MCP Servers: MCP 服务
- Skills: Rust Skills
- Remote Agents: 其他 Agent
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional
import json
import uuid
import time


class ToolSource(Enum):
    """工具来源类型"""
    LOCAL_FUNCTION = "local_function"
    MCP_SERVER = "mcp_server"
    SKILL = "skill"
    REMOTE_AGENT = "remote_agent"
    LLM_GENERATED = "llm_generated"


class ToolExecutionMode(Enum):
    """工具执行模式"""
    SYNC = "sync"
    ASYNC = "async"
    SANDBOXED = "sandboxed"
    REMOTE = "remote"


@dataclass
class ToolParameter:
    """工具参数定义"""
    name: str
    parameter_type: str  # string, number, boolean, array, object
    description: str
    required: bool = True
    default_value: Optional[Any] = None
    enum_values: Optional[List[Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "name": self.name,
            "type": self.parameter_type,
            "description": self.description,
            "required": self.required,
        }
        if self.default_value is not None:
            result["default"] = self.default_value
        if self.enum_values:
            result["enum"] = self.enum_values
        return result


@dataclass
class ToolDefinition:
    """工具定义 - 统一所有工具类型"""
    id: str
    name: str
    description: str
    source: ToolSource
    parameters: List[ToolParameter]
    return_type: str = "object"
    execution_mode: ToolExecutionMode = ToolExecutionMode.ASYNC
    metadata: Dict[str, Any] = field(default_factory=dict)
    generated_by: Optional[str] = None
    
    def to_llm_schema(self) -> Dict[str, Any]:
        """转换为 LLM Function Calling 的 Schema (OpenAI 格式)"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        p.name: {
                            "type": p.parameter_type,
                            "description": p.description,
                            **({"default": p.default_value} if p.default_value is not None else {}),
                            **({"enum": p.enum_values} if p.enum_values else {}),
                        }
                        for p in self.parameters
                    },
                    "required": [p.name for p in self.parameters if p.required],
                },
            },
        }
    
    def to_anthropic_schema(self) -> Dict[str, Any]:
        """转换为 Anthropic Tool Use 格式"""
        return {
            "name": self.name,
            "description": self.description,
            "input_schema": {
                "type": "object",
                "properties": {
                    p.name: {
                        "type": p.parameter_type,
                        "description": p.description,
                        **({"default": p.default_value} if p.default_value is not None else {}),
                    }
                    for p in self.parameters
                },
                "required": [p.name for p in self.parameters if p.required],
            }
        }


@dataclass
class ToolCall:
    """工具调用请求"""
    tool_id: str
    tool_name: str
    arguments: Dict[str, Any]
    call_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timeout_ms: int = 30000


@dataclass
class ToolResult:
    """工具执行结果"""
    call_id: str
    success: bool
    result: Any
    error: Optional[str] = None
    execution_time_ms: int = 0
    tokens_used: Optional[Dict[str, int]] = None
    
    def to_llm_message(self) -> Dict[str, Any]:
        """转换为 LLM 消息格式"""
        if self.success:
            return {
                "role": "tool",
                "content": json.dumps(self.result) if not isinstance(self.result, str) else self.result,
                "tool_call_id": self.call_id,
            }
        else:
            return {
                "role": "tool",
                "content": json.dumps({"error": self.error}),
                "tool_call_id": self.call_id,
            }


class ToolExecutor(ABC):
    """工具执行器接口 - 所有工具类型的统一接口"""
    
    @abstractmethod
    async def execute(self, call: ToolCall) -> ToolResult:
        """执行工具调用"""
        pass
    
    @abstractmethod
    async def validate(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """验证参数"""
        pass
    
    @abstractmethod
    async def get_schema(self, tool_name: str) -> Optional[ToolDefinition]:
        """获取工具 Schema"""
        pass
    
    @abstractmethod
    def executor_type(self) -> ToolSource:
        """获取执行器类型"""
        pass


class UnifiedToolRegistry:
    """统一工具注册表"""
    
    def __init__(self):
        self._tools: Dict[str, ToolDefinition] = {}
        self._executors: Dict[ToolSource, ToolExecutor] = {}
    
    def register_tool(self, definition: ToolDefinition) -> None:
        """注册工具"""
        self._tools[definition.name] = definition
    
    def register_executor(self, source: ToolSource, executor: ToolExecutor) -> None:
        """注册执行器"""
        self._executors[source] = executor
    
    def get_tool(self, name: str) -> Optional[ToolDefinition]:
        """获取工具定义"""
        return self._tools.get(name)
    
    def list_tools(self) -> List[ToolDefinition]:
        """列出所有工具"""
        return list(self._tools.values())
    
    def get_all_llm_schemas(self) -> List[Dict[str, Any]]:
        """获取所有工具的 LLM Schema"""
        return [t.to_llm_schema() for t in self._tools.values()]
    
    async def execute(self, call: ToolCall) -> ToolResult:
        """执行工具调用"""
        tool = self.get_tool(call.tool_name)
        if not tool:
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error=f"Tool '{call.tool_name}' not found",
            )
        
        executor = self._executors.get(tool.source)
        if not executor:
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error=f"No executor for source '{tool.source}'",
            )
        
        return await executor.execute(call)
    
    async def remove_tool(self, name: str) -> bool:
        """移除工具"""
        if name in self._tools:
            del self._tools[name]
            return True
        return False
    
    def count(self) -> int:
        """获取工具数量"""
        return len(self._tools)


__all__ = [
    "ToolSource",
    "ToolExecutionMode",
    "ToolParameter",
    "ToolDefinition",
    "ToolCall",
    "ToolResult",
    "ToolExecutor",
    "UnifiedToolRegistry",
]
