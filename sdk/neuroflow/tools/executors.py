"""
NeuroFlow Python SDK - Tool Executors

工具执行器实现:
- LocalFunctionExecutor: 本地 Python 函数
- MCPToolExecutor: MCP 服务
- SkillExecutor: Rust Skills
"""

import asyncio
import aiohttp
import time
from typing import Any, Dict, List, Optional
import logging

from .protocol import (
    ToolExecutor,
    ToolCall,
    ToolResult,
    ToolDefinition,
    ToolParameter,
    ToolSource,
    ToolExecutionMode,
    UnifiedToolRegistry,
)

logger = logging.getLogger(__name__)


class LocalFunctionExecutor(ToolExecutor):
    """本地函数执行器"""
    
    def __init__(self):
        self._functions: Dict[str, callable] = {}
        self._schemas: Dict[str, ToolDefinition] = {}
    
    def register_function(self, func: callable, schema: ToolDefinition) -> None:
        """注册本地函数"""
        self._functions[schema.name] = func
        self._schemas[schema.name] = schema
    
    async def execute(self, call: ToolCall) -> ToolResult:
        start = time.time()
        
        try:
            func = self._functions.get(call.tool_name)
            if not func:
                return ToolResult(
                    call_id=call.call_id,
                    success=False,
                    result=None,
                    error=f"Function '{call.tool_name}' not found",
                )
            
            if asyncio.iscoroutinefunction(func):
                result = await func(**call.arguments)
            else:
                result = func(**call.arguments)
            
            elapsed = int((time.time() - start) * 1000)
            
            return ToolResult(
                call_id=call.call_id,
                success=True,
                result=result,
                execution_time_ms=elapsed,
            )
        except Exception as e:
            logger.exception(f"Error executing function {call.tool_name}")
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error=str(e),
            )
    
    async def validate(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        # TODO: 实现参数验证
        return True
    
    async def get_schema(self, tool_name: str) -> Optional[ToolDefinition]:
        return self._schemas.get(tool_name)
    
    def executor_type(self) -> ToolSource:
        return ToolSource.LOCAL_FUNCTION


class MCPToolExecutor(ToolExecutor):
    """MCP 工具执行器"""
    
    def __init__(self, mcp_endpoint: str = "http://localhost:8081"):
        self._mcp_endpoint = mcp_endpoint
        self._schemas: Dict[str, ToolDefinition] = {}
        self._tool_mappings: Dict[str, str] = {}  # tool_name -> server_url
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def discover_tools(self, server_url: Optional[str] = None) -> List[ToolDefinition]:
        """从 MCP 服务器发现工具"""
        url = server_url or self._mcp_endpoint
        
        try:
            session = await self._ensure_session()
            async with session.get(f"{url}/tools") as response:
                if response.status == 200:
                    tools_data = await response.json()
                    tools = []
                    
                    for tool_data in tools_data:
                        # 转换为 ToolDefinition
                        params = [
                            ToolParameter(
                                name=p.get("name", ""),
                                parameter_type=p.get("type", "string"),
                                description=p.get("description", ""),
                                required=p.get("required", True),
                                default_value=p.get("default"),
                            )
                            for p in tool_data.get("parameters", [])
                        ]
                        
                        definition = ToolDefinition(
                            id=tool_data.get("id", tool_data.get("name")),
                            name=tool_data.get("name"),
                            description=tool_data.get("description"),
                            source=ToolSource.MCP_SERVER,
                            parameters=params,
                            metadata={"server_url": url},
                        )
                        
                        self._schemas[definition.name] = definition
                        self._tool_mappings[definition.name] = url
                        tools.append(definition)
                    
                    logger.info(f"Discovered {len(tools)} tools from MCP server at {url}")
                    return tools
        except Exception as e:
            logger.error(f"Failed to discover MCP tools: {e}")
        
        return []
    
    async def execute(self, call: ToolCall) -> ToolResult:
        start = time.time()
        
        try:
            session = await self._ensure_session()
            server_url = self._tool_mappings.get(
                call.tool_name, 
                self._mcp_endpoint
            )
            
            async with session.post(
                f"{server_url}/tools/invoke",
                json={
                    "toolName": call.tool_name,
                    "arguments": call.arguments,
                    "timeoutMs": call.timeout_ms,
                },
                timeout=aiohttp.ClientTimeout(total=call.timeout_ms / 1000),
            ) as response:
                elapsed = int((time.time() - start) * 1000)
                
                if response.status == 200:
                    result = await response.json()
                    return ToolResult(
                        call_id=call.call_id,
                        success=True,
                        result=result,
                        execution_time_ms=elapsed,
                    )
                else:
                    error_text = await response.text()
                    return ToolResult(
                        call_id=call.call_id,
                        success=False,
                        result=None,
                        error=f"MCP error: {error_text}",
                        execution_time_ms=elapsed,
                    )
        except asyncio.TimeoutError:
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error="MCP request timeout",
            )
        except Exception as e:
            logger.exception(f"Error executing MCP tool {call.tool_name}")
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error=str(e),
            )
    
    async def validate(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        return True
    
    async def get_schema(self, tool_name: str) -> Optional[ToolDefinition]:
        return self._schemas.get(tool_name)
    
    def executor_type(self) -> ToolSource:
        return ToolSource.MCP_SERVER


class SkillExecutor(ToolExecutor):
    """Rust Skills 执行器 - 通过 HTTP 调用 Kernel"""
    
    def __init__(self, kernel_endpoint: str = "http://localhost:8080"):
        self._kernel_endpoint = kernel_endpoint
        self._schemas: Dict[str, ToolDefinition] = {}
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        if not self._session or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def load_skills(self) -> List[ToolDefinition]:
        """从 Kernel 加载 Skills"""
        try:
            session = await self._ensure_session()
            async with session.get(f"{self._kernel_endpoint}/tools") as response:
                if response.status == 200:
                    result = await response.json()
                    tools_data = result.get("tools", [])
                    
                    tools = []
                    for tool_data in tools_data:
                        # 检查是否是 Skill 类型的工具
                        # TODO: 根据实际 API 调整
                        pass
                    
                    return tools
        except Exception as e:
            logger.error(f"Failed to load skills: {e}")
        
        return []
    
    async def execute(self, call: ToolCall) -> ToolResult:
        start = time.time()
        
        try:
            session = await self._ensure_session()
            
            async with session.post(
                f"{self._kernel_endpoint}/tools/invoke",
                json={
                    "toolName": call.tool_name,
                    "arguments": call.arguments,
                    "timeoutMs": call.timeout_ms,
                },
                timeout=aiohttp.ClientTimeout(total=call.timeout_ms / 1000),
            ) as response:
                elapsed = int((time.time() - start) * 1000)
                
                if response.status == 200:
                    result = await response.json()
                    return ToolResult(
                        call_id=call.call_id,
                        success=result.get("success", False),
                        result=result.get("result"),
                        error=result.get("error"),
                        execution_time_ms=elapsed,
                    )
                else:
                    error_text = await response.text()
                    return ToolResult(
                        call_id=call.call_id,
                        success=False,
                        result=None,
                        error=f"Skill error: {error_text}",
                        execution_time_ms=elapsed,
                    )
        except Exception as e:
            logger.exception(f"Error executing skill {call.tool_name}")
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error=str(e),
            )
    
    async def validate(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        return True
    
    async def get_schema(self, tool_name: str) -> Optional[ToolDefinition]:
        return self._schemas.get(tool_name)
    
    def executor_type(self) -> ToolSource:
        return ToolSource.SKILL


__all__ = [
    "LocalFunctionExecutor",
    "MCPToolExecutor",
    "SkillExecutor",
]
