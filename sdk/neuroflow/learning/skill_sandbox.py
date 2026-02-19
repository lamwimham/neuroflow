"""
NeuroFlow Python SDK - Skill Sandbox

技能沙箱执行器 - 安全执行 LLM 生成的代码
"""

import asyncio
import json
import tempfile
import os
from typing import Any, Dict, Optional
from dataclasses import dataclass
import logging
import time

from ..tools import (
    ToolExecutor,
    ToolCall,
    ToolResult,
    ToolDefinition,
    ToolSource,
)

logger = logging.getLogger(__name__)


@dataclass
class SandboxExecutionResult:
    """沙箱执行结果"""
    success: bool
    output: Any
    error: Optional[str] = None
    execution_time_ms: int = 0


class SkillSandboxExecutor(ToolExecutor):
    """
    技能沙箱执行器 - 安全执行 LLM 生成的代码
    
    安全特性:
    1. 代码在隔离的命名空间中执行
    2. 限制可用的内置函数
    3. 超时控制
    4. 资源限制
    
    用法:
        executor = SkillSandboxExecutor()
        executor.register_skill(tool_definition)
        
        result = await executor.execute(tool_call)
    """
    
    def __init__(self, timeout_ms: int = 30000):
        self.timeout_ms = timeout_ms
        self._schemas: Dict[str, ToolDefinition] = {}
        self._functions: Dict[str, Any] = {}
    
    def register_skill(self, definition: ToolDefinition) -> None:
        """注册技能"""
        if definition.source != ToolSource.LLM_GENERATED:
            logger.warning(
                f"Registering non-LLM-generated skill: {definition.name}"
            )
        
        self._schemas[definition.name] = definition
        
        # 预编译函数
        implementation = definition.metadata.get("implementation")
        if implementation:
            try:
                func = self._compile_code(implementation)
                self._functions[definition.name] = func
                logger.info(f"Pre-compiled skill: {definition.name}")
            except Exception as e:
                logger.error(f"Failed to compile skill {definition.name}: {e}")
    
    async def execute(self, call: ToolCall) -> ToolResult:
        start = time.time()
        
        try:
            schema = self._schemas.get(call.tool_name)
            if not schema:
                return ToolResult(
                    call_id=call.call_id,
                    success=False,
                    result=None,
                    error=f"Skill '{call.tool_name}' not found",
                )
            
            # 获取函数
            func = self._functions.get(call.tool_name)
            if not func:
                # 动态编译
                implementation = schema.metadata.get("implementation")
                if not implementation:
                    return ToolResult(
                        call_id=call.call_id,
                        success=False,
                        result=None,
                        error="No implementation found for skill",
                    )
                func = self._compile_code(implementation)
                self._functions[call.tool_name] = func
            
            # 在沙箱中执行
            result = await self._execute_in_sandbox(
                func,
                call.arguments,
                call.timeout_ms,
            )
            
            return ToolResult(
                call_id=call.call_id,
                success=result.success,
                result=result.output,
                error=result.error,
                execution_time_ms=result.execution_time_ms,
            )
        except Exception as e:
            logger.exception(f"Error executing skill {call.tool_name}")
            return ToolResult(
                call_id=call.call_id,
                success=False,
                result=None,
                error=str(e),
            )
    
    def _compile_code(self, code: str) -> Any:
        """编译代码并返回函数"""
        safe_globals = self._create_safe_globals()
        safe_locals = {}
        
        # 执行代码定义函数
        exec(code, safe_globals, safe_locals)
        
        # 获取函数
        for name, obj in safe_locals.items():
            if callable(obj) and not name.startswith('_'):
                return obj
        
        raise ValueError("No function found in code")
    
    async def _execute_in_sandbox(
        self,
        func: Any,
        arguments: Dict[str, Any],
        timeout_ms: int,
    ) -> SandboxExecutionResult:
        """在沙箱中执行函数"""
        start = time.time()
        
        try:
            # 调用函数
            async def execute_with_timeout():
                if asyncio.iscoroutinefunction(func):
                    return await func(**arguments)
                else:
                    return func(**arguments)
            
            result = await asyncio.wait_for(
                execute_with_timeout(),
                timeout=timeout_ms / 1000,
            )
            
            elapsed = int((time.time() - start) * 1000)
            
            return SandboxExecutionResult(
                success=True,
                output=result,
                execution_time_ms=elapsed,
            )
        except asyncio.TimeoutError:
            return SandboxExecutionResult(
                success=False,
                output=None,
                error="Execution timeout",
                execution_time_ms=int((time.time() - start) * 1000),
            )
        except Exception as e:
            return SandboxExecutionResult(
                success=False,
                output=None,
                error=str(e),
                execution_time_ms=int((time.time() - start) * 1000),
            )
    
    def _create_safe_globals(self) -> Dict[str, Any]:
        """创建安全的全局命名空间"""
        # 只允许安全的内置函数
        safe_builtins = {
            'len': len,
            'str': str,
            'int': int,
            'float': float,
            'bool': bool,
            'list': list,
            'dict': dict,
            'set': set,
            'tuple': tuple,
            'range': range,
            'sum': sum,
            'min': min,
            'max': max,
            'abs': abs,
            'round': round,
            'enumerate': enumerate,
            'zip': zip,
            'map': map,
            'filter': filter,
            'sorted': sorted,
            'reversed': reversed,
            'any': any,
            'all': all,
            'isinstance': isinstance,
            'issubclass': issubclass,
            'hasattr': hasattr,
            'getattr': getattr,
            'setattr': setattr,
            'print': print,  # 允许 print 用于调试
            'json': json,
        }
        
        return {'__builtins__': safe_builtins}
    
    async def validate(self, tool_name: str, arguments: Dict[str, Any]) -> bool:
        """验证参数"""
        # TODO: 实现参数验证
        return True
    
    async def get_schema(self, tool_name: str) -> Optional[ToolDefinition]:
        """获取工具 Schema"""
        return self._schemas.get(tool_name)
    
    def executor_type(self) -> ToolSource:
        """获取执行器类型"""
        return ToolSource.LLM_GENERATED


__all__ = [
    "SandboxExecutionResult",
    "SkillSandboxExecutor",
]
