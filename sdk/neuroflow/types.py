"""
NeuroFlow 类型定义
"""
from typing import Callable, Dict, Any, Optional, Union
from enum import Enum

# Agent相关类型
AgentFunction = Callable[..., Any]

class ToolMetadata:
    """工具元数据"""
    def __init__(self, name: str, description: str, parameters: Dict[str, Any], 
                 return_value_description: str, func: AgentFunction):
        self.name = name
        self.description = description
        self.parameters = parameters
        self.return_value_description = return_value_description
        self.func = func

class AgentMetadata:
    """Agent元数据"""
    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.tools = []

# 内存相关类型
class MemoryType(Enum):
    SHORT_TERM = "short_term"
    LONG_TERM = "long_term"
    EPISODIC = "episodic"
    SEMANTIC = "semantic"
    PROCEDURAL = "procedural"

# A2A通信相关类型
class A2AMessageType(Enum):
    REQUEST = "request"
    RESPONSE = "response"
    NOTIFICATION = "notification"
    QUERY = "query"
    ASSISTANCE_REQUEST = "assistance_request"
    STATUS_UPDATE = "status_update"

class A2APriority(Enum):
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

# MCP相关类型
class ModelTaskType(Enum):
    EMBEDDING = "embedding"
    GENERATION = "generation"
    CLASSIFICATION = "classification"
    TRANSLATION = "translation"
    SUMMARIZATION = "summarization"