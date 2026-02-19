import asyncio
import functools
import inspect
from typing import Any, Callable, Dict, List, Optional, Union
import traceback
from .context import Context, get_context
from .types import AgentFunction, ToolMetadata
import importlib
import sys
from pathlib import Path
import json
import uuid
from datetime import datetime
import aiohttp
from enum import Enum

# A2A通信相关枚举和类
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

class A2AMessage:
    """A2A消息类"""
    def __init__(self, sender: str, receiver: str, message_type: A2AMessageType, 
                 content: Dict[str, Any], correlation_id: Optional[str] = None, 
                 priority: A2APriority = A2APriority.NORMAL):
        self.id = str(uuid.uuid4())
        self.sender = sender
        self.receiver = receiver
        self.message_type = message_type
        self.content = content
        self.timestamp = datetime.utcnow()
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.priority = priority
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'sender': self.sender,
            'receiver': self.receiver,
            'message_type': self.message_type.value,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'priority': self.priority.value
        }

class A2ACommunicator:
    """A2A通信器"""
    def __init__(self, agent_name: str, endpoint: str = "http://localhost:8080/a2a"):
        self.agent_name = agent_name
        self.endpoint = endpoint
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def send_message(self, message: A2AMessage) -> Optional[Dict[str, Any]]:
        """发送A2A消息"""
        if not self.session:
            raise RuntimeError("A2ACommunicator not initialized. Use as context manager.")
        
        try:
            async with self.session.post(self.endpoint, json=message.to_dict()) as response:
                if response.status == 200:
                    return await response.json()
                else:
                    raise RuntimeError(f"Failed to send message: {response.status}")
        except Exception as e:
            raise RuntimeError(f"Error sending A2A message: {str(e)}")
    
    async def request_assistance(self, target_agent: str, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """请求其他Agent的协助"""
        message = A2AMessage(
            sender=self.agent_name,
            receiver=target_agent,
            message_type=A2AMessageType.ASSISTANCE_REQUEST,
            content={
                'task': task,
                'params': params
            },
            priority=A2APriority.HIGH
        )
        
        return await self.send_message(message)

# MCP (Model Context Protocol) 客户端
class MCPClient:
    """MCP客户端，用于与模型服务通信"""
    def __init__(self, endpoint: str = "http://localhost:8081/mcp"):
        self.endpoint = endpoint
        self.session = None
    
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    async def get_embeddings(self, texts: List[str], model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
        """获取文本嵌入向量"""
        if not self.session:
            raise RuntimeError("MCPClient not initialized. Use as context manager.")
        
        payload = {
            'model': model,
            'input': texts,
            'task': 'embedding'
        }
        
        try:
            async with self.session.post(f"{self.endpoint}/embeddings", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('embeddings', [])
                else:
                    raise RuntimeError(f"Failed to get embeddings: {response.status}")
        except Exception as e:
            raise RuntimeError(f"Error getting embeddings: {str(e)}")
    
    async def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", params: Optional[Dict[str, Any]] = None) -> str:
        """生成文本"""
        if not self.session:
            raise RuntimeError("MCPClient not initialized. Use as context manager.")
        
        payload = {
            'model': model,
            'prompt': prompt,
            'task': 'generation',
            'params': params or {}
        }
        
        try:
            async with self.session.post(f"{self.endpoint}/generate", json=payload) as response:
                if response.status == 200:
                    result = await response.json()
                    return result.get('generated_text', '')
                else:
                    raise RuntimeError(f"Failed to generate text: {response.status}")
        except Exception as e:
            raise RuntimeError(f"Error generating text: {str(e)}")

# 全局注册表
_global_tools_registry = {}
_global_agents_registry = {}

def tool(
    name: Optional[str] = None,
    description: str = "",
    parameters: Optional[Dict[str, Any]] = None,
    return_value_description: str = ""
):
    """
    装饰器：将函数注册为工具
    """
    def decorator(func: AgentFunction):
        # 获取函数名作为工具名
        tool_name = name or func.__name__
        
        # 如果没有提供参数，则尝试从类型注解推断
        if parameters is None:
            sig = inspect.signature(func)
            params = {}
            for param_name, param in sig.parameters.items():
                param_schema = {"type": "string"}  # 默认为字符串类型
                if param.annotation != inspect.Parameter.empty:
                    # 根据类型注解设置类型
                    if param.annotation == int:
                        param_schema["type"] = "integer"
                    elif param.annotation == float:
                        param_schema["type"] = "number"
                    elif param.annotation == bool:
                        param_schema["type"] = "boolean"
                    elif param.annotation == list:
                        param_schema["type"] = "array"
                    elif param.annotation == dict:
                        param_schema["type"] = "object"
                
                if param.default != inspect.Parameter.empty:
                    param_schema["default"] = param.default
                    param_schema["required"] = False
                else:
                    param_schema["required"] = True
                
                params[param_name] = param_schema
        else:
            params = parameters
        
        # 创建工具元数据
        tool_metadata = ToolMetadata(
            name=tool_name,
            description=description,
            parameters=params,
            return_value_description=return_value_description,
            func=func
        )
        
        # 注册到全局工具注册表
        _global_tools_registry[tool_name] = tool_metadata
        
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)
        
        # 将元数据附加到函数上
        wrapper.tool_metadata = tool_metadata
        return wrapper
    
    return decorator

class BaseAgent:
    """
    增强的BaseAgent类，支持A2A通信、MCP和更丰富的记忆功能
    """
    def __init__(self, name: str, description: str = ""):
        self.name = name
        self.description = description
        self.tools = {}
        self.context = get_context()
        self.a2a_communicator = A2ACommunicator(name)
        self.mcp_client = MCPClient()
        
        # 自动注册已装饰的方法
        self._register_decorated_methods()
    
    def _register_decorated_methods(self):
        """
        注册所有已用@tool装饰的方法
        """
        for attr_name in dir(self):
            attr = getattr(self, attr_name)
            if hasattr(attr, 'tool_metadata'):
                tool_meta = attr.tool_metadata
                self.tools[tool_meta.name] = {
                    'metadata': tool_meta,
                    'callable': attr
                }
    
    def register_tool(self, func: AgentFunction, name: Optional[str] = None, 
                     description: str = "", parameters: Optional[Dict[str, Any]] = None):
        """
        手动注册工具
        """
        tool_name = name or func.__name__
        tool_metadata = ToolMetadata(
            name=tool_name,
            description=description,
            parameters=parameters or {},
            return_value_description="",
            func=func
        )
        
        self.tools[tool_name] = {
            'metadata': tool_metadata,
            'callable': func
        }
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """
        执行指定的工具
        """
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_info = self.tools[tool_name]
        func = tool_info['callable']
        
        try:
            # 如果是协程函数，await它；否则直接调用
            if asyncio.iscoroutinefunction(func):
                result = await func(**kwargs)
            else:
                result = func(**kwargs)
            return result
        except Exception as e:
            raise RuntimeError(f"Error executing tool '{tool_name}': {str(e)}")
    
    def get_tool_metadata(self, tool_name: str) -> Optional[ToolMetadata]:
        """
        获取工具的元数据
        """
        if tool_name in self.tools:
            return self.tools[tool_name]['metadata']
        return None
    
    def list_tools(self) -> List[str]:
        """
        列出所有可用的工具
        """
        return list(self.tools.keys())
    
    async def request_assistance(self, target_agent: str, task: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        请求其他Agent的协助
        """
        async with self.a2a_communicator as communicator:
            return await communicator.request_assistance(target_agent, task, params)
    
    async def get_embeddings(self, texts: List[str], model: str = "sentence-transformers/all-MiniLM-L6-v2") -> List[List[float]]:
        """
        获取文本嵌入向量
        """
        async with self.mcp_client as client:
            return await client.get_embeddings(texts, model)
    
    async def generate_text(self, prompt: str, model: str = "gpt-3.5-turbo", params: Optional[Dict[str, Any]] = None) -> str:
        """
        生成文本
        """
        async with self.mcp_client as client:
            return await client.generate_text(prompt, model, params)
    
    def store_memory(self, key: str, value: Any, memory_type: str = "short_term", 
                     tags: List[str] = None, importance: float = 0.5, ttl_seconds: Optional[int] = None):
        """
        存储记忆
        """
        from .context import MemoryType
        memory_type_enum = MemoryType.__members__.get(memory_type.upper(), MemoryType.SHORT_TERM)
        self.context.memory.store(key, value, memory_type_enum, tags, importance, ttl_seconds)
    
    def retrieve_memory(self, key: str) -> Optional[Any]:
        """
        检索记忆
        """
        return self.context.memory.retrieve(key)
    
    def search_memories_by_tags(self, tags: List[str]) -> List[Any]:
        """
        根据标签搜索记忆
        """
        entries = self.context.memory.search_by_tags(tags)
        return [entry.value for entry in entries]
    
    def search_memories_by_type(self, memory_type: str) -> List[Any]:
        """
        根据类型搜索记忆
        """
        from .context import MemoryType
        memory_type_enum = MemoryType.__members__.get(memory_type.upper(), MemoryType.SHORT_TERM)
        entries = self.context.memory.search_by_type(memory_type_enum)
        return [entry.value for entry in entries]
    
    async def learn_new_skill(self, skill_description: str, examples: List[Dict[str, Any]]) -> str:
        """
        让Agent学习新技能
        """
        # 这里可以调用Rust内核的学习功能
        # 暂时使用模拟实现
        skill_id = f"learned:{uuid.uuid4().hex[:8]}"
        
        # 存储学习示例作为记忆
        for i, example in enumerate(examples):
            self.store_memory(
                f"skill_learning_example_{skill_id}_{i}",
                {
                    "input": example.get("input"),
                    "expected_output": example.get("expected_output"),
                    "context": example.get("context", {})
                },
                "long_term",
                tags=["skill_learning", skill_id],
                importance=0.9
            )
        
        # 存储技能定义
        self.store_memory(
            f"skill_definition_{skill_id}",
            {
                "description": skill_description,
                "examples_count": len(examples),
                "created_at": datetime.utcnow().isoformat()
            },
            "long_term",
            tags=["skill_definition", skill_id],
            importance=1.0
        )
        
        return skill_id
    
    async def adapt_to_context(self, context_description: str) -> List[str]:
        """
        根据上下文自适应，返回推荐的技能列表
        """
        # 搜索与上下文相关的记忆
        context_related = self.search_memories_by_tags([context_description.lower()])
        
        # 分析记忆以推荐相关技能
        recommended_skills = []
        
        # 这里可以实现更复杂的上下文分析逻辑
        # 暂时返回一些通用技能
        if "calculate" in context_description.lower() or "math" in context_description.lower():
            recommended_skills.extend(["calculate", "simple_calculator"])
        
        if "search" in context_description.lower() or "find" in context_description.lower():
            recommended_skills.extend(["web_search"])
        
        if "analyze" in context_description.lower() or "text" in context_description.lower():
            recommended_skills.extend(["analyze_text"])
        
        # 检查推荐的技能是否已注册
        available_skills = self.list_tools()
        final_recommendations = [skill for skill in recommended_skills if skill in available_skills]
        
        return final_recommendations
    
    async def improve_existing_skill(self, skill_name: str, feedback: Dict[str, Any]) -> bool:
        """
        根据反馈改进现有技能
        """
        if skill_name not in self.tools:
            return False
        
        # 存储反馈作为改进依据
        feedback_id = f"feedback_{skill_name}_{int(datetime.utcnow().timestamp())}"
        self.store_memory(
            feedback_id,
            {
                "skill_name": skill_name,
                "feedback": feedback,
                "timestamp": datetime.utcnow().isoformat()
            },
            "long_term",
            tags=["skill_improvement", skill_name],
            importance=0.8
        )
        
        # 这里可以实现技能优化逻辑
        # 暂时只记录反馈
        print(f"Recorded improvement feedback for skill '{skill_name}'")
        return True

# 用于注册Agent的装饰器
def agent(name: Optional[str] = None, description: str = ""):
    """
    装饰器：注册Agent类
    """
    def decorator(cls):
        agent_name = name or cls.__name__
        _global_agents_registry[agent_name] = {
            'cls': cls,
            'description': description
        }
        return cls
    return decorator