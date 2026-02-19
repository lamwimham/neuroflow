"""
NeuroFlow SDK - LLM 增强版

直接在 Agent 中集成 LLM 能力，无需依赖 MCP 服务
"""

import asyncio
import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai"  # openai, anthropic, ollama, etc.
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    
    def __post_init__(self):
        # 自动从环境变量获取 API Key
        if not self.api_key:
            if self.provider == "openai":
                self.api_key = os.getenv("OPENAI_API_KEY")
            elif self.provider == "anthropic":
                self.api_key = os.getenv("ANTHROPIC_API_KEY")


class LLMClient:
    """
    原生 LLM 客户端 - 直接调用各大 LLM 服务
    
    支持:
    - OpenAI (GPT-3.5, GPT-4)
    - Anthropic (Claude)
    - Ollama (本地模型)
    - 其他 OpenAI 兼容服务
    """
    
    def __init__(self, config: Optional[LLMConfig] = None):
        self.config = config or LLMConfig()
        self._session = None
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        对话式调用 LLM
        
        Args:
            messages: 对话历史 [{"role": "user", "content": "..."}]
            **kwargs: 额外参数
        
        Returns:
            LLM 回复的文本
        """
        if self.config.provider == "openai":
            return await self._call_openai(messages, **kwargs)
        elif self.config.provider == "anthropic":
            return await self._call_anthropic(messages, **kwargs)
        elif self.config.provider == "ollama":
            return await self._call_ollama(messages, **kwargs)
        else:
            raise ValueError(f"Unsupported provider: {self.config.provider}")
    
    async def _call_openai(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用 OpenAI API"""
        try:
            import openai
        except ImportError:
            raise ImportError("Please install openai: pip install openai")
        
        client = openai.AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url
        )
        
        response = await client.chat.completions.create(
            model=self.config.model,
            messages=messages,
            temperature=kwargs.get("temperature", self.config.temperature),
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens)
        )
        
        return response.choices[0].message.content
    
    async def _call_anthropic(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用 Anthropic API"""
        try:
            from anthropic import AsyncAnthropic
        except ImportError:
            raise ImportError("Please install anthropic: pip install anthropic")
        
        client = AsyncAnthropic(api_key=self.config.api_key)
        
        # 转换消息格式
        system_message = ""
        chat_messages = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_message = msg["content"]
            else:
                chat_messages.append(msg)
        
        response = await client.messages.create(
            model=self.config.model,
            max_tokens=kwargs.get("max_tokens", self.config.max_tokens),
            system=system_message,
            messages=chat_messages
        )
        
        return response.content[0].text
    
    async def _call_ollama(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """调用 Ollama (本地模型)"""
        import aiohttp
        
        url = self.config.base_url or "http://localhost:11434/api/chat"
        
        payload = {
            "model": self.config.model,
            "messages": messages,
            "stream": False
        }
        
        async with aiohttp.ClientSession() as session:
            async with session.post(url, json=payload) as response:
                result = await response.json()
                return result["message"]["content"]
    
    async def complete(self, prompt: str, **kwargs) -> str:
        """
        完成式调用（简单模式）
        
        Args:
            prompt: 输入提示词
        
        Returns:
            LLM 生成的文本
        """
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(messages, **kwargs)


class LLMAgent:
    """
    基于 LLM 的 Agent 基类
    
    用法:
        @agent(name="chat_agent")
        class ChatAgent(LLMAgent):
            async def handle(self, request: dict) -> dict:
                # 直接使用 self.llm 调用 LLM
                response = await self.llm.complete(request.get("prompt"))
                return {"response": response}
    """
    
    def __init__(self, name: str, description: str = "", 
                 llm_config: Optional[LLMConfig] = None):
        self.name = name
        self.description = description
        self.llm = LLMClient(llm_config)
        self.tools = {}
    
    async def handle(self, request: dict) -> dict:
        """
        处理请求（子类必须实现）
        
        Args:
            request: 请求字典
        
        Returns:
            响应字典
        """
        raise NotImplementedError("Subclasses must implement handle()")
    
    async def chat_with_context(self, 
                                 user_message: str,
                                 system_prompt: str = "",
                                 history: Optional[List[Dict]] = None) -> str:
        """
        带上下文的对话
        
        Args:
            user_message: 用户消息
            system_prompt: 系统提示词
            history: 对话历史
        
        Returns:
            LLM 回复
        """
        messages = []
        
        # 添加系统消息
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        
        # 添加历史消息
        if history:
            messages.extend(history)
        
        # 添加当前消息
        messages.append({"role": "user", "content": user_message})
        
        return await self.llm.chat(messages)
    
    async def execute_tool(self, tool_name: str, **kwargs) -> Any:
        """执行工具"""
        if tool_name not in self.tools:
            raise ValueError(f"Tool '{tool_name}' not found")
        
        tool_func = self.tools[tool_name]
        
        if asyncio.iscoroutinefunction(tool_func):
            return await tool_func(**kwargs)
        else:
            return tool_func(**kwargs)
    
    def register_tool(self, func, name: str = None):
        """注册工具"""
        tool_name = name or func.__name__
        self.tools[tool_name] = func


# 装饰器
def agent(name: str, description: str = "", llm_config: Optional[LLMConfig] = None):
    """
    Agent 装饰器（LLM 增强版）
    
    用法:
        @agent(name="my_agent", llm_config=LLMConfig(provider="openai", model="gpt-4"))
        class MyAgent(LLMAgent):
            async def handle(self, request: dict) -> dict:
                response = await self.llm.complete(request.get("prompt"))
                return {"response": response}
    """
    def decorator(cls):
        # 保存原始类
        original_init = cls.__init__
        
        def new_init(self, *args, **kwargs):
            # 调用原始初始化
            if hasattr(original_init, '__wrapped__'):
                original_init(self, *args, **kwargs)
            else:
                # 如果没有自定义初始化，调用父类
                super(cls, self).__init__(
                    name=name,
                    description=description,
                    llm_config=llm_config
                )
            
            # 自动注册已装饰的方法为工具
            for attr_name in dir(self):
                attr = getattr(self, attr_name)
                if hasattr(attr, 'tool_metadata'):
                    meta = attr.tool_metadata
                    self.register_tool(attr, meta.get('name', attr_name))
        
        cls.__init__ = new_init
        return cls
    
    return decorator


def tool(name: str = None, description: str = ""):
    """工具装饰器"""
    def decorator(func):
        func.tool_metadata = {
            'name': name or func.__name__,
            'description': description
        }
        return func
    return decorator


# 便捷函数
async def get_llm(config: Optional[LLMConfig] = None) -> LLMClient:
    """获取 LLM 客户端"""
    return LLMClient(config or LLMConfig())
