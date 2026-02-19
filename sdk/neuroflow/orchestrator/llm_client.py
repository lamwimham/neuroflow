"""
NeuroFlow Python SDK - LLM Client

增强的 LLM 客户端，支持 Function Calling
支持：OpenAI, Anthropic, Ollama 等
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum
import json
import logging

logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """LLM 提供商"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    OLLAMA = "ollama"
    CUSTOM = "custom"


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: LLMProvider = LLMProvider.OPENAI
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def __post_init__(self):
        """自动从环境变量获取 API Key"""
        if not self.api_key:
            import os
            if self.provider == LLMProvider.OPENAI:
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == LLMProvider.ANTHROPIC:
                self.api_key = os.getenv("ANTHROPIC_API_KEY")


@dataclass
class Message:
    """消息"""
    role: str  # system, user, assistant, tool
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    tool_calls: Optional[List[Dict[str, Any]]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {"role": self.role, "content": self.content}
        if self.name:
            result["name"] = self.name
        if self.tool_call_id:
            result["tool_call_id"] = self.tool_call_id
        if self.tool_calls:
            result["tool_calls"] = self.tool_calls
        return result
    
    @classmethod
    def system(cls, content: str) -> "Message":
        """创建系统消息"""
        return cls(role="system", content=content)
    
    @classmethod
    def user(cls, content: str) -> "Message":
        """创建用户消息"""
        return cls(role="user", content=content)
    
    @classmethod
    def assistant(cls, content: str, tool_calls: Optional[List[Dict[str, Any]]] = None) -> "Message":
        """创建助手消息"""
        return cls(role="assistant", content=content, tool_calls=tool_calls)
    
    @classmethod
    def tool(cls, content: str, tool_call_id: str) -> "Message":
        """创建工具消息"""
        return cls(role="tool", content=content, tool_call_id=tool_call_id)


@dataclass
class LLMResponse:
    """LLM 响应"""
    content: str
    model: str
    usage: Optional[Dict[str, int]] = None
    tool_calls: Optional[List[Any]] = None
    finish_reason: Optional[str] = None
    raw_response: Optional[Any] = None
    
    def has_tool_calls(self) -> bool:
        """检查是否有工具调用"""
        return bool(self.tool_calls)


class LLMClient:
    """
    增强的 LLM 客户端 - 支持 Function Calling
    
    用法:
        client = LLMClient(LLMConfig(provider="openai", model="gpt-4"))
        
        # 带工具调用
        response = await client.chat(
            messages=[Message.user("计算 1+1")],
            tools=[...],
        )
        
        # 不带工具调用
        response = await client.chat(
            messages=[Message.user("你好")],
        )
    """
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self._session = None
    
    async def chat(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]] = None,
        tool_choice: str = "auto",  # auto, none, required, or specific tool name
        response_format: Optional[Dict[str, str]] = None,
        **kwargs,
    ) -> LLMResponse:
        """
        对话式调用 - 支持 Function Calling
        
        Args:
            messages: 消息历史
            tools: 工具 Schema 列表
            tool_choice: 工具选择策略
            response_format: 响应格式 (如 JSON)
            **kwargs: 额外参数
            
        Returns:
            LLM 响应
        """
        if self.config.provider == LLMProvider.OPENAI:
            return await self._call_openai(
                messages, tools, tool_choice, response_format, **kwargs
            )
        elif self.config.provider == LLMProvider.ANTHROPIC:
            return await self._call_anthropic(
                messages, tools, **kwargs
            )
        elif self.config.provider == LLMProvider.OLLAMA:
            return await self._call_ollama(
                messages, tools, **kwargs
            )
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    async def _call_openai(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        tool_choice: str,
        response_format: Optional[Dict[str, str]],
        **kwargs,
    ) -> LLMResponse:
        """OpenAI 调用"""
        try:
            import openai
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
        )
        
        # 构建请求
        request_params = {
            "model": self.config.model,
            "messages": [m.to_dict() for m in messages],
            "temperature": kwargs.get("temperature", self.config.temperature),
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
        }
        
        # 添加工具
        if tools:
            request_params["tools"] = tools
            if tool_choice != "auto":
                if tool_choice == "none":
                    request_params["tool_choice"] = "none"
                elif tool_choice == "required":
                    request_params["tool_choice"] = "required"
                else:
                    request_params["tool_choice"] = {
                        "type": "function", 
                        "function": {"name": tool_choice}
                    }
        
        # 设置响应格式
        if response_format:
            request_params["response_format"] = response_format
        
        response = await client.chat.completions.create(**request_params)
        
        choice = response.choices[0]
        message = choice.message
        
        return LLMResponse(
            content=message.content or "",
            model=response.model,
            usage={
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            } if response.usage else None,
            tool_calls=message.tool_calls,
            finish_reason=choice.finish_reason,
            raw_response=response,
        )
    
    async def _call_anthropic(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        """Anthropic Claude 调用 - 支持 Tool Use"""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        
        client = AsyncAnthropic(api_key=self.config.api_key)
        
        # 分离系统消息
        system_message = ""
        chat_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                chat_messages.append(msg.to_dict())
        
        # 构建请求
        request_params = {
            "model": self.config.model,
            "max_tokens": kwargs.get("max_tokens", self.config.max_tokens),
            "messages": chat_messages,
        }
        
        if system_message:
            request_params["system"] = system_message
        
        # 添加工具 (Claude 的工具格式)
        if tools:
            request_params["tools"] = [
                {
                    "name": t["function"]["name"],
                    "description": t["function"]["description"],
                    "input_schema": t["function"]["parameters"],
                }
                for t in tools
            ]
        
        response = await client.messages.create(**request_params)
        
        # 提取内容
        tool_calls = []
        content_text = ""
        
        for block in response.content:
            if hasattr(block, 'type') and block.type == "text":
                content_text += block.text
            elif hasattr(block, 'type') and block.type == "tool_use":
                tool_calls.append(block)
        
        return LLMResponse(
            content=content_text,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
            tool_calls=tool_calls if tool_calls else None,
        )
    
    async def _call_ollama(
        self,
        messages: List[Message],
        tools: Optional[List[Dict[str, Any]]],
        **kwargs,
    ) -> LLMResponse:
        """Ollama 调用"""
        import aiohttp
        
        url = self.config.base_url or "http://localhost:11434/api/chat"
        
        payload = {
            "model": self.config.model,
            "messages": [m.to_dict() for m in messages],
            "stream": False,
        }
        
        # Ollama 的工具支持还在实验中
        if tools:
            payload["tools"] = tools
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                
                return LLMResponse(
                    content=result["message"]["content"],
                    model=self.config.model,
                    usage=result.get("usage"),
                )
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """
        简单完成式调用
        
        Args:
            prompt: 提示词
            
        Returns:
            生成的文本
        """
        messages = [Message.user(prompt)]
        response = await self.chat(messages, **kwargs)
        return response.content


__all__ = [
    "LLMProvider",
    "LLMConfig",
    "Message",
    "LLMResponse",
    "LLMClient",
]
